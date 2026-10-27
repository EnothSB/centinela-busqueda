"""Algoritmos de búsqueda en grafo al estilo AIMA, con métricas.

Implementa la búsqueda en anchura (BFS), la búsqueda en profundidad (DFS),
A* y la búsqueda de costo uniforme (UCS, A* con h = 0), siguiendo a Russell
y Norvig (2021, cap. 3) y la implementación de referencia aima-python
(https://github.com/aimacode/aima-python).

Todos los algoritmos son búsquedas en grafo: mantienen un conjunto de
estados ya explorados para no expandir dos veces el mismo estado.

Métricas que devuelve cada algoritmo (``ResultadoBusqueda``):

- ``nodos_expandidos``: nodos a los que se les generaron sucesores.
- ``nodos_generados``: nodos hijo creados durante la búsqueda (sin contar
  la raíz), aunque luego se descarten por repetidos. Es el N de la fórmula
  del factor de ramificación efectivo.
- ``max_frontera``: tamaño máximo alcanzado por la frontera.
- ``max_memoria``: máximo de nodos en frontera más estados explorados
  almacenados al mismo tiempo.
"""

from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import dataclass
from itertools import count
from typing import Any, Callable, Hashable


class Problema:
    """Interfaz abstracta de un problema de búsqueda (estilo AIMA).

    Las subclases deben implementar ``acciones``, ``resultado`` y
    ``es_meta``; ``costo_accion`` vale 1 por omisión.

    Args:
        estado_inicial: estado desde el que parte la búsqueda; debe ser
            hashable para poder detectar estados repetidos.
    """

    def __init__(self, estado_inicial: Hashable):
        self.estado_inicial = estado_inicial

    def acciones(self, estado) -> list:
        """Devuelve las acciones aplicables en ``estado``."""
        raise NotImplementedError

    def resultado(self, estado, accion):
        """Devuelve el estado que resulta de aplicar ``accion``."""
        raise NotImplementedError

    def es_meta(self, estado) -> bool:
        """Indica si ``estado`` es un estado meta."""
        raise NotImplementedError

    def costo_accion(self, estado, accion, siguiente) -> float:
        """Costo de la transición; 1 por omisión."""
        return 1


class Nodo:
    """Nodo del árbol de búsqueda.

    Atributos:
        estado: estado del problema que representa el nodo.
        padre: nodo del que se generó (``None`` en la raíz).
        accion: acción que llevó del padre a este nodo.
        costo_ruta: costo acumulado g(n) desde la raíz.
        profundidad: número de acciones desde la raíz.
    """

    __slots__ = ("estado", "padre", "accion", "costo_ruta", "profundidad")

    def __init__(self, estado, padre: Nodo | None = None, accion=None,
                 costo_ruta: float = 0, profundidad: int = 0):
        self.estado = estado
        self.padre = padre
        self.accion = accion
        self.costo_ruta = costo_ruta
        self.profundidad = profundidad

    def __repr__(self) -> str:
        return f"<Nodo g={self.costo_ruta} d={self.profundidad} {self.estado}>"

    def hijo(self, problema: Problema, accion) -> Nodo:
        """Crea el nodo hijo que resulta de aplicar ``accion``."""
        siguiente = problema.resultado(self.estado, accion)
        costo = problema.costo_accion(self.estado, accion, siguiente)
        return Nodo(siguiente, self, accion, self.costo_ruta + costo,
                    self.profundidad + 1)

    def expandir(self, problema: Problema) -> list[Nodo]:
        """Genera los nodos hijo en el orden de ``problema.acciones``."""
        return [self.hijo(problema, a) for a in problema.acciones(self.estado)]

    def camino(self) -> list[Nodo]:
        """Lista de nodos desde la raíz hasta este nodo."""
        nodos = []
        nodo: Nodo | None = self
        while nodo is not None:
            nodos.append(nodo)
            nodo = nodo.padre
        return list(reversed(nodos))

    def solucion(self) -> list:
        """Secuencia de acciones desde la raíz hasta este nodo."""
        return [nodo.accion for nodo in self.camino()[1:]]


