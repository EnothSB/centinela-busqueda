"""Pruebas de la interfaz de línea de comandos ``python -m centinela``."""

import io
import unittest
from contextlib import redirect_stdout

from centinela.__main__ import ejecutar, principal


class PruebasCLI(unittest.TestCase):
    """Ejecución de la CLI con distintos algoritmos."""

    def test_ejecutar_cada_algoritmo(self):
        for algoritmo in ("bfs", "dfs", "ucs", "astar"):
            with self.subTest(algoritmo=algoritmo):
                self.assertTrue(ejecutar("severo", algoritmo).exito)

    def test_algoritmo_desconocido(self):
        with self.assertRaises(ValueError):
            ejecutar("severo", "greedy")

    def test_salida_del_escenario_severo(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            codigo = principal(["--escenario", "severo", "--algoritmo", "astar"])
        texto = salida.getvalue()
        self.assertEqual(codigo, 0)
        self.assertIn("Costo total: 12", texto)
        self.assertIn("Plan de remediación:", texto)
        self.assertIn("Nodos expandidos:", texto)


if __name__ == "__main__":
    unittest.main()
