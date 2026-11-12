"""Servicio de carga de datos de citas desde el Excel de insumos.

Lee Insumos/Citas.xlsx (una hoja, una fila por cita) y devuelve
todas las citas con estado Pendiente (R10).
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from app.models.cita import Cita

INSUMOS_PATH = Path(__file__).resolve().parent.parent.parent / "Insumos" / "Citas.xlsx"


def cargar_citas_excel(ruta: str | Path = INSUMOS_PATH) -> List[Cita]:
    """Carga citas desde el archivo Excel de insumos.

    Columnas esperadas (8):
    Solicitante, Fecha, Hora inicio, Hora fin, Corte láser,
    Impresión 3D, Dobot, Otros

    Todas las citas se devuelven con estado Pendiente (R10).
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ImportError(
            "openpyxl no está instalado. Ejecuta: uv add openpyxl"
        ) from exc

    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo de insumos: {ruta}")

    wb = load_workbook(ruta, data_only=True)
    hoja = wb.active  # primera hoja (Sheet1)

    # Leer encabezados de la fila 1
    encabezados = [
        hoja.cell(row=1, column=c).value for c in range(1, hoja.max_column + 1)
    ]
    columnas_esperadas = [
        "Solicitante",
        "Fecha",
        "Hora inicio",
        "Hora fin",
        "Corte láser",
        "Impresión 3D",
        "Dobot",
        "Otros",
    ]
    if encabezados != columnas_esperadas:
        raise ValueError(
            f"Columnas inesperadas en el Excel: {encabezados}. "
            f"Esperadas: {columnas_esperadas}"
        )

    citas: List[Cita] = []
    for fila in range(2, hoja.max_row + 1):
        valores = [hoja.cell(row=fila, column=c).value for c in range(1, 9)]
        if all(v is None or str(v).strip() == "" for v in valores):
            continue  # saltar filas vacías

        solicitante = str(valores[0]).strip() if valores[0] else ""
        fecha = _formato_fecha(valores[1])
        hora_inicio = _formato_hora(valores[2])
        hora_fin = _formato_hora(valores[3])
        corte_laser = str(valores[4]).strip() if valores[4] else "No"
        impresion_3d = str(valores[5]).strip() if valores[5] else "No"
        dobot = str(valores[6]).strip() if valores[6] else "No"
        otros = str(valores[7]).strip() if valores[7] else "No"

        citas.append(
            Cita(
                solicitante=solicitante,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                corte_laser=corte_laser,
                impresion_3d=impresion_3d,
                dobot=dobot,
                otros=otros,
                estado="Pendiente",  # R10: toda solicitud nueva entra como Pendiente
            )
        )

    return citas


def _formato_fecha(valor) -> str:
    """Convierte un valor de celda a fecha AAAA-MM-DD."""
    if valor is None:
        return ""
    if hasattr(valor, "strftime"):
        return valor.strftime("%Y-%m-%d")
    return str(valor).strip()


def _formato_hora(valor) -> str:
    """Convierte un valor de celda a hora HH:MM."""
    if valor is None:
        return ""
    if hasattr(valor, "strftime"):
        return valor.strftime("%H:%M")
    if hasattr(valor, "hour"):
        return f"{valor.hour:02d}:{valor.minute:02d}"
    return str(valor).strip()


def cargar_citas_desde_lista(datos: List[dict]) -> List[Cita]:
    """Crea citas Pendiente a partir de una lista de diccionarios (para pruebas)."""
    citas = []
    for d in datos:
        citas.append(
            Cita(
                solicitante=d.get("solicitante", ""),
                fecha=d.get("fecha", ""),
                hora_inicio=d.get("hora_inicio", ""),
                hora_fin=d.get("hora_fin", ""),
                corte_laser=d.get("corte_laser", "No"),
                impresion_3d=d.get("impresion_3d", "No"),
                dobot=d.get("dobot", "No"),
                otros=d.get("otros", "No"),
                estado="Pendiente",
            )
        )
    return citas
