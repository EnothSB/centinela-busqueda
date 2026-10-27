"""Pruebas de la formalización del problema de Centinela.

Verifican la prueba de meta, las precondiciones y los efectos de cada
acción, el orden determinista de generación de acciones, la inmutabilidad
del estado y los escenarios definidos.
"""

import dataclasses
import unittest

from centinela.escenarios import ESCENARIOS, obtener_escenario
from centinela.problema import (
    APP,
    BD,
    WEB,
    Accion,
    Estado,
    ProblemaCentinela,
)


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


def nombres(acciones):
    """Convierte una lista de acciones en sus nombres legibles."""
    return [str(a) for a in acciones]


class PruebasMeta(unittest.TestCase):
    """Prueba de meta del problema."""

    def setUp(self):
        self.problema = ProblemaCentinela(estado_base())

    def test_estado_sano_es_meta(self):
        self.assertTrue(self.problema.es_meta(estado_base()))

    def test_disco_en_nivel_uno_sigue_siendo_meta(self):
        self.assertTrue(self.problema.es_meta(estado_base(disco=(1, 1, 1))))

    def test_disco_mayor_a_uno_no_es_meta(self):
        self.assertFalse(self.problema.es_meta(estado_base(disco=(0, 2, 0))))

    def test_servicio_caido_no_es_meta(self):
        self.assertFalse(
            self.problema.es_meta(estado_base(activo=(True, False, True)))
        )

    def test_memoria_alta_no_es_meta(self):
        self.assertTrue(self.problema.es_meta(estado_base(mem_app=1)))
        self.assertFalse(self.problema.es_meta(estado_base(mem_app=2)))

    def test_bloqueo_no_es_meta(self):
        self.assertFalse(self.problema.es_meta(estado_base(bloqueo=True)))


class PruebasAcciones(unittest.TestCase):
    """Precondiciones, efectos y costos de las acciones."""

    def test_orden_de_generacion_determinista(self):
        estado = estado_base(
            disco=(2, 2, 2), activo=(False, False, True), bloqueo=True
        )
        problema = ProblemaCentinela(estado)
        self.assertEqual(
            nombres(problema.acciones(estado)),
            [
                "rotar_logs(web)",
                "rotar_logs(app)",
                "rotar_logs(bd)",
                "limpiar_tmp(web)",
                "limpiar_tmp(app)",
                "limpiar_tmp(bd)",
                "reiniciar_nginx",
                "reiniciar_app",
                "reiniciar_bd",
                "terminar_bloqueo",
            ],
        )

    def test_app_no_reinicia_con_bd_caida(self):
        estado = estado_base(activo=(True, False, False))
        problema = ProblemaCentinela(estado)
        self.assertNotIn("reiniciar_app", nombres(problema.acciones(estado)))

    def test_disco_lleno_impide_reinicio(self):
        estado = estado_base(disco=(4, 4, 4))
        problema = ProblemaCentinela(estado)
        disponibles = nombres(problema.acciones(estado))
        for reinicio in ("reiniciar_nginx", "reiniciar_app", "reiniciar_bd"):
            self.assertNotIn(reinicio, disponibles)

    def test_rotar_logs_solo_una_vez(self):
        estado = estado_base(disco=(4, 0, 0))
        problema = ProblemaCentinela(estado)
        rotar = Accion("rotar_logs", WEB)
        self.assertIn(rotar, problema.acciones(estado))
        despues = problema.resultado(estado, rotar)
        self.assertEqual(despues.disco, (2, 0, 0))
        self.assertTrue(despues.rotado[WEB])
        self.assertNotIn(rotar, problema.acciones(despues))

    def test_limpiar_tmp_solo_una_vez_y_baja_un_nivel(self):
        estado = estado_base(disco=(0, 0, 3))
        problema = ProblemaCentinela(estado)
        limpiar = Accion("limpiar_tmp", BD)
        despues = problema.resultado(estado, limpiar)
        self.assertEqual(despues.disco, (0, 0, 2))
        self.assertTrue(despues.limpiado[BD])
        self.assertNotIn(limpiar, problema.acciones(despues))

    def test_no_se_limpia_un_disco_vacio(self):
        estado = estado_base()
        problema = ProblemaCentinela(estado)
        disponibles = nombres(problema.acciones(estado))
        self.assertFalse(any(n.startswith("rotar_logs") for n in disponibles))
        self.assertFalse(any(n.startswith("limpiar_tmp") for n in disponibles))

    def test_rotar_no_baja_de_cero(self):
        estado = estado_base(disco=(0, 1, 0))
        problema = ProblemaCentinela(estado)
        despues = problema.resultado(estado, Accion("rotar_logs", APP))
        self.assertEqual(despues.disco, (0, 0, 0))

    def test_reiniciar_bd_tumba_la_app_y_quita_el_bloqueo(self):
        estado = estado_base(bloqueo=True)
        problema = ProblemaCentinela(estado)
        despues = problema.resultado(estado, Accion("reiniciar_bd"))
        self.assertTrue(despues.activo[BD])
        self.assertFalse(despues.activo[APP])
        self.assertFalse(despues.bloqueo)

    def test_reiniciar_app_libera_memoria(self):
        estado = estado_base(mem_app=3)
        problema = ProblemaCentinela(estado)
        despues = problema.resultado(estado, Accion("reiniciar_app"))
        self.assertTrue(despues.activo[APP])
        self.assertEqual(despues.mem_app, 0)

    def test_terminar_bloqueo_requiere_bd_activa(self):
        caida = estado_base(activo=(True, True, False), bloqueo=True)
        problema = ProblemaCentinela(caida)
        self.assertNotIn("terminar_bloqueo", nombres(problema.acciones(caida)))
        activa = estado_base(bloqueo=True)
        despues = problema.resultado(activa, Accion("terminar_bloqueo"))
        self.assertFalse(despues.bloqueo)
        self.assertTrue(despues.activo[BD])

    def test_reinicio_aplicable_aunque_el_servicio_este_activo(self):
        estado = estado_base()
        problema = ProblemaCentinela(estado)
        self.assertIn("reiniciar_nginx", nombres(problema.acciones(estado)))

    def test_costos_de_las_acciones(self):
        estado = estado_base(disco=(2, 2, 2), bloqueo=True)
        problema = ProblemaCentinela(estado)
        esperados = {
            "rotar_logs(web)": 2,
            "limpiar_tmp(web)": 1,
            "reiniciar_nginx": 1,
            "reiniciar_app": 3,
            "reiniciar_bd": 5,
            "terminar_bloqueo": 2,
        }
        por_nombre = {str(a): a for a in problema.acciones(estado)}
        for nombre, costo in esperados.items():
            accion = por_nombre[nombre]
            siguiente = problema.resultado(estado, accion)
            self.assertEqual(
                problema.costo_accion(estado, accion, siguiente), costo, nombre
            )


