"""Die zentrale Korrektheits-Kette für Prim: jede Variante liefert einen Spannbaum; Baum == Kruskal auch bei Gleichständen (strikte Schlüsselordnung); Startknoten-Invarianz; Schnitt-Eigenschaft
direkt an der Prim-Reihenfolge; Heap-Invarianten und Decrease-Key; Zähler-Identitäten; Kruskal-Kopie treu; Sonderfälle."""

import itertools
import math
import random

import numpy as np
import pytest
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import minimum_spanning_tree

import prim_algorithm as A
import prim_scenario as S

VARIANTS = A.VARIANTS


def _is_spanning_tree(n, edges, tree):
    if len(tree) != n - 1 or len(set(tree)) != n - 1:
        return False
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for i in tree:
        u, v, _w = edges[i]
        ru, rv = find(u), find(v)
        if ru == rv:
            return False
        parent[ru] = rv
    return len({find(x) for x in range(n)}) == 1


def _brute_force_cost(n, edges):
    best = math.inf
    for combo in itertools.combinations(range(len(edges)), n - 1):
        if _is_spanning_tree(n, edges, list(combo)):
            best = min(best, sum(edges[i][2] for i in combo))
    return best


def _scipy_cost(n, edges):
    us, vs, ws = zip(*edges)
    return float(minimum_spanning_tree(coo_matrix((ws, (us, vs)), shape=(n, n)).tocsr()).sum())


def _instances():
    for seed in range(5):
        for k in (3, 6, 100):
            for rounded in (False, True):
                yield S.generate(20, k, 0.4, rounded, seed)
    yield S.textbook_instance()


# --- Spannbaum, Optimalität, Gleichheit mit Kruskal -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("inst", list(_instances()))
def test_result_is_a_spanning_tree_equal_to_kruskal_even_with_ties(inst, variant):
    r = A.prim(inst.n, inst.edges, variant)
    k = A.kruskal(inst.n, inst.edges)
    assert _is_spanning_tree(inst.n, inst.edges, r.tree) and r.connected
    assert sorted(r.tree) == sorted(k.tree) and r.cost == pytest.approx(k.cost)
    assert r.cost == pytest.approx(sum(inst.edges[i][2] for i in r.tree))


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("inst", list(_instances()))
def test_matches_scipy_cost(inst, variant):
    assert A.prim(inst.n, inst.edges, variant).cost == pytest.approx(_scipy_cost(inst.n, inst.edges))


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("seed", range(8))
def test_equals_brute_force_on_small_graphs(seed, variant):
    inst = S.generate(4, 100, 0.5, seed % 2 == 0, seed)
    assert A.prim(inst.n, inst.edges, variant).cost == pytest.approx(_brute_force_cost(inst.n, inst.edges))


def test_all_variants_give_identical_trees_and_orders():
    for inst in list(_instances())[:12]:
        base = A.prim(inst.n, inst.edges, "lazy")
        for variant in ("eager", "array"):
            r = A.prim(inst.n, inst.edges, variant)
            assert r.tree == base.tree                                     # dieselbe Annahmereihenfolge: immer die kleinste (Kosten, Index)-Randkante


@pytest.mark.parametrize("variant", VARIANTS)
def test_the_tree_does_not_depend_on_the_start_node_but_the_order_does(variant):
    for rounded in (False, True):
        inst = S.generate(12, 100, 0.4, rounded, 3)
        base = A.prim(inst.n, inst.edges, variant, 0)
        orders = set()
        for start in range(inst.n):
            r = A.prim(inst.n, inst.edges, variant, start)
            assert sorted(r.tree) == sorted(base.tree)
            orders.add(tuple(r.tree))
        assert len(orders) > 1                                             # die Reihenfolge ändert sich wirklich (der Zweig wird ausgeführt)


def test_start_node_choices():
    inst = S.generate(30, 6, 0.3, False, 5)
    assert A.start_node(inst, "depot") == 0
    far, center = A.start_node(inst, "far"), A.start_node(inst, "center")
    d = np.hypot(inst.xy[:, 0] - inst.xy[0, 0], inst.xy[:, 1] - inst.xy[0, 1])
    assert d[far] == d.max() and far != 0 and center != far
    with pytest.raises(ValueError):
        A.start_node(inst, "x")


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("seed", range(5))
def test_every_accepted_edge_is_the_cheapest_across_the_current_cut(seed, variant):
    inst = S.generate(20, 8, 0.4, seed % 2 == 0, seed)
    r = A.prim(inst.n, inst.edges, variant)
    in_tree = {0}
    for idx in r.tree:
        cut = [(e[2], i) for i, e in enumerate(inst.edges) if (e[0] in in_tree) != (e[1] in in_tree)]
        assert (inst.edges[idx][2], idx) == min(cut)
        u, v, _w = inst.edges[idx]
        in_tree.add(v if u in in_tree else u)
    assert len(in_tree) == inst.n


