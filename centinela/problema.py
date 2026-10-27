"""Formalización del problema de Centinela como espacio de estados.

El problema sigue la definición de Russell y Norvig (2021, cap. 3): estado
inicial, acciones aplicables, modelo de transición, prueba de meta y costo
de acción. El entorno se supone determinista, discreto, totalmente
observable y estático mientras el agente planifica.

Servidores (en orden fijo): ``web`` (nginx), ``app`` (aplicación) y ``bd``
(base de datos).

Niveles de ocupación de disco:

====== ==============
Nivel  Ocupación
====== ==============
0      menos de 60 %
1      60 % a 75 %
2      75 % a 85 %
3      85 % a 95 %
4      95 % o más
====== ==============

El costo de cada acción representa minutos de servicio degradado
ponderados por el riesgo operativo del runbook correspondiente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

#: Índice del servidor web (nginx).
WEB = 0
#: Índice del servidor de aplicación.
APP = 1
#: Índice del servidor de base de datos.
BD = 2

#: Nombres de los servidores en el orden fijo usado por el estado.
SERVIDORES = ("web", "app", "bd")
#: Servicio que corre en cada servidor, en el mismo orden.
SERVICIOS = ("nginx", "aplicación", "base de datos")

#: Nivel máximo de ocupación de disco (lleno).
NIVEL_DISCO_MAXIMO = 4
#: Nivel máximo de la fuga de memoria de la aplicación.
NIVEL_MEMORIA_MAXIMO = 3

#: Costo de cada tipo de acción.
COSTOS = {
    "rotar_logs": 2,
    "limpiar_tmp": 1,
    "reiniciar_nginx": 1,
    "reiniciar_app": 3,
    "reiniciar_bd": 5,
    "terminar_bloqueo": 2,
}

#: Niveles de disco que libera cada acción de limpieza.
REDUCCION_DISCO = {"rotar_logs": 2, "limpiar_tmp": 1}


@dataclass(frozen=True)
class Estado:
    """Estado inmutable y hashable de la plataforma.

    Las tuplas siguen el orden de ``SERVIDORES`` (web, app, bd).

    Atributos:
        disco: nivel de ocupación de disco de cada servidor (0 a 4).
        rotado: indica si los logs del servidor ya se rotaron.
        limpiado: indica si los temporales del servidor ya se limpiaron.
        activo: indica si el servicio del servidor está activo.
        mem_app: nivel de fuga de memoria de la aplicación (0 a 3).
        bloqueo: indica si hay una consulta bloqueada en la base de datos.
    """

    disco: tuple[int, int, int]
    rotado: tuple[bool, bool, bool]
    limpiado: tuple[bool, bool, bool]
    activo: tuple[bool, bool, bool]
    mem_app: int
    bloqueo: bool

    def describir(self) -> str:
        """Devuelve una descripción legible del estado en una línea."""
        partes = []
        for i, nombre in enumerate(SERVIDORES):
            marcas = ("R" if self.rotado[i] else "-") + (
                "L" if self.limpiado[i] else "-"
            )
            servicio = "activo" if self.activo[i] else "caído"
            partes.append(
                f"{nombre}[disco={self.disco[i]} {marcas} {servicio}]"
            )
        partes.append(f"mem_app={self.mem_app}")
        partes.append(f"bloqueo={'sí' if self.bloqueo else 'no'}")
        return " ".join(partes)


class Accion(NamedTuple):
    """Acción (runbook) que Centinela puede aplicar.

    Atributos:
        tipo: nombre del runbook, una clave de ``COSTOS``.
        servidor: índice del servidor para ``rotar_logs`` y ``limpiar_tmp``;
            ``None`` para las acciones que no lo requieren.
    """

    tipo: str
    servidor: int | None = None

    @property
    def costo(self) -> int:
        """Costo de la acción según ``COSTOS``."""
        return COSTOS[self.tipo]

    def __str__(self) -> str:
        """Nombre legible, p. ej. ``rotar_logs(web)`` o ``reiniciar_bd``."""
        if self.servidor is None:
            return self.tipo
        return f"{self.tipo}({SERVIDORES[self.servidor]})"


def _reemplazar(tupla: tuple, indice: int, valor) -> tuple:
    """Devuelve una copia de ``tupla`` con ``valor`` en ``indice``."""
    return tupla[:indice] + (valor,) + tupla[indice + 1 :]


def es_meta(estado: Estado) -> bool:
    """Prueba de meta de Centinela.

    La plataforma está sana cuando los tres servicios están activos, todos
    los discos están en nivel 1 o menos, la fuga de memoria es a lo sumo 1
    y no hay consultas bloqueadas en la base de datos.
    """
    return (
        all(estado.activo)
        and all(nivel <= 1 for nivel in estado.disco)
        and estado.mem_app <= 1
        and not estado.bloqueo
    )


def acciones_aplicables(estado: Estado) -> list[Accion]:
    """Devuelve las acciones aplicables en ``estado`` en orden fijo.

    Orden: ``rotar_logs`` (web, app, bd), ``limpiar_tmp`` (web, app, bd),
    ``reiniciar_nginx``, ``reiniciar_app``, ``reiniciar_bd`` y
    ``terminar_bloqueo``. Los reinicios son aplicables aunque el servicio
    ya esté activo; la búsqueda en grafo descarta los estados repetidos.
    """
    acciones: list[Accion] = []
    for s in range(len(SERVIDORES)):
        if not estado.rotado[s] and estado.disco[s] > 0:
            acciones.append(Accion("rotar_logs", s))
    for s in range(len(SERVIDORES)):
        if not estado.limpiado[s] and estado.disco[s] > 0:
            acciones.append(Accion("limpiar_tmp", s))
    if estado.disco[WEB] < NIVEL_DISCO_MAXIMO:
        acciones.append(Accion("reiniciar_nginx"))
    if estado.disco[APP] < NIVEL_DISCO_MAXIMO and estado.activo[BD]:
        acciones.append(Accion("reiniciar_app"))
    if estado.disco[BD] < NIVEL_DISCO_MAXIMO:
        acciones.append(Accion("reiniciar_bd"))
    if estado.activo[BD] and estado.bloqueo:
        acciones.append(Accion("terminar_bloqueo"))
    return acciones


def aplicar(estado: Estado, accion: Accion) -> Estado:
    """Modelo de transición: devuelve el estado que resulta de ``accion``.

    No verifica precondiciones; se asume que ``accion`` proviene de
    ``acciones_aplicables(estado)``. El estado original no se modifica.

    Raises:
        ValueError: si el tipo de acción no existe.
    """
    tipo, s = accion.tipo, accion.servidor
    if tipo in REDUCCION_DISCO:
        nuevo_nivel = max(0, estado.disco[s] - REDUCCION_DISCO[tipo])
        disco = _reemplazar(estado.disco, s, nuevo_nivel)
        if tipo == "rotar_logs":
            rotado = _reemplazar(estado.rotado, s, True)
            return Estado(disco, rotado, estado.limpiado, estado.activo,
                          estado.mem_app, estado.bloqueo)
        limpiado = _reemplazar(estado.limpiado, s, True)
        return Estado(disco, estado.rotado, limpiado, estado.activo,
                      estado.mem_app, estado.bloqueo)
    if tipo == "reiniciar_nginx":
        activo = _reemplazar(estado.activo, WEB, True)
        return Estado(estado.disco, estado.rotado, estado.limpiado, activo,
                      estado.mem_app, estado.bloqueo)
    if tipo == "reiniciar_app":
        activo = _reemplazar(estado.activo, APP, True)
        return Estado(estado.disco, estado.rotado, estado.limpiado, activo,
                      0, estado.bloqueo)
    if tipo == "reiniciar_bd":
        # Reiniciar la BD rompe el pool de conexiones: la app queda caída.
        activo = _reemplazar(estado.activo, BD, True)
        activo = _reemplazar(activo, APP, False)
        return Estado(estado.disco, estado.rotado, estado.limpiado, activo,
                      estado.mem_app, False)
    if tipo == "terminar_bloqueo":
        return Estado(estado.disco, estado.rotado, estado.limpiado,
                      estado.activo, estado.mem_app, False)
    raise ValueError(f"Acción desconocida: {tipo}")


class ProblemaCentinela:
    """Problema de búsqueda de Centinela con la interfaz de AIMA.

    Expone ``estado_inicial``, ``acciones(s)``, ``resultado(s, a)``,
    ``es_meta(s)`` y ``costo_accion(s, a, s2)``, que son los métodos que
    usan los algoritmos de ``centinela.busqueda``.

    Args:
        estado_inicial: estado de la plataforma al iniciar la planificación.
    """

    def __init__(self, estado_inicial: Estado):
        self.estado_inicial = estado_inicial

    def acciones(self, estado: Estado) -> list[Accion]:
        """Acciones aplicables en ``estado``, en orden determinista."""
        return acciones_aplicables(estado)

    def resultado(self, estado: Estado, accion: Accion) -> Estado:
        """Estado resultante de aplicar ``accion`` en ``estado``."""
        return aplicar(estado, accion)

    def es_meta(self, estado: Estado) -> bool:
        """Indica si ``estado`` satisface la prueba de meta."""
        return es_meta(estado)

    def costo_accion(self, estado: Estado, accion: Accion,
                     siguiente: Estado) -> int:
        """Costo de pasar de ``estado`` a ``siguiente`` con ``accion``."""
        return accion.costo
