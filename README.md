# Prim – ein Baum, der von einem Punkt aus wächst – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-prim-demo.streamlit.app/)**

Zweites Stück der **Spannbaum-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", der **Kontrast zu Kruskal**. Dieselbe Aufgabe (ein Depot und n Filialen, gesucht das billigste Leitungsnetz, das alle verbindet: ein **minimaler Spannbaum**), derselbe Baum, aber ein anderer Weg dorthin: **Prim** (Jarník 1930, Prim 1957) startet an **einem** Knoten und lässt einen einzigen Baum wachsen. In jedem Schritt kommt die billigste Kante hinzu, die den Baum mit einem noch nicht angeschlossenen Knoten verbindet. Nur diese Kanten - der **Rand** - müssen verwaltet werden. Wie, ist die eigentliche Frage: als **Array** (jede Runde alle Kandidaten scannen), als **Heap aus Kanten** (veraltete Einträge beim Entnehmen verwerfen, "lazy") oder als **Heap aus Knoten mit Decrease-Key**. Kruskal aus [kruskal-demo](../kruskal-demo) läuft als Vergleich und Kontrollrechnung mit.

**Einordnung in die Reihe:** geplant sind elf Stücke, dies ist das zweite:

```
Kruskal (Wurzel)                                                                           [gebaut: kruskal-demo]
 ├─ Prim (Kontrast: wächst von einem Punkt)                                                [DIESES STÜCK]
 ├─ Borůvka (Kontrast: alle Komponenten parallel)                                          [nicht gebaut]
 ├─ Euklidischer MST (keine n²-Kantenliste, Delaunay)                                      [nicht gebaut]
 ├─ Gerichteter Spannbaum (Chu-Liu/Edmonds)                                                [nicht gebaut]
 ├─ Bottleneck-/Grad-/Hop-beschränkter Spannbaum → Kapazitierter MST                       [nicht gebaut]
 ├─ Steiner-Baum → Prize-Collecting Steiner-Baum                                           [nicht gebaut]
 ├─ MST-Sensitivität & dynamischer MST                                                     [nicht gebaut]
 └─ Zufällige Spannbäume & Kirchhoff                                                       [nicht gebaut]
```

Ergebnis in Kürze: **Der Baum ist immer derselbe - der Aufwand nicht, und Kruskal ist dabei nie das billigste Verfahren.** In **Elementarschritten** (Schlüsselvergleiche plus je eine Einheit je Heap-Operation bzw. Union-Find-Suche, ausdrücklich keine Laufzeit) braucht bei 30 Filialen und k = 6 Nachbarn der **Heap mit Decrease-Key 431**, das **Array 552**, Kruskal **947** und der **lazy-Heap 1157** Schritte. Der lazy-Heap ist also nicht "praktisch gleich gut": Decrease-Key braucht nur das **0,37-Fache**, und beim vollständigen Graphen mit 160 Filialen wächst der lazy-Heap auf **12 424** Einträge (Decrease-Key: 160). Dafür wird das Array **bei dichten Graphen und kleinen Instanzen** unschlagbar (n = 30: ab k = 20; vollständiger Graph: bis n = 40). Startknoten und Umsetzung ändern **nie** den Baum, aber die Reihenfolge, in der Prim die Kanten annimmt, ist der von Kruskal nur lose verwandt (Rang-Korrelation 0,40; bei weit entferntem Start 0,10).

