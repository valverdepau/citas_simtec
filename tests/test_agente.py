"""Pruebas de integración del agente de IA (contrato JSON).

No se modifica el código de la app.
"""

from app.services.agente import (
    validar_json_agente,
    preparar_texto_para_agente,
    limpiar_texto,
)


class TestContratoJSON:
    """Contrato JSON del agente: 5 llaves exactas."""

    def test_json_valido(self):
        json_str = '{"solicitante_tipo": "profesor", "fecha": "2026-11-16", "hora_inicio": "08:00", "hora_fin": "10:00", "equipos": ["Impresión 3D"]}'
        r = validar_json_agente(json_str)
        assert "error" not in r
        assert r["solicitante_tipo"] == "profesor"
        assert r["fecha"] == "2026-11-16"
        assert r["hora_inicio"] == "08:00"
        assert r["hora_fin"] == "10:00"
        assert r["equipos"] == ["Impresión 3D"]

    def test_llave_faltante(self):
        r = validar_json_agente('{"solicitante_tipo": "profesor", "fecha": "2026-11-16"}')
        assert "error" in r
        assert "Complétala a mano" in r["error"]

    def test_llave_sobrante(self):
        r = validar_json_agente('{"solicitante_tipo": "profesor", "fecha": "2026-11-16", "hora_inicio": "08:00", "hora_fin": "10:00", "equipos": ["Impresión 3D"], "extra": "x"}')
        assert "error" in r

    def test_no_es_json(self):
        r = validar_json_agente("Hola mundo")
        assert "error" in r

    def test_fecha_invalida(self):
        r = validar_json_agente('{"solicitante_tipo": "profesor", "fecha": "no-fecha", "hora_inicio": "08:00", "hora_fin": "10:00", "equipos": ["Impresión 3D"]}')
        assert "error" in r


class TestLimpiezaTexto:
    """R14: Datos sensibles eliminados antes de enviar al agente."""

    def test_correo(self):
        assert "[dato eliminado]" in limpiar_texto("profe@test.com")

    def test_telefono_8_digitos(self):
        assert "[dato eliminado]" in limpiar_texto("8888 1234")

    def test_carne_8_digitos(self):
        assert "[dato eliminado]" in limpiar_texto("12345678")
