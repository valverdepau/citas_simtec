# AGENTS.md — CitasSIMTEC

## Qué es esta app

CitasSIMTEC es una app web que corre en un computador del laboratorio SIMTEC (Escuela de Ingeniería en Producción Industrial, TEC).

- **Para quién:** el técnico encargado (decide), el coordinador (ve y registra) y los asistentes de turno (consultan).
- **Problema:** las citas llegan por caminos separados (Forms del coordinador, o directo o por correo al técnico). Coordinador, técnico y asistentes se enteran en momentos distintos y tarde: el coordinador se entera el mismo día, o el técnico se entera con poca antelación, y a veces el asistente se entera justo antes de que llegue el grupo.
- **Qué hace:** el técnico o el coordinador pega el texto de una solicitud. Un agente de IA lo convierte en datos. El código revisa las reglas y los choques de máquina, y la app genera avisos listos para copiar y enviar a todos al mismo tiempo.
- **Fuera de alcance (v1):** enviar mensajes o correos automáticamente. Contraseñas y cuentas de usuario. Leer PDF o imágenes. Calendarios externos. Integrarse con el Forms.

## Datos de entrada

### Archivos de insumos (carpeta `Insumos/`)

**`Citas.xlsx`** — 1 hoja (`Sheet1`), 9 filas de datos, 8 columnas:
- `Solicitante` (texto)
- `Fecha`
- `Hora inicio`
- `Hora fin`
- `Corte láser` (`Si` / `No`)
- `Impresión 3D` (`Si` / `No`)
- `Dobot` (`Si` / `No`)
- `Otros` (nombre de la máquina o `No`)

### Otros datos de entrada

**Texto de la solicitud:** texto libre pegado en pantalla (correo o mensaje, español o inglés), sin estructura fija.
Ejemplo: `"Soy profesor. Necesito el láser el lunes 9 de noviembre de 8:00 a 10:00."`

**Lista de máquinas (fija, en el código):** 8 nombres — Corte láser, Impresión 3D, Dobot, Termoformadora, Celda de manufactura, Realidad virtual, Torno CNC, Fresadora.

**Turnos de asistentes (fijos; se llenan una vez en la app):** tabla Día de la semana, hora inicio, hora fin, nombre del asistente.

**Fecha de hoy:** reloj del sistema.

## Reglas de negocio (código, sin IA)

Todas las reglas las aplica el código; la IA no interviene en ellas.

| # | Regla |
|---|-------|
| R1 | Las únicas máquinas válidas son las 8 de la lista de la sección 3. |
| R2 | Horario: lunes a viernes, de 08:00 a 16:00. Una cita es válida solo si la fecha es lunes a viernes, hora_inicio ≥ 08:00 y hora_fin ≤ 16:00. |
| R3 | Almuerzo (12:00 a 13:00): una cita lo cruza si hora_inicio < 13:00 y hora_fin > 12:00. Terminar a las 12:00 o empezar a las 13:00 es válido. |
| R4 | hora_fin debe ser mayor que hora_inicio, y la duración mínima es de 30 minutos (exactamente 30 es válido). No hay duración máxima. |
| R5 | No hay anticipación mínima. El código no valida cuántos días antes se pide. |
| R6 | Hay conflicto entre dos citas si tienen la misma fecha, sus horarios se traslapan (inicio_A < fin_B y inicio_B < fin_A) y comparten al menos una máquina. Que una termine a la hora exacta en que empieza la otra NO es conflicto. |
| R7 | Dos citas a la misma hora con máquinas distintas son válidas. |
| R8 | Una cita requiere al técnico presente si incluye Torno CNC o Fresadora. |
| R9 | Semáforo: amarillo si falta fecha, hora de inicio, hora de fin o máquina (o la máquina no está en la lista); en ese caso no se evalúan R2 a R6. Si no, rojo si se viola R2, R3, R4 o R6. Si no, verde. |
| R10 | Estados de una cita: Pendiente, Aprobada, Rechazada, Cancelada. Toda solicitud nueva entra como Pendiente. Solo el técnico cambia el estado. |
| R11 | Solo se puede Aprobar una cita en verde. |
| R12 | Para R6 cuentan las citas Pendiente y Aprobada. Las Rechazadas y Canceladas no cuentan para conflictos, tablas, contadores ni el Excel semanal. |
| R13 | Asistentes de turno de una cita: todos los asistentes cuyo turno es el mismo día de la semana y se traslapa con la cita (turno.inicio < cita.fin y turno.fin > cita.inicio). Si no hay ninguno, se muestra la alerta "Sin asistente de turno". La alerta no cambia el color del semáforo. |
| R14 | Antes de enviar el texto al agente, el código reemplaza por [dato eliminado]: correos electrónicos, y números de 8 a 10 dígitos (con o sin espacios ...). |

