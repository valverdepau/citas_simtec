"""Pruebas del semáforo (R9) con los casos T-01 a T-11 de AGENTS.md.

No se modifica el código de la app.
"""

import pytest

from app.services.semaforo import evaluar_semaforo, evaluar_aprobacion


# Las 9 citas originales de Insumos/Citas.xlsx (todas Aprobadas para pruebas de conflicto)
CITAS_BASE = [
    {"fecha": "2026-11-09", "hora_inicio": "08:00", "hora_fin": "10:00",
     "corte_laser": "Si", "impresion_3d": "No", "dobot": "Si", "otros": "Termoformadora", "estado": "Pendiente"},
    {"fecha": "2026-11-09", "hora_inicio": "11:00", "hora_fin": "12:00",
     "corte_laser": "No", "impresion_3d": "Si", "dobot": "No", "otros": "No", "estado": "Pendiente"},
    {"fecha": "2026-11-10", "hora_inicio": "08:00", "hora_fin": "09:00",
     "corte_laser": "Si", "impresion_3d": "No", "dobot": "Si", "otros": "Realidad virtual", "estado": "Pendiente"},
    {"fecha": "2026-11-10", "hora_inicio": "09:00", "hora_fin": "10:30",
     "corte_laser": "Si", "impresion_3d": "No", "dobot": "No", "otros": "No", "estado": "Pendiente"},
    {"fecha": "2026-11-11", "hora_inicio": "13:00", "hora_fin": "14:00",
     "corte_laser": "No", "impresion_3d": "Si", "dobot": "No", "otros": "Celda de manufactura", "estado": "Pendiente"},
    {"fecha": "2026-11-12", "hora_inicio": "08:00", "hora_fin": "10:00",
     "corte_laser": "No", "impresion_3d": "No", "dobot": "No", "otros": "Torno CNC", "estado": "Pendiente"},
    {"fecha": "2026-11-13", "hora_inicio": "08:00", "hora_fin": "09:00",
     "corte_laser": "Si", "impresion_3d": "No", "dobot": "Si", "otros": "Fresadora", "estado": "Pendiente"},
    {"fecha": "2026-11-16", "hora_inicio": "10:30", "hora_fin": "11:00",
     "corte_laser": "Si", "impresion_3d": "No", "dobot": "No", "otros": "No", "estado": "Pendiente"},
    {"fecha": "2026-11-19", "hora_inicio": "14:00", "hora_fin": "15:00",
     "corte_laser": "Si", "impresion_3d": "No", "dobot": "No", "otros": "No", "estado": "Pendiente"},
]

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