| Frage | Ergebnis (30 Filialen + Depot, k = 6 nächste Nachbarn, Geländezuschlag 0,3, exakte Kosten, Start am Depot, sofern nicht anders angegeben; **Median** über 5 feste Instanzen, Seeds 100000–100004; vollständig deterministisch) |
|---|---|
| **Derselbe Baum?** | ✅ ja, in **100 %** der Instanzen für alle drei Umsetzungen und Kruskal, auch bei gerundeten Kosten mit vielen Gleichständen (der Schlüssel (Kosten, Kantenindex) ordnet strikt) |
| **Spielt der Startknoten eine Rolle?** | Für den Baum nein: von jedem der 31 Knoten aus derselbe Baum (0 % anderer Baum), aber **22 verschiedene Annahmereihenfolgen** bei 31 Starts |
| **Welche Umsetzung ist billig?** | Elementarschritte Array / lazy-Heap / Decrease-Key / Kruskal: **552 / 1157 / 431 / 947**; Decrease-Key gegen lazy: **0,37-fach** |
| **Wo kreuzen sich die Verfahren (Dichte)?** | Steigende Kandidatenzahl k = 3/4/6/10/20/vollständig: Array **495/515/552/624/802/900**, lazy **524/750/1157/1642/2409/2747**, Decrease-Key **245/297/431/599/884/1012**, Kruskal **446/616/947/1521/2992/3805**. Gewinner: Decrease-Key bei k ≤ 10 (5 von 5 Instanzen), **Array ab k = 20** (5 von 5) |
| **Wo kreuzen sich die Verfahren (Größe)?** | k = 6: Array gewinnt bei n = 10 (5 von 5), bei n = 20 gemischt (3 zu 2), ab n = 40 gewinnt Decrease-Key (5 von 5). Vollständiger Graph: Array bei n = 10/20/40, **Decrease-Key ab n = 80** |
| **Wann gewinnt Kruskal?** | ⚠️ nie in Elementarschritten. Nur der lazy-Heap ist im dünnen Graphen **schlechter** als Kruskal (k = 6: 1157 gegen 947); bei k = 3 schlägt Kruskal (446) auch das Array (495) und den lazy-Heap (524), bleibt aber hinter dem Decrease-Key (245) |
| **Wie groß wird der Heap?** | lazy: **68** Einträge (n = 30, k = 6), Decrease-Key: **15**, der Rand selbst bis zu 42 Kanten; 43 veraltete Einträge werden verworfen. Vollständiger Graph n = 160: lazy **12 424**, Decrease-Key **160** |
| **Stimmt n·ln(m/n) für Decrease-Keys?** | ⚠️ nur als Größenordnung: gemessen **56** gegen erwartet 41,2 (n = 30, k = 6); n = 160 vollständig **1850** gegen 705,5. Räumliche Instanzen liegen bis zum 2,6-Fachen darüber |
| **Wie ähnlich ist die Reihenfolge zu Kruskal?** | Rang-Korrelation der Annahmereihenfolge **0,40** (Start am Depot), **0,10** bei weit entferntem Start |

## Was die Demo zeigt

1. **Prim in Aktion** (Schritt-Slider): **Instanz** → **Wachsen im Vergleich** (Slider über die angenommenen Kanten: links Kruskal mit vielen Fragmenten, rechts Prim als ein wachsender Baum ab dem Stern, orange dünn = Rand, orange dick = zuletzt angenommene Kante) → **Ergebnis** (der Baum, dazu ein Streudiagramm: Rang jeder Baumkante bei Kruskal gegen Rang bei Prim; die Diagonale wäre gleiche Reihenfolge).
2. **Was kostet welche Umsetzung?** Gewinner, gewählte Umsetzung, Kruskal, größter Heap; Balken der Elementarschritte je Verfahren; Größe der Datenstruktur über die Schritte (Heap aus Kanten, Heap aus Knoten, Array-Kandidaten, tatsächlicher Rand).
3. **🚩 Startknoten-Experiment** (auf Abruf): Prim von jedem Knoten aus - Anteil anderer Bäume und Zahl verschiedener Annahmereihenfolgen für alle drei Umsetzungen.
4. **📐 Sweeps** über n und k (Elementarschritte, Verhältnis zu Kruskal, größter Heap, Decrease-Keys gegen Erwartung, Rang-Korrelation; 5 feste Instanzen, Median, 10.–90. Perzentil-Band).
5. **🚧 Grenzen:** Tabelle "Annahme – was passiert – wer setzt an".

Regler: Instanz (Depot und Filialen / **Lehrbuchbeispiel**), Filialen n (5–200), Kandidaten k (3 bis vollständig), Geländezuschlag (0–1), Kosten (exakt / gerundet), Seed (+ 🎲), **Prim-Umsetzung** (Array / Heap aus Kanten / Heap mit Decrease-Key) und **Startknoten** (Depot / weitester Knoten / Kartenmitte) - die beiden letzten ändern Aufwand, Reihenfolge und Anzeige, nie den Baum (als Test hinterlegt). Kein Zufall im Kern.

## Messwerte der Presets