## Lo que hace el agente de IA (contrato JSON)

**Rol:** lector de solicitudes. Convierte un texto libre en datos. No decide si la cita se puede hacer, no revisa choques ni horarios, y no redacta avisos.

**Qué recibe:**
1. El texto ya limpio (R14).
2. La fecha de hoy y su día de la semana.
3. La lista de las 8 máquinas.

**Qué devuelve:** únicamente un JSON con estas cinco llaves, sin texto adicional.

| Llave | Tipo | Qué significa |
|-------|------|---------------|
| `solicitante_tipo` | texto | `"profesor"`, `"estudiante"` o `"no indicado"` (docente cuenta como profesor) |
| `fecha` | texto AAAA-MM-DD | Día solicitado, o `"no indicado"` |
| `hora_inicio` | texto HH:MM (24 h) | Hora de inicio, o `"no indicado"` |
| `hora_fin` | texto HH:MM (24 h) | Hora de fin, o `"no indicado"` |
| `equipos` | lista de textos | Nombres exactos de la lista de 8 máquinas, o `["no indicado"]` |

**Ejemplo:**
```json
{"solicitante_tipo": "profesor", "fecha": "2026-11-16", "hora_inicio": "08:00", "hora_fin": "10:00", "equipos": ["Impresión 3D"]}
```

**Reglas del agente:**
- A1: Nunca inventa. Si un dato no aparece en el texto, escribe `"no indicado"`.
- A2: Responde siempre con el JSON y con esas llaves en español, aunque el texto venga en inglés o con faltas de ortografía.
- A3: Las fechas relativas ("mañana", "el jueves") se resuelven con la fecha de hoy que recibe. "El jueves" significa la próxima ocurrencia posterior a hoy. Si el texto da dos fechas posibles, `fecha` es `"no indicado"`.
- A4: Las horas imprecisas ("en la mañana", "en la tarde") dan `"no indicado"`. Si el texto da la duración ("por 2 horas desde las 9"), calcula hora_fin. Una hora sin AM/PM se interpreta dentro de 08:00 a 16:00; si no queda claro, `"no indicado"`.
- A5: Acepta sinónimos evidentes de máquinas (impresora 3D = Impresión 3D, láser = Corte láser, VR = Realidad virtual). Si el texto menciona una máquina que no está en la lista, `equipos` es `["no indicado"]` para que el técnico lo revise.
- A6: No devuelve nombres, correos, teléfonos ni carnés.

**Validación del código:** el código valida el JSON: deben estar exactamente las cinco llaves, la fecha y las horas deben tener formato válido y las máquinas deben ser de la lista. Si no cumple, la app muestra `"No pude leer la solicitud. Complétala a mano"` y deja el formulario vacío para llenarlo.

## Qué produce la app

### Pantallas (todas en español, sencillas)

| Pantalla | Contenido |
|----------|-----------|
| P1 · Citas de la semana (principal) | Selector de semana. Tabla con: fecha, hora, máquinas, ¿requiere técnico?, asistente de turno, estado y semáforo (verde, amarillo, rojo) con su mensaje. Botones: Nueva solicitud, Importar Excel, Descargar Excel de la semana. |
| P2 · Nueva solicitud | Cuadro para pegar el texto y botón "Leer solicitud". Luego un formulario editable con lo que entendió el agente (fecha, horas, máquinas, tipo de solicitante), el semáforo y sus mensajes. Botones: Guardar como pendiente, Aprobar, Rechazar. |
| P3 · Detalle de cita | Datos de la cita. Botones: Cancelar cita, Generar aviso (copiar). |
| P4 · Turnos | Tabla de turnos de asistentes, editable. |

