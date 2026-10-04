"""Konstanten der Prim-Demo: Instanz-Geometrie (wortgleich zur Kruskal-Demo), Regler, gemessene Werte, Presets."""
AREA = 100.0
DEPOT_XY = (15.0, 50.0)
N_MIN, N_MAX, DEFAULT_N, N_STEP = 5, 200, 30, 1
K_MIN, DEFAULT_K = 3, 6
TERRAIN_MIN, TERRAIN_MAX, DEFAULT_TERRAIN, TERRAIN_STEP = 0.0, 1.0, 0.3, 0.05
SEED_MAX = 999999
DEFAULT_SEED = 35
ROUND_UNIT = 1.0
KINDS = ("depot", "textbook")
KIND_LABELS = {"depot": "Depot und Filialen (Karte)", "textbook": "Lehrbuchbeispiel (5 Knoten)"}
K_OPTIONS = (3, 4, 5, 6, 8, 10, 15, 20, 40, 1000)
TERRAIN_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0)
VARIANTS = ("lazy", "eager", "array")
VARIANT_LABELS = {"lazy": "Heap aus Kanten (lazy)", "eager": "Heap aus Knoten (Decrease-Key)", "array": "Array (Scan)"}
DEFAULT_VARIANT = "eager"
STARTS = ("depot", "far", "center")
START_LABELS = {"depot": "Depot", "far": "weitester Knoten vom Depot", "center": "Kartenmitte"}
SWEEP_SEEDS = tuple(range(100000, 100005))
N_SWEEP = (10, 20, 40, 80, 160)
K_SWEEP = (3, 4, 6, 10, 20, 1000)

# --- Gemessene Werte (MEDIAN über 5 feste Instanzen, Seeds 100000-100004; 30 Filialen + Depot, k = 6 nächste Nachbarn, Geländezuschlag 0.3, exakte Kosten, Start am Depot;
# --- 2026-09-24, alle Werte über ev.run_config/ev.sweep nachgerechnet, s. tests/test_claims.py). Aufwand in ELEMENTARSCHRITTEN (Schlüsselvergleiche plus je eine Einheit je
# --- Heap-Operation bzw. Union-Find-Suche und Zeigerschritt), NICHT in Laufzeit - ein Näherungsmaß. Alle Verfahren sind deterministisch. ---
# GLEICHER BAUM: alle drei Prim-Umsetzungen und Kruskal liefern in 100 % der Läufe dieselbe Kantenmenge (Schlüssel (Kosten, Kantenindex) = strikte Ordnung), auch mit gerundeten
#   Kosten und von JEDEM der 31 Startknoten aus (Seed 35: 0 % Abweichung, aber 22 verschiedene Annahmereihenfolgen).
# AUFWAND (n = 30, k = 6): Array 552, Heap lazy 1157, Heap mit Decrease-Key (eager) 431, Kruskal 947 Schritte - eager gewinnt in 5 von 5 Instanzen und braucht nur das 0.37-Fache
#   von lazy. Kruskal ist nie der billigste; der lazy-Heap verliert gegen Kruskal, solange der Graph dünn ist (k = 3/4/6/10: lazy 524/750/1157/1642 gegen Kruskal 446/616/947/1521) und
#   gewinnt erst bei k = 20 (2409 gegen 2992) bzw. beim vollständigen Graphen (2747 gegen 3805).
# KREUZUNGSPUNKT ARRAY GEGEN HEAP: Array-Prim (n(n-1)/2 gescannte Kandidaten) gewinnt bei k = 20 (802 gegen 884 für eager) und beim vollständigen Graphen (900 gegen 1012), und bei
#   kleinem n (n = 10: 5 von 5; n = 20: 3 von 5); bei k = 6 gewinnt eager ab n = 40 (576 gegen 932). Beim vollständigen Graphen kippt es zwischen n = 40 (Array 1600, eager 1668) und
#   n = 80 (Array 6400, eager 5621); bei n = 160: eager 19195, Array 25600, lazy 57950, Kruskal 161015.
# RAND UND HEAP: größter Heap bei n = 30: lazy 68 Einträge (k = 6), 397 (vollständig); eager 15 bzw. 30 (höchstens n). Veraltete Einträge beim lazy-Heap: 43. Bei n = 160 vollständig:
#   lazy 12424 Einträge gegen 160 bei eager.
# DECREASE-KEYS: 56 beobachtet gegen n * ln(m / n) = 41.2 erwartet (n = 30, k = 6); bei n = 160 vollständig 1850 gegen 706 - die Erwartung für Zufallsreihenfolge wird auf dieser
#   räumlichen Instanz um das 1.4- bis 2.6-Fache überschritten.
# REIHENFOLGE: Rang-Korrelation der Annahmereihenfolge Prim gegen Kruskal 0.40 (n = 30) und fallend mit n: 0.31/0.42/0.41/0.32/0.14 bei n = 10/20/40/80/160; ein Start am weitesten Knoten
#   senkt sie auf 0.10.

