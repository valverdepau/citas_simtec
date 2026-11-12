"""Pruebas de carga de datos desde Insumos/Citas.xlsx.

No se modifica el código de la app.
"""

from app.services.datos import cargar_citas_excel
from app.models.cita import Cita


def test_carga_nueve_citas(ruta_insumos="Insumos/Citas.xlsx"):
    citas = cargar_citas_excel(ruta_insumos)
    assert len(citas) == 9
    for c in citas:
        assert isinstance(c, Cita)
        assert c.estado == "Pendiente"


def test_columnas_8():
    citas = cargar_citas_excel("Insumos/Citas.xlsx")
    # Verificar que las citas tienen los 8 campos
    primera = citas[0]
    assert primera.solicitante == "Juan Pérez"
    assert primera.fecha == "2026-11-09"
    assert primera.hora_inicio == "08:00"
    assert primera.hora_fin == "10:00"
    assert primera.corte_laser == "Si"
    assert primera.impresion_3d == "No"
    assert primera.dobot == "Si"
    assert primera.otros == "Termoformadora"


def test_estado_inicial_pendiente():
    citas = cargar_citas_excel("Insumos/Citas.xlsx")
    estados = {c.estado for c in citas}
    assert estados == {"Pendiente"}
