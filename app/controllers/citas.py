"""Controlador de citas: rutas Flask que conectan pantallas y modelos.

No contiene lógica de negocio; solo expone endpoints.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, send_file, flash

from app.services.datos import cargar_citas_excel
from app.services.semaforo import evaluar_semaforo, evaluar_aprobacion
from app.services.agente import preparar_texto_para_agente, enviar_al_agente
from app.models.cita import Cita

citas_bp = Blueprint("citas", __name__)

# Almacenamiento en memoria de la sesión actual (se reemplazará por SQLite en S20)
_citas: list = []
_contador_id = 1


def _cita_a_dict_con_id(cita, cita_id):
    """Convierte una Cita a dict agregando el id interno."""
    d = cita.a_dict() if hasattr(cita, "a_dict") else dict(cita)
    d["id"] = cita_id
    return d


# ---------------------------------------------------------------------------
# Rutas de páginas (HTML)
# ---------------------------------------------------------------------------

@citas_bp.route("/inicio", methods=["GET"])
def inicio():
    """Pantalla de inicio (P2): formulario para pegar texto de solicitud."""
    return render_template("inicio.html")


@citas_bp.route("/inicio/leer", methods=["POST"])
def leer_solicitud():
    """Recibe el texto de la solicitud, llama al agente y muestra el resultado."""
    texto_original = request.form.get("texto_solicitud", "").strip()
    if not texto_original:
        return render_template("inicio.html", error="Pega el texto de la solicitud")

    # R14: limpiar texto antes de enviar al agente
    texto_limpio = preparar_texto_para_agente(texto_original)

    from datetime import datetime
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    dia_semana = ahora.strftime("%A")
    # Mapear día al español
    dias_es = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo",
    }
    dia_semana_es = dias_es.get(dia_semana, dia_semana)

    maquinas_validas = [
        "Corte láser", "Impresión 3D", "Dobot", "Termoformadora",
        "Celda de manufactura", "Realidad virtual", "Torno CNC", "Fresadora",
    ]

    # Llamar al agente
    respuesta_agente = enviar_al_agente(texto_limpio, fecha_hoy, dia_semana_es, maquinas_validas)

    if "error" in respuesta_agente:
        return render_template(
            "inicio.html",
            texto_original=texto_original,
            error=respuesta_agente["error"],
            detalle=respuesta_agente.get("detalle", ""),
        )

    # Validar semáforo con los datos del agente
    equipos = respuesta_agente.get("equipos", ["no indicado"])
    fecha = respuesta_agente.get("fecha", "no indicado")
    hora_inicio = respuesta_agente.get("hora_inicio", "no indicado")
    hora_fin = respuesta_agente.get("hora_fin", "no indicado")

    semaforo = evaluar_semaforo(
        fecha, hora_inicio, hora_fin, equipos, _citas, turnos=None
    )

    # Convertir equipos a lista de nombres legibles para las checkboxes
    maquinas_seleccionadas = equipos if equipos != ["no indicado"] else []

    return render_template(
        "inicio.html",
        texto_original=texto_original,
        resultado=respuesta_agente,
        semaforo_color=semaforo["color"],
        mensajes=semaforo["mensajes"],
        alerta=semaforo["alertas"][0] if semaforo["alertas"] else None,
        requiere_tecnico=semaforo["requiere_tecnico"],
        maquinas_validas=maquinas_validas,
    )


@citas_bp.route("/inicio/guardar", methods=["POST"])
def guardar_solicitud():
    """Guarda la cita como Pendiente (o Aprobada/Rechazada según acción)."""
    global _contador_id

    solicitante_tipo = request.form.get("solicitante_tipo", "no indicado")
    fecha = request.form.get("fecha", "")
    hora_inicio = request.form.get("hora_inicio", "")
    hora_fin = request.form.get("hora_fin", "")
    equipos = request.form.getlist("equipos")
    accion = request.form.get("accion", "guardar")

    # Construir dict de máquinas para el modelo
    maquinas_dict = {
        "corte_laser": "Si" if "Corte láser" in equipos else "No",
        "impresion_3d": "Si" if "Impresión 3D" in equipos else "No",
        "dobot": "Si" if "Dobot" in equipos else "No",
        "otros": "No",
    }

    estado = "Pendiente"
    if accion == "aprobar":
        semaforo = evaluar_semaforo(fecha, hora_inicio, hora_fin, equipos, _citas)
        apr = evaluar_aprobacion(semaforo["color"], "tecnico")
        if not apr["valido"]:
            flash(apr["mensaje"], "error")
            return redirect(url_for("citas.inicio"))
        estado = "Aprobada"
    elif accion == "rechazar":
        estado = "Rechazada"

    cita = Cita(
        solicitante="Solicitante",
        solicitante_tipo=solicitante_tipo,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        corte_laser=maquinas_dict["corte_laser"],
        impresion_3d=maquinas_dict["impresion_3d"],
        dobot=maquinas_dict["dobot"],
        otros=maquinas_dict["otros"],
        estado=estado,
    )
    cita.id = _contador_id
    _contador_id += 1
    _citas.append(cita)

    return redirect(url_for("citas.listar_citas_html"))


# ---------------------------------------------------------------------------
# Rutas de citas (HTML + JSON)
# ---------------------------------------------------------------------------

@citas_bp.route("/citas", methods=["GET"])
def listar_citas_html():
    """Pantalla de resultados (P1): tabla de citas con contadores y filtro por servidor."""
    from datetime import datetime, date, timedelta

    # Cargar citas automáticamente si no están en memoria
    global _citas, _contador_id
    if not _citas:
        citas_cargadas = cargar_citas_excel()
        _citas = citas_cargadas
        _contador_id = len(citas_cargadas) + 1

    # Obtener parámetros de filtro
    tipo_filtro = request.args.get("tipo", "ninguno")  # semana, dia, ninguno
    fecha_str = request.args.get("fecha", "")

    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%Y-%m-%d")

    # Calcular rango de fechas según el filtro
    fecha_inicio = None
    fecha_fin = None

    if tipo_filtro == "semana" and fecha_str:
        partes = fecha_str.split("-")
        ano, mes, dia = int(partes[0]), int(partes[1]), int(partes[2])
        fecha_sel = date(ano, mes, dia)
        dia_semana = fecha_sel.weekday()  # 0=lunes, 6=domingo
        fecha_inicio = fecha_sel - timedelta(days=dia_semana)  # lunes
        fecha_fin = fecha_inicio + timedelta(days=6)  # domingo
    elif tipo_filtro == "dia" and fecha_str:
        partes = fecha_str.split("-")
        ano, mes, dia = int(partes[0]), int(partes[1]), int(partes[2])
        fecha_inicio = date(ano, mes, dia)
        fecha_fin = fecha_inicio

    # Construir citas vista con semáforo
    citas_vista = []
    contador_verde = 0
    contador_amarillo = 0
    contador_rojo = 0
    contador_tecnico = 0

    maquinas_validas = [
        "Corte láser", "Impresión 3D", "Dobot", "Termoformadora",
        "Celda de manufactura", "Realidad virtual", "Torno CNC", "Fresadora",
    ]

    turnos = [
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

    for i, c in enumerate(_citas):
        d = c.a_dict() if hasattr(c, "a_dict") else dict(c)
        d["id"] = getattr(c, "id", i + 1)

        # Calcular equipos para el semáforo
        equipos = []
        if d.get("corte_laser") == "Si": equipos.append("Corte láser")
        if d.get("impresion_3d") == "Si": equipos.append("Impresión 3D")
        if d.get("dobot") == "Si": equipos.append("Dobot")
        if d.get("otros") and d.get("otros") != "No": equipos.append(d["otros"])

        semaforo = evaluar_semaforo(
            d["fecha"], d["hora_inicio"], d["hora_fin"], equipos, [], turnos
        )
        d["semaforo_color"] = semaforo["color"]
        d["mensajes_semaforo"] = semaforo["mensajes"]
        d["alerta_turno"] = semaforo["alertas"][0] if semaforo["alertas"] else None
        d["requiere_tecnico"] = semaforo["requiere_tecnico"]
        d["asistente_turno"] = semaforo["asistentes"][0] if semaforo["asistentes"] else None

        # Construir lista de máquinas para mostrar
        maquinas_mostrar = []
        for m in maquinas_validas:
            clave = m.lower().replace(" ", "_")
            if d.get(clave) == "Si":
                maquinas_mostrar.append(m)
        if d.get("otros") and d.get("otros") != "No":
            maquinas_mostrar.append(d["otros"])
        d["maquinas"] = maquinas_mostrar

        # Aplicar filtro de fecha en el servidor
        if fecha_inicio and fecha_fin:
            fecha_cita = date.fromisoformat(d["fecha"])
            if fecha_cita < fecha_inicio or fecha_cita > fecha_fin:
                continue

        if semaforo["color"] == "verde":
            contador_verde += 1
        elif semaforo["color"] == "amarillo":
            contador_amarillo += 1
        elif semaforo["color"] == "rojo":
            contador_rojo += 1
        if semaforo["requiere_tecnico"]:
            contador_tecnico += 1

        citas_vista.append(d)

    return render_template(
        "resultados.html",
        citas=citas_vista,
        total_citas=len(citas_vista),
        contador_verde=contador_verde,
        contador_amarillo=contador_amarillo,
        contador_rojo=contador_rojo,
        contador_tecnico=contador_tecnico,
        semana_seleccionada=fecha_str or fecha_hoy,
        tipo_filtro=tipo_filtro,
    )


@citas_bp.route("/citas/json", methods=["GET"])
def listar_citas_json():
    """Devuelve todas las citas cargadas (JSON)."""
    return jsonify([c.a_dict() if hasattr(c, "a_dict") else c for c in _citas])


@citas_bp.route("/citas/cargar", methods=["POST"])
def cargar_citas():
    """Carga las citas desde Insumos/Citas.xlsx (entrega 2)."""
    global _citas, _contador_id
    citas = cargar_citas_excel()
    _citas = citas
    _contador_id = len(citas) + 1
    return jsonify(
        {
            "mensaje": f"Se cargaron {len(citas)} citas desde Insumos/Citas.xlsx",
            "total": len(citas),
            "estado": "Pendiente",
        }
    )


@citas_bp.route("/citas/<int:cita_id>", methods=["GET"])
def detalle_cita(cita_id):
    """Pantalla de detalle (P3): datos de una cita y acciones."""
    cita = next((c for c in _citas if getattr(c, "id", None) == cita_id), None)
    if not cita:
        return "Cita no encontrada", 404

    d = cita.a_dict() if hasattr(cita, "a_dict") else dict(cita)
    d["id"] = cita_id

    # Calcular equipos para el semáforo
    equipos = []
    if d.get("corte_laser") == "Si": equipos.append("Corte láser")
    if d.get("impresion_3d") == "Si": equipos.append("Impresión 3D")
    if d.get("dobot") == "Si": equipos.append("Dobot")
    if d.get("otros") and d.get("otros") != "No": equipos.append(d["otros"])

    semaforo = evaluar_semaforo(
        d["fecha"], d["hora_inicio"], d["hora_fin"], equipos, [], turnos=None
    )
    d["semaforo_color"] = semaforo["color"]
    d["mensajes_semaforo"] = semaforo["mensajes"]
    d["alerta_turno"] = semaforo["alertas"][0] if semaforo["alertas"] else None
    d["requiere_tecnico"] = semaforo["requiere_tecnico"]
    d["asistente_turno"] = semaforo["asistentes"][0] if semaforo["asistentes"] else None

    # Generar texto del aviso
    aviso_texto = (
        f"NUEVA CITA EN SIMTEC\n"
        f"Fecha: {d['fecha']}\n"
        f"Hora: {d['hora_inicio']} a {d['hora_fin']}\n"
        f"Máquinas: {', '.join(equipos) if equipos else 'No indicado'}\n"
        f"Requiere al técnico presente: {'Sí' if d['requiere_tecnico'] else 'No'}\n"
        f"Asistente de turno: {d['asistente_turno'] or 'SIN ASISTENTE'}"
    )

    maquinas_validas = [
        "Corte láser", "Impresión 3D", "Dobot", "Termoformadora",
        "Celda de manufactura", "Realidad virtual", "Torno CNC", "Fresadora",
    ]
    maquinas_mostrar = []
    for m in maquinas_validas:
        clave = m.lower().replace(" ", "_")
        if d.get(clave) == "Si":
            maquinas_mostrar.append(m)
    if d.get("otros") and d.get("otros") != "No":
        maquinas_mostrar.append(d["otros"])
    d["maquinas"] = maquinas_mostrar

    return render_template(
        "detalle.html",
        cita=d,
        aviso_texto=aviso_texto,
    )


@citas_bp.route("/citas/<int:cita_id>/aprobar", methods=["POST"])
def aprobar_cita(cita_id):
    """Aprueba una cita si el semáforo es verde."""
    global _citas
    cita = next((c for c in _citas if getattr(c, "id", None) == cita_id), None)
    if not cita:
        return "Cita no encontrada", 404

    d = cita.a_dict() if hasattr(cita, "a_dict") else dict(cita)
    equipos = []
    if d.get("corte_laser") == "Si": equipos.append("Corte láser")
    if d.get("impresion_3d") == "Si": equipos.append("Impresión 3D")
    if d.get("dobot") == "Si": equipos.append("Dobot")
    if d.get("otros") and d.get("otros") != "No": equipos.append(d["otros"])

    semaforo = evaluar_semaforo(
        d["fecha"], d["hora_inicio"], d["hora_fin"], equipos, _citas
    )
    apr = evaluar_aprobacion(semaforo["color"], "tecnico")
    if not apr["valido"]:
        return apr["mensaje"], 400

    cita.estado = "Aprobada"
    return redirect(url_for("citas.detalle_cita", cita_id=cita_id))


@citas_bp.route("/citas/<int:cita_id>/rechazar", methods=["POST"])
def rechazar_cita(cita_id):
    """Rechaza una cita."""
    cita = next((c for c in _citas if getattr(c, "id", None) == cita_id), None)
    if not cita:
        return "Cita no encontrada", 404
    cita.estado = "Rechazada"
    return redirect(url_for("citas.detalle_cita", cita_id=cita_id))


@citas_bp.route("/citas/<int:cita_id>/cancelar", methods=["POST"])
def cancelar_cita(cita_id):
    """Cancela una cita."""
    cita = next((c for c in _citas if getattr(c, "id", None) == cita_id), None)
    if not cita:
        return "Cita no encontrada", 404
    cita.estado = "Cancelada"
    return redirect(url_for("citas.detalle_cita", cita_id=cita_id))


@citas_bp.route("/citas/excel", methods=["GET"])
def descargar_excel():
    """Descarga Excel semanal (placeholder)."""
    from flask import make_response
    import io
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Citas semana"
    ws.append(["Fecha", "Hora inicio", "Hora fin", "Corte láser", "Impresión 3D", "Dobot", "Otros"])

    for c in _citas:
        d = c.a_dict() if hasattr(c, "a_dict") else dict(c)
        if d.get("estado") in ("Rechazada", "Cancelada"):
            continue
        ws.append([
            d.get("fecha", ""),
            d.get("hora_inicio", ""),
            d.get("hora_fin", ""),
            d.get("corte_laser", "No"),
            d.get("impresion_3d", "No"),
            d.get("dobot", "No"),
            d.get("otros", "No"),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="citas_semana.xlsx",
    )