PRESETS = {
    "Standardfall (Voreinstellung)": {"kind": "depot", "n": 30, "k": 6, "terrain": 0.3, "round_costs": False, "seed": 35, "variant": "eager", "start": "depot"},
    "Dünnes Netz (k = 3)": {"kind": "depot", "n": 30, "k": 3, "terrain": 0.3, "round_costs": False, "seed": 35, "variant": "lazy", "start": "depot"},
    "Dichter Graph (k = 20)": {"kind": "depot", "n": 30, "k": 20, "terrain": 0.3, "round_costs": False, "seed": 35, "variant": "array", "start": "depot"},
    "Vollständiger Graph (n = 30)": {"kind": "depot", "n": 30, "k": 1000, "terrain": 0.3, "round_costs": False, "seed": 35, "variant": "array", "start": "depot"},
    "Große Instanz (n = 160, vollständig)": {"kind": "depot", "n": 160, "k": 1000, "terrain": 0.3, "round_costs": False, "seed": 35, "variant": "eager", "start": "depot"},
    "Start weit weg": {"kind": "depot", "n": 30, "k": 6, "terrain": 0.3, "round_costs": False, "seed": 35, "variant": "eager", "start": "far"},
    "Gleichstände (gerundet)": {"kind": "depot", "n": 30, "k": 6, "terrain": 0.3, "round_costs": True, "seed": 35, "variant": "eager", "start": "depot"},
    "Lehrbuchbeispiel": {"kind": "textbook", "n": 30, "k": 6, "terrain": 0.3, "round_costs": False, "seed": 35, "variant": "eager", "start": "depot"},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "30 Filialen, k = 6, Seed 35: Prim mit Decrease-Key-Heap braucht 413 Elementarschritte, Array 548, Kruskal 929, Prim mit lazy-Heap 1282. Alle liefern denselben Baum (Kosten 466.63), aber Prim wächst als EIN Baum vom Depot aus, Kruskal aus 31 Fragmenten (30 Filialen und das Depot). Rang-Korrelation der Reihenfolge 0.47.",
    "Dünnes Netz (k = 3)": "Nur 59 Kandidatenkanten: Prim mit lazy-Heap (466 Schritte) ist kaum billiger als Kruskal (456); der Decrease-Key-Heap braucht 249, das Array 494. Im dünnen Graphen hat Kruskal gegen die lazy-Umsetzung nichts zu verlieren.",
    "Dichter Graph (k = 20)": "361 Kanten: jetzt gewinnt das einfache Array (796 Schritte) knapp gegen den Decrease-Key-Heap (841); der lazy-Heap (2848) und Kruskal (3009) liegen weit zurück. Der lazy-Heap hält bis zu 307 Einträge, der Decrease-Key-Heap höchstens 26.",
    "Vollständiger Graph (n = 30)": "465 Kanten: Array 900, Decrease-Key 977, lazy 3298, Kruskal 3913 Schritte. Der lazy-Heap wächst auf 410 Einträge (79 veraltete), der Decrease-Key-Heap bleibt bei 30; Kruskal muss 465 Kanten sortieren, obwohl es nur 109 ansieht.",
    "Große Instanz (n = 160, vollständig)": "12 880 Kanten: der Decrease-Key-Heap gewinnt (19 071), vor dem Array (25 600), dem lazy-Heap (66 602) und Kruskal (162 373). Der lazy-Heap hält bis zu 12 532 Einträge, der Decrease-Key-Heap höchstens 160; die Rang-Korrelation der Reihenfolge fällt auf 0.12.",
    "Start weit weg": "Derselbe Baum, aber Prim startet am vom Depot weitesten Knoten (Knoten 13): die Annahmereihenfolge gleicht der von Kruskal kaum noch (Rang-Korrelation 0.06), der größte Rand schrumpft von 41 auf 34 Kanten.",
    "Gleichstände (gerundet)": "Kosten auf ganze km gerundet: trotz vieler Gleichstände liefern Prim (jede Variante, jeder Start) und Kruskal dieselbe Kantenmenge, weil der Schlüssel (Kosten, Kantenindex) strikt ordnet. Kosten 467.00.",
    "Lehrbuchbeispiel": "Fünf Knoten A bis E, sieben Kanten: Prim ab A nimmt A–B (4), B–D (2), B–C (6), C–E (3); Kruskal nimmt B–D, C–E, A–B, B–C - derselbe MST mit Kosten 15, andere Reihenfolge. Hier gewinnt das Array (13 Schritte) vor Decrease-Key (17), lazy (24) und Kruskal (26).",
}
# Beobachtete Spannweite des MEDIANS der Elementarschritte der gewählten Umsetzung über die 5 festen Instanzen (mit Sicherheitsabstand).
PRESET_EXPECTED_BANDS = {
    "Standardfall (Voreinstellung)": (350.0, 520.0),
    "Dünnes Netz (k = 3)": (440.0, 610.0),
    "Dichter Graph (k = 20)": (700.0, 900.0),
    "Vollständiger Graph (n = 30)": (800.0, 1000.0),
    "Große Instanz (n = 160, vollständig)": (16500.0, 22000.0),
    "Start weit weg": (350.0, 520.0),
    "Gleichstände (gerundet)": (350.0, 520.0),
}