### Mensajes del semáforo

| Color | Mensajes |
|-------|----------|
| Amarillo | `"Falta: fecha"` · `"Falta: hora de inicio"` · `"Falta: hora de fin"` · `"Falta: máquina (o no está en la lista)"` |
| Rojo | `"Conflicto: [máquina] ya está reservada el [fecha] de [hh:mm] a [hh:mm]"` · `"Fuera de horario: el laboratorio atiende de lunes a viernes de 08:00 a 16:00"` · `"Cruza el almuerzo (12:00 a 13:00)"` · `"Dura menos de 30 minutos"` · `"La hora de fin debe ser después de la de inicio"` · `"La fecha ya pasó"` |
| Alertas | `"Requiere al técnico presente"` · `"Sin asistente de turno en ese horario"` |

### Permisos

| Acción | Técnico | Coordinador | Asistente |
|--------|---------|-------------|-----------|
| Ver citas (el asistente puede filtrar las de su turno) | Sí | Sí | Sí |
| Registrar solicitud y generar avisos | Sí | Sí | No |
| Aprobar, rechazar o cancelar | Sí | No | No |
| Editar turnos e importar Excel | Sí | No | No |
| Descargar Excel semanal | Sí | Sí | No |

### Avisos (texto fijo generado por el código, sin IA)

```
NUEVA CITA EN SIMTEC
Fecha: lunes 09/11/2026
Hora: 08:00 a 10:00
Máquinas: Corte láser, Dobot, Termoformadora
Requiere al técnico presente: No
Asistente de turno: Asistente A
```

- El aviso 1 va para el coordinador y el técnico. El aviso 2 va para los asistentes de turno, con el mismo contenido y dirigido a ellos.
- Cuando la cita se cancela, el título cambia a `CITA CANCELADA EN SIMTEC` y se genera el mismo par de avisos.
- Si no hay asistente, la línea dice `Asistente de turno: SIN ASISTENTE`.

### Excel semanal descargable

Columnas: Fecha, Hora inicio, Hora fin, Corte láser, Impresión 3D, Dobot, Otros (valores `"Si"` o `"No"`; en Otros, el nombre de la máquina o `"No"`), ordenadas por fecha y hora.

## Quién decide

El técnico encargado toma la decisión final sobre cada cita (aprobar, rechazar, cancelar). La IA solo lee el texto y nunca aprueba nada. El coordinador registra y consulta. Los asistentes solo consultan. Cuando una cita se cancela o cambia, el técnico es quien organiza las nuevas citas.

## Cifras de control

Con `citas_original.xlsx` importado (9 citas, todas Aprobadas) y `turnos_prueba.csv`:

| Indicador | Resultado exacto |
|-----------|------------------|
| Citas registradas | 9 |
| Citas en verde / amarillo / rojo | 9 / 0 / 0 |
| Citas con conflicto | 0 |
| Citas que requieren al técnico | 2 (la del 12/11 con Torno CNC y la del 13/11 con Fresadora) |
| Citas sin asistente de turno | 0 |
| Citas por día | 09/11: 2 · 10/11: 2 · 11/11: 1 · 12/11: 1 · 13/11: 1 · 16/11: 1 · 19/11: 1 |
| Excel de la semana 09/11 al 13/11 | 7 filas (las 7 primeras de la tabla de citas originales, en ese orden) |

**Uso por máquina (de las 9 citas originales):**

| Máquina | Citas | Horas de uso |
|---------|-------|--------------|
| Corte láser | 6 | 7,0 |
| Impresión 3D | 2 | 2,0 |
| Dobot | 3 | 4,0 |
| Termoformadora | 1 | 2,0 |
| Celda de manufactura | 1 | 1,0 |
| Realidad virtual | 1 | 1,0 |
| Torno CNC | 1 | 2,0 |
| Fresadora | 1 | 1,0 |

