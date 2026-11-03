# Pruebas manuales con curl

Base: `http://localhost:8000`. Clientes del seed:

| Documento | Nombre | Estado | Saldo | Corte |
|---|---|---|---|---|
| 1020304050 | Laura Gómez | activo | 0 | 2026-11-05 |
| 52123456 | Carlos Pérez | suspendido | 85000 | 2026-10-20 |
| 79876543 | Ana Ruiz | activo | 120500 | 2026-11-15 |

Todos los errores tienen la forma `{"error": "mensaje"}`. Los valores de `id`, `fecha`, `celular` y `plan` son ilustrativos.

## GET /health

```bash
curl -i http://localhost:8000/health
```
- 200: `{"status":"ok"}`
- 503 (base de datos caída): `{"error":"Servicio no disponible, intente más tarde"}`

## GET /api/clientes/{documento}

Éxito:
```bash
curl -i http://localhost:8000/api/clientes/79876543
```
200:
```json
{"documento":"79876543","nombre":"Ana Ruiz","celular":"3023334455","plan":"Plan Combo Plus","estado":"activo","saldo":120500,"fecha_corte":"2026-11-15"}
```

Cliente suspendido:
```bash
curl -i http://localhost:8000/api/clientes/52123456
```
200 con `"estado":"suspendido"`, `"saldo":85000`, `"fecha_corte":"2026-10-20"`.

Documento mal formado (menos de 6 dígitos, más de 10, letras o puntos):
```bash
curl -i http://localhost:8000/api/clientes/12345
```
400: `{"error":"El documento debe ser numérico, de 6 a 10 dígitos"}`

No existe:
```bash
curl -i http://localhost:8000/api/clientes/999999
```
404: `{"error":"No existe un cliente con documento 999999"}`

Base de datos caída: 503 `{"error":"Servicio no disponible, intente más tarde"}`.

## POST /api/gestiones

Canales válidos: `ivr`, `whatsapp`, `agente`. Tipificaciones válidas: `Consulta de saldo`, `Consulta de estado`, `Reclamo`, `Solicitud de asesor`, `Otro`.

Registro nuevo:
```bash
curl -i -X POST http://localhost:8000/api/gestiones \
  -H "Content-Type: application/json" \
  -d '{"documento":"1020304050","canal":"ivr","tipificacion":"Consulta de saldo","observacion":"Pregunta por su saldo"}'
```
201: `{"id":1,"fecha":"2026-11-01T10:30:00-05:00"}`

Idempotencia (misma clave dos veces):
```bash
curl -i -X POST http://localhost:8000/api/gestiones \
  -H "Content-Type: application/json" -H "Idempotency-Key: demo-001" \
  -d '{"documento":"79876543","canal":"whatsapp","tipificacion":"Otro"}'
```
- Primera vez, 201: `{"id":2,"fecha":"2026-11-01T10:31:00-05:00"}`
- Repetida, 200 con el mismo cuerpo (mismo `id` y `fecha`), sin crear otra gestión.

Gestión sin cliente identificado. El `documento` es opcional solo para los canales `ivr` y `whatsapp`; sin documento, la observación es obligatoria porque explica el motivo:
```bash
curl -i -X POST http://localhost:8000/api/gestiones   -H "Content-Type: application/json" -H "Idempotency-Key: llamada-123-asesor"   -d '{"canal":"ivr","tipificacion":"Solicitud de asesor","observacion":"Transferida al asesor tras 3 errores en el menú"}'
```
- Primera vez, 201: `{"id":3,"fecha":"2026-11-01T10:32:00-05:00"}`
- Repetida con la misma clave, 200 con el mismo cuerpo.
- Estas gestiones no aparecen en `GET /api/gestiones?documento=...`, que lista por cliente.

Errores propios de la gestión sin documento:

```bash
# Canal agente sin documento
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json"   -d '{"canal":"agente","tipificacion":"Otro","observacion":"Sin documento"}'
```
400: `{"error":"El documento es obligatorio para el canal agente"}`

```bash
# IVR sin documento y sin observación
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json"   -d '{"canal":"ivr","tipificacion":"Solicitud de asesor"}'
```
400: `{"error":"La observación es obligatoria cuando no se informa documento"}`

Con documento informado, las reglas son las de siempre: formato inválido da 400 y un documento que no existe da 404, también para `ivr` y `whatsapp`.

Errores 400 (todos con `{"error":"..."}`):

```bash
# Canal inválido
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json" \
  -d '{"documento":"1020304050","canal":"telegram","tipificacion":"Otro"}'
```
400: `{"error":"Canal inválido. Valores permitidos: ivr, whatsapp, agente"}`

```bash
# Tipificación inválida
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json" \
  -d '{"documento":"1020304050","canal":"ivr","tipificacion":"Queja"}'
```
400: `{"error":"Tipificación inválida. Valores permitidos: Consulta de saldo, Consulta de estado, Reclamo, Solicitud de asesor, Otro"}`

```bash
# Reclamo sin observación
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json" \
  -d '{"documento":"1020304050","canal":"agente","tipificacion":"Reclamo"}'
```
400: `{"error":"La observación es obligatoria cuando la tipificación es Reclamo"}`

Observación de más de 1000 caracteres, 400: `{"error":"La observación no puede superar 1000 caracteres"}`.

```bash
# Cuerpo sin campos
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json" -d '{}'
```
400: `{"error":"Solicitud inválida: canal: campo obligatorio; tipificacion: campo obligatorio"}`

```bash
# Documento mal formado
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json" \
  -d '{"documento":"1.020.304","canal":"ivr","tipificacion":"Otro"}'
```
400: `{"error":"El documento debe ser numérico, de 6 a 10 dígitos"}`

Idempotency-Key de más de 64 caracteres (`-H "Idempotency-Key: <65 caracteres>"`), 400: `{"error":"Idempotency-Key no puede superar 64 caracteres"}`.

Cliente inexistente:
```bash
curl -i -X POST http://localhost:8000/api/gestiones -H "Content-Type: application/json" \
  -d '{"documento":"999999","canal":"ivr","tipificacion":"Otro"}'
```
404: `{"error":"No existe un cliente con documento 999999"}`

Base de datos caída: 503 `{"error":"Servicio no disponible, intente más tarde"}`.

## GET /api/gestiones?documento=...

Historial, la gestión más reciente primero:
```bash
curl -i "http://localhost:8000/api/gestiones?documento=1020304050"
```
200:
```json
[{"id":3,"documento":"1020304050","canal":"agente","tipificacion":"Reclamo","observacion":"Cobro duplicado","fecha":"2026-11-01T10:40:00-05:00"},
 {"id":1,"documento":"1020304050","canal":"ivr","tipificacion":"Consulta de saldo","observacion":"Pregunta por su saldo","fecha":"2026-11-01T10:30:00-05:00"}]
```

Cliente sin gestiones: 200 `[]`.

Sin el parámetro:
```bash
curl -i http://localhost:8000/api/gestiones
```
400: `{"error":"El parámetro documento es obligatorio"}`

Documento mal formado (`?documento=12`), 400: `{"error":"El documento debe ser numérico, de 6 a 10 dígitos"}`.

Cliente inexistente (`?documento=999999`), 404: `{"error":"No existe un cliente con documento 999999"}`.

Base de datos caída: 503 `{"error":"Servicio no disponible, intente más tarde"}`.

## Ruta inexistente

```bash
curl -i http://localhost:8000/api/no-existe
```
404 con cuerpo JSON `{"error":"Recurso no encontrado"}`.
