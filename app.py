"""Prim – ein Baum, der von einem Punkt aus wächst - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zweites Stück der Spannbaum-Reihe der "Konzepte"-Reihe, der Kontrast zu Kruskal: derselbe billigste Baum, aber ein anderer Weg dorthin. Prim wächst aus EINEM Baum vom Startknoten aus
und nimmt immer die billigste Kante vom Baum zu einem noch nicht angeschlossenen Knoten; Kruskal sortiert alles und fügt Fragmente zusammen. Gemessen wird, wann welche der drei
Prim-Umsetzungen (Array, Heap aus Kanten, Heap mit Decrease-Key) und wann Kruskal weniger Elementarschritte braucht.

Lauffähig mit: streamlit run app.py
"""

from dataclasses import replace

import streamlit as st

import prim_constants as C
from prim_evaluation import ALGOS, SWEEP_LABELS, Settings, analyse, start_invariance, sweep
from prim_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from prim_visualization import (
    ALGO_COLORS,
    ALGO_LABELS,
    build_growth,
    build_heap_curves,
    build_instance,
    build_ops_bars,
    build_order_scatter,
    build_result,
    build_sweep,
)

st.set_page_config(page_title="Prim – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


@st.cache_data(show_spinner=False)
def _starts(settings):
    inst = analyse(settings).inst
    return {v: start_invariance(inst, v) for v in C.VARIANTS}


st.title("🌱 Prim – ein Baum, der von einem Punkt aus wächst")
st.markdown(
    """
**Zweites Stück der Spannbaum-Reihe** - der Kontrast zu Kruskal. Beide finden **denselben billigsten Baum** (den minimalen Spannbaum), aber auf verschiedenen Wegen: Kruskal sortiert alle
Kanten und fügt viele kleine Fragmente zusammen. **Prim** (Jarník 1930, Prim 1957) startet an **einem** Knoten und lässt einen einzigen Baum wachsen: in jedem Schritt kommt die billigste Kante hinzu,
die den Baum mit einem noch nicht angeschlossenen Knoten verbindet. Die Kanten zwischen Baum und Rest bilden den **Rand**; nur er muss verwaltet werden.

Wie man den Rand verwaltet, ist die eigentliche Frage: **Array** (jede Runde alle Kandidaten scannen), **Heap aus Kanten** (veraltete Einträge werden beim Entnehmen verworfen, "lazy") oder
**Heap aus Knoten mit Decrease-Key**. Hier wird gemessen, wann welche Umsetzung und wann Kruskal weniger Arbeit braucht - in Elementarschritten, nicht in Laufzeit.
"""
)
st.caption(
    "Setzt auf [kruskal-demo](https://github.com/sebastian-hanisch/kruskal-demo) auf (dieselben Instanzen; Kruskal läuft als Vergleich mit). Geplante Nachfolger (nicht gebaut): Borůvka, "
    "Euklidischer MST, Gerichteter Spannbaum, Grad-/Hop-beschränkter und Kapazitierter MST, Steiner-Baum, Prize-Collecting Steiner-Baum, Sensitivität, zufällige Spannbäume."
)

with st.expander("So funktioniert Prim", expanded=True):
    st.markdown(
        """
1. **Start:** ein Knoten bildet den Baum; alle seine Kanten sind der **Rand**.
2. **Wachsen:** die billigste Randkante nehmen (Schlüssel: Kosten, bei Gleichstand der Kantenindex), ihren neuen Endpunkt in den Baum aufnehmen, dessen Kanten zum Rest dem Rand hinzufügen.
3. **Stopp** nach n - 1 Kanten.
4. **Drei Umsetzungen des Rands:** *Array* scannt je Runde alle Nicht-Baum-Knoten (n²/2 Schritte insgesamt); *Heap, lazy* legt jede Randkante in einen Heap und verwirft beim Entnehmen veraltete Einträge; *Heap, Decrease-Key* hält je Knoten nur die billigste bekannte Kante und senkt deren Schlüssel bei Bedarf.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:4], preset_names[4:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                    help="Das Lehrbuchbeispiel hat 5 Knoten und 7 Kanten.")
    if kind == "depot":
        n = st.slider("Filialen n", *bounds("n_slider"), key="n_slider",
                      help="Mit wachsendem n gewinnt bei gleicher Dichte der Decrease-Key-Heap immer deutlicher (bei k = 6 ab n = 40; Array bei n = 10 in 5 von 5 Instanzen).")
        k = st.select_slider("Kandidaten: nächste Nachbarn k", options=list(C.K_OPTIONS), key="k_select", format_func=lambda v: "vollständig" if v == 1000 else str(v),
                             help="Je dichter der Graph, desto besser das Array gegenüber den Heaps (bei n = 30: Array gewinnt ab k = 20). \"vollständig\" = alle Paare.")
        terrain = st.select_slider("Geländezuschlag", options=list(C.TERRAIN_OPTIONS), key="terrain_select", format_func=lambda v: f"{v:g}",
                                   help="Jede Kante kostet Länge mal einen Faktor zwischen 1 und 1 + Zuschlag.")
        rounded = st.radio("Kosten", options=[False, True], format_func=lambda v: "ganzzahlig gerundet (viele Gleichstände)" if v else "exakt", key="round_select",
                           help="Gerundete Kosten erzeugen Gleichstände - der Baum bleibt trotzdem eindeutig, weil der Schlüssel (Kosten, Kantenindex) strikt ordnet.")
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        n, k, terrain, rounded, seed = C.DEFAULT_N, C.DEFAULT_K, C.DEFAULT_TERRAIN, False, C.DEFAULT_SEED
    variant = st.radio("Prim-Umsetzung", options=list(C.VARIANTS), format_func=lambda v: C.VARIANT_LABELS[v], key="variant_select",
                       help="Ändert Aufwand, Heapgröße und Anzeige, nie den Baum: alle drei nehmen in jedem Schritt dieselbe Kante.")
    start = st.radio("Startknoten", options=list(C.STARTS), format_func=lambda v: C.START_LABELS[v], key="start_select",
                     help="Ändert die Annahmereihenfolge und den Wachstumsverlauf, nie den Baum (in 31 von 31 Startknoten getestet).")

sync_query_params({"kind_select": kind, "n_slider": int(n), "k_select": int(k), "terrain_select": float(terrain), "round_select": bool(rounded), "seed_input": int(seed),
                   "variant_select": variant, "start_select": start})

settings = Settings(kind, int(n), int(k), float(terrain), bool(rounded), int(seed), variant, start)
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst, prim, kr = a.inst, a.prim, a.kruskal

# --- Prim in Aktion ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Prim in Aktion")
STEP_LABELS = {1: "1 · Instanz", 2: "2 · Wachsen im Vergleich", 3: "3 · Ergebnis"}
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="prim_step", format_func=lambda s: STEP_LABELS[s])

if step == 1:
    st.markdown(f"**{inst.n - 1 if kind == 'depot' else inst.n} " + ("Filialen" if kind == "depot" else "Knoten") + f"** (Depot ⭐), **{inst.m} Kandidatenkanten**. Prim startet am Stern.")
    st.plotly_chart(build_instance(inst, a.start), width="stretch", key="s1_map")
elif step == 2:
    total = len(prim.tree)
    if total >= 1:
        if "prim_edges" in st.session_state:
            st.session_state["prim_edges"] = min(max(1, int(st.session_state["prim_edges"])), total)
        k_now = st.slider("Angenommene Kanten", 1, max(2, total), key="prim_edges", help="Nach so vielen angenommenen Kanten: links Kruskal, rechts Prim.") if total > 1 else 1
        k_now = min(k_now, total)
        idx = prim.tree[k_now - 1]
        u, v, w = inst.edges[idx]
        names = inst.labels
        label = f"{names[u]}–{names[v]}" if names else f"{u}–{v}"
        step_info = prim.steps[k_now - 1]
        st.markdown(f"**Nach {k_now} von {total} Kanten:** Prim nahm zuletzt Kante {label} (Kosten {w:.2f}); der Baum hat {step_info[1]} Knoten, der Rand {step_info[3]} Kanten.")
        st.plotly_chart(build_growth(inst, kr.tree, prim.tree, a.start, k_now), width="stretch", key=f"s2_map_{k_now}")
        st.caption("Links: Kruskal hat bis hierher die k billigsten angenommenen Kanten (Fragmente, Punktfarbe = Komponente). Rechts: Prim hat einen einzigen Baum ab dem Stern; orange dünn = Rand, orange dick = zuletzt angenommene Kante.")
    else:
        st.info("Nichts zu wachsen.")
else:
    st.plotly_chart(build_result(inst, prim.tree, a.start), width="stretch", key="s3_map")
    st.markdown(f"**Derselbe Baum:** {'ja' if a.same_tree else 'NEIN (!)'} - Prim (alle drei Umsetzungen) und Kruskal wählen dieselben {len(prim.tree)} Kanten (Kosten {prim.cost:.2f}).")
    st.plotly_chart(build_order_scatter(kr.tree, prim.tree, a.rank_correlation), width="stretch", key="order")
    st.caption("Nur die Reihenfolge unterscheidet sich: je weiter die Punkte von der Diagonale entfernt sind, desto anders hat Prim die Kanten angenommen als Kruskal.")

st.markdown("---")

# --- Aufwand -----------------------------------------------------------------------------------------------------------------------------------

st.markdown("## ⚙️ Was kostet welche Umsetzung?")
st.caption(
    "**Elementarschritte:** Schlüsselvergleiche plus je eine Einheit je Heap-Einfügung, -Entnahme und Decrease-Key (Prim) bzw. Sortier-Vergleiche plus je Union-Find-Suche und Zeigerschritt (Kruskal). "
    "Ein Näherungsmaß für den Vergleich, **keine Laufzeitmessung**: was eine Vergleichsoperation in einer bestimmten Sprache oder Bibliothek kostet, steckt nicht darin."
)
ops = a.ops
m1, m2, m3, m4 = st.columns(4)
SHORT = {"array": "Array", "lazy": "Heap lazy", "eager": "Decrease-Key", "kruskal": "Kruskal"}
m1.metric("Gewinner", SHORT[a.winner], delta=f"{ops[a.winner]:,} Schritte".replace(",", "."), delta_color="off")
m2.metric("Gewählte Umsetzung", f"{ops[variant]:,}".replace(",", "."), delta=f"{ops[variant] / ops[a.winner]:.2f}x der billigsten", delta_color="off")
m3.metric("Kruskal", f"{ops['kruskal']:,}".replace(",", "."), delta=f"{kr.examined} von {inst.m} Kanten angesehen", delta_color="off")
m4.metric("Größter Heap", str(prim.max_heap), delta=("Kanten" if variant == "lazy" else "Knoten" if variant == "eager" else "Kandidaten"), delta_color="off")
st.plotly_chart(build_ops_bars({x: ops[x] for x in ALGOS}, a.winner), width="stretch", key="ops_bars")
extra = []
lazy, eager = a.prims["lazy"], a.prims["eager"]
extra.append(f"lazy: {lazy.pushes} Einfügungen, {lazy.stale_pops} veraltete Einträge verworfen, größter Heap {lazy.max_heap}")
extra.append(f"Decrease-Key: {eager.decrease_keys} Senkungen (Erwartung bei Zufallsreihenfolge etwa {a.expected_decrease_keys:.0f}), größter Heap {eager.max_heap}")
extra.append(f"Array: {a.prims['array'].scans} gescannte Kandidaten (n(n-1)/2)")
st.caption(" · ".join(extra))
st.plotly_chart(build_heap_curves(a.prims), width="stretch", key="heap_curves")
st.caption("Größe der Datenstruktur nach jedem Schritt; gepunktet der tatsächliche Rand (Kanten zwischen Baum und Rest). Der lazy-Heap hält den Rand samt veralteten Einträgen, der Decrease-Key-Heap höchstens einen Eintrag je Knoten.")

st.markdown("---")

# --- Startknoten -------------------------------------------------------------------------------------------------------------------------------

if kind == "depot":
    st.subheader("🚩 Spielt der Startknoten eine Rolle?")
    st.caption("Prim von JEDEM Knoten aus starten: verändert sich der Baum, und wie viele verschiedene Annahmereihenfolgen entstehen?")
    if st.button("Von allen Knoten aus starten", key="start_start"):
        st.session_state["start_done"] = st.session_state.get("start_done", set()) | {replace(settings, variant="lazy", start="depot")}
    if replace(settings, variant="lazy", start="depot") in st.session_state.get("start_done", set()):
        res = _starts(replace(settings, variant="lazy", start="depot"))
        cols = st.columns(len(res))
        for col, (v, (differ, orders)) in zip(cols, res.items()):
            col.metric(C.VARIANT_LABELS[v], f"{differ:.0f} %", delta=f"anderer Baum · {orders} Reihenfolgen bei {inst.n} Starts", delta_color="off")
    st.markdown("---")

# --- Sweeps ------------------------------------------------------------------------------------------------------------------------------------

if kind == "depot":
    st.subheader("📐 Wo kreuzen sich die Verfahren?")
    sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", list(SWEEP_LABELS), format_func=lambda v: SWEEP_LABELS[v], key="sweep_select")
    metric = st.radio("Kennzahl", options=["ops", "ratio", "heap", "dk", "order"],
                       format_func=lambda v: {"ops": "Elementarschritte", "ratio": "Verhältnis zu Kruskal", "heap": "Größter Heap", "dk": "Decrease-Keys", "order": "Rang-Korrelation"}[v],
                       key="sweep_metric", horizontal=True)
    base_sweep = replace(settings, seed=0)
    if st.button("Sweep über 5 feste Instanzen berechnen (kann einige Sekunden dauern)", key="sweep_start"):
        st.session_state["sweep_done"] = st.session_state.get("sweep_done", set()) | {(sweep_param, base_sweep)}
    if (sweep_param, base_sweep) in st.session_state.get("sweep_done", set()):
        with st.spinner("Rechne den Sweep über 5 feste Instanzen..."):
            rows_sweep = _sweep(sweep_param, base_sweep)
        label = SWEEP_LABELS[sweep_param]
        if metric == "ops":
            st.plotly_chart(build_sweep(rows_sweep, label, [(f"ops_{x}", ALGO_LABELS[x], ALGO_COLORS[x]) for x in ALGOS], "Elementarschritte (logarithmisch)", log_y=True), width="stretch", key="sweep_ops")
        elif metric == "ratio":
            st.plotly_chart(build_sweep(rows_sweep, label, [("lazy_over_kruskal", "Prim (lazy) / Kruskal", ALGO_COLORS["lazy"]), ("array_over_kruskal", "Prim (Array) / Kruskal", ALGO_COLORS["array"]),
                                                            ("eager_over_lazy", "Decrease-Key / lazy", ALGO_COLORS["eager"])], "Verhältnis", ref_line=1.0, ref_label="gleich viele Schritte"), width="stretch", key="sweep_ratio")
        elif metric == "heap":
            st.plotly_chart(build_sweep(rows_sweep, label, [("max_heap_lazy", "Heap aus Kanten (lazy)", ALGO_COLORS["lazy"]), ("max_heap_eager", "Heap aus Knoten (Decrease-Key)", ALGO_COLORS["eager"]),
                                                            ("max_frontier", "Rand (Kanten Baum-Rest)", "#888888")], "Einträge (logarithmisch)", log_y=True), width="stretch", key="sweep_heap")
        elif metric == "dk":
            st.plotly_chart(build_sweep(rows_sweep, label, [("decrease_keys", "Decrease-Keys (gemessen)", ALGO_COLORS["eager"]), ("expected_decrease_keys", "n·ln(m/n) (Erwartung bei Zufall)", "#888888")], "Anzahl"), width="stretch", key="sweep_dk")
        else:
            st.plotly_chart(build_sweep(rows_sweep, label, [("rank_correlation", "Rang-Korrelation Prim / Kruskal", "#2F6B65")], "Korrelation", ref_line=1.0, ref_label="gleiche Reihenfolge"), width="stretch", key="sweep_order")
        st.caption("Median über 5 feste Instanzen (Seeds 100000–100004), Band = 10. bis 90. Perzentil. Die übrigen Regler stehen wie in der Seitenleiste.")
    st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Prim und Kruskal sind gleichwertig** | Beim Ergebnis ja (immer derselbe Baum), beim Aufwand nicht: in Elementarschritten war Kruskal auf allen gemessenen Instanzen nie das billigste Verfahren; nur der lazy-Heap verliert im dünnen Graphen gegen ihn (k = 6: 1157 gegen 947). | Borůvka (Nachfolger): dritter Weg zum selben Baum |
| **Der lazy-Heap ist praktisch so gut wie Decrease-Key** | Nicht in Elementarschritten: Decrease-Key braucht nur das 0.37-Fache, und der lazy-Heap wird bei n = 160 vollständig 12 424 Einträge groß (Decrease-Key: 160). Ob das in einer konkreten Sprache auch die Laufzeit entscheidet, ist hier nicht gemessen. | Fibonacci-Heap (nicht gebaut) |
| **Die Erwartung n·ln(m/n) für Decrease-Keys gilt** | Nur als Größenordnung: gemessen 56 gegen 41 (n = 30, k = 6), bei n = 160 vollständig 1850 gegen 706 - räumliche Instanzen liegen bis 2.6-fach darüber. | - |
| **Das einfache Array ist veraltet** | Nein: bei dichten Graphen (n = 30: ab k = 20) und kleinen Instanzen gewinnt es, weil es keine Datenstruktur verwaltet; es verliert erst, wenn n² schneller wächst als m log n (beim vollständigen Graphen zwischen n = 40 und n = 80). | - |
| **Elementarschritte sind Laufzeit** | Nein. Sie zählen Vergleiche und Heap-Operationen einheitlich, ignorieren aber, wie teuer sie in einer bestimmten Sprache sind (ein in C geschriebener Sortierer ist viel schneller als derselbe Algorithmus in Python). | Laufzeitmessung an echten Netzen (hier nicht gebaut) |
| **Synthetische Instanzen** | Punkte im Quadrat, euklidische Kosten mit Zufallszuschlag; keine Straßennetze, Kapazitäten oder Richtungen. | Echte Trassen (hier nicht gebaut) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Schnitt-Eigenschaft.** Für den Schnitt $(T, V\setminus T)$ gehört eine billigste Kante über den Schnitt zu einem MST. Prim wählt in jedem Schritt genau diese Kante für den Schnitt aus Baum $T$ und Rest.

**Strikte Ordnung.** Der Schlüssel $(w_e, \text{Index}(e))$ ordnet alle Kanten strikt; der MST ist dann eindeutig, und jedes Verfahren, das nur Schnitt- und Kreis-Eigenschaft nutzt, findet ihn -
Prim von jedem Startknoten aus, Kruskal mit derselben Ordnung. Nur die Annahmereihenfolge hängt vom Verfahren (und vom Start) ab.

**Aufwand.** Array: $\sum_{r=1}^{n-1}(n-r) = n(n-1)/2$ gescannte Kandidaten, $O(n^2)$. Heap aus Kanten (lazy): bis zu $m$ Einfügungen und Entnahmen, $O(m \log m)$. Heap aus Knoten mit Decrease-Key:
$n$ Einfügungen und Entnahmen sowie bis zu $m$ Decrease-Keys, $O(m \log n)$ mit binärem Heap, $O(m + n \log n)$ mit Fibonacci-Heap (Fredman & Tarjan 1987). Kruskal: $O(m \log m)$ für das Sortieren plus Union-Find.

**Literatur.** Prim, R. C. (1957). *Shortest connection networks and some generalizations.* Bell System Technical Journal 36(6), 1389-1401. Jarník, V. (1930). *O jistém problému minimálním.* Práce Moravské
přírodovědecké společnosti 6, 57-63. Fredman, M. L., & Tarjan, R. E. (1987). *Fibonacci heaps and their uses in improved network optimization algorithms.* Journal of the ACM 34(3), 596-615.

Implementiert in `prim_algorithm.py` (`BinaryHeap`, `prim` in drei Umsetzungen, Kruskal-Kopie mit Vergleichszähler), `prim_scenario.py` (Instanzen), `prim_evaluation.py` (Kennzahlen, Sweeps, Start-Invarianz).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
