"""Benchmark de BFS, DFS y A* sobre los escenarios de Centinela.

Ejecuta dos comparaciones:

1. **Algoritmos**: BFS, DFS y A* con h2 en los cuatro escenarios.
2. **Heurísticas**: A* con h0 (equivalente a UCS), h1 y h2.

Las métricas de nodos son deterministas, así que se toman de una
ejecución; el tiempo es la mediana de ``repeticiones`` ejecuciones (30 por
omisión) medidas con ``time.perf_counter``, en milisegundos.

Uso::

    python -m centinela.benchmark
    python -m centinela.benchmark --repeticiones 10 --salida otra_carpeta

Escribe ``benchmark.csv``, ``benchmark.md`` y ``soluciones.md`` en
``resultados/`` e imprime las tablas junto con la versión de Python y la
plataforma.
"""

from __future__ import annotations

import argparse
import csv
import platform
import statistics
import sys
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Callable

from . import configurar_salida_utf8
from .busqueda import ResultadoBusqueda, a_estrella, bfs, dfs, ucs
from .escenarios import ESCENARIOS
from .heuristicas import h0, h1, h2
from .problema import ProblemaCentinela

#: Repeticiones por omisión para medir el tiempo.
REPETICIONES = 30

#: Carpeta de resultados por omisión (``resultados/`` en la raíz del repo).
CARPETA_RESULTADOS = Path(__file__).resolve().parent.parent / "resultados"

#: Escenario cuyas soluciones se detallan en ``soluciones.md``.
ESCENARIO_PRINCIPAL = "severo"


@dataclass
class FilaBenchmark:
    """Una fila del benchmark: un algoritmo sobre un escenario.

    Atributos:
        tabla: ``algoritmos`` o ``heuristicas``, según la comparación.
        escenario: nombre del escenario.
        algoritmo: etiqueta del algoritmo, p. ej. ``A*(h2)``.
        costo: costo de la solución encontrada.
        profundidad: número de acciones de la solución.
        nodos_expandidos: nodos expandidos.
        nodos_generados: nodos generados (sin contar la raíz).
        max_frontera: tamaño máximo de la frontera.
        max_memoria: máximo de frontera más explorados.
        factor_ramificacion: factor de ramificación efectivo b*.
        tiempo_ms: mediana del tiempo de ejecución en milisegundos.
    """

    tabla: str
    escenario: str
    algoritmo: str
    costo: float | None
    profundidad: int | None
    nodos_expandidos: int
    nodos_generados: int
    max_frontera: int
    max_memoria: int
    factor_ramificacion: float | None
    tiempo_ms: float


def medir(funcion: Callable[[], object], repeticiones: int = REPETICIONES
          ) -> tuple[object, float]:
    """Ejecuta ``funcion`` varias veces y mide la mediana del tiempo.

    Returns:
        Una tupla ``(resultado, mediana_ms)`` con el resultado de la última
        ejecución y la mediana de los tiempos en milisegundos.
    """
    tiempos = []
    resultado = None
    for _ in range(max(1, repeticiones)):
        inicio = time.perf_counter()
        resultado = funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    return resultado, statistics.median(tiempos)


def _fila(tabla: str, escenario: str, resultado: ResultadoBusqueda,
          tiempo_ms: float) -> FilaBenchmark:
    """Convierte un resultado de búsqueda en una fila del benchmark."""
    return FilaBenchmark(
        tabla=tabla,
        escenario=escenario,
        algoritmo=resultado.algoritmo,
        costo=resultado.costo,
        profundidad=resultado.profundidad,
        nodos_expandidos=resultado.nodos_expandidos,
        nodos_generados=resultado.nodos_generados,
        max_frontera=resultado.max_frontera,
        max_memoria=resultado.max_memoria,
        factor_ramificacion=resultado.factor_ramificacion,
        tiempo_ms=tiempo_ms,
    )


def _configuraciones(problema: ProblemaCentinela) -> dict:
    """Funciones a medir en cada comparación para un problema dado."""
    return {
        "algoritmos": [
            lambda: bfs(problema),
            lambda: dfs(problema),
            lambda: a_estrella(problema, h2),
        ],
        "heuristicas": [
            lambda: a_estrella(problema, h0),
            lambda: a_estrella(problema, h1),
            lambda: a_estrella(problema, h2),
        ],
    }


def ejecutar_benchmark(repeticiones: int = REPETICIONES) -> list[FilaBenchmark]:
    """Ejecuta ambas comparaciones en todos los escenarios.

    Returns:
        Las filas de la tabla ``algoritmos`` seguidas de las de la tabla
        ``heuristicas``, cada una en el orden de ``ESCENARIOS``.
    """
    filas: dict[str, list[FilaBenchmark]] = {"algoritmos": [],
                                              "heuristicas": []}
    for escenario, estado in ESCENARIOS.items():
        problema = ProblemaCentinela(estado)
        for tabla, funciones in _configuraciones(problema).items():
            for funcion in funciones:
                resultado, tiempo = medir(funcion, repeticiones)
                filas[tabla].append(_fila(tabla, escenario, resultado, tiempo))
    return filas["algoritmos"] + filas["heuristicas"]


def tabla_markdown(encabezados: list[str], filas: list[list]) -> str:
    """Construye una tabla Markdown a partir de encabezados y filas."""
    lineas = [
        "| " + " | ".join(encabezados) + " |",
        "|" + "|".join("---" for _ in encabezados) + "|",
    ]
    for fila in filas:
        lineas.append("| " + " | ".join(str(celda) for celda in fila) + " |")
    return "\n".join(lineas)


