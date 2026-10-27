"""Pruebas de la verificación exhaustiva de las heurísticas.

Enumeran todos los estados alcanzables de cada escenario, calculan el
costo exacto h* con Dijkstra inverso y comprueban que h1 y h2 son
admisibles y consistentes en todo el espacio.
"""

import math
import unittest

from centinela.escenarios import ESCENARIOS
from centinela.heuristicas import h1, h2
from centinela.problema import ProblemaCentinela
from centinela.verificar import (
    analizar_escenario,
    costos_exactos,
    explorar_espacio,
    verificar_heuristica,
)


class PruebasEspacio(unittest.TestCase):
    """Enumeración del espacio y cálculo de h*."""

    def test_h_estrella_del_inicial_es_el_costo_optimo(self):
        problema = ProblemaCentinela(ESCENARIOS["severo"])
        estados, aristas = explorar_espacio(problema)
        h_estrella = costos_exactos(estados, aristas, problema.es_meta)
        self.assertEqual(h_estrella[problema.estado_inicial], 12)

    def test_metas_tienen_h_estrella_cero(self):
        problema = ProblemaCentinela(ESCENARIOS["leve"])
        estados, aristas = explorar_espacio(problema)
        h_estrella = costos_exactos(estados, aristas, problema.es_meta)
        for estado in estados:
            if problema.es_meta(estado):
                self.assertEqual(h_estrella[estado], 0)

    def test_aristas_salen_de_estados_alcanzables(self):
        problema = ProblemaCentinela(ESCENARIOS["moderado"])
        estados, aristas = explorar_espacio(problema)
        conjunto = set(estados)
        for origen, _, costo, destino in aristas:
            self.assertIn(origen, conjunto)
            self.assertIn(destino, conjunto)
            self.assertGreater(costo, 0)


class PruebasAdmisibilidadConsistencia(unittest.TestCase):
    """h1 y h2 admisibles y consistentes en los cuatro escenarios."""

    def test_h1_y_h2_sin_violaciones(self):
        for nombre, estado in ESCENARIOS.items():
            problema = ProblemaCentinela(estado)
            estados, aristas = explorar_espacio(problema)
            h_estrella = costos_exactos(estados, aristas, problema.es_meta)
            for h in (h1, h2):
                with self.subTest(escenario=nombre, heuristica=h.__name__):
                    informe = verificar_heuristica(h, estados, aristas,
                                                   h_estrella)
                    self.assertEqual(informe.violaciones_admisibilidad, 0)
                    self.assertEqual(informe.violaciones_consistencia, 0)
                    self.assertGreater(informe.razon_promedio, 0)
                    self.assertLessEqual(informe.razon_promedio, 1)

    def test_h2_infinita_solo_en_estados_sin_salida(self):
        for nombre, estado in ESCENARIOS.items():
            problema = ProblemaCentinela(estado)
            estados, aristas = explorar_espacio(problema)
            h_estrella = costos_exactos(estados, aristas, problema.es_meta)
            with self.subTest(escenario=nombre):
                for s in estados:
                    self.assertEqual(math.isinf(h2(s)),
                                     math.isinf(h_estrella[s]))

    def test_h2_mas_informada_que_h1(self):
        informe = analizar_escenario("severo")
        self.assertGreater(informe.heuristicas["h2"].razon_promedio,
                           informe.heuristicas["h1"].razon_promedio)

    def test_detecta_una_heuristica_no_admisible(self):
        problema = ProblemaCentinela(ESCENARIOS["leve"])
        estados, aristas = explorar_espacio(problema)
        h_estrella = costos_exactos(estados, aristas, problema.es_meta)

        def exagerada(estado):
            return 100 * h2(estado)

        informe = verificar_heuristica(exagerada, estados, aristas, h_estrella)
        self.assertGreater(informe.violaciones_admisibilidad, 0)
        self.assertGreater(informe.violaciones_consistencia, 0)


if __name__ == "__main__":
    unittest.main()
