"""Integración con el agente de IA (entrega 6).

Este es el ÚNICO módulo que llama al agente.
- Lee la llave del agente exclusivamente de .env (nunca hardcodeada).
- Limpia el texto antes de enviarlo (R14: reemplaza datos sensibles).
- Valida que el JSON devuelto tenga exactamente las 5 llaves del contrato.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from app.services.reglas import limpiar_texto

# ---------------------------------------------------------------------------
# Llave del agente: SOLO desde .env, nunca en el código.
# ---------------------------------------------------------------------------
AGENTE_API_KEY = os.environ.get("AGENTE_API_KEY", "")

# Llaves exactas que el agente debe devolver (contrato JSON, AGENTS.md)
CONTRATO_LLAVES = [
    "solicitante_tipo",
    "fecha",
    "hora_inicio",
    "hora_fin",
    "equipos",
]


def _llave_configurada() -> bool:
    """Indica si existe una llave de agente configurada en el entorno."""
    return bool(AGENTE_API_KEY and AGENTE_API_KEY.strip())


def enviar_al_agente(texto_limpio: str, fecha_hoy: str, dia_semana: str, maquinas: List[str]) -> Dict[str, Any]:
    """Envía el texto al agente de IA y valida la respuesta.

    Parámetros:
        texto_limpio: texto de la solicitud ya procesado con limpiar_texto (R14).
        fecha_hoy: fecha actual en formato AAAA-MM-DD.
        dia_semana: nombre del día de la semana en español.
        maquinas: lista de las 8 máquinas válidas.

    Retorna:
        Dict con las 5 llaves del contrato si todo es válido, o
        {"error": str} si hay un problema.
    """
    if not _llave_configurada():
        return {
            "error": "No se pudo conectar con el agente. Puedes llenar la solicitud a mano.",
            "detalle": "Falta AGENTE_API_KEY en .env",
        }

    # Construir el prompt para el agente (según AGENTS.md, sección 5)
    prompt = _construir_prompt(texto_limpio, fecha_hoy, dia_semana, maquinas)

    try:
        respuesta = _llamar_agente(prompt)
    except Exception:
        return {
            "error": "No se pudo conectar con el agente. Puedes llenar la solicitud a mano.",
            "detalle": "Error llamando al servicio de IA",
        }

    # Validar el JSON devuelto
    return validar_json_agente(respuesta)


def _construir_prompt(texto: str, fecha_hoy: str, dia_semana: str, maquinas: List[str]) -> str:
    """Construye el prompt enviado al agente (según contrato de AGENTS.md)."""
    maquinas_lista = ", ".join(f'"{m}"' for m in maquinas)
    return f"""Eres un lector de solicitudes de citas de laboratorio. Convierte el texto libre en datos. No decidas si la cita se puede hacer, no revises choques ni horarios, y no redactes avisos.

Fecha de hoy: {fecha_hoy} ({dia_semana})
Lista de máquinas válidas: [{maquinas_lista}]

Texto de la solicitud: {texto}

Reglas:
- Nunca inventes. Si un dato no aparece en el texto, escribe "no indicado".
- Responde siempre con un JSON y con estas llaves en español, aunque el texto venga en inglés o con faltas.
- Las fechas relativas ("mañana", "el jueves") se resuelven con la fecha de hoy. "El jueves" es la próxima ocurrencia posterior a hoy. Si hay dos fechas posibles, fecha es "no indicado".
- Las horas imprecisas ("en la mañana", "en la tarde") dan "no indicado". Si hay duración ("por 2 horas desde las 9"), calcula hora_fin. Una hora sin AM/PM se interpreta dentro de 08:00 a 16:00; si no queda claro, "no indicado".
- Acepta sinónimos evidentes (impresora 3D = Impresión 3D, láser = Corte láser, VR = Realidad virtual). Si la máquina no está en la lista, equipos es ["no indicado"].
- No devuelvas nombres, correos, teléfonos ni carnés.

