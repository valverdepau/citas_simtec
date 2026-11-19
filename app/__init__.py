import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from app.controllers.auth import auth_bp, login_requerido
from app.controllers.citas import citas_bp


def create_app():
    """Crea y configura la aplicación Flask (patrón MVC)."""
    load_dotenv()

    app = Flask(__name__)

    # Control de acceso: usuario y contraseña SOLO desde variables de entorno.
    app.config["APP_USUARIO"] = os.environ.get("APP_USUARIO", "")
    app.config["APP_CLAVE"] = os.environ.get("APP_CLAVE", "")
    app.secret_key = os.environ.get("SECRET_KEY", "")

    # La sesión expira a las 8 horas.
    app.permanent_session_lifetime = timedelta(hours=8)

    if not all(
        os.environ.get(nombre, "").strip()
        for nombre in ("APP_USUARIO", "APP_CLAVE", "SECRET_KEY")
    ):
        print("Faltan variables de entorno: APP_USUARIO, APP_CLAVE o SECRET_KEY")

    app.register_blueprint(auth_bp)
    app.register_blueprint(citas_bp)

    @app.route("/")
    @login_requerido
    def index():
        """Página de entrada: pantalla principal con opciones para registrar o ver citas."""
        return render_template("inicio_principal.html")

    @app.route("/health")
    @login_requerido
    def health():
        return jsonify({"status": "healthy"})

    return app