| Preset | Instanz | Ergebnis (Elementarschritte Array / lazy / Decrease-Key / Kruskal) |
|---|---|---|
| Standardfall (Voreinstellung) | 30 Filialen, k = 6, Seed 35 | 548 / 1282 / **413** / 929; Kosten 466,63; Rang-Korrelation 0,47 |
| Dünnes Netz (k = 3) | 59 Kanten | 494 / 466 / **249** / 456 |
| Dichter Graph (k = 20) | 361 Kanten | **796** / 2848 / 841 / 3009; lazy-Heap bis 307 Einträge (Decrease-Key 26) |
| Vollständiger Graph (n = 30) | 465 Kanten | **900** / 3298 / 977 / 3913; lazy-Heap bis 410 Einträge, 79 veraltete Einträge verworfen |
| Große Instanz (n = 160, vollständig) | 12 880 Kanten | 25 600 / 66 602 / **19 071** / 162 373; lazy-Heap bis 12 532 Einträge (Decrease-Key 160) |
| Start weit weg | Standardfall, Start = Knoten 13 | derselbe Baum, Rang-Korrelation 0,06, größter Rand 34 statt 41 Kanten |
| Gleichstände (gerundet) | Seed 35 | Kosten 467,00; von jedem Start und in jeder Umsetzung derselbe Baum |
| Lehrbuchbeispiel | 5 Knoten, 7 Kanten | **13** / 24 / 17 / 26; Prim nimmt A–B, B–D, B–C, C–E, Kruskal B–D, C–E, A–B, B–C; Kosten 15 |

Die einzelne Instanz weicht von den Medianen ab - die Mediane sind die belastbaren Zahlen; die Karten-Presets prüfen sich zusätzlich über die 5 festen Instanzen gegen eine gemessene Spannweite des Medians der Schritte der gewählten Umsetzung (`tests/test_presets.py`).

## Modell und Verfahren

- **Instanz** (`prim_scenario.py`, aus kruskal-demo übernommen): Depot (Knoten 0, am linken Rand) und n Filialen im Quadrat; Kantenkosten = euklidischer Abstand mal ein Geländefaktor in [1, 1 + Zuschlag]; Kandidatengraph vollständig oder die k nächsten Nachbarn (Zusammenhang garantiert); "Kosten runden" erzeugt bewusst viele Gleichstände; ein Lehrbuchbeispiel mit 5 Knoten.
- **Prim** (`prim_algorithm.py`): ein eigener binärer Heap mit Zählern (Vergleiche, Vertauschungen, Einfügungen, Entnahmen, Decrease-Keys, größte Größe) in zwei Formen (Heap aus Kanten mit veralteten Einträgen, indizierter Heap aus Knoten mit Decrease-Key) und die Array-Variante. Alle drei nutzen den Schlüssel (Kosten, Kantenindex), der strikt ordnet: derselbe Baum für jeden Startknoten und jede Umsetzung, auch bei Gleichständen.
- **Kruskal** (Kopie aus kruskal-demo mit **eigenem Mergesort**, der Vergleiche zählt - CPython-`sorted` wäre plattform- und versionsabhängig): Aufwand = Sortier-Vergleiche + Union-Find-Suchen + Zeigerschritte.
- **Elementarschritte:** Prim-Array = gescannte Kandidaten (genau n(n − 1)/2); Prim-Heap = Vergleiche plus je eine Einheit je Einfügung, Entnahme und Decrease-Key; Kruskal wie oben. Ein Näherungsmaß für den Vergleich, **keine Laufzeit**.
- **Auswertung** (`prim_evaluation.py`): alle Verfahren auf derselben Instanz, Gewinner, Baumgleichheit, Rang-Korrelation der Annahmereihenfolge (Spearman), Decrease-Keys gegen n·ln(m/n), Startknoten-Invarianz, `run_config` (5 feste Instanzen, Median + Spanne) und `sweep`.

## Was nicht funktioniert hat / Grenzen