class PruebasEstado(unittest.TestCase):
    """Inmutabilidad y uso del estado como clave."""

    def test_estado_inmutable(self):
        estado = estado_base()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            estado.mem_app = 3

    def test_resultado_no_modifica_el_estado_original(self):
        estado = estado_base(disco=(3, 3, 3))
        problema = ProblemaCentinela(estado)
        problema.resultado(estado, Accion("rotar_logs", WEB))
        self.assertEqual(estado.disco, (3, 3, 3))
        self.assertEqual(estado.rotado, (False, False, False))

    def test_estados_iguales_tienen_el_mismo_hash(self):
        a = estado_base(disco=(1, 2, 3))
        b = estado_base(disco=(1, 2, 3))
        self.assertEqual(a, b)
        self.assertEqual(len({a, b}), 1)


class PruebasEscenarios(unittest.TestCase):
    """Escenarios definidos para el benchmark."""

    def test_existen_los_cuatro_escenarios(self):
        self.assertEqual(
            list(ESCENARIOS), ["leve", "moderado", "severo", "critico"]
        )

    def test_escenario_severo(self):
        severo = obtener_escenario("severo")
        self.assertEqual(severo.disco, (4, 3, 2))
        self.assertEqual(severo.activo, (False, True, True))
        self.assertEqual(severo.mem_app, 3)
        self.assertTrue(severo.bloqueo)

    def test_ningun_escenario_inicia_en_meta(self):
        for nombre, estado in ESCENARIOS.items():
            with self.subTest(escenario=nombre):
                self.assertFalse(ProblemaCentinela(estado).es_meta(estado))
                self.assertEqual(estado.rotado, (False, False, False))
                self.assertEqual(estado.limpiado, (False, False, False))

    def test_escenario_desconocido(self):
        with self.assertRaises(KeyError):
            obtener_escenario("inexistente")


if __name__ == "__main__":
    unittest.main()
