"""Verificación exhaustiva de admisibilidad y consistencia de las heurísticas.

Para cada escenario:

1. Enumera todos los estados alcanzables desde el inicial y todas las
   aristas (transiciones) entre ellos.
2. Calcula el costo exacto h*(n) hasta la meta más cercana con Dijkstra
   inverso, partiendo simultáneamente de todos los estados meta. Como todo
   sucesor de un estado alcanzable también es alcanzable, h* calculado
   sobre este subgrafo coincide con el h* del problema completo.
3. Comprueba para h1 y h2 la admisibilidad, h(n) <= h*(n) en todo estado,
   y la consistencia, h(n) <= c(n, a, n') + h(n') en toda arista.
4. Reporta el número de violaciones y la razón promedio h/h* sobre los
   estados no meta con h* finito (más cerca de 1 indica una heurística
   más informada).

Uso::

    python -m centinela.verificar

Escribe ``resultados/heuristica.md`` e imprime el mismo informe.
"""

from __future__ import annotations

import argparse
import heapq
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
from typing import Callable, Hashable

from . import configurar_salida_utf8
from .escenarios import ESCENARIOS
from .heuristicas import h1, h2
from .problema import ProblemaCentinela

#: Tolerancia numérica para comparar costos.
EPSILON = 1e-9

#: Heurísticas que se verifican.
HEURISTICAS_VERIFICADAS = {"h1": h1, "h2": h2}

#: Carpeta de resultados por omisión (``resultados/`` en la raíz del repo).
CARPETA_RESULTADOS = Path(__file__).resolve().parent.parent / "resultados"

Arista = tuple[Hashable, object, float, Hashable]


@dataclass
class InformeHeuristica:
    """Resultado de verificar una heurística sobre un espacio de estados.

    Atributos:
        nombre: nombre de la heurística.
        valor_inicial: valor de la heurística en el estado inicial.
        violaciones_admisibilidad: estados con h(n) > h*(n).
        violaciones_consistencia: aristas con h(n) > c + h(n').
        razon_promedio: promedio de h/h* en estados no meta con h* finito.
        estados_exactos: estados no meta con h* finito donde h = h*.
    """

    nombre: str
    valor_inicial: float
    violaciones_admisibilidad: int
    violaciones_consistencia: int
    razon_promedio: float
    estados_exactos: int


@dataclass
class InformeEscenario:
    """Resumen del espacio de estados de un escenario y sus heurísticas."""

    escenario: str
    estados: int
    aristas: int
    metas: int
    sin_salida: int
    h_estrella_inicial: float
    heuristicas: dict[str, InformeHeuristica] = field(default_factory=dict)


def explorar_espacio(problema) -> tuple[list, list[Arista]]:
    """Enumera los estados alcanzables y las aristas con un recorrido BFS.

    Returns:
        Una tupla ``(estados, aristas)``: la lista de estados alcanzables en
        orden de descubrimiento y la lista de aristas
        ``(origen, accion, costo, destino)``.
    """
    inicial = problema.estado_inicial
    vistos = {inicial}
    estados = [inicial]
    aristas: list[Arista] = []
    cola = deque([inicial])
    while cola:
        estado = cola.popleft()
        for accion in problema.acciones(estado):
            siguiente = problema.resultado(estado, accion)
            costo = problema.costo_accion(estado, accion, siguiente)
            aristas.append((estado, accion, costo, siguiente))
            if siguiente not in vistos:
                vistos.add(siguiente)
                estados.append(siguiente)
                cola.append(siguiente)
    return estados, aristas


def costos_exactos(estados: list, aristas: list[Arista],
                   es_meta: Callable[[Hashable], bool]) -> dict:
    """Calcula h*(n) para cada estado con Dijkstra inverso multifuente.

    Invierte las aristas y propaga distancias desde todos los estados meta
    a la vez. Los estados desde los que no se alcanza ninguna meta reciben
    ``math.inf``.
    """
    inversas: dict = defaultdict(list)
    for origen, _, costo, destino in aristas:
        inversas[destino].append((origen, costo))
    distancia = {estado: math.inf for estado in estados}
    desempate = count()
    cola: list = []
    for estado in estados:
        if es_meta(estado):
            distancia[estado] = 0
            heapq.heappush(cola, (0, next(desempate), estado))
    while cola:
        d, _, estado = heapq.heappop(cola)
        if d > distancia[estado]:
            continue
        for anterior, costo in inversas[estado]:
            nueva = d + costo
            if nueva < distancia[anterior]:
                distancia[anterior] = nueva
                heapq.heappush(cola, (nueva, next(desempate), anterior))
    return distancia


