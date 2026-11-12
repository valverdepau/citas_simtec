#!/usr/bin/env bash
set -e
echo "==> Instalando dependencias con uv..."
uv sync
echo "==> Encendiendo la app y abriendo el navegador..."
uv run flask --app wsgi run --host=127.0.0.1 --port=5000 &
APP_PID=$!
sleep 2
open http://127.0.0.1:5000
wait $APP_PID
