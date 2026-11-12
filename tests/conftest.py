"""Configuración de pytest para CitasSIMTEC.

Configura pythonpath para importar los módulos de la app y define fixtures
comunes para las pruebas.
"""

import sys
from pathlib import Path

# Añadir la raíz del proyecto al pythonpath para importar app.*
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from app.services.reglas import (  # noqa: E402
    validar_maquinas_validas,
    validar_horario,
    validar_almuerzo,
    validar_duracion,
    validar_anticipacion,
    validar_conflicto,
    requiere_tecnico,
    asistentes_turno,
    limpiar_texto,
    inicializar_estado,
    puede_aprobar,
    puede_cambiar_estado,
)
from app.services.semaforo import (  # noqa: E402
    evaluar_semaforo,
    evaluar_aprobacion,
)
from app.services.datos import cargar_citas_excel  # noqa: E402
from app.models.cita import Cita  # noqa: E402

INSUMOS_XLSX = ROOT / "Insumos" / "Citas.xlsx"

# Turnos de prueba (ficticios, como indica AGENTS.md sección 8)
TURNOS_PRUEBA = [
    {"día": "Lunes", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
    {"día": "Lunes", "hora_inicio": "13:00", "hora_fin": "16:00", "nombre": "Asistente B"},
    {"día": "Martes", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
    {"día": "Martes", "hora_inicio": "13:00", "hora_fin": "16:00", "nombre": "Asistente B"},
    {"día": "Miércoles", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
    {"día": "Miércoles", "hora_inicio": "13:00", "hora_fin": "16:00", "nombre": "Asistente B"},
    {"día": "Jueves", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
    {"día": "Jueves", "hora_inicio": "13:00", "hora_fin": "16:00", "nombre": "Asistente B"},
    {"día": "Viernes", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
]


@pytest.fixture
def citas_base():
    """Las 9 citas reales de Insumos/Citas.xlsx, todas Pendiente."""
    return cargar_citas_excel(INSUMOS_XLSX)
