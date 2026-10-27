"""Interfaz de línea de comandos de Centinela (Fase 2).

Uso::

    python -m centinela --escenario severo --algoritmo astar
    python -m centinela --escenario critico --algoritmo astar --heuristica h1
    python -m centinela --escenario leve --algoritmo bfs

Imprime el estado inicial, el plan de remediación paso a paso con el costo
de cada acción, el costo total y las métricas de la búsqueda.
"""

from __future__ import annotations

import argparse
import sys
import time

from . import configurar_salida_utf8
from .busqueda import ALGORITMOS, ResultadoBusqueda, a_estrella, bfs, dfs, ucs
from .escenarios import ESCENARIOS
from .heuristicas import HEURISTICAS
from .problema import ProblemaCentinela


def ejecutar(nombre_escenario: str, algoritmo: str,
             heuristica: str = "h2") -> ResultadoBusqueda:
    """Resuelve un escenario con el algoritmo indicado.

    Args:
        nombre_escenario: clave de ``ESCENARIOS``.
        algoritmo: uno de ``bfs``, ``dfs``, ``ucs`` o ``astar``.
        heuristica: heurística para A* (``h0``, ``h1`` o ``h2``).

    Raises:
        ValueError: si el algoritmo no existe.
    """
    problema = ProblemaCentinela(ESCENARIOS[nombre_escenario])
    if algoritmo == "bfs":
        return bfs(problema)
    if algoritmo == "dfs":
        return dfs(problema)
    if algoritmo == "ucs":
        return ucs(problema)
    if algoritmo == "astar":
        return a_estrella(problema, HEURISTICAS[heuristica])
    raise ValueError(f"Algoritmo desconocido: {algoritmo}")


def formatear_resultado(resultado: ResultadoBusqueda, problema:
                        ProblemaCentinela, tiempo_ms: float) -> str:
    """Construye el informe en texto de un resultado de búsqueda."""
    lineas = [
        f"Algoritmo: {resultado.algoritmo}",
        f"Estado inicial: {problema.estado_inicial.describir()}",
        "",
    ]
    if not resultado.exito:
        lineas.append("No se encontró un plan que alcance la meta.")
    else:
        lineas.append("Plan de remediación:")
        for paso, nodo in enumerate(resultado.nodo.camino()[1:], start=1):
            lineas.append(
                f"  {paso:2d}. {str(nodo.accion):<20} costo "
                f"{nodo.accion.costo}  (acumulado {nodo.costo_ruta})"
            )
        lineas.append(f"Estado final: {resultado.nodo.estado.describir()}")
        lineas.append("")
        lineas.append(f"Costo total: {resultado.costo}")
        lineas.append(f"Profundidad: {resultado.profundidad}")
    lineas.append(f"Nodos expandidos: {resultado.nodos_expandidos}")
    lineas.append(f"Nodos generados: {resultado.nodos_generados}")
    lineas.append(f"Frontera máxima: {resultado.max_frontera}")
    lineas.append(f"Memoria máxima (frontera + explorados): "
                  f"{resultado.max_memoria}")
    if resultado.factor_ramificacion is not None:
        lineas.append(f"Factor de ramificación efectivo b*: "
                      f"{resultado.factor_ramificacion:.3f}")
    lineas.append(f"Tiempo: {tiempo_ms:.3f} ms")
    return "\n".join(lineas)


def principal(argumentos: list[str] | None = None) -> int:
    """Punto de entrada de la CLI; devuelve el código de salida."""
    analizador = argparse.ArgumentParser(
        prog="python -m centinela",
        description="Planifica la remediación de un incidente de Centinela "
                    "con búsqueda en el espacio de estados.",
    )
    analizador.add_argument("--escenario", choices=list(ESCENARIOS),
                            default="severo",
                            help="escenario de incidente (por omisión: severo)")
    analizador.add_argument("--algoritmo", choices=ALGORITMOS, default="astar",
                            help="algoritmo de búsqueda (por omisión: astar)")
    analizador.add_argument("--heuristica", choices=list(HEURISTICAS),
                            default="h2",
                            help="heurística para A* (por omisión: h2)")
    args = analizador.parse_args(argumentos)
    configurar_salida_utf8()

    problema = ProblemaCentinela(ESCENARIOS[args.escenario])
    inicio = time.perf_counter()
    resultado = ejecutar(args.escenario, args.algoritmo, args.heuristica)
    tiempo_ms = (time.perf_counter() - inicio) * 1000
    print(f"Escenario: {args.escenario}")
    print(formatear_resultado(resultado, problema, tiempo_ms))
    return 0 if resultado.exito else 1


if __name__ == "__main__":
    sys.exit(principal())
