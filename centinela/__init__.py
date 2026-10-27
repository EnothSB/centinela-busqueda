"""Centinela, Fase 2: búsqueda en el espacio de estados.

Centinela es el agente basado en utilidad de la Fase 1 que atiende
incidentes de una plataforma web institucional (servidores Oracle Linux 9
con nginx, aplicación y base de datos, monitoreados con Prometheus, Loki y
Alertmanager) aplicando runbooks de bajo riesgo.

En esta fase el entorno se abstrae como determinista, discreto, totalmente
observable y estático durante la planificación, de modo que el plan de
remediación puede obtenerse con algoritmos clásicos de búsqueda (BFS, DFS
y A*), siguiendo a Russell y Norvig (2021).

Módulos:

- ``problema``: estado, acciones, modelo de transición, meta y costos.
- ``escenarios``: estados iniciales de prueba (leve, moderado, severo, crítico).
- ``heuristicas``: heurísticas h0, h1 y h2 para A*.
- ``busqueda``: nodos, BFS, DFS, A*, UCS y métricas.
- ``benchmark``: comparación experimental de los algoritmos.
- ``verificar``: verificación exhaustiva de admisibilidad y consistencia.
"""

import sys

__version__ = "1.0.0"


def configurar_salida_utf8() -> None:
    """Fuerza UTF-8 en la salida estándar para imprimir tildes y eñes.

    En Windows, cuando la salida se redirige a un archivo o a una tubería,
    Python usa la página de códigos local; esta función la cambia a UTF-8
    para que los informes se lean igual en cualquier terminal.
    """
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
