"""Auswertung: Analysis-Felder gegen unabhängige Neuberechnung, Gewinner, Start-Invarianz, run_config/sweep."""

import math

import pytest

import prim_algorithm as A
import prim_constants as C
import prim_evaluation as ev
import prim_scenario as S

SMALL = dict(seeds=C.SWEEP_SEEDS[:2])


def test_default_settings_come_from_the_constants_and_are_members_of_the_controls():
    s = ev.Settings()
    assert (s.n, s.k, s.terrain, s.seed) == (C.DEFAULT_N, C.DEFAULT_K, C.DEFAULT_TERRAIN, C.DEFAULT_SEED)
    assert s.k in C.K_OPTIONS and s.terrain in C.TERRAIN_OPTIONS and s.variant in C.VARIANTS and s.start in C.STARTS and s.kind in C.KINDS and C.DEFAULT_VARIANT in C.VARIANTS
    assert set(C.K_SWEEP) <= set(C.K_OPTIONS)


@pytest.mark.parametrize("seed", [35, 100001])
def test_analysis_fields_match_an_independent_recomputation(seed):
    a = ev.analyse(ev.Settings(seed=seed, variant="eager"))
    inst = S.generate(30, 6, 0.3, False, seed)
    for v in C.VARIANTS:
        assert a.prims[v].ops == A.prim(inst.n, inst.edges, v, 0).ops
    assert a.kruskal.ops == A.kruskal(inst.n, inst.edges).ops and a.prim is a.prims["eager"]
    assert a.same_tree and a.expected_decrease_keys == pytest.approx(inst.n * math.log(inst.m / inst.n))
    assert -1.0 <= a.rank_correlation <= 1.0 and a.ops["kruskal"] == a.kruskal.ops


def test_winner_is_the_cheapest_algorithm_with_a_deterministic_tie_break():
    a = ev.analyse(ev.Settings())
    assert a.ops[a.winner] == min(a.ops.values())
    assert ev.analyse(ev.Settings(kind="textbook")).winner == "array"


def test_start_choice_changes_the_start_node_the_order_and_never_the_tree():
    depot, far = ev.analyse(ev.Settings(start="depot")), ev.analyse(ev.Settings(start="far"))
    assert depot.start == 0 and far.start != 0 and depot.prim.tree != far.prim.tree and sorted(depot.prim.tree) == sorted(far.prim.tree)


def test_start_invariance_over_all_nodes():
    inst = ev.instance_of(ev.Settings(n=12))
    for variant in C.VARIANTS:
        differ, orders = ev.start_invariance(inst, variant)
        assert differ == 0.0 and orders > 1
    assert ev.start_invariance(inst, "lazy", starts=[0]) == (0.0, 1)


def test_kruskal_beats_the_array_on_a_sparse_tree_like_graph_and_the_array_beats_kruskal_on_dense_graphs():
    path = tuple((i, i + 1, float(i + 1)) for i in range(59))
    assert A.kruskal(60, path).ops < A.prim(60, path, "array").ops
    dense = S.generate(30, 1000, 0.3, False, 1)
    assert A.prim(dense.n, dense.edges, "array").ops < A.kruskal(dense.n, dense.edges).ops


def test_run_config_keys_ranges_and_base_seed_independence():
    r = ev.run_config(ev.Settings(seed=1), **SMALL)
    assert r["n_runs"] == 2 and r["same_tree_share"] == 100.0 and sum(r[f"wins_{a}"] for a in ev.ALGOS) == 2
    for key in ("ops_array", "ops_lazy", "ops_eager", "ops_kruskal", "edges", "lazy_over_kruskal", "array_over_kruskal", "eager_over_lazy", "max_heap_lazy", "max_heap_eager", "stale_pops",
                "decrease_keys", "expected_decrease_keys", "rank_correlation", "max_frontier"):
        assert r[f"{key}_lo"] <= r[key] <= r[f"{key}_hi"]
    assert r == pytest.approx(ev.run_config(ev.Settings(seed=999), **SMALL))


def test_sweep_rows_and_labels():
    rows = ev.sweep("n", ev.Settings(), values=(10, 20))
    assert [r["value"] for r in rows] == [10, 20] and rows[1]["ops_kruskal"] > rows[0]["ops_kruskal"]
    assert set(ev.SWEEP_VALUES) == set(ev.SWEEP_LABELS) == {"n", "k"}
