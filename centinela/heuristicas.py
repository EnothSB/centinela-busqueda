"""Heurísticas para A* en el problema de Centinela.

Todas reciben un ``Estado`` y devuelven una estimación del costo restante
hasta la meta.

- ``h0``: siempre 0; con ella A* equivale a la búsqueda de costo uniforme.
- ``h1``: número de condiciones de meta incumplidas.
- ``h2``: suma de subproblemas relajados e independientes (propuesta).

La admisibilidad y la consistencia se argumentan en cada docstring y se
comprueban de forma exhaustiva con ``python -m centinela.verificar``.
"""

from __future__ import annotations

import math
from itertools import combinations

from .problema import (
    APP,
    BD,
    COSTOS,
    REDUCCION_DISCO,
    SERVIDORES,
    Estado,
)

#: Costo de reinicio del servicio de cada servidor (nginx, app, bd).
COSTO_REINICIO = (
    COSTOS["reiniciar_nginx"],
    COSTOS["reiniciar_app"],
    COSTOS["reiniciar_bd"],
)


def h0(estado: Estado) -> int:
    """Heurística nula: siempre devuelve 0.

    Es trivialmente admisible y consistente; A* con ``h0`` se comporta como
    la búsqueda de costo uniforme (Dijkstra).
    """
    return 0


def h1(estado: Estado) -> int:
    """Número de condiciones de meta incumplidas.

    Cuenta: cada disco con nivel mayor a 1, cada servicio caído, la fuga de
    memoria mayor a 1 con la app activa y el bloqueo en la BD.

    Es consistente porque ninguna acción reduce el conteo en más que su
    costo: cada acción de disco o reinicio arregla a lo sumo una condición
    con costo de al menos 1; ``reiniciar_app`` (costo 3) arregla la caída o
    la memoria, no ambas a la vez, porque la memoria solo se cuenta con la
    app activa; ``reiniciar_bd`` (costo 5) arregla a lo sumo dos (BD caída y
    bloqueo) y además puede tumbar la app. Como h1 vale 0 en la meta, la
    consistencia implica admisibilidad.
    """
    incumplidas = sum(1 for nivel in estado.disco if nivel > 1)
    incumplidas += sum(1 for activo in estado.activo if not activo)
    if estado.activo[APP] and estado.mem_app > 1:
        incumplidas += 1
    if estado.bloqueo:
        incumplidas += 1
    return incumplidas


def costo_minimo_disco(estado: Estado, servidor: int) -> float:
    """Costo mínimo para dejar el disco de ``servidor`` en nivel 1 o menos.

    Enumera los subconjuntos de las acciones de limpieza aún disponibles en
    ese servidor (``rotar_logs`` si no se ha rotado, ``limpiar_tmp`` si no
    se ha limpiado) y devuelve el costo del más barato que alcanza. Si
    ninguno alcanza, devuelve ``math.inf``: el estado no tiene salida,
    porque solo esas acciones reducen el disco.
    """
    exceso = estado.disco[servidor] - 1
    if exceso <= 0:
        return 0
    disponibles = []
    if not estado.rotado[servidor]:
        disponibles.append("rotar_logs")
    if not estado.limpiado[servidor]:
        disponibles.append("limpiar_tmp")
    mejor = math.inf
    for tamano in range(1, len(disponibles) + 1):
        for subconjunto in combinations(disponibles, tamano):
            reduccion = sum(REDUCCION_DISCO[a] for a in subconjunto)
            if reduccion >= exceso:
                mejor = min(mejor, sum(COSTOS[a] for a in subconjunto))
    return mejor


def h2(estado: Estado) -> float:
    """Suma de subproblemas relajados e independientes (heurística propuesta).

    Componentes:

    a) Por servidor, ``costo_minimo_disco``: costo mínimo de bajar el disco
       a nivel 1 o menos con las acciones de limpieza aún disponibles
       (infinito si ninguna combinación alcanza).
    b) Costo de reinicio de cada servicio caído (nginx 1, app 3, bd 5).
    c) Si la app está activa y ``mem_app > 1``, +3 (``reiniciar_app``).
    d) Si hay bloqueo y la BD está activa, +2 (``terminar_bloqueo``). Si la
       BD está caída no se suma, porque su reinicio ya quita el bloqueo.

    Relajación: se ignoran las precondiciones de disco lleno y de BD activa
    para reiniciar, y la caída de la app que provoca ``reiniciar_bd``.

    Admisibilidad: cada acción del plan óptimo reduce como máximo un
    componente, salvo ``reiniciar_bd``, que solo puede cubrir a la vez su
    propio reinicio y el bloqueo; pero el bloqueo con la BD caída no se
    suma (d). Del mismo modo, ``reiniciar_app`` con la app caída cubre su
    reinicio y la memoria, que en ese caso no se suma (c). Por tanto, el
    costo del plan óptimo es al menos la suma de los componentes.

    Consistencia: para toda arista ``n -> n'`` con acción ``a`` se cumple
    ``h2(n) <= c(a) + h2(n')``. ``rotar_logs`` y ``limpiar_tmp`` reducen el
    componente (a) de su servidor en a lo sumo su costo, porque toda
    solución del subproblema en ``n'`` más la acción usada es una solución
    en ``n``. ``reiniciar_nginx`` reduce h2 en 1; ``reiniciar_app`` en 3 (o
    su reinicio o la memoria); ``terminar_bloqueo`` en 2; ``reiniciar_bd``
    reduce a lo sumo 5 (su reinicio con la BD caída, o el bloqueo 2 y la
    memoria 3 con la BD activa, pero entonces suma 3 por tumbar la app).
    Como h2 vale 0 en toda meta, la consistencia implica admisibilidad. Los
    estados con h2 infinita no tienen salida, y sus sucesores tampoco.
    """
    total: float = 0
    for servidor in range(len(SERVIDORES)):
        total += costo_minimo_disco(estado, servidor)
    for servidor, activo in enumerate(estado.activo):
        if not activo:
            total += COSTO_REINICIO[servidor]
    if estado.activo[APP] and estado.mem_app > 1:
        total += COSTOS["reiniciar_app"]
    if estado.bloqueo and estado.activo[BD]:
        total += COSTOS["terminar_bloqueo"]
    return total


#: Heurísticas disponibles por nombre.
HEURISTICAS = {"h0": h0, "h1": h1, "h2": h2}