# --- Heap ---------------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(5))
def test_heap_invariant_and_order(seed):
    rng = random.Random(seed)
    h = A.BinaryHeap()
    keys = [rng.random() for _ in range(60)]
    for i, k in enumerate(keys):
        h.push(k, i)
        assert h.valid()
    out = []
    while len(h):
        out.append(h.pop()[0])
        assert h.valid()
    assert out == sorted(keys) and h.pushes == 60 and h.pops == 60 and h.max_size == 60


@pytest.mark.parametrize("seed", range(5))
def test_indexed_heap_decrease_key_against_a_reference(seed):
    rng = random.Random(seed)
    h = A.BinaryHeap(indexed=True)
    ref = {}
    for item in range(40):
        ref[item] = rng.random() * 100
        h.push(ref[item], item)
    for _ in range(60):
        item = rng.choice(list(ref))
        new = ref[item] - rng.random() * 30
        ref[item] = new
        h.decrease(item, new)
        assert h.valid() and h.contains(item)
    got = [h.pop() for _ in range(40)]
    assert [k for k, _i in got] == sorted(ref.values()) and {i for _k, i in got} == set(ref) and h.decrease_keys == 60 and not h.contains(0)


def test_heap_comparison_counter_matches_an_instrumented_key():
    class Key:
        calls = 0

        def __init__(self, v):
            self.v = v

        def __lt__(self, other):
            Key.calls += 1
            return self.v < other.v

        def __le__(self, other):
            return self.v <= other.v

    rng = random.Random(1)
    h = A.BinaryHeap()
    for i in range(50):
        h.push(Key(rng.random()), i)
    while len(h):
        h.pop()
    assert h.comparisons == Key.calls


# --- Zähler-Identitäten -------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("inst", list(_instances())[:14])
def test_counter_identities(inst):
    n, m = inst.n, inst.m
    arr = A.prim(n, inst.edges, "array")
    assert arr.scans == n * (n - 1) // 2 and arr.ops == arr.scans + arr.key_compares and arr.max_heap <= n - 1
    lazy = A.prim(n, inst.edges, "lazy")
    assert lazy.pops - lazy.stale_pops == n - 1 and lazy.max_heap <= m and lazy.pushes <= m and lazy.decrease_keys == 0
    eager = A.prim(n, inst.edges, "eager")
    assert eager.pushes == n - 1 and eager.pops == n - 1 and eager.max_heap <= n - 1 and eager.stale_pops == 0 and eager.pushes + eager.decrease_keys <= m
    for r in (lazy, eager):
        assert r.comparisons >= r.pops - 1 and r.ops == r.comparisons + r.pushes + r.pops + r.decrease_keys


def test_steps_track_tree_size_and_frontier():
    inst = S.generate(20, 6, 0.3, False, 2)
    for variant in VARIANTS:
        r = A.prim(inst.n, inst.edges, variant)
        assert [s[1] for s in r.steps] == list(range(2, inst.n + 1)) and [s[0] for s in r.steps] == r.tree
        for (idx, size, _heap, frontier), k in zip(r.steps, range(1, inst.n)):
            inside = set()
            # Rand nach k angenommenen Kanten = Kanten mit genau einem Endpunkt im Baum
            for j in r.tree[:k]:
                inside |= set(inst.edges[j][:2])
            inside.add(0)
            assert frontier == sum(1 for u, v, _w in inst.edges if (u in inside) != (v in inside))
    assert r.steps[-1][3] == 0                                                 # am Ende ist der Rand leer


def test_lazy_heap_grows_larger_than_the_eager_heap_on_dense_graphs():
    inst = S.generate(60, 1000, 0.3, False, 1)
    lazy, eager = A.prim(inst.n, inst.edges, "lazy"), A.prim(inst.n, inst.edges, "eager")
    assert lazy.max_heap > 3 * eager.max_heap and lazy.stale_pops > 0 and eager.decrease_keys > 0


