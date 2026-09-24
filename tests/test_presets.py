"""Presets: Vollständigkeit, gültige Werte, der Median der Elementarschritte der gewählten Umsetzung bleibt bei den Karten-Presets in der gemessenen Spannweite, und jedes Preset zeigt,
was sein Name und sein Hilfetext sagen."""

import pytest

import prim_algorithm as A
import prim_constants as C
import prim_evaluation as ev
import prim_presets as P


def _settings(p):
    return ev.Settings(kind=p["kind"], n=p["n"], k=p["k"], terrain=p["terrain"], round_costs=p["round_costs"], seed=p["seed"], variant=p["variant"], start=p["start"])


def _analyse(name):
    return ev.analyse(_settings(C.PRESETS[name]))


def test_every_preset_has_help_and_the_map_presets_a_band():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 8
    for name, p in C.PRESETS.items():
        assert set(p) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]
    assert set(C.PRESET_EXPECTED_BANDS) <= {n for n, p in C.PRESETS.items() if p["kind"] == "depot"}


def test_preset_values_are_valid_members_of_the_controls():
    for p in C.PRESETS.values():
        assert p["kind"] in C.KINDS and p["k"] in C.K_OPTIONS and p["terrain"] in C.TERRAIN_OPTIONS and p["variant"] in C.VARIANTS and p["start"] in C.STARTS
        assert C.N_MIN <= p["n"] <= C.N_MAX and 0 <= p["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings_with_the_default_variant():
    assert _settings(C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings(variant=C.DEFAULT_VARIANT)
    assert P.SETTING_SPECS["variant_select"].default == C.DEFAULT_VARIANT


@pytest.mark.parametrize("name", list(C.PRESET_EXPECTED_BANDS))
def test_map_preset_median_ops_stay_in_the_measured_band(name):
    p = C.PRESETS[name]
    lo, hi = C.PRESET_EXPECTED_BANDS[name]
    assert lo <= ev.run_config(_settings(p))[f"ops_{p['variant']}"] <= hi


def test_standard_preset_numbers():
    a = _analyse("Standardfall (Voreinstellung)")
    assert a.ops == {"lazy": 1282, "eager": 413, "array": 548, "kruskal": 929} and a.winner == "eager" and a.same_tree and a.prim.cost == pytest.approx(466.63, abs=0.01)
    assert round(a.rank_correlation, 2) == 0.47


def test_thin_network_preset():
    a = _analyse("Dünnes Netz (k = 3)")
    assert a.inst.m == 59 and a.ops == {"lazy": 466, "eager": 249, "array": 494, "kruskal": 456}


def test_dense_presets_favour_the_array():
    a, b = _analyse("Dichter Graph (k = 20)"), _analyse("Vollständiger Graph (n = 30)")
    assert (a.inst.m, a.winner, a.ops["array"], a.ops["eager"], a.ops["lazy"], a.ops["kruskal"]) == (361, "array", 796, 841, 2848, 3009)
    assert (b.inst.m, b.winner, b.ops["array"], b.ops["eager"], b.ops["lazy"], b.ops["kruskal"]) == (465, "array", 900, 977, 3298, 3913)
    assert (b.prims["lazy"].max_heap, b.prims["lazy"].stale_pops, b.prims["eager"].max_heap) == (410, 79, 30) and a.prims["lazy"].max_heap == 307 and a.prims["eager"].max_heap == 26


def test_big_preset():
    a = _analyse("Große Instanz (n = 160, vollständig)")
    assert (a.inst.m, a.winner) == (12880, "eager") and a.ops == {"lazy": 66602, "eager": 19071, "array": 25600, "kruskal": 162373}
    assert (a.prims["lazy"].max_heap, a.prims["eager"].max_heap) == (12532, 160) and round(a.rank_correlation, 2) == 0.12


def test_far_start_preset_changes_the_order_not_the_tree():
    a, s = _analyse("Start weit weg"), _analyse("Standardfall (Voreinstellung)")
    assert a.start == 13 and round(a.rank_correlation, 2) == 0.06 and sorted(a.prim.tree) == sorted(s.prim.tree)
    assert max(x[3] for x in a.prim.steps) == 34 and max(x[3] for x in s.prim.steps) == 41


def test_ties_preset_still_gives_the_same_tree_for_every_start_and_variant():
    a = _analyse("Gleichstände (gerundet)")
    assert a.prim.cost == 467.0 and a.same_tree
    for variant in C.VARIANTS:
        assert ev.start_invariance(a.inst, variant)[0] == 0.0


def test_textbook_preset():
    a = _analyse("Lehrbuchbeispiel")
    assert a.ops == {"lazy": 24, "eager": 17, "array": 13, "kruskal": 26} and a.winner == "array" and a.prim.cost == 15.0
    assert [a.inst.edges[i][:2] for i in a.prim.tree] == [(0, 1), (1, 3), (1, 2), (2, 4)] and [a.inst.edges[i][:2] for i in a.kruskal.tree] == [(1, 3), (2, 4), (0, 1), (1, 2)]


def test_bounds_and_permalink_constants():
    assert P.bounds("n_slider") == (C.N_MIN, C.N_MAX) and P.bounds("seed_input") == (0, C.SEED_MAX)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)


def test_permalink_casters_accept_members_and_reject_everything_else():
    c = P.SETTING_SPECS
    assert c["variant_select"].caster("array") == "array" and c["start_select"].caster("far") == "far" and c["k_select"].caster("1000") == 1000
    assert c["round_select"].caster("true") is True and c["round_select"].caster("False") is False
    for key, bad in (("kind_select", "x"), ("k_select", "7"), ("terrain_select", "0.35"), ("round_select", "maybe"), ("variant_select", "x"), ("start_select", "x")):
        with pytest.raises(ValueError):
            c[key].caster(bad)
