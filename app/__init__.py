from flask import Flask, jsonify, render_template

from app.controllers.citas import citas_bp


def create_app():
    """Crea y configura la aplicación Flask (patrón MVC)."""
    app = Flask(__name__)

    app.register_blueprint(citas_bp)

    @app.route("/")
    def index():
        """Página de entrada: pantalla principal con opciones para registrar o ver citas."""
        return render_template("inicio_principal.html")

    @app.route("/health")
    def health():
        return jsonify({"status": "healthy"})

    return app