# --- Kruskal-Kopie treu -------------------------------------------------------------------------------------------------------------------------


def test_kruskal_copy_reproduces_the_kruskal_demo_numbers():
    inst = S.generate(30, 6, 0.3, False, 35)
    k = A.kruskal(inst.n, inst.edges)
    assert k.cost == pytest.approx(466.63, abs=0.01) and (k.examined, inst.m) == (90, 113)
    dense = S.generate(30, 1000, 0.3, False, 35)
    assert (A.kruskal(dense.n, dense.edges).examined, dense.m) == (109, 465)
    t = S.textbook_instance()
    assert A.kruskal(t.n, t.edges).cost == 15.0


def test_counted_sort_sorts_and_stays_within_the_mergesort_bounds():
    rng = random.Random(3)
    for size in (0, 1, 2, 7, 64, 100, 500):
        xs = [(rng.random(), i) for i in range(size)]
        out, cmps = A.counted_sort(xs)
        assert out == sorted(xs)
        if size > 1:
            assert cmps <= size * math.ceil(math.log2(size)) - 2 ** math.ceil(math.log2(size)) + 1 and cmps >= size // 2 * int(math.log2(size)) // 2
    assert A.counted_sort([(i, i) for i in range(64)])[1] == 192                    # sortierte Eingabe: n/2 * log2 n Vergleiche
    assert A.counted_sort([(-i, i) for i in range(64)])[1] == 192                   # umgekehrt sortiert: ebenfalls


def test_kruskal_sort_comparisons_are_bounded_by_m_log_m():
    for seed in range(5):
        inst = S.generate(40, 100, 0.3, False, seed)
        k = A.kruskal(inst.n, inst.edges)
        assert inst.m - 1 <= k.sort_comparisons <= inst.m * math.ceil(math.log2(inst.m))
        assert k.ops == k.sort_comparisons + k.finds + k.find_steps and k.finds == 2 * k.examined


# --- Sonderfälle --------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("variant", VARIANTS)
def test_single_two_nodes_path_and_invalid_arguments(variant):
    one = A.prim(1, [], variant)
    assert one.tree == [] and one.cost == 0.0 and one.connected
    two = A.prim(2, [(0, 1, 3.0), (0, 1, 5.0)], variant)
    assert two.cost == 3.0 and two.tree == [0]
    path = [(i, i + 1, float(i + 1)) for i in range(9)]
    r = A.prim(10, path, variant, 4)
    assert len(r.tree) == 9 and r.cost == 45.0
    with pytest.raises(ValueError):
        A.prim(3, [(0, 1, 1.0)], "x")
    with pytest.raises(ValueError):
        A.prim(3, [(0, 1, 1.0)], variant, 5)


@pytest.mark.parametrize("variant", VARIANTS)
def test_disconnected_graph_gives_the_tree_of_the_start_component(variant):
    edges = [(0, 1, 1.0), (1, 2, 2.0), (3, 4, 1.0)]
    r = A.prim(5, edges, variant, 0)
    assert not r.connected and len(r.tree) == 2 and r.cost == 3.0
    assert A.prim(5, edges, variant, 3).tree == [2]


def test_complete_graph_with_equal_costs_gives_a_valid_star_like_tree_for_every_start():
    n = 6
    edges = tuple((u, v, 1.0) for u in range(n) for v in range(u + 1, n))
    trees = set()
    for start in range(n):
        for variant in VARIANTS:
            r = A.prim(n, edges, variant, start)
            assert _is_spanning_tree(n, edges, r.tree) and r.cost == 5.0
            trees.add(tuple(sorted(r.tree)))
    assert 1 <= len(trees) <= n                                              # (Kosten, Index)-Ordnung: der Baum ist eindeutig, nicht vom Start abhängig
    assert len(trees) == 1 and trees == {tuple(sorted(A.kruskal(n, edges).tree))}


def test_spearman_and_expected_decrease_keys():
    assert A.spearman([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0 and A.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert A.spearman([1], [1]) == 1.0 and -1.0 <= A.spearman([1, 3, 2, 4], [2, 1, 4, 3]) <= 1.0
    assert A.expected_decrease_keys(10, 10) == 0.0 and A.expected_decrease_keys(100, 1000) == pytest.approx(100 * math.log(10))
