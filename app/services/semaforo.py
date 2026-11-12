"""Lógica del semáforo (R9) e integración de reglas R1–R6, R10–R14.

Python puro, sin Flask ni IA.
"""

from __future__ import annotations

from datetime import date, datetime, time

from app.services.reglas import (
    MAQUINAS_VALIDAS,
    validar_maquinas_validas,
    validar_horario,
    validar_almuerzo,
    validar_duracion,
    validar_conflicto,
    validar_anticipacion,
    requiere_tecnico,
    asistentes_turno,
    limpiar_texto,
    inicializar_estado,
    puede_aprobar,
    puede_cambiar_estado,
)


def evaluar_semaforo(
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    equipos: list,
    citas_existentes: list,
    turnos: list | None = None,
) -> dict:
    """R9: devuelve el color del semáforo y sus mensajes.

    Reglas:
    - Amarillo si falta fecha, hora de inicio, hora de fin o máquina
      (o la máquina no está en la lista). En ese caso no se evalúan R2 a R6.
    - Rojo si se viola R2, R3, R4 o R6.
    - Verde si no hay problema.

    Retorna:
        {
            "color": "verde" | "amarillo" | "rojo",
            "mensajes": [str, ...],
            "alertas": [str, ...],          # p. ej. "Sin asistente de turno"
            "requiere_tecnico": bool,
        }
    """
    mensajes = []
    alertas = []

    # --- Amarillo: faltan datos básicos (R9) -------------------------------
    if not fecha or fecha == "no indicado":
        mensajes.append("Falta: fecha")
    if not hora_inicio or hora_inicio == "no indicado":
        mensajes.append("Falta: hora de inicio")
    if not hora_fin or hora_fin == "no indicado":
        mensajes.append("Falta: hora de fin")
    if not equipos or equipos == ["no indicado"]:
        mensajes.append("Falta: máquina (o no está en la lista)")
    else:
        maquinas_invalidas = [e for e in equipos if e not in MAQUINAS_VALIDAS]
        if maquinas_invalidas:
            mensajes.append(
                "Falta: máquina (o no está en la lista): "
                + ", ".join(maquinas_invalidas)
            )

    if mensajes:
        return {
            "color": "amarillo",
            "mensajes": mensajes,
            "alertas": alertas,
            "requiere_tecnico": requiere_tecnico(equipos).get("requiere_tecnico", False),
            "asistentes": [],
        }

    # --- Rojo: R2 horario --------------------------------------------------
    r2 = validar_horario(fecha, hora_inicio, hora_fin)
    if not r2["valido"]:
        return {
            "color": "rojo",
            "mensajes": [r2["mensaje"]],
            "alertas": alertas,
            "requiere_tecnico": requiere_tecnico(equipos).get("requiere_tecnico", False),
            "asistentes": [],
        }

    # --- Rojo: R3 almuerzo -------------------------------------------------
    r3 = validar_almuerzo(hora_inicio, hora_fin)
    if not r3["valido"]:
        return {
            "color": "rojo",
            "mensajes": [r3["mensaje"]],
            "alertas": alertas,
            "requiere_tecnico": requiere_tecnico(equipos).get("requiere_tecnico", False),
            "asistentes": [],
        }

    # --- Rojo: R4 duración -------------------------------------------------
    r4 = validar_duracion(hora_inicio, hora_fin)
    if not r4["valido"]:
        return {
            "color": "rojo",
            "mensajes": [r4["mensaje"]],
            "alertas": alertas,
            "requiere_tecnico": requiere_tecnico(equipos).get("requiere_tecnico", False),
            "asistentes": [],
        }

    # --- Rojo: R6 conflicto ------------------------------------------------
    cita_nueva = {
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "corte_laser": "Si" if "Corte láser" in equipos else "No",
        "impresion_3d": "Si" if "Impresión 3D" in equipos else "No",
        "dobot": "Si" if "Dobot" in equipos else "No",
        "otros": equipos[-1] if len(equipos) > 3 else "No",
        "estado": inicializar_estado(),  # R10: Pendiente
    }
    r6 = validar_conflicto(cita_nueva, citas_existentes)
    if not r6["valido"]:
        return {
            "color": "rojo",
            "mensajes": [r6["mensaje"]],
            "alertas": alertas,
            "requiere_tecnico": requiere_tecnico(equipos).get("requiere_tecnico", False),
            "asistentes": [],
        }

    # --- R13: asistentes de turno ------------------------------------------
    if turnos is not None:
        at = asistentes_turno(fecha, hora_inicio, hora_fin, turnos)
        if at["alerta"]:
            alertas.append(at["alerta"])

    # --- Verde -------------------------------------------------------------
    return {
        "color": "verde",
        "mensajes": [],
        "alertas": alertas,
        "requiere_tecnico": requiere_tecnico(equipos).get("requiere_tecnico", False),
        "asistentes": at.get("asistentes", []) if turnos is not None else [],
    }


def evaluar_aprobacion(semaforo_color: str, usuario_rol: str) -> dict:
    """R11 + R10: solo el técnico puede aprobar, y solo si el semáforo es verde."""
    p_estado = puede_cambiar_estado(usuario_rol)
    if not p_estado["valido"]:
        return {"valido": False, "mensaje": p_estado["mensaje"]}
    p_aprobar = puede_aprobar(semaforo_color)
    if not p_aprobar["valido"]:
        return {"valido": False, "mensaje": p_aprobar["mensaje"]}
    return {"valido": True, "mensaje": "Cita aprobada."}
