"""Reglas de negocio R1–R4 (patrón MVC, Python puro, sin Flask ni IA).

Cada función tiene un comentario indicando a qué regla de AGENTS.md corresponde.
Todas las funciones reciben datos simples y retornan un dict:
    {"valido": bool, "mensaje": str}  # mensaje vacío si es válido
"""

from __future__ import annotations

from datetime import date, datetime, time

# ---------------------------------------------------------------------------
# R1 — Las únicas máquinas válidas son las 8 de la lista de la sección 3.
# ---------------------------------------------------------------------------
MAQUINAS_VALIDAS = [
    "Corte láser",
    "Impresión 3D",
    "Dobot",
    "Termoformadora",
    "Celda de manufactura",
    "Realidad virtual",
    "Torno CNC",
    "Fresadora",
]


def validar_maquinas_validas(equipos: list) -> dict:
    """R1: valida que cada máquina de `equipos` esté en la lista de las 8 válidas."""
    if not equipos or equipos == ["no indicado"]:
        return {"valido": False, "mensaje": "Falta: máquina (o no está en la lista)"}

    invalidas = [e for e in equipos if e not in MAQUINAS_VALIDAS]
    if invalidas:
        return {
            "valido": False,
            "mensaje": f"Máquina(s) no válida(s): {', '.join(invalidas)}",
        }
    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R2 — Horario: lunes a viernes, de 08:00 a 16:00.
# Una cita es válida solo si la fecha es lunes a viernes,
# hora_inicio >= 08:00 y hora_fin <= 16:00.
# ---------------------------------------------------------------------------
HORA_INICIO_LAB = time(8, 0)
HORA_FIN_LAB = time(16, 0)


def validar_horario(fecha_str: str, hora_inicio_str: str, hora_fin_str: str) -> dict:
    """R2: valida que la fecha sea lunes a viernes y las horas estén dentro de 08:00–16:00."""
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {"valido": False, "mensaje": "Falta: fecha"}

    # Lunes a viernes: weekday() devuelve 0 (lunes) a 4 (viernes)
    if fecha.weekday() > 4:
        return {
            "valido": False,
            "mensaje": "Fuera de horario: el laboratorio atiende de lunes a viernes de 08:00 a 16:00",
        }

    try:
        hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
        hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()
    except (ValueError, TypeError):
        return {"valido": False, "mensaje": "Falta: hora de inicio o hora de fin"}

    if hora_inicio < HORA_INICIO_LAB or hora_fin > HORA_FIN_LAB:
        return {
            "valido": False,
            "mensaje": "Fuera de horario: el laboratorio atiende de lunes a viernes de 08:00 a 16:00",
        }

    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R3 — Almuerzo (12:00 a 13:00): una cita lo cruza si
# hora_inicio < 13:00 y hora_fin > 12:00.
# Terminar a las 12:00 o empezar a las 13:00 es válido.
# ---------------------------------------------------------------------------
ALMUERZO_INICIO = time(12, 0)
ALMUERZO_FIN = time(13, 0)


def validar_almuerzo(hora_inicio_str: str, hora_fin_str: str) -> dict:
    """R3: valida que la cita no cruce el almuerzo (12:00 a 13:00)."""
    try:
        hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
        hora_fin = datetime.strptime(hora_fin_str, "%H:%M").time()
    except (ValueError, TypeError):
        return {"valido": False, "mensaje": "Falta: hora de inicio o hora de fin"}

    # Cruza almuerzo si hora_inicio < 13:00 y hora_fin > 12:00
    if hora_inicio < ALMUERZO_FIN and hora_fin > ALMUERZO_INICIO:
        return {
            "valido": False,
            "mensaje": "Cruza el almuerzo (12:00 a 13:00)",
        }

    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R4 — hora_fin debe ser mayor que hora_inicio, y la duración mínima es
# de 30 minutos (exactamente 30 es válido). No hay duración máxima.
# ---------------------------------------------------------------------------
DURACION_MINIMA_MINUTOS = 30


def validar_duracion(hora_inicio_str: str, hora_fin_str: str) -> dict:
    """R4: valida que hora_fin > hora_inicio y que la duración sea >= 30 minutos."""
    try:
        hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M")
        hora_fin = datetime.strptime(hora_fin_str, "%H:%M")
    except (ValueError, TypeError):
        return {"valido": False, "mensaje": "Falta: hora de inicio o hora de fin"}

    if hora_fin <= hora_inicio:
        return {
            "valido": False,
            "mensaje": "La hora de fin debe ser después de la de inicio",
        }

    duracion_minutos = (hora_fin - hora_inicio).total_seconds() / 60
    if duracion_minutos < DURACION_MINIMA_MINUTOS:
        return {
            "valido": False,
            "mensaje": "Dura menos de 30 minutos",
        }

    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R5 — No hay anticipación mínima. El código no valida cuántos días antes se pide.