Devuelve ÚNICAMENTE un JSON con estas 5 llaves:
{{
  "solicitante_tipo": "profesor" | "estudiante" | "no indicado",
  "fecha": "AAAA-MM-DD" | "no indicado",
  "hora_inicio": "HH:MM" | "no indicado",
  "hora_fin": "HH:MM" | "no indicado",
  "equipos": ["..."] | ["no indicado"]
}}


No incluyas texto adicional antes o después del JSON."""


def _llamar_agente(prompt: str) -> str:
    """Llama al servicio de IA con la llave de .env.

    Esta función es un punto de extensión: aquí se integraría el cliente
    del proveedor de IA (OpenAI, Anthropic, etc.) usando AGENTE_API_KEY.

    Por ahora retorna el prompt como texto simulado para permitir pruebas
    sin llave real. Reemplazar con la llamada real al servicio.
    """
    # TODO: Integrar cliente real de IA usando AGENTE_API_KEY
    # Ejemplo placeholder:
    # import openai
    # client = openai.OpenAI(api_key=AGENTE_API_KEY)
    # resp = client.chat.completions.create(...)
    # return resp.choices[0].message.content
    return prompt  # placeholder para pruebas sin llave real


def validar_json_agente(respuesta: Any) -> Dict[str, Any]:
    """Valida que la respuesta del agente tenga exactamente las 5 llaves del contrato.

    Retorna el dict válido o {"error": str} si falla.
    """
    if isinstance(respuesta, dict):
        datos = respuesta
    elif isinstance(respuesta, str):
        try:
            datos = json.loads(respuesta)
        except json.JSONDecodeError:
            return {
                "error": "No pude leer la solicitud. Complétala a mano.",
                "detalle": "El agente no devolvió un JSON válido",
            }
    else:
        return {
            "error": "No pude leer la solicitud. Complétala a mano.",
            "detalle": "Respuesta del agente con tipo inesperado",
        }

    # Verificar que estén exactamente las 5 llaves
    llaves_presentes = set(datos.keys())
    llaves_esperadas = set(CONTRATO_LLAVES)
    if llaves_presentes != llaves_esperadas:
        faltantes = llaves_esperadas - llaves_presentes
        sobrantes = llaves_presentes - llaves_esperadas
        detalle = []
        if faltantes:
            detalle.append(f"llaves faltantes: {sorted(faltantes)}")
        if sobrantes:
            detalle.append(f"llaves sobrantes: {sorted(sobrantes)}")
        return {
            "error": "No pude leer la solicitud. Complétala a mano.",
            "detalle": "; ".join(detalle),
        }

    # Verificar tipos y valores básicos
    solicitante_tipo = datos.get("solicitante_tipo", "")
    if solicitante_tipo not in ("profesor", "estudiante", "no indicado"):
        datos["solicitante_tipo"] = "no indicado"

    fecha = datos.get("fecha", "")
    if fecha != "no indicado" and not _fecha_valida(fecha):
        return {
            "error": "No pude leer la solicitud. Complétala a mano.",
            "detalle": f"Fecha con formato inválido: {fecha}",
        }

    for campo in ("hora_inicio", "hora_fin"):
        valor = datos.get(campo, "")
        if valor != "no indicado" and not _hora_valida(valor):
            return {
                "error": "No pude leer la solicitud. Complétala a mano.",
                "detalle": f"{campo} con formato inválido: {valor}",
            }

    equipos = datos.get("equipos", [])
    if not isinstance(equipos, list):
        return {
            "error": "No pude leer la solicitud. Complétala a mano.",
            "detalle": "equipos debe ser una lista",
        }

    return datos


def _fecha_valida(fecha_str: str) -> bool:
    try:
        from datetime import datetime
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def _hora_valida(hora_str: str) -> bool:
    try:
        from datetime import datetime
        datetime.strptime(hora_str, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


def preparar_texto_para_agente(texto_original: str) -> str:
    """Limpia el texto antes de enviarlo al agente (R14)."""
    return limpiar_texto(texto_original)
