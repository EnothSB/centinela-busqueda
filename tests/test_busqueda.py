"""Pruebas de los algoritmos de búsqueda y sus métricas.

Comprueban que BFS encuentra la solución de menor profundidad, que A* con
h1 y h2 es óptimo en costo (igual que UCS), que h2 no expande más nodos que
UCS, que DFS devuelve un plan válido y que el factor de ramificación
efectivo se calcula correctamente.
"""

import unittest
from collections import deque

from centinela.busqueda import (
    Nodo,
    Problema,
    a_estrella,
    bfs,
    dfs,
    factor_ramificacion_efectivo,
    ucs,
)
from centinela.escenarios import ESCENARIOS
from centinela.heuristicas import h1, h2
from centinela.problema import ProblemaCentinela


def profundidad_minima(problema):
    """BFS de referencia por niveles: profundidad mínima hasta una meta."""
    inicial = problema.estado_inicial
    if problema.es_meta(inicial):
        return 0
    vistos = {inicial}
    cola = deque([(inicial, 0)])
    while cola:
        estado, profundidad = cola.popleft()
        for accion in problema.acciones(estado):
            siguiente = problema.resultado(estado, accion)
            if siguiente in vistos:
                continue
            if problema.es_meta(siguiente):
                return profundidad + 1
            vistos.add(siguiente)
            cola.append((siguiente, profundidad + 1))
    return None


def simular(problema, acciones):
    """Aplica ``acciones`` desde el inicial verificando precondiciones.

    Devuelve el estado final y el costo acumulado.
    """
    estado = problema.estado_inicial
    costo = 0
    for accion in acciones:
        if accion not in problema.acciones(estado):
            raise AssertionError(f"Acción no aplicable: {accion}")
        siguiente = problema.resultado(estado, accion)
        costo += problema.costo_accion(estado, accion, siguiente)
        estado = siguiente
    return estado, costo


class ProblemaLineal(Problema):
    """Problema de juguete: avanzar de 0 a ``meta`` sumando 1 o 2."""

    def __init__(self, meta):
        super().__init__(0)
        self.meta = meta

    def acciones(self, estado):
        return [paso for paso in (1, 2) if estado + paso <= self.meta]

    def resultado(self, estado, accion):
        return estado + accion

    def es_meta(self, estado):
        return estado == self.meta


class PruebasNodo(unittest.TestCase):
    """Estructura de nodos y reconstrucción del camino."""

    def test_camino_y_solucion(self):
        raiz = Nodo(0)
        hijo = Nodo(1, raiz, 1, 1, 1)
        nieto = Nodo(3, hijo, 2, 2, 2)
        self.assertEqual([n.estado for n in nieto.camino()], [0, 1, 3])
        self.assertEqual(nieto.solucion(), [1, 2])

    def test_problema_base_exige_implementar_metodos(self):
        problema = Problema(0)
        with self.assertRaises(NotImplementedError):
            problema.acciones(0)
        self.assertEqual(problema.costo_accion(0, "a", 1), 1)


class PruebasAlgoritmosJuguete(unittest.TestCase):
    """Comportamiento básico sobre un problema pequeño conocido."""

    def test_bfs_en_problema_lineal(self):
        resultado = bfs(ProblemaLineal(4))
        self.assertEqual(resultado.profundidad, 2)
        self.assertEqual(resultado.acciones, ["2", "2"])

    def test_meta_en_el_estado_inicial(self):
        for algoritmo in (bfs, dfs, ucs):
            with self.subTest(algoritmo=algoritmo.__name__):
                resultado = algoritmo(ProblemaLineal(0))
                self.assertTrue(resultado.exito)
                self.assertEqual(resultado.costo, 0)
                self.assertEqual(resultado.profundidad, 0)

    def test_sin_solucion(self):
        class SinSalida(ProblemaLineal):
            def es_meta(self, estado):
                return False

        for algoritmo in (bfs, dfs, ucs):
            with self.subTest(algoritmo=algoritmo.__name__):
                resultado = algoritmo(SinSalida(3))
                self.assertFalse(resultado.exito)
                self.assertIsNone(resultado.nodo)
                self.assertIsNone(resultado.costo)
                self.assertEqual(resultado.acciones, [])


