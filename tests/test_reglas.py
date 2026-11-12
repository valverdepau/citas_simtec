"""Pruebas de reglas de negocio R1-R14 (código, sin IA).

No se modifica el código de la app. Se importan las funciones de app/services.
"""

from app.services.reglas import (
    validar_maquinas_validas,
    validar_horario,
    validar_almuerzo,
    validar_duracion,
    validar_anticipacion,
    validar_estado,
    requiere_tecnico,
    asistentes_turno,
    limpiar_texto,
    inicializar_estado,
    puede_aprobar,
    puede_cambiar_estado,
)


class TestR1MaquinasValidas:
    """R1: Las únicas máquinas válidas son las 8 de la lista."""

    def test_maquina_valida(self):
        assert validar_maquinas_validas(["Corte láser"])["valido"] is True

    def test_maquina_invalida(self):
        r = validar_maquinas_validas(["cortadora de vinil"])
        assert r["valido"] is False
        assert "no válida" in r["mensaje"]

    def test_maquina_no_indicado(self):
        r = validar_maquinas_validas(["no indicado"])
        assert r["valido"] is False
        assert "Falta: máquina" in r["mensaje"]

    def test_lista_vacia(self):
        r = validar_maquinas_validas([])
        assert r["valido"] is False


class TestR2Horario:
    """R2: Lunes a viernes, 08:00-16:00."""

    def test_lunes_valido(self):
        assert validar_horario("2026-11-09", "08:00", "10:00")["valido"] is True

    def test_fin_de_semana_invalido(self):
        r = validar_horario("2026-11-14", "09:00", "11:00")  # sábado
        assert r["valido"] is False
        assert "Fuera de horario" in r["mensaje"]

    def test_domingo_invalido(self):
        r = validar_horario("2026-11-15", "09:00", "11:00")  # domingo
        assert r["valido"] is False

    def test_antes_de_08_invalido(self):
        r = validar_horario("2026-11-09", "07:00", "09:00")
        assert r["valido"] is False

    def test_despues_de_16_invalido(self):
        r = validar_horario("2026-11-09", "15:00", "17:00")
        assert r["valido"] is False


class TestR3Almuerzo:
    """R3: Almuerzo 12:00-13:00. Terminar a 12:00 o empezar a 13:00 es válido."""

    def test_cruza_almuerzo_invalido(self):
        r = validar_almuerzo("11:30", "12:30")
        assert r["valido"] is False
        assert "almuerzo" in r["mensaje"]

    def test_termina_a_12_valido(self):
        assert validar_almuerzo("10:00", "12:00")["valido"] is True

    def test_empieza_a_13_valido(self):
        assert validar_almuerzo("13:00", "14:00")["valido"] is True


class TestR4Duracion:
    """R4: hora_fin > hora_inicio, duración mínima 30 min."""

    def test_menos_de_30_invalido(self):
        r = validar_duracion("09:00", "09:20")
        assert r["valido"] is False
        assert "30 minutos" in r["mensaje"]

    def test_exactamente_30_valido(self):
        assert validar_duracion("09:00", "09:30")["valido"] is True

    def test_misma_hora_invalido(self):
        r = validar_duracion("10:30", "10:30")
        assert r["valido"] is False
        assert "después de la de inicio" in r["mensaje"]

    def test_dos_horas_valido(self):
        assert validar_duracion("08:00", "10:00")["valido"] is True


class TestR5Anticipacion:
    """R5: No hay anticipación mínima."""

    def test_sin_anticipacion(self):
        assert validar_anticipacion("2026-11-05")["valido"] is True


class TestR8Tecnico:
    """R8: Torno CNC y Fresadora requieren técnico."""

    def test_torno_requiere_tecnico(self):
        assert requiere_tecnico(["Torno CNC"])["requiere_tecnico"] is True

    def test_fresadora_requiere_tecnico(self):
        assert requiere_tecnico(["Fresadora"])["requiere_tecnico"] is True

    def test_otras_no_requieren(self):
        assert requiere_tecnico(["Corte láser"])["requiere_tecnico"] is False
        assert requiere_tecnico(["Dobot", "Termoformadora"])["requiere_tecnico"] is False


class TestR10Estados:
    """R10: Estados Pendiente, Aprobada, Rechazada, Cancelada."""

    def test_inicializar_pendiente(self):
        assert inicializar_estado() == "Pendiente"

    def test_estado_valido(self):
        for estado in ["Pendiente", "Aprobada", "Rechazada", "Cancelada"]:
            assert validar_estado(estado)["valido"] is True

    def test_estado_invalido(self):
        assert validar_estado("Desconocida")["valido"] is False

    def test_solo_tecnico_cambia_estado(self):
        assert puede_cambiar_estado("tecnico")["valido"] is True
        assert puede_cambiar_estado("coordinador")["valido"] is False
        assert puede_cambiar_estado("asistente")["valido"] is False


class TestR11AprobarSoloVerde:
    """R11: Solo se puede aprobar una cita en verde."""

    def test_aprobar_verde(self):
        assert puede_aprobar("verde")["valido"] is True

    def test_no_aprobar_rojo(self):
        assert puede_aprobar("rojo")["valido"] is False

    def test_no_aprobar_amarillo(self):
        assert puede_aprobar("amarillo")["valido"] is False


class TestR13AsistentesTurno:
    """R13: Asistentes de turno por traslapo de horario."""

    def test_asistente_lunes_manana(self):
        turnos = [
            {"día": "Lunes", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
        ]
        r = asistentes_turno("2026-11-09", "08:00", "10:00", turnos)
        assert "Asistente A" in r["asistentes"]
        assert r["alerta"] is None

    def test_sin_asistente(self):
        turnos = [
            {"día": "Lunes", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
        ]
        r = asistentes_turno("2026-11-09", "14:00", "16:00", turnos)
        assert r["asistentes"] == []
        assert r["alerta"] == "Sin asistente de turno"

    def test_otro_dia_no_coincide(self):
        turnos = [
            {"día": "Lunes", "hora_inicio": "08:00", "hora_fin": "12:00", "nombre": "Asistente A"},
        ]
        r = asistentes_turno("2026-11-10", "08:00", "10:00", turnos)  # martes
        assert r["asistentes"] == []


class TestR14LimpiezaTexto:
    """R14: Reemplazar datos sensibles por [dato eliminado]."""

    def test_correo_eliminado(self):
        r = limpiar_texto("Contacto: profe@test.com")
        assert "[dato eliminado]" in r
        assert "profe@test.com" not in r

    def test_telefono_eliminado(self):
        r = limpiar_texto("Tel: 8888 1234")
        assert "[dato eliminado]" in r

    def test_carne_eliminado(self):
        r = limpiar_texto("Carné 12345678")
        assert "[dato eliminado]" in r
