"""Unabhängige Orakel (anderer Rechenweg als der Demo-Code): networkx (MST-Kosten, auch bei Gleichständen und unzusammenhängenden Graphen), eine unabhängige heapq-Nachbildung des lazy-Prim
(Einfügungen, veraltete Einträge, größter Heap), Neuzählen des Rands aus der Kantenliste, scipy.stats.spearmanr (Rang-Korrelation), Brute-Force-Nachbarn für den Kandidatengraphen."""

import heapq

import numpy as np
import pytest

import prim_algorithm as A
import prim_scenario as S

nx = pytest.importorskip("networkx")
stats = pytest.importorskip("scipy.stats")


def _graph(seed):
    rng = np.random.default_rng(seed)
    n, p = int(rng.integers(3, 25)), float(rng.uniform(0.2, 1.0))
    ties = seed % 2 == 0
    edges = [(u, v, float(rng.integers(1, 5)) if ties else float(rng.uniform(1, 10))) for u in range(n) for v in range(u + 1, n) if rng.random() < p]
    return n, edges, int(rng.integers(0, n))


@pytest.mark.parametrize("seed", range(40))
@pytest.mark.parametrize("variant", A.VARIANTS)
def test_prim_cost_frontier_and_tree_size_equal_independent_recount(seed, variant):
    n, edges, start = _graph(seed)
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_weighted_edges_from(edges)
    comp = nx.node_connected_component(g, start)
    ref = sum(d["weight"] for *_e, d in nx.minimum_spanning_edges(g.subgraph(comp), data=True))
    r = A.prim(n, edges, variant, start)
    assert r.cost == pytest.approx(ref) and len(r.tree) == len(comp) - 1 and r.connected == (len(comp) == n)
    inside = {start}
    fronts = []
    for idx in r.tree:
        u, v, _w = edges[idx]
        inside.add(v if u in inside else u)
        fronts.append(sum((a in inside) != (b in inside) for a, b, _ in edges))
    assert [s[3] for s in r.steps] == fronts
    assert [s[1] for s in r.steps] == list(range(2, len(r.tree) + 2))


@pytest.mark.parametrize("seed", range(40))
def test_lazy_counters_equal_a_heapq_simulation(seed):
    n, edges, start = _graph(seed)
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((v, w, i))
        adj[v].append((u, w, i))
    seen, heap, pushes, stale, biggest, tree = {start}, [], 0, 0, 0, []
    for v, w, i in adj[start]:
        heapq.heappush(heap, (w, i, v))
        pushes += 1
    biggest = len(heap)
    while heap and len(tree) < n - 1:
        w, i, v = heapq.heappop(heap)
        if v in seen:
            stale += 1
            continue
        seen.add(v)
        tree.append(i)
        for x, w2, i2 in adj[v]:
            if x not in seen:
                heapq.heappush(heap, (w2, i2, x))
                pushes += 1
        biggest = max(biggest, len(heap))
    r = A.prim(n, edges, "lazy", start)
    assert (r.tree, r.pushes, r.stale_pops, r.max_heap) == (tree, pushes, stale, biggest)


@pytest.mark.parametrize("seed", range(15))
def test_rank_correlation_equals_scipy_spearman(seed):
    n, edges, start = _graph(seed + 100)
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from((u, v) for u, v, _w in edges)
    if not nx.is_connected(g) or len(edges) < 4:
        pytest.skip("kein zusammenhängender Graph")
    k, r = A.kruskal(n, edges), A.prim(n, edges, "eager", start)
    if len(k.tree) < 2:
        pytest.skip("zu kleiner Baum")
    pos = {e: i for i, e in enumerate(k.tree)}
    assert A.spearman(k.tree, r.tree) == pytest.approx(stats.spearmanr(range(len(k.tree)), [pos[e] for e in r.tree]).statistic)


@pytest.mark.parametrize("seed", range(15))
def test_candidate_graph_contains_all_nearest_neighbours_and_adds_exactly_the_bridges(seed):
    rng = np.random.default_rng(seed)
    nc, k = int(rng.integers(4, 30)), int(rng.integers(1, 6))
    inst = S.generate(nc, k, 0.3, False, 700 + seed)
    pts, n = inst.xy, nc + 1
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    knn = set()
    for u in range(n):
        for v in sorted((x for x in range(n) if x != u), key=lambda x: (d[u, x], x))[:k]:
            knn.add((min(u, v), max(u, v)))
    es = {(u, v) for u, v, _ in inst.edges}
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(knn)
    assert knn <= es and nx.is_connected(nx.Graph(list(es))) and len(es - knn) == nx.number_connected_components(g) - 1
