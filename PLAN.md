# PLAN.md — CitasSIMTEC

Plan de entregas por subagente para este proyecto. Basado en `AGENTS.md`, `Contexto/` e `Insumos/`. Ninguna entrega asume datos que no estén definidos en esos orígenes.

## 1. RESUMEN

Vamos a construir CitasSIMTEC, una app web local (Flask + Python, gestionada con uv) para el laboratorio SIMTEC del TEC. Entra: el archivo `Insumos/Citas.xlsx` (9 citas, 8 columnas) y texto libre de solicitudes pegado en pantalla. El agente de IA convierte ese texto libre en un JSON con 5 llaves (solicitante_tipo, fecha, hora_inicio, hora_fin, equipos) sin decidir nada. Sale: citas con semáforo (verde/amarillo/rojo), avisos listos para copiar (coordinador + técnico; asistentes), Excel semanal descargable, y pantallas para técnico, coordinador y asistentes.

## 2. LO QUE ENCONTRÉ

**En `Contexto/`:** `Documento_de_contexto_CitasSIMTEC.docx` ya extraído a `Contexto_Mi_App.md` (85 líneas). Contiene: qué es la app, el proceso hoy, datos de entrada, reglas de negocio R1–R14, contrato del agente (5 llaves, reglas A1–A6), qué produce la app, quién decide, cifras de control, casos límite, reglas del sistema y supuestos S1–S21 **sin confirmar**.

**En `Insumos/`:** solo `Citas.xlsx` (1 hoja `Sheet1`, 9 filas de datos, 8 columnas: `Solicitante`, `Fecha`, `Hora inicio`, `Hora fin`, `Corte láser`, `Impresión 3D`, `Dobot`, `Otros`). No hay CSV, ni otro Excel, ni PDF, ni Word.

**Coincidencia con `AGENTS.md`:** `AGENTS.md` ya existe en la raíz y coincide con el contexto. Incluye `Solicitante` como 8vo campo de `Citas.xlsx` (solicitado por usted). Las 9 citas originales de la sección 8 del contexto coinciden con las 9 filas del Excel.

**Qué falta o no cuadra:**
- El contexto enumera 7 campos del Excel en su sección 3 y omite `Solicitante`; `AGENTS.md` ya lo incluyó como 8vo campo.
- El contexto menciona la regla R18 en un caso límite ("Fila del Excel con datos ilegibles | Se omite y se lista con el motivo (R18)"), pero solo se definieron reglas hasta R14. No existe R14 completa ni R15–R18 en el documento.
- Los supuestos S1–S21 están marcados como "por confirmar" y no deben asumirse como reglas.
- No hay archivo de turnos real en `Insumos/` (solo se menciona `turnos_prueba.csv` como ficticio para pruebas).

## 3. ENTREGAS POR SUBAGENTE

Orden de ejecución. Cada entrega es pequeña, construible y verificable en pocos minutos.

| N° | Responsable | Qué debe entregar | Archivos que crea o modifica | Qué recibe de la entrega anterior | Cómo se verifica en pantalla |
|----|-------------|-------------------|------------------------------|-----------------------------------|------------------------------|
| 1 | @backend | Esqueleto MVC con uv: `app/__init__.py` con `create_app()`, `wsgi.py`, `iniciar_app.bat` (instala con `uv`, enciende, abre navegador). | `app/__init__.py`, `wsgi.py`, `iniciar_app.bat`, `pyproject.toml` (o `uv.lock`) | `AGENTS.md`, `Contexto/`, `Insumos/` (solo lectura) | Ejecutar `iniciar_app.bat`: se abre el navegador y la app responde sin errores. |
| 2 | @backend | Carga de `Insumos/Citas.xlsx`: lee las 9 filas y las almacena como citas Pendiente (modelo de datos). | `app/models/` o `app/services/datos.py` (nuevo) | Entrega 1 (esqueleto MVC) | Abrir P1 "Citas de la semana": tabla muestra 9 citas con sus fechas, horas y máquinas. |
| 3 | @backend | Reglas de negocio R1–R4 (una función por regla con comentario): máquinas válidas, horario 08:00–16:00 lunes–viernes, almuerzo 12:00–13:00, duración mínima 30 min. | `app/services/reglas.py` (nuevo) | Entrega 2 (datos cargados) | Probar una cita fin de semana → rojo "Fuera de horario"; una cita de 20 min → rojo "Dura menos de 30 minutos". |
| 4 | @backend | Reglas de negocio R5–R8: sin anticipación mínima, detección de conflicto (traslapo + misma máquina), máquinas distintas válidas, técnico presente para Torno CNC y Fresadora. | `app/services/reglas.py` (modifica) | Entrega 3 (R1–R4) | Probar T-02 (corte láser 09/11 9:00–10:30) → rojo "Conflicto" con la cita 08:00–10:00. |
| 5 | @backend | Reglas de negocio R9–R14: semáforo (amarillo/rojo/verde), estados Pendiente/Aprobada/Rechazada/Cancelada, aprobar solo en verde, conflictos cuentan Pendiente y Aprobada, asistentes de turno y alerta, limpieza de texto R14. | `app/services/reglas.py`, `app/services/semaforo.py` (nuevo/modifica) | Entrega 4 (R5–R8) | Probar cita sin fecha → amarillo "Falta: fecha"; aprobar cita en rojo → no se permite. |
| 6 | @backend | Integración agente de IA: lectura de llave desde `.env`, limpieza de texto (R14), envío al agente, validación del JSON (5 llaves exactas), mensaje de error si JSON inválido. | `app/services/agente.py` (nuevo), `.env.example` (nuevo), `.gitignore` (modifica) | Entrega 5 (R9–R14) | Pegar texto de ejemplo → agente devuelve JSON válido con 5 llaves; texto inválido → "No pude leer la solicitud. Complétala a mano". |
| 7 | @frontend | Pantalla de inicio (P2): cuadro para pegar texto, botón "Leer solicitud", formulario editable con lo que entendió el agente, semáforo y mensajes, botones Guardar como pendiente / Aprobar / Rechazar. | `app/templates/inicio.html` (nuevo), `app/templates/base.html` (nuevo) | Entrega 6 (integración agente) | Pegar una solicitud → se ve el formulario editable con fecha, horas, máquinas, tipo de solicitante y semáforo. |
| 8 | @frontend | Pantalla de resultados (P1): tablero con contadores grandes (citas registradas, verde/amarillo/rojo, requieren técnico) y tabla con filtro; detalle por registro (P3). | `app/templates/resultados.html` (nuevo), `app/templates/detalle.html` (nuevo), CSS en `base.html` | Entrega 7 (pantalla de inicio) | Abrir P1: se ven los contadores y la tabla de citas con filtro; al clic en una cita se abre su detalle. |
| 9 | @frontend | Estilo de la app: CSS dentro de `base.html`, pantallas sencillas y profesionales en español, fechas dd/mm/aaaa, horas 24 h, sin librerías externas de JavaScript. | `app/templates/base.html` (modifica), `app/static/` (nuevo si es necesario) | Entrega 8 (pantallas) | Recorrer todas las pantallas: todo en español, sin librerías JS externas, errores como mensajes comprensibles. |
| 10 | @tester | Pruebas en `tests/` con pytest contra las cifras de control y los casos límite de `AGENTS.md` (pythonpath configurado). | `tests/test_*.py` (nuevo) | Entrega 9 (app completa) | Ejecutar `pytest`: cada prueba pasa o reporta diferencia con causa probable. |
| 11 | @tester | `VALIDACION.md` con esperado vs obtenido por cada cifra de control y caso límite. | `VALIDACION.md` (nuevo) | Entrega 10 (pruebas ejecutadas) | Abrir `VALIDACION.md`: se ve tabla esperado vs obtenido y diferencias, si las hay. |
| 12 | @revisor | Revisión de seguridad (llaves no hardcodeadas, `.env` en `.gitignore`, datos sensibles expuestos) y de que todo esté en `AGENTS.md`. | Ningún archivo (solo lectura y reporte) | Entrega 11 (VALIDACION.md) | Revisor entrega lista de hallazgos con prioridad y corrección propuesta; no modifica código. |

