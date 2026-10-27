"""Pruebas del benchmark y de la generación de informes."""

import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from centinela.benchmark import (
    ejecutar_benchmark,
    medir,
    principal,
    tabla_markdown,
)


class PruebasBenchmark(unittest.TestCase):
    """Medición, filas del benchmark y archivos generados."""

    def test_medir_devuelve_resultado_y_mediana(self):
        resultado, mediana = medir(lambda: 42, repeticiones=5)
        self.assertEqual(resultado, 42)
        self.assertGreaterEqual(mediana, 0)

    def test_filas_del_benchmark(self):
        filas = ejecutar_benchmark(repeticiones=1)
        algoritmos = [f for f in filas if f.tabla == "algoritmos"]
        heuristicas = [f for f in filas if f.tabla == "heuristicas"]
        self.assertEqual(len(algoritmos), 12)  # 4 escenarios x 3 algoritmos
        self.assertEqual(len(heuristicas), 12)  # 4 escenarios x 3 heurísticas
        severo = {f.algoritmo: f for f in algoritmos if f.escenario == "severo"}
        self.assertEqual(severo["A*(h2)"].costo, 12)
        for fila in heuristicas:
            self.assertIsNotNone(fila.costo)

    def test_tabla_markdown(self):
        tabla = tabla_markdown(["a", "b"], [[1, 2], [3, 4]])
        self.assertEqual(tabla.splitlines()[0], "| a | b |")
        self.assertEqual(tabla.splitlines()[1], "|---|---|")
        self.assertEqual(tabla.splitlines()[3], "| 3 | 4 |")

    def test_principal_escribe_los_archivos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with redirect_stdout(io.StringIO()) as salida:
                principal(["--repeticiones", "1", "--salida", carpeta])
            ruta = Path(carpeta)
            for nombre in ("benchmark.csv", "benchmark.md", "soluciones.md"):
                self.assertTrue((ruta / nombre).exists(), nombre)
            with open(ruta / "benchmark.csv", encoding="utf-8", newline="") as f:
                filas = list(csv.DictReader(f))
            self.assertEqual(len(filas), 24)
            soluciones = (ruta / "soluciones.md").read_text(encoding="utf-8")
            self.assertIn("rotar_logs(web)", soluciones)
            self.assertIn("Python", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