class TestSemáforoCasosPrueba:
    """Casos T-01 a T-11 de AGENTS.md."""

    def test_T01_verde_asistente_a(self):
        r = evaluar_semaforo("2026-11-16", "08:00", "10:00", ["Impresión 3D"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "verde"
        assert "Asistente A" in r["asistentes"]

    def test_T02_rojo_conflicto(self):
        r = evaluar_semaforo("2026-11-09", "09:00", "10:30", ["Corte láser"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "rojo"
        assert "Conflicto" in r["mensajes"][0]
        assert "Corte láser" in r["mensajes"][0]

    def test_T03_verde_asistente_b(self):
        r = evaluar_semaforo("2026-11-11", "13:00", "14:00", ["Dobot"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "verde"
        assert "Asistente B" in r["asistentes"]

    def test_T04_verde_frontera(self):
        r = evaluar_semaforo("2026-11-10", "10:30", "11:30", ["Corte láser"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "verde"

    def test_T05_amarillo_falta_horas(self):
        r = evaluar_semaforo("2026-11-05", "no indicado", "no indicado", ["Corte láser"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "amarillo"
        assert any("hora de inicio" in m for m in r["mensajes"])
        assert any("hora de fin" in m for m in r["mensajes"])

    def test_T06_rojo_fuera_horario_tecnico(self):
        r = evaluar_semaforo("2026-11-12", "15:00", "17:00", ["Torno CNC"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "rojo"
        assert r["requiere_tecnico"] is True

    def test_T07_rojo_almuerzo_tecnico(self):
        r = evaluar_semaforo("2026-11-17", "11:30", "13:30", ["Fresadora"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "rojo"
        assert "almuerzo" in r["mensajes"][0]
        assert r["requiere_tecnico"] is True

    def test_T08_rojo_menos_30_min(self):
        r = evaluar_semaforo("2026-11-17", "09:00", "09:20", ["Corte láser"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "rojo"
        assert "30 minutos" in r["mensajes"][0]

    def test_T09_rojo_fin_de_semana(self):
        r = evaluar_semaforo("2026-11-14", "09:00", "11:00", ["Impresión 3D"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "rojo"

    def test_T10_amarillo_maquina_no_lista(self):
        r = evaluar_semaforo("2026-11-18", "08:00", "09:00", ["no indicado"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "amarillo"

    def test_T11_verde(self):
        r = evaluar_semaforo("2026-11-19", "08:00", "09:00", ["Impresión 3D"], CITAS_BASE, TURNOS_PRUEBA)
        assert r["color"] == "verde"


class TestSemáforoCifrasControl:
    """Cifras de control de AGENTS.md sección 9."""

    def test_nueve_citas_registradas(self):
        assert len(CITAS_BASE) == 9

    def test_todas_verdes_con_turnos(self):
        verdes = 0
        amarillos = 0
        rojos = 0
        for c in CITAS_BASE:
            equipos = []
            if c["corte_laser"] == "Si": equipos.append("Corte láser")
            if c["impresion_3d"] == "Si": equipos.append("Impresión 3D")
            if c["dobot"] == "Si": equipos.append("Dobot")
            if c["otros"] not in ("No", ""): equipos.append(c["otros"])
            r = evaluar_semaforo(c["fecha"], c["hora_inicio"], c["hora_fin"], equipos, [], TURNOS_PRUEBA)
            if r["color"] == "verde": verdes += 1
            elif r["color"] == "amarillo": amarillos += 1
            else: rojos += 1
        assert verdes == 9
        assert amarillos == 0
        assert rojos == 0

    def test_dos_requieren_tecnico(self):
        tecnico = 0
        for c in CITAS_BASE:
            equipos = []
            if c["corte_laser"] == "Si": equipos.append("Corte láser")
            if c["impresion_3d"] == "Si": equipos.append("Impresión 3D")
            if c["dobot"] == "Si": equipos.append("Dobot")
            if c["otros"] not in ("No", ""): equipos.append(c["otros"])
            if "Torno CNC" in equipos or "Fresadora" in equipos:
                tecnico += 1
        assert tecnico == 2

    def test_citas_por_dia(self):
        por_dia = {}
        for c in CITAS_BASE:
            por_dia[c["fecha"]] = por_dia.get(c["fecha"], 0) + 1
        assert por_dia["2026-11-09"] == 2
        assert por_dia["2026-11-10"] == 2
        assert por_dia["2026-11-11"] == 1
        assert por_dia["2026-11-12"] == 1
        assert por_dia["2026-11-13"] == 1
        assert por_dia["2026-11-16"] == 1
        assert por_dia["2026-11-19"] == 1

    def test_excel_semanal_09_11_al_13_11_siiete_filas(self):
        semana = ["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13"]
        filas = [c for c in CITAS_BASE if c["fecha"] in semana]
        assert len(filas) == 7


class TestAprobacion:
    """R11: Solo se puede aprobar en verde."""

    def test_aprobar_verde_tecnico(self):
        assert evaluar_aprobacion("verde", "tecnico")["valido"] is True

    def test_no_aprobar_rojo_tecnico(self):
        assert evaluar_aprobacion("rojo", "tecnico")["valido"] is False

    def test_no_aprobar_verde_asistente(self):
        assert evaluar_aprobacion("verde", "asistente")["valido"] is False