# ---------------------------------------------------------------------------
def validar_anticipacion(fecha_str: str) -> dict:
    """R5: no hay anticipación mínima; cualquier fecha es válida."""
    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R6 — Hay conflicto entre dos citas si tienen la misma fecha,
# sus horarios se traslapan (inicio_A < fin_B y inicio_B < fin_A)
# y comparten al menos una máquina.
# Que una termine a la hora exacta en que empieza la otra NO es conflicto.
# ---------------------------------------------------------------------------
def _maquinas_de_cita(cita: dict) -> list:
    """Extrae la lista de nombres de máquina de una cita (dict o Cita)."""
    if hasattr(cita, "a_dict"):
        cita = cita.a_dict()
    maquinas = []
    if str(cita.get("corte_laser", "No")).strip() == "Si":
        maquinas.append("Corte láser")
    if str(cita.get("impresion_3d", "No")).strip() == "Si":
        maquinas.append("Impresión 3D")
    if str(cita.get("dobot", "No")).strip() == "Si":
        maquinas.append("Dobot")
    otros = str(cita.get("otros", "No")).strip()
    if otros and otros != "No":
        maquinas.append(otros)
    return maquinas


def _horas(cita: dict):
    from datetime import datetime
    if hasattr(cita, "a_dict"):
        cita = cita.a_dict()
    hi = datetime.strptime(cita["hora_inicio"], "%H:%M")
    hf = datetime.strptime(cita["hora_fin"], "%H:%M")
    return hi, hf


def validar_conflicto(cita_nueva: dict, citas_existentes: list) -> dict:
    """R6: detecta conflicto entre cita_nueva y citas_existentes.

    Solo considera citas Pendiente y Aprobada (R12: Rechazadas y Canceladas no cuentan).
    """
    fecha_nueva = cita_nueva.get("fecha") if isinstance(cita_nueva, dict) else cita_nueva.fecha
    hi_nueva, hf_nueva = _horas(cita_nueva)
    maquinas_nueva = set(_maquinas_de_cita(cita_nueva))

    for cita in citas_existentes:
        estado = cita.get("estado") if isinstance(cita, dict) else cita.estado
        if estado in ("Rechazada", "Cancelada"):
            continue  # R12
        fecha_exist = cita.get("fecha") if isinstance(cita, dict) else cita.fecha
        if fecha_exist != fecha_nueva:
            continue
        hi_exist, hf_exist = _horas(cita)
        # Traslapo: inicio_A < fin_B y inicio_B < fin_A
        if hi_nueva < hf_exist and hi_exist < hf_nueva:
            maquinas_exist = set(_maquinas_de_cita(cita))
            compartidas = maquinas_nueva & maquinas_exist
            if compartidas:
                maquina = sorted(compartidas)[0]
                fecha_fmt = fecha_nueva
                try:
                    from datetime import datetime as _dt
                    fecha_fmt = _dt.strptime(fecha_nueva, "%Y-%m-%d").strftime("%d/%m/%Y")
                except Exception:
                    pass
                hi_exist_s = cita.get("hora_inicio") if isinstance(cita, dict) else cita.hora_inicio
                hf_exist_s = cita.get("hora_fin") if isinstance(cita, dict) else cita.hora_fin
                return {
                    "valido": False,
                    "mensaje": (
                        f"Conflicto: {maquina} ya está reservada el {fecha_fmt} "
                        f"de {hi_exist_s} a {hf_exist_s}"
                    ),
                    "maquinas_conflicto": sorted(compartidas),
                    "cita_conflicto": cita,
                }
    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R7 — Dos citas a la misma hora con máquinas distintas son válidas.
# ---------------------------------------------------------------------------
def validar_maquinas_distintas_misma_hora(cita_a: dict, cita_b: dict) -> dict:
    """R7: misma hora con máquinas distintas no es conflicto."""
    fecha_a = cita_a.get("fecha") if isinstance(cita_a, dict) else cita_a.fecha
    fecha_b = cita_b.get("fecha") if isinstance(cita_b, dict) else cita_b.fecha
    if fecha_a != fecha_b:
        return {"valido": True, "mensaje": ""}
    hi_a, hf_a = _horas(cita_a)
    hi_b, hf_b = _horas(cita_b)
    misma_hora = hi_a == hi_b and hf_a == hf_b
    if not misma_hora:
        return {"valido": True, "mensaje": ""}
    maquinas_a = set(_maquinas_de_cita(cita_a))
    maquinas_b = set(_maquinas_de_cita(cita_b))
    if maquinas_a & maquinas_b:
        return {"valido": False, "mensaje": "Mismas máquinas a la misma hora"}
    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R8 — Una cita requiere al técnico presente si incluye Torno CNC o Fresadora.
