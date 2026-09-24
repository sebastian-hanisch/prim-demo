"""Auswertung: wann ist welche Prim-Umsetzung und wann Kruskal billiger? Vier Verfahren auf derselben Instanz: Prim mit Array (`array`), Prim mit binärem Heap aus Kanten (`lazy`), Prim mit
Heap aus Knoten und Decrease-Key (`eager`) und Kruskal (Sortieren + Union-Find). Alle liefern denselben Baum (Schlüssel = (Kosten, Kantenindex), strikte Ordnung). Aufwand in
**Elementarschritten** (Schlüsselvergleiche plus je eine Einheit je Heap-Operation bzw. Union-Find-Suche und Zeigerschritt), nicht in Laufzeit; das ist ein Näherungsmaß.
Alle Verfahren sind deterministisch: Kennzahlen laufen über 5 feste Instanzen (Seeds 100000-100004), Median mit 10./90. Perzentil.

- **Rand** = Kanten zwischen Baum und noch nicht angeschlossenen Knoten; **Heap** = tatsächlicher Bestand der Datenstruktur (lazy: Kanten inkl. veralteter, eager: Knoten).
- **Rang-Korrelation** = Spearman-Korrelation der Annahmereihenfolge der Baumkanten bei Prim und bei Kruskal (1 = gleiche Reihenfolge).
- **Decrease-Keys (Erwartung)** = n * ln(m / n), die bekannte Größenordnung bei zufälliger Kantenreihenfolge (Vergleichsgröße, keine Garantie für diese Instanzen)."""

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import prim_algorithm as A
import prim_constants as C
import prim_scenario as S

INF = float("inf")
ALGOS = ("array", "lazy", "eager", "kruskal")
ALGO_LABELS = {"array": "Prim (Array)", "lazy": "Prim (Heap, lazy)", "eager": "Prim (Heap, Decrease-Key)", "kruskal": "Kruskal"}


@dataclass(frozen=True)
class Settings:
    kind: str = "depot"
    n: int = C.DEFAULT_N
    k: int = C.DEFAULT_K
    terrain: float = C.DEFAULT_TERRAIN
    round_costs: bool = False
    seed: int = C.DEFAULT_SEED
    variant: str = "lazy"
    start: str = "depot"


@lru_cache(maxsize=512)
def _generate(n, k, terrain, round_costs, seed):
    return S.generate(n, k, terrain, round_costs, seed)


def instance_of(settings):
    if settings.kind == "textbook":
        return S.textbook_instance()
    return _generate(settings.n, settings.k, settings.terrain, settings.round_costs, settings.seed)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    start: int
    prims: dict               # variant -> PrimResult (alle drei, vom Startknoten aus)
    kruskal: A.KruskalResult

    @property
    def prim(self):
        return self.prims[self.settings.variant]

    @property
    def ops(self):
        out = {v: self.prims[v].ops for v in C.VARIANTS}
        out["kruskal"] = self.kruskal.ops
        return out

    @property
    def winner(self):
        ops = self.ops
        return min(ALGOS, key=lambda a: (ops[a], ALGOS.index(a)))

    @property
    def same_tree(self):
        return all(sorted(p.tree) == sorted(self.kruskal.tree) for p in self.prims.values())

    @property
    def rank_correlation(self):
        return A.spearman(self.kruskal.tree, self.prim.tree) if len(self.kruskal.tree) > 1 else 1.0

    @property
    def expected_decrease_keys(self):
        return A.expected_decrease_keys(self.inst.n, self.inst.m)


def analyse(settings):
    inst = instance_of(settings)
    start = A.start_node(inst, settings.start)
    prims = {v: A.prim(inst.n, inst.edges, v, start) for v in C.VARIANTS}
    return Analysis(settings, inst, start, prims, A.kruskal(inst.n, inst.edges))


def start_invariance(inst, variant="lazy", starts=None):
    """(Anteil der Startknoten, deren Baum vom Baum ab Knoten 0 abweicht, Zahl verschiedener Annahmereihenfolgen) über `starts` (Standard: alle Knoten)."""
    starts = range(inst.n) if starts is None else starts
    base = sorted(A.prim(inst.n, inst.edges, variant, 0).tree)
    differ, orders = 0, set()
    starts = list(starts)
    for s in starts:
        r = A.prim(inst.n, inst.edges, variant, s)
        differ += sorted(r.tree) != base
        orders.add(tuple(r.tree))
    return 100.0 * differ / max(1, len(starts)), len(orders)


# --- Sweeps ---------------------------------------------------------------------------------------------------------------------------------------


def _stats(values):
    values = [v for v in values if not np.isnan(v) and v != INF]
    if not values:
        return float("nan"), float("nan"), float("nan")
    return float(np.median(values)), float(np.percentile(values, 10)), float(np.percentile(values, 90))


def run_config(base, seeds=C.SWEEP_SEEDS, **changes):
    s0 = replace(base, **changes)
    rows = [analyse(replace(s0, seed=seed)) for seed in seeds]
    out = {"n_runs": len(rows), "same_tree_share": 100.0 * sum(r.same_tree for r in rows) / len(rows)}
    for a in ALGOS:
        out[f"wins_{a}"] = sum(r.winner == a for r in rows)
    for key, values in (
        *[(f"ops_{a}", [float(r.ops[a]) for r in rows]) for a in ALGOS],
        ("edges", [float(r.inst.m) for r in rows]),
        ("lazy_over_kruskal", [r.ops["lazy"] / r.ops["kruskal"] for r in rows]),
        ("array_over_kruskal", [r.ops["array"] / r.ops["kruskal"] for r in rows]),
        ("eager_over_lazy", [r.ops["eager"] / r.ops["lazy"] for r in rows]),
        ("max_heap_lazy", [float(r.prims["lazy"].max_heap) for r in rows]),
        ("max_heap_eager", [float(r.prims["eager"].max_heap) for r in rows]),
        ("stale_pops", [float(r.prims["lazy"].stale_pops) for r in rows]),
        ("decrease_keys", [float(r.prims["eager"].decrease_keys) for r in rows]),
        ("expected_decrease_keys", [r.expected_decrease_keys for r in rows]),
        ("rank_correlation", [r.rank_correlation for r in rows]),
        ("max_frontier", [float(max((s[3] for s in r.prim.steps), default=0)) for r in rows]),
    ):
        out[key], out[f"{key}_lo"], out[f"{key}_hi"] = _stats(values)
    return out


SWEEP_VALUES = {"n": C.N_SWEEP, "k": C.K_SWEEP}
SWEEP_LABELS = {"n": "Filialen n", "k": "Nächste Nachbarn k (dichter = größer)"}


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]
