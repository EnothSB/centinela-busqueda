# Verificación de las heurísticas h1 y h2

Generado con `python -m centinela.verificar`. Para cada escenario se enumeran todos los estados alcanzables, se calcula h* exacto con Dijkstra inverso desde los estados meta y se comprueban la admisibilidad (h(n) ≤ h*(n) en todo estado) y la consistencia (h(n) ≤ c(n, a, n') + h(n') en toda arista).

## Espacio de estados alcanzable

| Escenario | Estados alcanzables | Aristas | Estados meta | Estados sin salida | h* del inicial |
|---|---|---|---|---|---|
| leve | 144 | 768 | 18 | 0 | 5 |
| moderado | 63 | 318 | 9 | 0 | 6 |
| severo | 672 | 3896 | 6 | 0 | 12 |
| critico | 259 | 1249 | 1 | 0 | 18 |

## Admisibilidad y consistencia

La razón h/h* se promedia sobre los estados no meta con h* finito; un valor más cercano a 1 indica una heurística más informada.

| Escenario | Heurística | h(inicial) | Violaciones de admisibilidad | Violaciones de consistencia | h/h* promedio | Estados con h = h* |
|---|---|---|---|---|---|---|
| leve | h1 | 2 | 0 | 0 | 0.386 | 0 |
| leve | h2 | 5 | 0 | 0 | 1.000 | 126 |
| moderado | h1 | 2 | 0 | 0 | 0.511 | 9 |
| moderado | h2 | 6 | 0 | 0 | 1.000 | 54 |
| severo | h1 | 6 | 0 | 0 | 0.545 | 26 |
| severo | h2 | 12 | 0 | 0 | 1.000 | 666 |
| critico | h1 | 7 | 0 | 0 | 0.535 | 15 |
| critico | h2 | 18 | 0 | 0 | 1.000 | 258 |

## Conclusión

Ninguna heurística presenta violaciones: h1 y h2 son admisibles y consistentes en todo el espacio alcanzable de los cuatro escenarios.
