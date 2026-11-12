# VALIDACIÓN — CitasSIMTEC

Resultado de las pruebas automáticas ejecutadas con pytest contra las cifras de control y los casos límite de `AGENTS.md`. No se modificó el código de la app; solo se escribieron pruebas en `tests/` y se reportan las diferencias.

## Resumen

- **Pruebas totales:** 63
- **Pruebas aprobadas:** 63
- **Pruebas fallidas:** 0
- **Diferencias encontradas:** 0

## Cifras de control (AGENTS.md sección 9)

Con `citas_original.xlsx` importado (9 citas, todas Pendiente) y `turnos_prueba.csv` (ficticio):

| Indicador | Esperado | Obtenido | Estado |
|-----------|----------|----------|--------|
| Citas registradas | 9 | 9 | ✅ |
| Citas en verde | 9 | 9 | ✅ |
| Citas en amarillo | 0 | 0 | ✅ |
| Citas en rojo | 0 | 0 | ✅ |
| Citas con conflicto | 0 | 0 | ✅ |
| Citas que requieren al técnico | 2 (12/11 Torno CNC, 13/11 Fresadora) | 2 | ✅ |
| Citas sin asistente de turno | 0 | 0 | ✅ |
| Citas por día | 09/11: 2 · 10/11: 2 · 11/11: 1 · 12/11: 1 · 13/11: 1 · 16/11: 1 · 19/11: 1 | Igual | ✅ |
| Excel de la semana 09/11 al 13/11 | 7 filas | 7 | ✅ |

Uso por máquina (de las 9 citas originales):

| Máquina | Citas esperadas | Citas obtenidas | Horas de uso esperadas | Horas de uso obtenidas | Estado |
|---------|-----------------|-----------------|------------------------|------------------------|--------|
| Corte láser | 6 | 6 | 7,0 | 7,0 | ✅ |
| Impresión 3D | 2 | 2 | 2,0 | 2,0 | ✅ |
| Dobot | 3 | 3 | 4,0 | 4,0 | ✅ |
| Termoformadora | 1 | 1 | 2,0 | 2,0 | ✅ |
| Celda de manufactura | 1 | 1 | 1,0 | 1,0 | ✅ |
| Realidad virtual | 1 | 1 | 1,0 | 1,0 | ✅ |
| Torno CNC | 1 | 1 | 2,0 | 2,0 | ✅ |
| Fresadora | 1 | 1 | 1,0 | 1,0 | ✅ |

## Casos límite (AGENTS.md sección Casos límite)

| Caso | Esperado | Obtenido | Estado |
|------|----------|----------|--------|
| Texto vacío | Mensaje "Pega el texto de la solicitud"; no se llama al agente | No probado en pantalla (pendiente de frontend) | ⚠️ Pendiente |
| Falta fecha, hora o máquina | Amarillo, indicando qué falta | Amarillo con mensajes específicos | ✅ |
| Máquina no en la lista | `equipos = ["no indicado"]`; amarillo | Amarillo | ✅ |
| Fecha vaga ("el jueves", "mañana") | Agente resuelve con fecha de hoy; si ambigua, amarillo | No probado (requiere agente real) | ⚠️ Pendiente |
| Dos fechas posibles | `fecha = "no indicado"`; amarillo | No probado (requiere agente real) | ⚠️ Pendiente |
| Fecha anterior a hoy | Rojo ("La fecha ya pasó") | No probado en regla explícita (R2 cubre fuera de horario) | ⚠️ Pendiente |
| Fuera de horario | Rojo | Rojo | ✅ |
| Fin de semana | Rojo | Rojo (T-09) | ✅ |
| Cruza almuerzo | Rojo | Rojo (T-07) | ✅ |
| Menos de 30 min | Rojo | Rojo (T-08) | ✅ |
| Traslapes misma máquina | Rojo, indicando con cuál cita | Rojo con mensaje de conflicto (T-02) | ✅ |
| Cita termina cuando empieza otra | Válido (verde) | Verde (T-04) | ✅ |
| Sin asistente de turno | Alerta "Sin asistente de turno" | Alerta generada | ✅ |
| Texto en inglés o con faltas | Agente lee y responde en español con llaves fijas | No probado (requiere agente real) | ⚠️ Pendiente |
| JSON inválido del agente | "No pude leer la solicitud. Complétala a mano" | Validado en pruebas unitarias | ✅ |
| Falla internet / servicio IA | "No se pudo conectar con el agente. Puedes llenar la solicitud a mano" | Validado sin llave configurada | ✅ |
| Excel vacío o columnas distintas | App no carga nada, explica qué falta | No probado (pendiente de integración frontend) | ⚠️ Pendiente |
| Fila con datos ilegibles | Se omite y lista con motivo (R18) | No probado (R18 no definida en contexto) | ⚠️ Pendiente |
| Correo, teléfono o carné | Reemplazados por [dato eliminado] (R14) | Validado en pruebas | ✅ |
| Cita cancelada o rechazada | No cuenta para conflictos ni tablas (R12) | Validado en pruebas | ✅ |
| Texto como imagen o PDF | No soportado; pantalla solo acepta texto | No probado (pendiente de frontend) | ⚠️ Pendiente |

## Casos de prueba T-01 a T-11

| Prueba | Esperado | Obtenido | Estado |
|--------|----------|----------|--------|
| T-01 | profesor, 2026-11-16, 08:00–10:00, [Impresión 3D]. Verde, asistente A. | Verde, asistentes: ['Asistente A'] | ✅ |
| T-02 | Rojo: conflicto con 09/11 08:00–10:00 | Rojo: "Conflicto: Corte láser ya está reservada el 09/11/2026 de 08:00 a 10:00" | ✅ |
| T-03 | Verde, asistente B | Verde, asistentes: ['Asistente B'] | ✅ |
| T-04 | Verde (empieza cuando termina otra) | Verde | ✅ |
| T-05 | fecha 2026-11-05, horas "no indicado", [Corte láser]. Amarillo: falta hora inicio y fin. | Amarillo: falta hora de inicio y hora de fin | ✅ |
| T-06 | Rojo: fuera de horario. Requiere técnico: Sí. | Rojo: fuera de horario, requiere_tecnico: True | ✅ |
| T-07 | Rojo: cruza almuerzo. Requiere técnico: Sí. | Rojo: cruza almuerzo, requiere_tecnico: True | ✅ |
| T-08 | Rojo: dura menos de 30 minutos | Rojo: dura menos de 30 minutos | ✅ |
| T-09 | Rojo: fin de semana | Rojo: fuera de horario (fin de semana) | ✅ |
| T-10 | equipos = ["no indicado"]. Amarillo. | Amarillo: máquina no en lista | ✅ |
| T-11 | estudiante, 2026-11-19, 08:00–09:00, [Impresión 3D]. Verde. | Verde | ✅ |

## Diferencias y causas probables

No se encontraron diferencias entre lo esperado (según `AGENTS.md`) y lo obtenido en las pruebas automatizadas.

Los casos marcados como "⚠️ Pendiente" requieren:
1. Integración del frontend (pantallas) para probar en pantalla.
2. Llave real del agente de IA para probar respuestas en inglés, fechas vagas, dos fechas posibles, etc.
3. Definición de R18 (fila con datos ilegibles) — el contexto menciona R18 pero no la define.

## Cómo reproducir

```bash
uv run pytest tests/ -v
```

Todas las pruebas deben pasar con 63/63.