@dataclass
class ResultadoBusqueda:
    """Resultado de un algoritmo de búsqueda con sus métricas.

    Atributos:
        algoritmo: nombre del algoritmo que produjo el resultado.
        nodo: nodo meta encontrado, o ``None`` si no hay solución.
        nodos_expandidos: nodos a los que se les generaron sucesores.
        nodos_generados: nodos hijo creados (sin contar la raíz).
        max_frontera: tamaño máximo de la frontera.
        max_memoria: máximo de frontera más explorados simultáneos.
    """

    algoritmo: str
    nodo: Nodo | None
    nodos_expandidos: int
    nodos_generados: int
    max_frontera: int
    max_memoria: int

    @property
    def exito(self) -> bool:
        """Indica si se encontró una solución."""
        return self.nodo is not None

    @property
    def costo(self) -> float | None:
        """Costo de la ruta solución, o ``None`` si no hay solución."""
        return self.nodo.costo_ruta if self.nodo else None

    @property
    def profundidad(self) -> int | None:
        """Número de acciones de la solución, o ``None``."""
        return self.nodo.profundidad if self.nodo else None

    @property
    def acciones(self) -> list[str]:
        """Nombres legibles de las acciones de la solución."""
        return [str(a) for a in self.nodo.solucion()] if self.nodo else []

    @property
    def factor_ramificacion(self) -> float | None:
        """Factor de ramificación efectivo b*, si está definido."""
        if not self.nodo or self.nodo.profundidad == 0:
            return None
        return factor_ramificacion_efectivo(self.nodos_generados,
                                            self.nodo.profundidad)


def bfs(problema: Problema) -> ResultadoBusqueda:
    """Búsqueda en anchura en grafo (``breadth_first_graph_search`` de AIMA).

    Usa una frontera FIFO con un conjunto de miembros para consultas en
    O(1) y un conjunto de explorados. La prueba de meta se aplica al
    generar cada nodo, lo que devuelve la solución de menor profundidad
    (no necesariamente la de menor costo).

    Complejidad en tiempo y memoria: O(b^d).
    """
    nodo = Nodo(problema.estado_inicial)
    if problema.es_meta(nodo.estado):
        return ResultadoBusqueda("BFS", nodo, 0, 0, 0, 0)
    frontera: deque[Nodo] = deque([nodo])
    en_frontera = {nodo.estado}
    explorados: set = set()
    expandidos = generados = 0
    max_frontera = max_memoria = 1
    while frontera:
        nodo = frontera.popleft()
        en_frontera.discard(nodo.estado)
        explorados.add(nodo.estado)
        expandidos += 1
        for hijo in nodo.expandir(problema):
            generados += 1
            if hijo.estado in explorados or hijo.estado in en_frontera:
                continue
            if problema.es_meta(hijo.estado):
                max_frontera = max(max_frontera, len(frontera))
                max_memoria = max(max_memoria,
                                  len(frontera) + len(explorados))
                return ResultadoBusqueda("BFS", hijo, expandidos, generados,
                                         max_frontera, max_memoria)
            frontera.append(hijo)
            en_frontera.add(hijo.estado)
        max_frontera = max(max_frontera, len(frontera))
        max_memoria = max(max_memoria, len(frontera) + len(explorados))
    return ResultadoBusqueda("BFS", None, expandidos, generados,
                             max_frontera, max_memoria)


def dfs(problema: Problema) -> ResultadoBusqueda:
    """Búsqueda en profundidad en grafo (``depth_first_graph_search`` de AIMA).

    Usa una pila LIFO, un conjunto de explorados y un conjunto de miembros
    de la frontera. La prueba de meta se aplica al extraer. Los hijos se
    apilan en orden inverso para que se explore primero la primera acción.
    Es completa en espacios finitos, pero no es óptima ni en costo ni en
    profundidad.

    Complejidad: O(b^m) en tiempo; en búsqueda en grafo la memoria queda
    acotada por el número de estados alcanzables.
    """
    raiz = Nodo(problema.estado_inicial)
    frontera: list[Nodo] = [raiz]
    en_frontera = {raiz.estado}
    explorados: set = set()
    expandidos = generados = 0
    max_frontera = max_memoria = 1
    while frontera:
        nodo = frontera.pop()
        en_frontera.discard(nodo.estado)
        if problema.es_meta(nodo.estado):
            return ResultadoBusqueda("DFS", nodo, expandidos, generados,
                                     max_frontera, max_memoria)
        explorados.add(nodo.estado)
        expandidos += 1
        hijos = nodo.expandir(problema)
        generados += len(hijos)
        for hijo in reversed(hijos):
            if hijo.estado in explorados or hijo.estado in en_frontera:
                continue
            frontera.append(hijo)
            en_frontera.add(hijo.estado)
        max_frontera = max(max_frontera, len(frontera))
        max_memoria = max(max_memoria, len(frontera) + len(explorados))
    return ResultadoBusqueda("DFS", None, expandidos, generados,
                             max_frontera, max_memoria)