def _num(valor, decimales: int = 3) -> str:
    """Formatea un número opcional para las tablas."""
    if valor is None:
        return "-"
    if isinstance(valor, float):
        return f"{valor:.{decimales}f}"
    return str(valor)


def describir_entorno() -> str:
    """Versión de Python y plataforma en que se ejecuta el benchmark."""
    return (f"Python {platform.python_version()} "
            f"({platform.python_implementation()}) en {platform.platform()}")


def tablas_markdown(filas: list[FilaBenchmark], repeticiones: int) -> str:
    """Genera el contenido de ``benchmark.md`` con las dos tablas."""
    tiempo = f"Tiempo (ms, mediana de {repeticiones})"
    algoritmos = [
        [f.escenario, f.algoritmo, _num(f.costo), _num(f.profundidad),
         f.nodos_expandidos, f.nodos_generados, f.max_frontera,
         f.max_memoria, _num(f.factor_ramificacion), _num(f.tiempo_ms)]
        for f in filas if f.tabla == "algoritmos"
    ]
    heuristicas = [
        [f.escenario, f.algoritmo, _num(f.costo), _num(f.profundidad),
         f.nodos_expandidos, f.nodos_generados, f.max_memoria,
         _num(f.factor_ramificacion), _num(f.tiempo_ms)]
        for f in filas if f.tabla == "heuristicas"
    ]
    return "\n".join([
        "# Benchmark de búsqueda de Centinela",
        "",
        f"Entorno: {describir_entorno()}.",
        "",
        "Generado con `python -m centinela.benchmark`. Las métricas de nodos "
        "son deterministas; el tiempo es la mediana de "
        f"{repeticiones} repeticiones medidas con `time.perf_counter`. "
        "b* es el factor de ramificación efectivo calculado con los nodos "
        "generados y la profundidad de la solución.",
        "",
        "## BFS, DFS y A* (h2)",
        "",
        tabla_markdown(
            ["Escenario", "Algoritmo", "Costo", "Profundidad", "Expandidos",
             "Generados", "Frontera máx.", "Memoria máx.", "b*", tiempo],
            algoritmos,
        ),
        "",
        "## A* con h0 (UCS), h1 y h2",
        "",
        tabla_markdown(
            ["Escenario", "Heurística", "Costo", "Profundidad", "Expandidos",
             "Generados", "Memoria máx.", "b*", tiempo],
            heuristicas,
        ),
        "",
    ])


def soluciones_markdown(escenario: str = ESCENARIO_PRINCIPAL) -> str:
    """Genera ``soluciones.md`` con el plan de cada algoritmo en un escenario."""
    problema = ProblemaCentinela(ESCENARIOS[escenario])
    resultados = [bfs(problema), dfs(problema), ucs(problema),
                  a_estrella(problema, h2)]
    lineas = [
        f"# Soluciones del escenario {escenario}",
        "",
        f"Estado inicial: `{problema.estado_inicial.describir()}`",
        "",
    ]
    for resultado in resultados:
        lineas += [
            f"## {resultado.algoritmo}",
            "",
            f"Costo {_num(resultado.costo)}, profundidad "
            f"{_num(resultado.profundidad)}, "
            f"{resultado.nodos_expandidos} nodos expandidos.",
            "",
        ]
        for paso, nodo in enumerate(resultado.nodo.camino()[1:], start=1):
            lineas.append(f"{paso}. `{nodo.accion}` (costo {nodo.accion.costo},"
                          f" acumulado {nodo.costo_ruta})")
        lineas.append("")
    return "\n".join(lineas)


def escribir_csv(filas: list[FilaBenchmark], destino: Path) -> None:
    """Escribe todas las filas del benchmark en un archivo CSV (UTF-8)."""
    columnas = [campo.name for campo in fields(FilaBenchmark)]
    with open(destino, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for fila in filas:
            datos = asdict(fila)
            if datos["factor_ramificacion"] is not None:
                datos["factor_ramificacion"] = round(
                    datos["factor_ramificacion"], 4)
            datos["tiempo_ms"] = round(datos["tiempo_ms"], 4)
            escritor.writerow(datos)


def principal(argumentos: list[str] | None = None) -> int:
    """Punto de entrada del benchmark; devuelve el código de salida."""
    analizador = argparse.ArgumentParser(
        prog="python -m centinela.benchmark",
        description="Compara BFS, DFS y A* en los escenarios de Centinela.",
    )
    analizador.add_argument("--repeticiones", type=int, default=REPETICIONES,
                            help="repeticiones para la mediana del tiempo")
    analizador.add_argument("--salida", type=Path, default=CARPETA_RESULTADOS,
                            help="carpeta donde se escriben los resultados")
    args = analizador.parse_args(argumentos)
    configurar_salida_utf8()

    filas = ejecutar_benchmark(args.repeticiones)
    args.salida.mkdir(parents=True, exist_ok=True)
    escribir_csv(filas, args.salida / "benchmark.csv")
    tablas = tablas_markdown(filas, args.repeticiones)
    (args.salida / "benchmark.md").write_text(tablas, encoding="utf-8")
    (args.salida / "soluciones.md").write_text(soluciones_markdown(),
                                               encoding="utf-8")
    print(tablas)
    print(f"Resultados escritos en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