## Casos límite

| Caso | Comportamiento esperado |
|------|-------------------------|
| Texto vacío | Mensaje "Pega el texto de la solicitud"; no se llama al agente. |
| Falta fecha, hora o máquina | Amarillo, indicando qué falta. |
| Máquina que no está en la lista | `equipos = ["no indicado"]`; amarillo. |
| Fecha vaga ("el jueves", "mañana") | El agente la resuelve con la fecha de hoy; si queda ambigua, amarillo. |
| El texto da dos fechas posibles | `fecha = "no indicado"`; amarillo; el técnico separa las solicitudes. |
| Fecha anterior a hoy | Rojo ("La fecha ya pasó"). |
| Fuera de horario, fin de semana, almuerzo o menos de 30 min | Rojo, con el mensaje correspondiente. |
| Misma máquina y horarios que se traslapan | Rojo, indicando con cuál cita. |
| Una cita termina a la hora en que empieza otra con la misma máquina | Válido (verde). |
| Hora sin asistente de turno | Alerta "Sin asistente de turno". |
| Texto en inglés o con faltas | El agente lo lee y responde en español con las llaves fijas. |
| El agente devuelve un JSON inválido | Mensaje "No pude leer la solicitud. Complétala a mano". |
| Falla internet o el servicio de IA | Mensaje "No se pudo conectar con el agente. Puedes llenar la solicitud a mano". La app sigue funcionando. |
| Excel vacío o con columnas distintas | La app no carga nada y explica qué falta, sin mostrar errores técnicos. |
| Fila del Excel con datos ilegibles | Se omite y se lista con el motivo (R18). |
| Texto con correo, teléfono o carné | Se reemplazan por [dato eliminado] antes de enviar (R14). |
| Cita cancelada o rechazada | No cuenta para conflictos ni tablas (R12). |
| Texto pegado como imagen o PDF | No soportado; la pantalla solo acepta texto. |

## Reglas del sistema

| Tema | Regla |
|------|-------|
| Tecnología | Python con Flask. Patrón MVC. Gestión de dependencias y ejecución con uv. |
| Estructura MVC | Modelos: citas, turnos, máquinas y todas las reglas R1 a R20 en Python puro, sin Flask ni IA. Vistas: plantillas HTML en español y estilos simples. Controladores: rutas Flask que conectan pantallas y modelos. El único módulo que llama al agente es el que limpia el texto (R14) y valida el JSON. |
| Llave del agente | Solo en el archivo `.env`, nunca en el código. Se entrega un `.env.example` sin llave real, y `.env` va en `.gitignore`. |
| Arranque | `iniciar_app.bat`: instala dependencias con uv, enciende la app y abre el navegador. |
| Pantallas | Sencillas y en español, con fechas dd/mm/aaaa y horas en 24 h. Los errores se muestran como mensajes comprensibles, nunca como errores técnicos. |
| Privacidad | Lo único que sale del computador es el texto de la solicitud ya limpio (R14) hacia el agente. Todo lo demás queda local. |
| Pruebas | Pruebas automáticas que reproduzcan las cifras de control de la sección 9 y los casos T-01 a T-15. Las reglas se prueban con respuestas del agente simuladas; además, una prueba aparte llama al agente real con la llave. |
| Alcance | Prohibido inventar reglas o campos que no estén en este documento. Si algo no está definido, el desarrollador debe detenerse y listar la duda en lugar de decidirla. |

## Supuestos sin resolver (abiertos)

El contexto incluye una sección "Supuestos por confirmar" (S1 a S21) que **no han sido confirmados**. No se asumen como reglas en este `AGENTS.md`. Quedan pendientes de confirmar con el técnico / coordinador / autora. Ejemplos: S1 (una sola unidad de cada máquina), S2 (la lista de 8 máquinas está completa), S6 (turnos reales pendientes), S13 (fecha anterior a hoy → rojo), S20 (almacenamiento local SQLite), S21 (meta de uso: registrar una solicitud y generar los avisos en menos de 2 minutos). No se afirma ninguno de ellos aquí.