# ---------------------------------------------------------------------------
MAQUINAS_REQUIEREN_TECNICO = {"Torno CNC", "Fresadora"}


def requiere_tecnico(equipos: list) -> dict:
    """R8: indica si la cita requiere al técnico presente."""
    requiere = any(e in MAQUINAS_REQUIEREN_TECNICO for e in equipos)
    return {"requiere_tecnico": requiere, "mensaje": ""}


# ---------------------------------------------------------------------------
# R10 — Estados de una cita: Pendiente, Aprobada, Rechazada, Cancelada.
# Toda solicitud nueva entra como Pendiente. Solo el técnico cambia el estado.
# ---------------------------------------------------------------------------
ESTADOS_VALIDOS = {"Pendiente", "Aprobada", "Rechazada", "Cancelada"}


def inicializar_estado() -> str:
    """R10: toda solicitud nueva entra como Pendiente."""
    return "Pendiente"


def validar_estado(estado: str) -> dict:
    """R10: valida que el estado sea uno de los cuatro permitidos."""
    if estado not in ESTADOS_VALIDOS:
        return {"valido": False, "mensaje": f"Estado no válido: {estado}"}
    return {"valido": True, "mensaje": ""}


def puede_cambiar_estado(usuario_rol: str) -> dict:
    """R10: solo el técnico cambia el estado."""
    if usuario_rol != "tecnico":
        return {"valido": False, "mensaje": "Solo el técnico puede cambiar el estado de una cita."}
    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R11 — Solo se puede Aprobar una cita en verde.
# ---------------------------------------------------------------------------
def puede_aprobar(semaforo_color: str) -> dict:
    """R11: solo se puede aprobar una cita en verde."""
    if semaforo_color != "verde":
        return {
            "valido": False,
            "mensaje": "Solo se puede aprobar una cita en verde.",
        }
    return {"valido": True, "mensaje": ""}


# ---------------------------------------------------------------------------
# R13 — Asistentes de turno de una cita: todos los asistentes cuyo turno es
# el mismo día de la semana y se traslapa con la cita
# (turno.inicio < cita.fin y turno.fin > cita.inicio).
# Si no hay ninguno, se muestra la alerta "Sin asistente de turno".
# La alerta no cambia el color del semáforo.
# ---------------------------------------------------------------------------
def _dia_semana_fecha(fecha_str: str) -> str:
    """Devuelve el nombre del día de la semana en español (Lunes, Martes...)."""
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    from datetime import datetime
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    return dias[fecha.weekday()]


def _traslapa_horarios(inicio_a: str, fin_a: str, inicio_b: str, fin_b: str) -> bool:
    from datetime import datetime
    hi_a = datetime.strptime(inicio_a, "%H:%M")
    hf_a = datetime.strptime(fin_a, "%H:%M")
    hi_b = datetime.strptime(inicio_b, "%H:%M")
    hf_b = datetime.strptime(fin_b, "%H:%M")
    return hi_a < hf_b and hi_b < hf_a


def asistentes_turno(fecha_cita: str, hora_inicio: str, hora_fin: str, turnos: list) -> dict:
    """R13: devuelve los asistentes de turno para una cita.

    turnos: lista de dicts con claves día, hora_inicio, hora_fin, nombre.
    """
    dia_cita = _dia_semana_fecha(fecha_cita)
    asistentes = []
    for turno in turnos:
        if turno.get("día", turno.get("dia")) != dia_cita:
            continue
        if _traslapa_horarios(
            hora_inicio, hora_fin,
            turno.get("hora_inicio", ""), turno.get("hora_fin", ""),
        ):
            asistentes.append(turno.get("nombre", ""))
    if not asistentes:
        return {
            "asistentes": [],
            "alerta": "Sin asistente de turno",
        }
    return {
        "asistentes": asistentes,
        "alerta": None,
    }


# ---------------------------------------------------------------------------
# R14 — Antes de enviar el texto al agente, el código reemplaza por
# [dato eliminado]: correos electrónicos, y números de 8 a 10 dígitos
# (con o sin espacios).
# ---------------------------------------------------------------------------
import re


def limpiar_texto(texto: str) -> str:
    """R14: reemplaza correos y teléfonos/carnés (8-10 dígitos) por [dato eliminado]."""
    # Correos electrónicos
    texto = re.sub(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[dato eliminado]", texto)
    # Números de 8 a 10 dígitos (con o sin espacios entre ellos)
    texto = re.sub(r"\b\d[\d\s]{6,8}\d\b", "[dato eliminado]", texto)
    return texto
