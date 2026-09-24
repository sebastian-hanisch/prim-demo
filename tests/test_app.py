"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt und jede Kante, beide Instanz-Typen, Randwerte, Würfel-Knopf, Permalink-Grenzen, Instanzwechsel,
Startknoten-Experiment und Sweeps auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import prim_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if step != 1:
        at.select_slider(key="prim_step").set_value(step).run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m.value for m in at.metric if m.label.startswith(label))


def test_default_run_has_no_exception_and_shows_the_four_metrics():
    at = _run()
    _ok(at)
    assert {"Gewinner", "Gewählte Umsetzung", "Kruskal", "Größter Heap"} <= {m.label for m in at.metric}
    assert _metric(at, "Gewinner") == "Decrease-Key" and _metric(at, "Gewählte") == "413" and _metric(at, "Kruskal") == "929"


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["kind_select"] == p["kind"] and at.session_state["variant_select"] == p["variant"] and at.session_state["start_select"] == p["start"]
    assert at.metric


@pytest.mark.parametrize("step", [1, 2, 3])
def test_every_step_runs_for_both_kinds(step):
    for kind in C.KINDS:
        at = _run(kind_select=kind, step=step)
        _ok(at)
        assert at.get("plotly_chart") and at.session_state["prim_step"] == step


def test_edge_slider_walks_through_all_tree_edges_and_survives_an_instance_change():
    at = _run(step=2)
    _ok(at)
    slider = at.slider(key="prim_edges")
    assert slider.max == 30
    slider.set_value(slider.max).run()
    _ok(at)
    assert at.session_state["prim_edges"] == 30
    at.session_state["kind_select"] = "textbook"
    at.run()
    _ok(at)
    assert at.session_state["prim_edges"] <= 4


@pytest.mark.parametrize("kw", [
    dict(n_slider=C.N_MIN), dict(n_slider=C.N_MAX), dict(n_slider=C.N_MAX, k_select=1000), dict(n_slider=C.N_MIN, k_select=3), dict(k_select=C.K_OPTIONS[0]), dict(k_select=C.K_OPTIONS[-1]),
    dict(terrain_select=C.TERRAIN_OPTIONS[0]), dict(terrain_select=C.TERRAIN_OPTIONS[-1]), dict(round_select=True), dict(variant_select="lazy"), dict(variant_select="array"),
    dict(start_select="far"), dict(start_select="center"), dict(n_slider=C.N_MIN, k_select=1000, variant_select="lazy", start_select="far"),
])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))
    _ok(_run(step=2, **kw))
    _ok(_run(step=3, **kw))


def test_variant_and_start_switches_never_change_the_tree_cost_shown_in_step_three():
    def cost(at):
        return next(m.value for m in at.markdown if m.value.startswith("**Derselbe Baum:**")).split("(Kosten ")[1]

    base = cost(_run(step=3))
    for kw in (dict(variant_select="lazy"), dict(variant_select="array"), dict(start_select="far"), dict(start_select="center")):
        assert cost(_run(step=3, **kw)) == base
    assert all("ja" in next(m.value for m in _run(step=3, **kw).markdown if m.value.startswith("**Derselbe Baum:**")) for kw in (dict(), dict(round_select=True), dict(kind_select="textbook")))


def test_dice_button_changes_the_seed():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(n="9999", k="7", terrain="0.35", round="maybe", variant="x", start="x", kind="nope").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert ss["n_slider"] == C.N_MAX
    assert (ss["k_select"], ss["terrain_select"], ss["round_select"], ss["variant_select"], ss["start_select"], ss["kind_select"]) == (C.DEFAULT_K, C.DEFAULT_TERRAIN, False, "eager", "depot", "depot")


def test_permalink_accepts_valid_values():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(kind="depot", n="50", k="1000", terrain="0.6", round="true", variant="array", start="far", seed="7").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["n_slider"], ss["k_select"], ss["terrain_select"], ss["round_select"], ss["variant_select"], ss["start_select"], ss["seed_input"]) == (50, 1000, 0.6, True, "array", "far", 7)


def test_sidebar_hides_map_only_controls_for_the_textbook_instance():
    at = _run(kind_select="textbook")
    _ok(at)
    assert not any(s.key == "k_select" for s in at.select_slider) and not any(n.key == "seed_input" for n in at.number_input) and not any(s.key == "n_slider" for s in at.slider)
    assert any(r.key == "variant_select" for r in at.radio) and any(r.key == "start_select" for r in at.radio)


def test_changing_the_instance_while_on_step_two_does_not_crash():
    at = _run(step=2)
    _ok(at)
    at.session_state["n_slider"] = C.N_MIN
    at.run()
    _ok(at)
    at.session_state["kind_select"] = "textbook"
    at.run()
    _ok(at)


@pytest.mark.parametrize("param", ["n", "k"])
@pytest.mark.parametrize("metric", ["ops", "ratio", "heap", "dk", "order"])
def test_sweeps_run_on_demand_for_every_metric(param, metric):
    at = _run(n_slider=15, sweep_metric=metric)
    at.selectbox(key="sweep_select").set_value(param).run()
    next(b for b in at.button if b.key == "sweep_start").click().run()
    _ok(at)
    assert at.get("plotly_chart")


def test_start_invariance_experiment_runs_on_demand():
    at = _run(n_slider=15)
    next(b for b in at.button if b.key == "start_start").click().run()
    _ok(at)
    assert [m.value for m in at.metric if m.delta.startswith("anderer Baum")] == ["0 %"] * 3


def test_no_experiments_for_the_textbook_instance():
    at = _run(kind_select="textbook")
    assert not any(b.key in ("start_start", "sweep_start") for b in at.button)


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Fredman & Tarjan 1987" in m.value for m in at.markdown)
