"""Pruebas del control de acceso: login sin base de datos."""

import pytest

from app import create_app

USUARIO = "admin"
CLAVE = "Cambiar2026"
SECRET_KEY_PRUEBA = "clave-de-sesion-de-prueba"


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv("APP_USUARIO", USUARIO)
    monkeypatch.setenv("APP_CLAVE", CLAVE)
    monkeypatch.setenv("SECRET_KEY", SECRET_KEY_PRUEBA)
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_1_entrar_bien(cliente):
    """Con usuario y contraseña correctos se entra a la pantalla principal."""
    respuesta = cliente.post("/login", data={"usuario": USUARIO, "clave": CLAVE})
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/")

    principal = cliente.get("/")
    assert principal.status_code == 200
    assert "CitasSIMTEC" in principal.get_data(as_text=True)


def test_2_clave_equivocada(cliente):
    """Con clave equivocada se muestra el mensaje general y no se entra."""
    respuesta = cliente.post("/login", data={"usuario": USUARIO, "clave": "otra-clave"})
    assert respuesta.status_code == 200
    texto = respuesta.get_data(as_text=True)
    assert "Usuario o contraseña incorrectos" in texto
    assert "Citas de la semana" not in texto

    principal = cliente.get("/")
    assert principal.status_code == 302
    assert "/login" in principal.headers["Location"]


def test_3_pantalla_principal_sin_entrar(cliente):
    """Sin sesión, todas las pantallas redirigen al login."""
    for ruta in ("/", "/inicio", "/citas", "/citas/json"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 302, ruta
        assert "/login" in respuesta.headers["Location"], ruta


def test_4_salir_y_volver_a_intentar(cliente):
    """Después de salir, la pantalla principal vuelve a pedir login."""
    cliente.post("/login", data={"usuario": USUARIO, "clave": CLAVE})
    assert cliente.get("/").status_code == 200

    salida = cliente.get("/salir")
    assert salida.status_code == 302
    assert "/login" in salida.headers["Location"]

    principal = cliente.get("/")
    assert principal.status_code == 302
    assert "/login" in principal.headers["Location"]


def test_5_faltan_variables_de_entorno(monkeypatch, capsys):
    """Sin las variables configuradas avisa en consola y no deja entrar a nadie."""
    monkeypatch.setattr("app.load_dotenv", lambda *args, **kwargs: None)
    for nombre in ("APP_USUARIO", "APP_CLAVE", "SECRET_KEY"):
        monkeypatch.delenv(nombre, raising=False)

    app = create_app()
    app.config.update(TESTING=True)
    salida = capsys.readouterr()
    assert "Faltan variables de entorno: APP_USUARIO, APP_CLAVE o SECRET_KEY" in salida.out

    cliente = app.test_client()
    # Incluso con campos vacíos, no debe dejar entrar.
    respuesta = cliente.post("/login", data={"usuario": "", "clave": ""})
    assert respuesta.status_code == 200
    assert cliente.get("/").status_code == 302
