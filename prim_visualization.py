"""Plotly-Abbildungen: Karte, Baumwachstum von Kruskal (Fragmente) und Prim (ein Baum mit Rand) nebeneinander, Streudiagramm der Annahmereihenfolge, Aufwands-Balken,
Rand-/Heapgröße über die Schritte, Sweeps. Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

MST_COLOR = "#2F6B65"
FRONTIER_COLOR = "#f58518"
GREY = "rgba(150,150,150,0.3)"
ALGO_COLORS = {"array": "#4c78a8", "lazy": "#e45756", "eager": "#54a24b", "kruskal": "#7b3fbf"}
ALGO_LABELS = {"array": "Prim (Array)", "lazy": "Prim (Heap, lazy)", "eager": "Prim (Heap, Decrease-Key)", "kruskal": "Kruskal"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.1):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=legend_y), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _map_axes(fig, height):
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, height)


def _segments(inst, edge_ids):
    xs, ys = [], []
    for i in edge_ids:
        u, v, _w = inst.edges[i]
        xs += [inst.xy[u, 0], inst.xy[v, 0], None]
        ys += [inst.xy[u, 1], inst.xy[v, 1], None]
    return xs, ys


def _line(fig, inst, edge_ids, name, color, width, dash="solid", showlegend=True, row=None, col=None):
    if len(edge_ids):
        xs, ys = _segments(inst, edge_ids)
        trace = go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), name=name, hoverinfo="skip", showlegend=showlegend)
        fig.add_trace(trace, row=row, col=col) if row else fig.add_trace(trace)


def _points(fig, inst, colors, size=9, start=None, row=None, col=None):
    trace = go.Scatter(x=inst.xy[:, 0], y=inst.xy[:, 1], mode="markers+text" if inst.labels is not None else "markers", text=list(inst.labels) if inst.labels is not None else None,
                       textposition="top center", marker=dict(size=size, color=colors, line=dict(width=1, color="white")), hoverinfo="skip", showlegend=False)
    fig.add_trace(trace, row=row, col=col) if row else fig.add_trace(trace)
    if start is not None:
        star = go.Scatter(x=[inst.xy[start, 0]], y=[inst.xy[start, 1]], mode="markers", marker=dict(size=15, symbol="star", color="#2ca02c", line=dict(width=1, color="white")),
                          name="Start", hoverinfo="skip", showlegend=False)
        fig.add_trace(star, row=row, col=col) if row else fig.add_trace(star)


def build_instance(inst, start=0):
    fig = go.Figure()
    _line(fig, inst, range(inst.m), "Kandidatenkanten", GREY, 1, showlegend=False)
    _points(fig, inst, "#4c78a8", 9, start)
    return _map_axes(fig, 440 if inst.kind == "depot" else 340)


def _component_colors(inst, accepted):
    parent = list(range(inst.n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in accepted:
        u, v, _w = inst.edges[i]
        parent[find(u)] = find(v)
    roots = [find(x) for x in range(inst.n)]
    sizes = {}
    for r in roots:
        sizes[r] = sizes.get(r, 0) + 1
    palette, colors = {}, []
    for r in roots:
        if sizes[r] == 1:
            colors.append("rgba(150,150,150,0.8)")
        else:
            if r not in palette:
                palette[r] = f"hsl({(len(palette) * 137) % 360},60%,45%)"
            colors.append(palette[r])
    return colors


def frontier_edges(inst, tree_edges, start):
    inside = {start}
    for i in tree_edges:
        inside |= set(inst.edges[i][:2])
    return [i for i, (u, v, _w) in enumerate(inst.edges) if (u in inside) != (v in inside)], inside


def build_growth(inst, kruskal_tree, prim_tree, start, k):
    """Nach k angenommenen Kanten: links Kruskal (viele Fragmente, Punktfarbe = Komponente), rechts Prim (EIN Baum ab dem Startknoten, orange dünn = Rand, orange dick = zuletzt angenommene Kante)."""
    k = max(0, min(k, len(prim_tree), len(kruskal_tree)))
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Kruskal: Fragmente wachsen zusammen", "Prim: ein Baum wächst vom Start aus"), horizontal_spacing=0.04)
    kt, pt = kruskal_tree[:k], prim_tree[:k]
    _line(fig, inst, range(inst.m), "", "rgba(150,150,150,0.18)", 1, showlegend=False, row=1, col=1)
    _line(fig, inst, kt, "Kruskal", MST_COLOR, 3.5, showlegend=False, row=1, col=1)
    _points(fig, inst, _component_colors(inst, kt), 9, start=None, row=1, col=1)
    front, inside = frontier_edges(inst, pt, start)
    _line(fig, inst, range(inst.m), "", "rgba(150,150,150,0.12)", 1, showlegend=False, row=1, col=2)
    _line(fig, inst, front, "Rand", FRONTIER_COLOR, 1.2, showlegend=False, row=1, col=2)
    _line(fig, inst, pt, "Prim", MST_COLOR, 3.5, showlegend=False, row=1, col=2)
    if k >= 1:
        _line(fig, inst, [pt[-1]], "zuletzt", "#ff7f0e", 6, showlegend=False, row=1, col=2)
    _points(fig, inst, [MST_COLOR if x in inside else "rgba(150,150,150,0.8)" for x in range(inst.n)], 9, start=start, row=1, col=2)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_layout(xaxis=dict(scaleanchor="y", scaleratio=1), xaxis2=dict(scaleanchor="y2", scaleratio=1))
    _base(fig, 420 if inst.kind == "depot" else 330)
    fig.update_layout(margin=dict(l=10, r=10, t=34, b=10))
    return fig


def build_result(inst, tree, start):
    fig = go.Figure()
    in_tree = set(tree)
    _line(fig, inst, [i for i in range(inst.m) if i not in in_tree], "Kandidatenkante", "rgba(150,150,150,0.2)", 1, showlegend=False)
    _line(fig, inst, tree, "Spannbaum", MST_COLOR, 3.5, showlegend=False)
    _points(fig, inst, "#4c78a8", 9, start)
    return _map_axes(fig, 440 if inst.kind == "depot" else 340)


def build_order_scatter(kruskal_tree, prim_tree, rho):
    """Jede Baumkante als Punkt: x = Rang in der Annahmereihenfolge bei Kruskal, y = Rang bei Prim; auf der Diagonale = gleiche Reihenfolge."""
    rank_k = {e: i + 1 for i, e in enumerate(kruskal_tree)}
    xs = [rank_k[e] for e in prim_tree]
    ys = list(range(1, len(prim_tree) + 1))
    n = max(len(prim_tree), 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, n], y=[1, n], mode="lines", line=dict(color="#888", dash="dash", width=1.5), name="gleiche Reihenfolge", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(size=8, color=MST_COLOR), name=f"Baumkanten (Rang-Korrelation {rho:.2f})", hoverinfo="skip"))
    fig.update_xaxes(title_text="Rang bei Kruskal")
    fig.update_yaxes(title_text="Rang bei Prim")
    return _base(fig, 340, legend_y=-0.3)


def build_ops_bars(ops, winner):
    """Elementarschritte je Verfahren für EINE Instanz; der Gewinner ist hervorgehoben."""
    algos = list(ops)
    fig = go.Figure(go.Bar(x=[ALGO_LABELS[a] for a in algos], y=[ops[a] for a in algos], marker_color=[ALGO_COLORS[a] for a in algos],
                           marker_line=dict(width=[3 if a == winner else 0 for a in algos], color="#14233B"), text=[f"{ops[a]:,}".replace(",", ".") for a in algos], textposition="outside"))
    fig.update_yaxes(title_text="Elementarschritte")
    return _base(fig, 320)


def build_heap_curves(prims):
    """Größe der Datenstruktur nach jedem Schritt: Heap (lazy: Kanten, eager: Knoten), Kandidatenbestand (Array) und der tatsächliche Rand (Kanten zwischen Baum und Rest)."""
    fig = go.Figure()
    for variant in ("lazy", "eager", "array"):
        steps = prims[variant].steps
        fig.add_trace(go.Scatter(x=[s[1] for s in steps], y=[s[2] for s in steps], mode="lines", line=dict(color=ALGO_COLORS[variant], width=2.5), name=ALGO_LABELS[variant]))
    steps = prims["lazy"].steps
    fig.add_trace(go.Scatter(x=[s[1] for s in steps], y=[s[3] for s in steps], mode="lines", line=dict(color="#888", width=2, dash="dot"), name="Rand (Kanten Baum-Rest)"))
    fig.update_xaxes(title_text="Knoten im Baum")
    fig.update_yaxes(title_text="Einträge / Kanten")
    return _base(fig, 340, legend_y=-0.3)


def build_sweep(rows, param_label, series, y_label, log_y=False, ref_line=None, ref_label=None):
    """`series` = [(key, Name, Farbe)]: Median als Linie, 10. bis 90. Perzentil als Band (`<key>_lo`/`<key>_hi`)."""
    xs = [str(r["value"]) for r in rows]
    fig = go.Figure()
    for key, name, color in series:
        ys = [r[key] for r in rows]
        lo = [r[f"{key}_lo"] for r in rows]
        hi = [r[f"{key}_hi"] for r in rows]
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], mode="lines", fill="toself", fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.13)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=color, width=2.5), name=name))
    if ref_line is not None:
        fig.add_hline(y=ref_line, line=dict(color="#888", dash="dash", width=1.5), annotation_text=ref_label, annotation_position="top left")
    fig.update_xaxes(title_text=param_label, type="category")
    fig.update_yaxes(title_text=y_label, type="log" if log_y else "linear")
    return _base(fig, 360, legend_y=-0.3)
