"""Jede Zahl, die App-Text und README nennen, wird hier über die echten Auswertungsfunktionen (ev.run_config / ev.sweep / ev.start_invariance) belegt - nie über ein Ad-hoc-Skript.
Ränder statt Punktwerte dort, wo ein Wert von Platz zu Platz um Rundungsfehler schwanken könnte; die Elementarschritte selbst sind ganzzahlig und plattformunabhängig (eigener
Mergesort, eigener Heap)."""

from functools import lru_cache

import pytest

import prim_constants as C
import prim_evaluation as ev

BASE = ev.Settings(seed=0)


@lru_cache(maxsize=None)
def _cfg(**kw):
    return ev.run_config(ev.Settings(**{"seed": 0, **kw}))


@lru_cache(maxsize=None)
def _sweep(param, **kw):
    return ev.sweep(param, ev.Settings(**{"seed": 0, **kw}))


def _by(rows):
    return {r["value"]: r for r in rows}


def test_default_case_medians_over_five_instances():
    r = _cfg()
    assert (r["ops_array"], r["ops_lazy"], r["ops_eager"], r["ops_kruskal"]) == (552, 1157, 431, 947)
    assert r["eager_over_lazy"] == pytest.approx(0.368, abs=0.001)
    assert r["same_tree_share"] == 100.0


def test_kruskal_is_never_the_cheapest_and_lazy_never_wins_on_the_measured_grids():
    for rows in (_sweep("k"), _sweep("n"), _sweep("n", k=1000)):
        for r in rows:
            assert r["wins_kruskal"] == 0 and r["wins_lazy"] == 0


def test_density_sweep_winners_and_medians():
    rows = _by(_sweep("k"))
    for k in (3, 4, 6, 10):
        assert rows[k]["wins_eager"] == 5
    for k in (20, 1000):
        assert rows[k]["wins_array"] == 5
    assert [rows[k]["ops_array"] for k in C.K_SWEEP] == [495, 515, 552, 624, 802, 900]
    assert [rows[k]["ops_lazy"] for k in C.K_SWEEP] == [524, 750, 1157, 1642, 2409, 2747]
    assert [rows[k]["ops_eager"] for k in C.K_SWEEP] == [245, 297, 431, 599, 884, 1012]
    assert [rows[k]["ops_kruskal"] for k in C.K_SWEEP] == [446, 616, 947, 1521, 2992, 3805]


def test_lazy_heap_loses_to_kruskal_in_the_sparse_graph_and_kruskal_beats_the_array_only_at_k3():
    rows = _by(_sweep("k"))
    assert rows[3]["ops_lazy"] > rows[3]["ops_array"] > rows[3]["ops_kruskal"] > rows[3]["ops_eager"]
    assert rows[6]["ops_lazy"] > rows[6]["ops_kruskal"] and rows[3]["lazy_over_kruskal"] > 1.0
    assert all(rows[k]["ops_array"] < rows[k]["ops_kruskal"] for k in (4, 6, 10, 20, 1000))


def test_size_sweep_crossover_for_k6_and_complete_graphs():
    n6, nc = _by(_sweep("n")), _by(_sweep("n", k=1000))
    assert n6[10]["wins_array"] == 5 and n6[20]["wins_array"] == 3 and n6[20]["wins_eager"] == 2
    for n in (40, 80, 160):
        assert n6[n]["wins_eager"] == 5
    for n in (10, 20, 40):
        assert nc[n]["wins_array"] == 5
    for n in (80, 160):
        assert nc[n]["wins_eager"] == 5


def test_complete_graph_n160_heap_sizes_and_decrease_keys():
    r = ev.run_config(ev.Settings(n=160, k=1000, seed=0))
    assert (r["ops_eager"], r["ops_array"], r["ops_lazy"], r["ops_kruskal"]) == (19195, 25600, 57950, 161015)
    assert (r["max_heap_lazy"], r["max_heap_eager"]) == (12424, 160)
    assert r["decrease_keys"] == 1850 and r["expected_decrease_keys"] == pytest.approx(705.5, abs=0.1)


def test_decrease_key_count_exceeds_the_random_order_expectation_on_spatial_instances():
    r = _cfg()
    assert r["decrease_keys"] == 56 and r["expected_decrease_keys"] == pytest.approx(41.17, abs=0.01)
    assert r["stale_pops"] == 43 and (r["max_heap_lazy"], r["max_heap_eager"], r["max_frontier"]) == (68, 15, 42)


def test_acceptance_order_of_prim_and_kruskal_is_only_loosely_related():
    near, far = _cfg(), _cfg(start="far")
    assert near["rank_correlation"] == pytest.approx(0.40, abs=0.01) and far["rank_correlation"] == pytest.approx(0.10, abs=0.01)
    assert far["same_tree_share"] == 100.0


def test_start_node_never_changes_the_tree_but_changes_the_order():
    inst = ev.instance_of(ev.Settings())
    for variant in C.VARIANTS:
        differ, orders = ev.start_invariance(inst, variant)
        assert differ == 0.0 and orders == 22 and inst.n == 31


def test_ties_do_not_change_the_answer_the_tree_stays_identical_across_variants_and_kruskal():
    r = _cfg(round_costs=True)
    assert r["same_tree_share"] == 100.0
    inst = ev.instance_of(ev.Settings(round_costs=True, seed=35))
    assert all(ev.start_invariance(inst, v)[0] == 0.0 for v in C.VARIANTS)
