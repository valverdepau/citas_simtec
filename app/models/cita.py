"""Modelo de datos de una cita (patrón MVC, sin Flask ni IA)."""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional


@dataclass
class Cita:
    """Registro de una cita de laboratorio.

    Estados (R10): Pendiente, Aprobada, Rechazada, Cancelada.
    Toda solicitud nueva entra como Pendiente.
    """

    solicitante: str
    fecha: str  # AAAA-MM-DD
    hora_inicio: str  # HH:MM
    hora_fin: str  # HH:MM
    corte_laser: str = "No"  # Si / No
    impresion_3d: str = "No"  # Si / No
    dobot: str = "No"  # Si / No
    otros: str = "No"  # nombre de la máquina o "No"
    estado: str = "Pendiente"  # R10

    def __post_init__(self):
        # Normalizar estados válidos (R10)
        estados_validos = {"Pendiente", "Aprobada", "Rechazada", "Cancelada"}
        if self.estado not in estados_validos:
            self.estado = "Pendiente"

    def a_dict(self):
        return {
            "solicitante": self.solicitante,
            "fecha": self.fecha,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "corte_laser": self.corte_laser,
            "impresion_3d": self.impresion_3d,
            "dobot": self.dobot,
            "otros": self.otros,
            "estado": self.estado,
        }
