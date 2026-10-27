# Benchmark de búsqueda de Centinela

Entorno: Python 3.14.8 (CPython) en Windows-11-10.0.26300-SP0.

Generado con `python -m centinela.benchmark`. Las métricas de nodos son deterministas; el tiempo es la mediana de 30 repeticiones medidas con `time.perf_counter`. b* es el factor de ramificación efectivo calculado con los nodos generados y la profundidad de la solución.

## BFS, DFS y A* (h2)

| Escenario | Algoritmo | Costo | Profundidad | Expandidos | Generados | Frontera máx. | Memoria máx. | b* | Tiempo (ms, mediana de 30) |
|---|---|---|---|---|---|---|---|---|---|
| leve | BFS | 5 | 2 | 3 | 23 | 16 | 19 | 4.322 | 0.053 |
| leve | DFS | 10 | 5 | 5 | 29 | 20 | 25 | 1.657 | 0.061 |
| leve | A*(h2) | 5 | 2 | 2 | 18 | 14 | 16 | 3.772 | 0.071 |
| moderado | BFS | 6 | 3 | 14 | 86 | 22 | 36 | 4.035 | 0.175 |
| moderado | DFS | 10 | 5 | 5 | 27 | 13 | 18 | 1.627 | 0.054 |
| moderado | A*(h2) | 6 | 3 | 3 | 24 | 15 | 18 | 2.485 | 0.078 |
| severo | BFS | 13 | 7 | 467 | 2938 | 192 | 597 | 2.950 | 6.065 |
| severo | DFS | 14 | 8 | 9 | 52 | 39 | 47 | 1.418 | 0.099 |
| severo | A*(h2) | 12 | 7 | 7 | 53 | 40 | 47 | 1.526 | 0.271 |
| critico | BFS | 18 | 9 | 251 | 1218 | 65 | 258 | 2.044 | 2.739 |
| critico | DFS | 18 | 9 | 9 | 36 | 25 | 34 | 1.272 | 0.120 |
| critico | A*(h2) | 18 | 9 | 9 | 46 | 31 | 40 | 1.320 | 0.215 |

## A* con h0 (UCS), h1 y h2

| Escenario | Heurística | Costo | Profundidad | Expandidos | Generados | Memoria máx. | b* | Tiempo (ms, mediana de 30) |
|---|---|---|---|---|---|---|---|---|
| leve | A*(h0) | 5 | 2 | 32 | 201 | 92 | 13.686 | 0.432 |
| leve | A*(h1) | 5 | 2 | 14 | 98 | 57 | 9.412 | 0.240 |
| leve | A*(h2) | 5 | 2 | 2 | 18 | 16 | 3.772 | 0.071 |
| moderado | A*(h0) | 6 | 3 | 38 | 210 | 59 | 5.576 | 0.433 |
| moderado | A*(h1) | 6 | 3 | 21 | 125 | 46 | 4.626 | 0.288 |
| moderado | A*(h2) | 6 | 3 | 3 | 24 | 18 | 2.485 | 0.078 |
| severo | A*(h0) | 12 | 7 | 566 | 3414 | 669 | 3.019 | 7.403 |
| severo | A*(h1) | 12 | 7 | 314 | 2024 | 601 | 2.785 | 4.695 |
| severo | A*(h2) | 12 | 7 | 7 | 53 | 47 | 1.526 | 0.274 |
| critico | A*(h0) | 18 | 9 | 258 | 1246 | 259 | 2.050 | 2.734 |
| critico | A*(h1) | 18 | 9 | 243 | 1177 | 259 | 2.035 | 2.787 |
| critico | A*(h2) | 18 | 9 | 9 | 46 | 40 | 1.320 | 0.214 |
