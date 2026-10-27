"""Escenarios de incidente usados como estados iniciales.

Cada escenario describe una situación plausible de la plataforma
institucional. En todos, ningún servidor tiene aún los logs rotados ni los
temporales limpiados.

- ``leve``: el disco de la app está al 85-95 % y hay una fuga de memoria
  moderada; todos los servicios siguen activos.
- ``moderado``: el disco de la app está lleno y la aplicación se cayó.
- ``severo`` (escenario principal del benchmark): disco web lleno con
  nginx caído, disco de la app al 85-95 %, fuga de memoria máxima y una
  consulta bloqueada en la base de datos.
- ``critico``: los tres discos llenos, los tres servicios caídos y una
  consulta bloqueada.
"""

from __future__ import annotations

from .problema import Estado

_NINGUNO = (False, False, False)


def _escenario(disco, activo, mem_app, bloqueo) -> Estado:
    """Crea un estado inicial sin logs rotados ni temporales limpiados."""
    return Estado(
        disco=disco,
        rotado=_NINGUNO,
        limpiado=_NINGUNO,
        activo=activo,
        mem_app=mem_app,
        bloqueo=bloqueo,
    )


#: Escenarios disponibles, en orden creciente de gravedad.
ESCENARIOS: dict[str, Estado] = {
    "leve": _escenario((1, 3, 1), (True, True, True), 2, False),
    "moderado": _escenario((1, 4, 1), (True, False, True), 0, False),
    "severo": _escenario((4, 3, 2), (False, True, True), 3, True),
    "critico": _escenario((4, 4, 4), (False, False, False), 0, True),
}


def obtener_escenario(nombre: str) -> Estado:
    """Devuelve el estado inicial del escenario ``nombre``.

    Raises:
        KeyError: si el escenario no existe.
    """
    if nombre not in ESCENARIOS:
        disponibles = ", ".join(ESCENARIOS)
        raise KeyError(f"Escenario desconocido: {nombre}. Opciones: {disponibles}")
    return ESCENARIOS[nombre]