## 4. PUNTOS DE CONTROL

| Después de la entrega | Quién interviene | Qué debe ver usted en pantalla exactamente |
|-----------------------|------------------|--------------------------------------------|
| 2 (datos cargados) | @tester | P1 muestra 9 citas registradas; contadores: 9 citas, 9 verde / 0 amarillo / 0 rojo. |
| 4 (conflictos) | @tester | Al probar T-02 aparece rojo con mensaje "Conflicto: [máquina] ya está reservada el 09/11/2026 de 08:00 a 10:00". |
| 6 (agente IA) | @tester | Pegar el texto de T-01 → el agente devuelve JSON con 5 llaves en español; semáforo verde. |
| 8 (resultados) | @tester | P1 muestra: citas que requieren al técnico = 2 (12/11 Torno CNC, 13/11 Fresadora); citas por día: 09/11: 2 · 10/11: 2 · 11/11: 1 · 12/11: 1 · 13/11: 1 · 16/11: 1 · 19/11: 1. |
| 10/11 (pruebas) | @revisor | `VALIDACION.md` existe con tabla esperado vs obtenido; revisor entrega lista de hallazgos sin modificar código. |

## 5. RIESGOS

| Riesgo | Qué hará cada subagente si pasa |
|--------|--------------------------------|
| Datos incompletos (falta columna `Solicitante` en contexto; supuestos S1–S21 sin confirmar) | @arquitecto lo anotó en LO QUE ENCONTRÉ y lo dejó en PREGUNTAS PARA MÍ. Ningún subagente asume supuestos no confirmados; si falta un dato, pregunta antes de continuar. |
| Archivos escaneados o PDF como entrada | Fuera de alcance (v1) según `AGENTS.md`. La pantalla solo acepta texto. @frontend no implementa lectura de PDF/imagen; @revisor lo marca si aparece en el código. |
| Respuestas del agente que no son JSON | @backend implementa validación del JSON y muestra "No pude leer la solicitud. Complétala a mano". @tester incluye este caso límite en `tests/`. |
| Llave gratis del agente con límites o sin conexión | @backend lee la llave solo de `.env`; si falla la conexión, la app muestra "No se pudo conectar con el agente. Puedes llenar la solicitud a mano" y sigue funcionando. @revisor verifica que la llave no esté hardcodeada. |
| Contradicción R18 mencionada pero no definida | @arquitecto lo anotó en LO QUE ENCONTRÉ. @revisor lo reporta como hallazgo si el código intenta usar R18 sin definición. |

## 6. PREGUNTAS PARA MÍ

Antes de empezar, necesito que confirme:

1. ¿Confirma que la columna `Solicitante` de `Citas.xlsx` es un campo oficial de entrada (8 campos totales), aunque el contexto original solo enumera 7?
2. ¿Desea que asuma los supuestos S1–S21 como reglas para construir, o prefiere que queden como abiertos y los resuelva antes de codificar?
3. ¿Ya existe una llave del agente de IA para poner en `.env`, o debo crear solo `.env.example` sin llave real?
4. ¿El almacenamiento local debe ser SQLite (supuesto S20) o está bien usar un modelo en memoria / archivo Excel mientras se confirma?

Al recibir sus respuestas, puedo pedirle a @backend que comience con la entrega 1. Muestro a continuación la tabla de entregas para su aprobación.