def a_estrella(problema: Problema, h: Callable[[Any], float],
               nombre: str | None = None) -> ResultadoBusqueda:
    """Búsqueda A* en grafo con f(n) = g(n) + h(n).

    La frontera es una cola de prioridad ordenada por f, con desempate por
    h (prefiere los nodos más cercanos a la meta) y luego por el orden de
    inserción, lo que hace el resultado determinista. Se guarda el mejor g
    conocido de cada estado; si se encuentra un camino más barato a un
    estado, se reinserta (reapertura), y las entradas obsoletas se
    descartan al extraerlas. La prueba de meta se aplica al extraer, lo que
    garantiza optimalidad con una heurística admisible (y sin reaperturas
    si además es consistente). Los hijos con h infinita se generan pero no
    se insertan: desde ellos la meta es inalcanzable.

    Args:
        problema: problema a resolver.
        h: heurística que recibe un estado y devuelve un costo estimado.
        nombre: etiqueta del algoritmo en el resultado (por omisión,
            ``A*(<nombre de h>)``).

    Complejidad: O(b^d) en el peor caso; una mejor heurística reduce el
    factor de ramificación efectivo.
    """
    etiqueta = nombre or f"A*({getattr(h, '__name__', 'h')})"
    raiz = Nodo(problema.estado_inicial)
    contador = count()
    h_raiz = h(raiz.estado)
    frontera: list = []
    if h_raiz != math.inf:
        frontera.append((h_raiz, h_raiz, next(contador), raiz))
    mejor_g = {raiz.estado: 0}
    cerrados: set = set()
    expandidos = generados = 0
    max_frontera = max_memoria = len(frontera)
    while frontera:
        _, _, _, nodo = heapq.heappop(frontera)
        if nodo.costo_ruta > mejor_g[nodo.estado]:
            continue  # Entrada obsoleta: ya hay un camino más barato.
        if problema.es_meta(nodo.estado):
            return ResultadoBusqueda(etiqueta, nodo, expandidos, generados,
                                     max_frontera, max_memoria)
        cerrados.add(nodo.estado)
        expandidos += 1
        for hijo in nodo.expandir(problema):
            generados += 1
            g_previo = mejor_g.get(hijo.estado)
            if g_previo is not None and hijo.costo_ruta >= g_previo:
                continue
            h_hijo = h(hijo.estado)
            if h_hijo == math.inf:
                continue
            mejor_g[hijo.estado] = hijo.costo_ruta
            cerrados.discard(hijo.estado)  # Reapertura si estaba cerrado.
            heapq.heappush(frontera, (hijo.costo_ruta + h_hijo, h_hijo,
                                      next(contador), hijo))
        max_frontera = max(max_frontera, len(frontera))
        max_memoria = max(max_memoria, len(frontera) + len(cerrados))
    return ResultadoBusqueda(etiqueta, None, expandidos, generados,
                             max_frontera, max_memoria)


def _h_nula(estado) -> int:
    """Heurística nula usada por ``ucs``."""
    return 0


def ucs(problema: Problema) -> ResultadoBusqueda:
    """Búsqueda de costo uniforme: A* con h(n) = 0.

    Expande en orden de g(n) y devuelve la solución de menor costo.
    Complejidad: O(b^(1 + C*/epsilon)), con C* el costo óptimo y epsilon el
    menor costo de acción.
    """
    return a_estrella(problema, _h_nula, nombre="UCS")


def factor_ramificacion_efectivo(n: int, d: int, tolerancia: float = 1e-10
                                 ) -> float:
    """Factor de ramificación efectivo b* (Russell y Norvig, 2021, §3.6).

    Resuelve por bisección ``N + 1 = 1 + b* + b*^2 + ... + b*^d``, donde N
    es el número de nodos generados y d la profundidad de la solución.

    Args:
        n: número de nodos generados (N >= 0).
        d: profundidad de la solución (d >= 1).
        tolerancia: ancho máximo del intervalo de bisección.

    Raises:
        ValueError: si ``d < 1`` o ``n < 0``.
    """
    if d < 1:
        raise ValueError("La profundidad debe ser al menos 1.")
    if n < 0:
        raise ValueError("El número de nodos no puede ser negativo.")
    objetivo = n + 1

    def suma(b: float) -> float:
        return sum(b ** i for i in range(d + 1))

    bajo, alto = 0.0, max(1.0, float(n))
    while alto - bajo > tolerancia:
        medio = (bajo + alto) / 2
        if suma(medio) < objetivo:
            bajo = medio
        else:
            alto = medio
    return (bajo + alto) / 2


#: Algoritmos disponibles por nombre corto (A* usa h2 por omisión en la CLI).
ALGORITMOS = ("bfs", "dfs", "ucs", "astar")
