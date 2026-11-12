@echo off
:: Instala dependencias con uv
uv sync
:: Enciende la app y abre el navegador
start "" http://127.0.0.1:5000
uv run flask --app wsgi run --host=127.0.0.1 --port=5000
