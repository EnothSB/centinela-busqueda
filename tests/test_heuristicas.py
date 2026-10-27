"""Pruebas de las heurísticas h0, h1 y h2.

Comprueban valores conocidos en estados concretos. La verificación
exhaustiva de admisibilidad y consistencia sobre todos los estados
alcanzables está en ``test_verificar.py``.
"""

import math
import unittest

from centinela.escenarios import obtener_escenario
from centinela.heuristicas import HEURISTICAS, h0, h1, h2
from centinela.problema import Estado


def estado_base(**cambios):
    """Devuelve un estado meta sin acciones usadas, con los cambios dados."""
    valores = dict(
        disco=(0, 0, 0),
        rotado=(False, False, False),
        limpiado=(False, False, False),
        activo=(True, True, True),
        mem_app=0,
        bloqueo=False,
    )
    valores.update(cambios)
    return Estado(**valores)


class PruebasHeuristicas(unittest.TestCase):
    """Valores de las heurísticas en estados conocidos."""

    def test_registro_de_heuristicas(self):
        self.assertEqual(list(HEURISTICAS), ["h0", "h1", "h2"])

    def test_todas_valen_cero_en_la_meta(self):
        meta = estado_base(disco=(1, 1, 1), mem_app=1)
        for nombre, h in HEURISTICAS.items():
            with self.subTest(heuristica=nombre):
                self.assertEqual(h(meta), 0)

    def test_h0_siempre_cero(self):
        self.assertEqual(h0(obtener_escenario("critico")), 0)

    def test_h1_cuenta_condiciones_incumplidas(self):
        # severo: disco web y app > 1 (bd = 2 también), nginx caído,
        # memoria alta con app activa y bloqueo -> 3 + 1 + 1 + 1 = 6.
        self.assertEqual(h1(obtener_escenario("severo")), 6)

    def test_h1_ignora_memoria_si_la_app_esta_caida(self):
        estado = estado_base(activo=(True, False, True), mem_app=3)
        self.assertEqual(h1(estado), 1)

    def test_h2_en_el_escenario_severo(self):
        # disco: web 4 -> rotar+limpiar (3), app 3 -> rotar (2),
        # bd 2 -> limpiar (1); nginx 1; memoria 3; bloqueo 2.
        self.assertEqual(h2(obtener_escenario("severo")), 12)

    def test_h2_elige_la_limpieza_mas_barata(self):
        self.assertEqual(h2(estado_base(disco=(2, 0, 0))), 1)
        self.assertEqual(h2(estado_base(disco=(3, 0, 0))), 2)
        self.assertEqual(h2(estado_base(disco=(4, 0, 0))), 3)

    def test_h2_usa_solo_acciones_disponibles(self):
        estado = estado_base(disco=(2, 0, 0), limpiado=(True, False, False))
        self.assertEqual(h2(estado), 2)

    def test_h2_infinita_en_estado_sin_salida(self):
        estado = estado_base(
            disco=(3, 0, 0),
            rotado=(True, False, False),
            limpiado=(True, False, False),
        )
        self.assertTrue(math.isinf(h2(estado)))

    def test_h2_no_suma_bloqueo_con_bd_caida(self):
        estado = estado_base(activo=(True, True, False), bloqueo=True)
        self.assertEqual(h2(estado), 5)

    def test_h2_no_suma_memoria_con_app_caida(self):
        estado = estado_base(activo=(True, False, True), mem_app=3)
        self.assertEqual(h2(estado), 3)

    def test_h2_domina_a_h1_en_los_escenarios(self):
        for nombre in ("leve", "moderado", "severo", "critico"):
            estado = obtener_escenario(nombre)
            with self.subTest(escenario=nombre):
                self.assertGreaterEqual(h2(estado), h1(estado))


if __name__ == "__main__":
    unittest.main()