class PruebasCentinela(unittest.TestCase):
    """Algoritmos sobre los cuatro escenarios de Centinela."""

    def problemas(self):
        for nombre, estado in ESCENARIOS.items():
            yield nombre, ProblemaCentinela(estado)

    def test_bfs_devuelve_la_solucion_de_menor_profundidad(self):
        for nombre, problema in self.problemas():
            with self.subTest(escenario=nombre):
                resultado = bfs(problema)
                self.assertEqual(
                    resultado.profundidad, profundidad_minima(problema)
                )
                final, _ = simular(problema, resultado.nodo.solucion())
                self.assertTrue(problema.es_meta(final))

    def test_a_estrella_es_optimo_con_h1_y_h2(self):
        for nombre, problema in self.problemas():
            with self.subTest(escenario=nombre):
                referencia = ucs(problema)
                self.assertTrue(referencia.exito)
                for h in (h1, h2):
                    resultado = a_estrella(problema, h)
                    self.assertEqual(resultado.costo, referencia.costo, h.__name__)

    def test_costo_optimo_del_escenario_severo(self):
        resultado = ucs(ProblemaCentinela(ESCENARIOS["severo"]))
        self.assertEqual(resultado.costo, 12)

    def test_h2_expande_a_lo_sumo_lo_mismo_que_ucs(self):
        for nombre, problema in self.problemas():
            with self.subTest(escenario=nombre):
                self.assertLessEqual(
                    a_estrella(problema, h2).nodos_expandidos,
                    ucs(problema).nodos_expandidos,
                )

    def test_dfs_devuelve_un_plan_valido(self):
        for nombre, problema in self.problemas():
            with self.subTest(escenario=nombre):
                resultado = dfs(problema)
                self.assertTrue(resultado.exito)
                final, costo = simular(problema, resultado.nodo.solucion())
                self.assertTrue(problema.es_meta(final))
                self.assertEqual(costo, resultado.costo)

    def test_costo_reportado_coincide_con_la_simulacion(self):
        problema = ProblemaCentinela(ESCENARIOS["critico"])
        for resultado in (bfs(problema), a_estrella(problema, h2)):
            _, costo = simular(problema, resultado.nodo.solucion())
            self.assertEqual(costo, resultado.costo)

    def test_metricas_coherentes(self):
        problema = ProblemaCentinela(ESCENARIOS["severo"])
        for resultado in (bfs(problema), dfs(problema), a_estrella(problema, h2)):
            self.assertGreater(resultado.nodos_expandidos, 0)
            self.assertGreaterEqual(
                resultado.nodos_generados, resultado.nodos_expandidos
            )
            self.assertGreaterEqual(resultado.max_memoria, resultado.max_frontera)
            self.assertEqual(len(resultado.acciones), resultado.profundidad)

    def test_acciones_legibles(self):
        resultado = a_estrella(ProblemaCentinela(ESCENARIOS["severo"]), h2)
        self.assertIn("rotar_logs(web)", resultado.acciones)
        self.assertTrue(all(isinstance(a, str) for a in resultado.acciones))

    def test_resultados_deterministas(self):
        problema = ProblemaCentinela(ESCENARIOS["severo"])
        for algoritmo in (bfs, dfs, ucs):
            with self.subTest(algoritmo=algoritmo.__name__):
                a, b = algoritmo(problema), algoritmo(problema)
                self.assertEqual(a.acciones, b.acciones)
                self.assertEqual(a.nodos_expandidos, b.nodos_expandidos)


class PruebasFactorRamificacion(unittest.TestCase):
    """Factor de ramificación efectivo b*."""

    def test_ejemplo_de_russell_y_norvig(self):
        # N = 52 nodos generados con la solución en profundidad 5: b* = 1,92.
        self.assertAlmostEqual(factor_ramificacion_efectivo(52, 5), 1.92, places=2)

    def test_casos_exactos(self):
        self.assertAlmostEqual(factor_ramificacion_efectivo(5, 1), 5.0, places=6)
        # 1 + b + b^2 = 7 -> b = 2.
        self.assertAlmostEqual(factor_ramificacion_efectivo(6, 2), 2.0, places=6)
        # 1 + b + b^2 + b^3 = 4 -> b = 1.
        self.assertAlmostEqual(factor_ramificacion_efectivo(3, 3), 1.0, places=6)

    def test_profundidad_invalida(self):
        with self.assertRaises(ValueError):
            factor_ramificacion_efectivo(10, 0)


if __name__ == "__main__":
    unittest.main()