- **Erwartung "der lazy-Heap ist so gut wie Decrease-Key" - in Elementarschritten widerlegt:** 1157 gegen 431 (n = 30, k = 6), beim vollständigen Graphen n = 160 57 950 gegen 19 195. Ob das in einer konkreten Sprache auch die Laufzeit entscheidet, ist hier **nicht gemessen** (ein in C geschriebener Heap oder die Speicherlokalität ändern das Bild).
- **Erwartung "Kruskal verliert bei dichten Graphen wegen des Sortierens" - bestätigt, aber nicht überall:** beim vollständigen Graphen n = 160 braucht Kruskal 161 015 Schritte gegen 19 195 (Decrease-Key). Im sehr dünnen Graphen (k = 3) ist er dagegen konkurrenzfähig und schlägt Array und lazy-Heap.
- **Erwartung "Decrease-Keys folgen n·ln(m/n)" - nur die Größenordnung:** die Herleitung gilt für zufällige Kantenreihenfolgen; räumliche Instanzen liegen bis zum 2,6-Fachen darüber.
- **Das einfache Array ist nicht veraltet:** bei dichten Graphen und kleinen Instanzen gewinnt es, weil es keine Datenstruktur verwaltet.
- **Nicht gebaut:** **Fibonacci-Heap** (Fredman & Tarjan 1987: O(m + n log n)); in der Praxis gilt der binäre Heap meist als schneller, das ist hier nicht gemessen. Ebenso nicht gebaut: Borůvka, Euklidischer MST, gerichtete Spannbäume, Nebenbedingungen, Steiner-Bäume, Sensitivität, Kirchhoff. Familienähnlichkeit: Prim ist Dijkstra mit anderer Schlüsselregel (Kosten der Randkante statt Weglänge) - ein Bezug zur Kürzeste-Wege-Linie, hier nicht vertieft.
- **Synthetische Instanzen:** Punkte im Quadrat, euklidische Kosten mit Zufallszuschlag; keine Straßennetze, Kapazitäten oder Richtungen.

## Verifikation

- **Korrektheitskette:** jede Umsetzung liefert einen Spannbaum; **Baum == Kruskal** über viele Instanzen inklusive Gleichständen; Kosten gegen scipy und Brute-Force (5 Knoten); **Startknoten-Invarianz** (von jedem Knoten aus derselbe Baum, Reihenfolgen verschieden); **Schnitt-Eigenschaft** direkt an der Annahmereihenfolge; Heap-Invarianten nach jeder Operation, Decrease-Key gegen eine Referenz mit sortierter Liste; Zähler-Identitäten (Array-Scans genau n(n − 1)/2, lazy Entnahmen = n − 1 + veraltete, Decrease-Key-Einfügungen = n); Mergesort-Vergleichsschranken (sortiert und umgekehrt sortiert, n = 64: 192); Sonderfälle (n = 1, n = 2, Pfad, gleiche Kosten, unzusammenhängend, Start außerhalb).
- **Alle Zahlen der App-Texte sind als Tests hinterlegt**, über dieselben Auswertungsfunktionen wie die App selbst (`ev.run_config`/`ev.sweep`/`ev.start_invariance`), NIE über ein Ad-hoc-Skript; die Elementarschritte sind ganzzahlig und plattformunabhängig; AppTest-Rauchtests (Voreinstellung, jedes Preset, jeder Schritt, jede Kante, beide Instanz-Typen, Extremwerte, Würfel, Permalink-Grenzen, Instanzwechsel, Startknoten-Experiment, Sweeps auf Abruf, Footer).

Literatur: Prim, R. C. (1957). *Shortest connection networks and some generalizations.* Bell System Technical Journal 36(6), 1389-1401. Jarník, V. (1930). *O jistém problému minimálním.* Práce Moravské přírodovědecké společnosti 6, 57-63. Fredman, M. L., & Tarjan, R. E. (1987). *Fibonacci heaps and their uses in improved network optimization algorithms.* Journal of the ACM 34(3), 596-615.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: Instanz, Schritte (mit Kanten-Slider), Aufwand, Startknoten-Experiment, Sweeps, Grenzen, Mathe |
| `prim_algorithm.py`, `prim_unionfind.py` | Heap mit Zählern, Prim in drei Umsetzungen, Kruskal-Kopie mit eigenem Mergesort; Union-Find |
| `prim_scenario.py` | Depot-Instanz, Lehrbuchbeispiel |
| `prim_constants.py` | Konstanten, Presets, gemessene Werte |
| `prim_evaluation.py` | Kennzahlen, Sweeps, Startknoten-Invarianz |
| `prim_presets.py`, `prim_visualization.py` | Permalink/Presets, Plotly-Figuren (Wachsen im Vergleich, Ergebnis, Reihenfolge, Aufwand, Heap-Verlauf, Sweeps) |
| `tests/` | Korrektheitskette, Szenario/Auswertung, Aussagen der App, Presets, AppTest |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
