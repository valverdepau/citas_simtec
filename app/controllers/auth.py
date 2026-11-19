"""Control de acceso con usuario administrador (sin base de datos).

Las credenciales se leen SOLO de variables de entorno:
- APP_USUARIO: usuario administrador.
- APP_CLAVE: contraseña del administrador.
- SECRET_KEY: clave de la sesión de Flask.

Este módulo solo expone las rutas de ingreso y salida y el decorador
`login_requerido`; las reglas de negocio siguen en los modelos.
"""

from __future__ import annotations

import hmac
import os
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

auth_bp = Blueprint("auth", __name__)

VARIABLES_REQUERIDAS = ("APP_USUARIO", "APP_CLAVE", "SECRET_KEY")
MENSAJE_FALTANTES = "Faltan variables de entorno: APP_USUARIO, APP_CLAVE o SECRET_KEY"


def acceso_configurado() -> bool:
    """Indica si las tres variables de entorno del acceso están presentes."""
    return all(bool(os.environ.get(nombre, "").strip()) for nombre in VARIABLES_REQUERIDAS)


def login_requerido(vista):
    """Exige haber entrado para acceder a la vista protegida."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not acceso_configurado():
            return redirect(url_for("auth.login"))
        if not session.get("usuario"):
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)

    return envoltura


@auth_bp.route("/login", methods=["GET"])
def login():
    """Muestra el formulario de ingreso (GET /login)."""
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def autenticar():
    """Compara usuario y contraseña con las variables de entorno (POST /login)."""
    if not acceso_configurado():
        print(MENSAJE_FALTANTES)
        return render_template(
            "login.html",
            error="El acceso no está configurado. Revisa las variables de entorno.",
        )

    usuario = request.form.get("usuario", "")
    clave = request.form.get("clave", "")

    usuario_ok = hmac.compare_digest(
        usuario.encode("utf-8"), str(current_app.config["APP_USUARIO"]).encode("utf-8")
    )
    clave_ok = hmac.compare_digest(
        clave.encode("utf-8"), str(current_app.config["APP_CLAVE"]).encode("utf-8")
    )

    if usuario_ok and clave_ok:
        session.clear()
        session.permanent = True  # la sesión expira a las 8 horas
        session["usuario"] = usuario
        return redirect(url_for("index"))

    return render_template("login.html", error="Usuario o contraseña incorrectos")


@auth_bp.route("/salir", methods=["GET"])
def salir():
    """Borra la sesión y vuelve al formulario de ingreso (GET /salir)."""
    session.clear()
    return redirect(url_for("auth.login"))