def verificar_heuristica(h: Callable, estados: list, aristas: list[Arista],
                         h_estrella: dict, inicial=None) -> InformeHeuristica:
    """Verifica admisibilidad y consistencia de ``h`` en todo el espacio.

    Args:
        h: heurística a verificar.
        estados: estados alcanzables.
        aristas: aristas ``(origen, accion, costo, destino)``.
        h_estrella: costo exacto hasta la meta de cada estado.
        inicial: estado inicial (por omisión, el primero de ``estados``).
    """
    valores = {estado: h(estado) for estado in estados}
    no_admisibles = sum(
        1 for estado in estados
        if valores[estado] > h_estrella[estado] + EPSILON
    )
    inconsistentes = sum(
        1 for origen, _, costo, destino in aristas
        if valores[origen] > costo + valores[destino] + EPSILON
    )
    razones = []
    exactos = 0
    for estado in estados:
        exacto = h_estrella[estado]
        if exacto == 0 or math.isinf(exacto):
            continue
        razones.append(valores[estado] / exacto)
        if abs(valores[estado] - exacto) <= EPSILON:
            exactos += 1
    razon = sum(razones) / len(razones) if razones else 0.0
    inicial = estados[0] if inicial is None else inicial
    return InformeHeuristica(
        nombre=getattr(h, "__name__", "h"),
        valor_inicial=valores[inicial],
        violaciones_admisibilidad=no_admisibles,
        violaciones_consistencia=inconsistentes,
        razon_promedio=razon,
        estados_exactos=exactos,
    )


def analizar_escenario(nombre: str) -> InformeEscenario:
    """Enumera el espacio de un escenario y verifica h1 y h2 sobre él."""
    problema = ProblemaCentinela(ESCENARIOS[nombre])
    estados, aristas = explorar_espacio(problema)
    h_estrella = costos_exactos(estados, aristas, problema.es_meta)
    informe = InformeEscenario(
        escenario=nombre,
        estados=len(estados),
        aristas=len(aristas),
        metas=sum(1 for s in estados if problema.es_meta(s)),
        sin_salida=sum(1 for s in estados if math.isinf(h_estrella[s])),
        h_estrella_inicial=h_estrella[problema.estado_inicial],
    )
    for clave, h in HEURISTICAS_VERIFICADAS.items():
        informe.heuristicas[clave] = verificar_heuristica(
            h, estados, aristas, h_estrella, problema.estado_inicial
        )
    return informe


def _formato(valor: float) -> str:
    """Formatea un costo, mostrando infinito como texto."""
    if math.isinf(valor):
        return "inf"
    return f"{valor:g}"


def generar_markdown(informes: list[InformeEscenario]) -> str:
    """Construye el informe en Markdown con las dos tablas de resultados."""
    lineas = [
        "# Verificación de las heurísticas h1 y h2",
        "",
        "Generado con `python -m centinela.verificar`. Para cada escenario se "
        "enumeran todos los estados alcanzables, se calcula h* exacto con "
        "Dijkstra inverso desde los estados meta y se comprueban la "
        "admisibilidad (h(n) ≤ h*(n) en todo estado) y la consistencia "
        "(h(n) ≤ c(n, a, n') + h(n') en toda arista).",
        "",
        "## Espacio de estados alcanzable",
        "",
        "| Escenario | Estados alcanzables | Aristas | Estados meta | "
        "Estados sin salida | h* del inicial |",
        "|---|---|---|---|---|---|",
    ]
    for inf in informes:
        lineas.append(
            f"| {inf.escenario} | {inf.estados} | {inf.aristas} | "
            f"{inf.metas} | {inf.sin_salida} | "
            f"{_formato(inf.h_estrella_inicial)} |"
        )
    lineas += [
        "",
        "## Admisibilidad y consistencia",
        "",
        "La razón h/h* se promedia sobre los estados no meta con h* finito; "
        "un valor más cercano a 1 indica una heurística más informada.",
        "",
        "| Escenario | Heurística | h(inicial) | Violaciones de "
        "admisibilidad | Violaciones de consistencia | h/h* promedio | "
        "Estados con h = h* |",
        "|---|---|---|---|---|---|---|",
    ]
    for inf in informes:
        for clave, hinf in inf.heuristicas.items():
            lineas.append(
                f"| {inf.escenario} | {clave} | "
                f"{_formato(hinf.valor_inicial)} | "
                f"{hinf.violaciones_admisibilidad} | "
                f"{hinf.violaciones_consistencia} | "
                f"{hinf.razon_promedio:.3f} | {hinf.estados_exactos} |"
            )
    total = sum(
        h.violaciones_admisibilidad + h.violaciones_consistencia
        for inf in informes for h in inf.heuristicas.values()
    )
    lineas += [
        "",
        "## Conclusión",
        "",
        ("Ninguna heurística presenta violaciones: h1 y h2 son admisibles y "
         "consistentes en todo el espacio alcanzable de los cuatro "
         "escenarios." if total == 0 else
         f"Se encontraron {total} violaciones; revise las tablas."),
        "",
    ]
    return "\n".join(lineas)


def principal(argumentos: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si no hay violaciones y 1 si las hay."""
    analizador = argparse.ArgumentParser(
        prog="python -m centinela.verificar",
        description="Verifica la admisibilidad y la consistencia de h1 y h2.",
    )
    analizador.add_argument("--salida", type=Path, default=CARPETA_RESULTADOS,
                            help="carpeta donde se escribe heuristica.md")
    args = analizador.parse_args(argumentos)
    configurar_salida_utf8()

    informes = [analizar_escenario(nombre) for nombre in ESCENARIOS]
    texto = generar_markdown(informes)
    args.salida.mkdir(parents=True, exist_ok=True)
    destino = args.salida / "heuristica.md"
    destino.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"Informe escrito en {destino}")
    violaciones = sum(
        h.violaciones_admisibilidad + h.violaciones_consistencia
        for inf in informes for h in inf.heuristicas.values()
    )
    return 0 if violaciones == 0 else 1


if __name__ == "__main__":
    raise SystemExit(principal())
