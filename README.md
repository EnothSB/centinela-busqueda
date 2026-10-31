# Centinela · Fase 2: búsqueda en el espacio de estados

Proyecto de la asignatura Inteligencia Artificial. Implementa y compara
búsqueda en anchura (BFS), búsqueda en profundidad (DFS) y A* sobre una
abstracción del problema de **Centinela**, el agente de la Fase 1, usando
solo la biblioteca estándar de Python.

| | |
|---|---|
| **Autor** | Enoth Salcedo Blandon (código 200632) |
| **Universidad** | Universidad Militar Nueva Granada, Facultad de Estudios a Distancia, Programa de Ingeniería |
| **Asignatura** | Inteligencia Artificial, Fase 2 del Proyecto Integrador |
| **Docente** | John Edwin Vera Vera |
| **Fecha** | Octubre de 2026 |

## Relación con la Fase 1

En la Fase 1, Centinela se definió como un agente basado en utilidad que
atiende incidentes de una plataforma web institucional (servidores Oracle
Linux 9 con nginx, aplicación y base de datos, monitoreados con
Prometheus, Loki y Alertmanager) aplicando runbooks de bajo riesgo. Ese
entorno es estocástico, parcialmente observable y continuo.

Para aplicar búsqueda clásica, en esta fase el entorno se abstrae como
**determinista, discreto, totalmente observable y estático durante la
planificación**: el agente observa el estado completo, planifica la
secuencia de runbooks de menor costo y luego la ejecuta.

## Formalización

**Estado** (inmutable y hashable), con los servidores en orden fijo
`web`, `app`, `bd`:

| Componente | Dominio | Significado |
|---|---|---|
| `disco` | 0..4 por servidor | 0: <60 %, 1: 60-75 %, 2: 75-85 %, 3: 85-95 %, 4: ≥95 % lleno |
| `rotado` | booleano por servidor | logs ya rotados |
| `limpiado` | booleano por servidor | temporales ya limpiados |
| `activo` | booleano por servidor | servicio activo (nginx, aplicación, base de datos) |
| `mem_app` | 0..3 | fuga de memoria de la aplicación |
| `bloqueo` | booleano | consulta bloqueada en la base de datos |

**Acciones** (se generan en este orden fijo):

| Acción | Precondición | Efecto | Costo |
|---|---|---|---|
| `rotar_logs(s)` | `not rotado[s]` y `disco[s] > 0` | `disco[s] -= 2` (mín. 0), `rotado[s] = True` | 2 |
| `limpiar_tmp(s)` | `not limpiado[s]` y `disco[s] > 0` | `disco[s] -= 1` (mín. 0), `limpiado[s] = True` | 1 |
| `reiniciar_nginx` | `disco[web] < 4` | `activo[web] = True` | 1 |
| `reiniciar_app` | `disco[app] < 4` y `activo[bd]` | `activo[app] = True`, `mem_app = 0` | 3 |
| `reiniciar_bd` | `disco[bd] < 4` | `activo[bd] = True`, `bloqueo = False`, `activo[app] = False` | 5 |
| `terminar_bloqueo` | `activo[bd]` y `bloqueo` | `bloqueo = False` | 2 |

**Meta**: los tres servicios activos, todos los discos en nivel ≤ 1,
`mem_app ≤ 1` y sin bloqueo. **Costo de ruta**: suma de los costos de las
acciones (minutos de servicio degradado ponderados por riesgo).

**Escenarios** (`centinela/escenarios.py`):

| Escenario | Discos (web, app, bd) | Servicios activos | `mem_app` | Bloqueo | Costo óptimo |
|---|---|---|---|---|---|
| `leve` | (1, 3, 1) | web, app, bd | 2 | no | 5 |
| `moderado` | (1, 4, 1) | web, bd | 0 | no | 6 |
| `severo` | (4, 3, 2) | app, bd | 3 | sí | 12 |
| `critico` | (4, 4, 4) | ninguno | 0 | sí | 18 |

**Heurísticas** (`centinela/heuristicas.py`):

- `h0`: 0; A* con h0 equivale a la búsqueda de costo uniforme (UCS).
- `h1`: número de condiciones de meta incumplidas.
- `h2` (propuesta): suma de subproblemas relajados e independientes:
  costo mínimo de limpieza por disco con las acciones aún disponibles,
  reinicio de cada servicio caído, +3 si la app activa tiene fuga y +2 si
  hay bloqueo con la BD activa. Su docstring justifica la admisibilidad y
  la consistencia, y `python -m centinela.verificar` las comprueba en
  todos los estados alcanzables (ver `resultados/heuristica.md`). En los
  cuatro escenarios h2 coincide con el costo exacto h* en todos los
  estados, porque los subproblemas casi no interactúan.

## Requisitos

- Python 3.10 o superior (probado con Python 3.14).
- Ninguna dependencia externa: solo la biblioteca estándar.

## Uso

Todos los comandos se ejecutan desde la raíz del repositorio.

```bash
# Resolver un escenario (algoritmos: bfs, dfs, ucs, astar; heurísticas: h0, h1, h2)
python -m centinela --escenario severo --algoritmo astar
python -m centinela --escenario critico --algoritmo astar --heuristica h1
python -m centinela --escenario leve --algoritmo bfs

# Benchmark: escribe resultados/benchmark.csv, benchmark.md y soluciones.md
python -m centinela.benchmark

# Verificación exhaustiva de h1 y h2: escribe resultados/heuristica.md
python -m centinela.verificar

# Pruebas unitarias
python -m unittest discover -s tests -v
```

## Estructura

```text
centinela-busqueda/
├── centinela/
│   ├── __init__.py      # descripción del paquete y utilidades de salida
│   ├── __main__.py      # CLI: python -m centinela
│   ├── problema.py      # estado, acciones, transición, meta y costos
│   ├── escenarios.py    # estados iniciales leve, moderado, severo y crítico
│   ├── heuristicas.py   # h0, h1 y h2
│   ├── busqueda.py      # Problema, Nodo, BFS, DFS, A*, UCS y b*
│   ├── benchmark.py     # comparación experimental
│   └── verificar.py     # admisibilidad y consistencia con h* exacto
├── tests/               # pruebas con unittest
├── resultados/          # tablas y soluciones generadas
└── README.md
```

## Resultados del benchmark

Copia de `resultados/benchmark.md`. Los tiempos dependen de la máquina;
las métricas de nodos son deterministas.

Entorno: Python 3.14.8 (CPython) en Windows-11-10.0.26300-SP0.

Generado con `python -m centinela.benchmark`. Las métricas de nodos son deterministas; el tiempo es la mediana de 30 repeticiones medidas con `time.perf_counter`. b* es el factor de ramificación efectivo calculado con los nodos generados y la profundidad de la solución.

### BFS, DFS y A* (h2)

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

### A* con h0 (UCS), h1 y h2

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

Las secuencias de acciones del escenario severo para cada algoritmo están
en `resultados/soluciones.md`. BFS encuentra el plan de menor profundidad
pero no de menor costo (13 frente a 12 en el escenario severo), DFS
encuentra planes válidos pero no garantiza optimalidad (en el escenario
crítico coincide con el óptimo por el orden de las acciones), y A* con h2 encuentra el plan
óptimo expandiendo tantos nodos como acciones tiene la solución.

## Referencias

- Russell, S. y Norvig, P. (2021). *Artificial Intelligence: A Modern
  Approach* (4.ª ed.). Pearson.
- aimacode. (s. f.). *aima-python: Python implementation of algorithms
  from Russell and Norvig's "Artificial Intelligence: A Modern Approach"*
  [Repositorio de código]. GitHub. https://github.com/aimacode/aima-python
