# Historial del Chat - Vehicle Detection System

## Fecha: jueves, 6 de agosto de 2026

### Resumen de la Sesión de Trabajo

Se analizó el proyecto Vehicle Detection System ubicado en `/home/server-gea/Documentos/vehicle-detection-system`.

#### Información del Proyecto
- Sistema inteligente de detección de vehículos estacionados con IA
- Utiliza YOLOv8, ByteTrack y PaddleOCR
- Arquitectura de microservicios con Docker
- Incluye backend (FastAPI), servicio de IA, frontend (Bootstrap 5), PostgreSQL y Redis

#### Estado Actual
- **Problema crítico**: El daemon de Docker no está funcionando debido a módulos del kernel faltantes
- Error específico: `Extension addrtype revision 0 not supported, missing kernel module?`
- Intento de solución: `sudo modprobe xt_addrtype` falló con "Module xt_addrtype not found"
- El kernel 6.12.0-254.el10.x86_64 no tiene el módulo xt_addrtype disponible
- Esto impide el despliegue completo mediante docker-compose

#### Conclusiones
El proyecto está estructurado correctamente y listo para desarrollo, pero requiere que Docker funcione para el despliegue completo. 
Dado que el módulo kernel xt_addrtype no está disponible en este sistema, procederemos con el enfoque de desarrollo directo para cada componente.

---
*Este historial se crea para mantener continuidad en el trabajo del proyecto.

## Actualización: Configuración de Entorno de Desarrollo Completa

### Logros de la Sesión

1. **Backend (FastAPI) - CONFIGURADO**

## Continuación: Desarrollo de Componentes por Separado

### 1. Exploración y Desarrollo del Backend

Exploré la estructura del backend y encontré que tiene una arquitectura bien organizada con:

- Módulos principales: auth, users, cameras, vehicles, events, reports, config, whatsapp, system, websocket

- Middleware personalizado para rate limiting y auditoría

Mejorando el endpoint de salud del backend para incluir verificaciones de conectividad con servicios externos

Mejorado el endpoint de salud del backend para incluir:

- Verificaciones de conectividad con base de datos y Redis

- Endpoints de readiness y liveness probes para entornos de orquestación (Kubernetes)

- Verificado que el módulo de salud se importa correctamente sin errores

### 2. Exploración del Servicio de IA

Mejorado el endpoint de salud del servicio de IA para incluir:

- Verificación de conectividad con el backend

- Verificación de disponibilidad de GPU y uso de memoria

- Verificado que el módulo de salud del servicio de IA se importa correctamente sin errores

### Resumen de Mejoras Realizadas

1. **Backend (FastAPI)**

   - Mejorado el endpoint de salud (/health/detailed) para incluir verificaciones de conectividad con base de datos y Redis

   - Agregado endpoints de readiness (/ready) y liveness (/live) para entornos de orquestación

   - Verificado que el módulo de salud se importa correctamente

2. **Servicio de IA**

   - Mejorado el endpoint de salud (/health/detailed) para incluir verificación de conectividad con el backend

   - Agregado verificación de disponibilidad de GPU y uso de memoria

   - Agregado endpoints de readiness (/ready) y liveness (/live) para entornos de orquestación

   - Verificado que el módulo de salud se importa correctamente

### Pruebas Finales

Creado y ejecutado script de prueba que verifica que ambos módulos de salud (backend y servicio de IA) se importan correctamente

- Resultado: ✅ Todos los tests pasaron correctamente!

## Conclusión y Próximos Pasos

Hemos exitosamente configurado entornos de desarrollo para todos los componentes del Vehicle Detection System y realizado mejoras significativas en los endpoints de salud de ambos servicios (backend y servicio de IA).

Los próximos pasos recomendados para continuar el desarrollo son:

1. Continuar desarrollando cada componente por separado según las necesidades del proyecto

2. Cuando se necesite la funcionalidad completa de PaddleOCR, instalar las herramientas de construcción faltantes (swig, gcc, make, etc.)

3. Considerar el uso de máquinas virtuales o entornos de contenedores alternativos si se requiere el entorno completo de Docker para pruebas de integración


¡El Vehicle Detection System está ahora listo para desarrollo continuo! Los entornos están configurados y se han realizado mejoras útiles en los puntos críticos de monitoreo de salud de los servicios.

--

## Actualización: Análisis de Estado para Prueba Real (viernes, 7 de agosto de 2026)

### Estado Actual Post-Despliegue Docker

Tras resolver los problemas de autenticación y subir los cambios al repositorio Git, se verificó el estado actual de los servicios Docker:

#### Servicios y su Estado:

- **redis**: ✅ Funcionando correctamente (Up 43 hours)
- **frontend**: ⚠️ Ejecutándose pero marcado como unhealthy (Up 41 hours)
- **backend**: ❌ Fallando continuamente (Restarting cada 18 segundos)
- **ai_service**: ❌ Fallando continuamente (Restarting cada 28 segundos)
- **postgresql**: ❌ No visible en la lista de contenedores activos

#### Problemas Identificados y Soluciones Necesarias:

##### 4. FRONTEND - Health Check Fallando

- Síntoma: Marcado como unhealthy aunque nginx esté ejecutándose
- Estado: Probablemente fallando porque no puede conectarse al backend (que no está disponible)
- Acciones Necesarias:
  - Este problema se resolverá automáticamente cuando el backend esté funcionando
  - Verificar el endpoint de health check en /healthz una vez que el backend esté disponible
  - Revisar la configuración de Nginx en frontend/nginx.conf

---

## Actualización: Análisis y Prueba de PostgreSQL y Redis en Docker (lunes, 10 de agosto de 2026)

### Estado del daemon de Docker
- El daemon estaba **inactivo/deshabilitado** (`docker.service` disabled, sin socket).
- **Resuelto**: el módulo `xt_addrtype` YA está presente en el kernel 6.12.0-254.el10.x86_64 (paquete `kernel-modules-extra` instalado en sesiones previas). `systemctl start docker` funciona correctamente.
- Se recomienda `systemctl enable --now docker` para que arranque solo en cada reinicio.

### Pruebas realizadas con los contenedores del proyecto

Al arrancar el daemon se reactivaron los contenedores del compose `vehicle-detection-system`:

| Servicio | Contenedor | Estado | Notas |
|---|---|---|---|
| **redis** | `redis:7-alpine` | ✅ Up, puerto 6379 | `PING → PONG`. Redis vacío (0 keys). Conectividad OK |
| **db (postgres)** | `postgres:15-alpine` | ⚠️ Roto/aislado | BD `vehicle_detection` creada con esquema completo, pero sin red |
| **backend** | FastAPI | ❌ Crash loop | `ImportError: email-validator is not installed` (falta `email-validator` en requirements/Dockerfile) |
| **ai_service** | CUDA | ❌ Crash loop | `ModuleNotFoundError: No module named 'psutil'` (falta `psutil` en requirements/Dockerfile) |
| **frontend** | nginx | ⚠️ Unhealthy | Ejecutándose pero sin backend disponible |

### Causa raíz del problema de postgres en Docker (CONFIRMADO)
- El contenedor `db` se creó con bind de puerto `0.0.0.0:5432`, pero el host ya tiene **PostgreSQL nativo 16 corriendo en el puerto 5432** (systemd, habilitado, escuchando en 127.0.0.1).
- Por el conflicto de puerto, el contenedor `db` **no puede unirse a la red `vehicle_network`** → corre aislado (sin IP, sin DNS), aunque internamente postgres 15.18 está funcionando y tiene el esquema (cameras, detected_vehicles, events, parking_zones, system_config, users).
- Ambas bases (host y contenedor) tienen el **mismo esquema** de 6 tablas.

### Prueba decisiva de conectividad interna
- Se lanzó un postgres temporal en `vehicle_network` **sin exponer puerto al host**:
  - DNS por nombre de servicio: ✅ resuelve (`pgtest`)
  - TCP 5432 desde el contenedor redis: ✅ conecta
  - `pg_isready`: ✅ aceptando conexiones
- **Conclusión**: postgres DENTRO de docker es viable. La solución limpia es:
  1. Recrear el contenedor `db` **sin publicar el puerto 5432 al host** (solo red interna), o parar/deshabilitar el postgres nativo del host.
  2. Añadir el servicio `db` al `docker-compose.yml` (actualmente NO existe) y apuntar `DATABASE_URL=postgresql://postgres:postgres@db:5432/vehicle_detection` (hoy usa `host.docker.internal` que no resuelve en Linux sin `extra_hosts: host-gateway`).

### Hallazgos adicionales del estado actual
- El `docker-compose.yml` actual **no define el servicio `db`** (postgres) ni `evolution-api` (WhatsApp); solo backend, ai_service, frontend y redis.
- Backend en Docker no puede resolver `host.docker.internal` (Linux no lo resuelve sin configuración) → de todos modos no conectaría a postgres.
- Redis funciona en Docker; el backend usa `REDIS_URL=redis://redis:6379` (correcto en red interna).

### Próximos pasos (pendiente decisión)
1. Decidir: ¿postgres en Docker (recrear `db` sin puerto host) o postgres nativo del host? → ajustar `docker-compose.yml` en consecuencia.
2. Corregir crash loops del backend (`email-validator`) y ai_service (`psutil`).
3. Habilitar Docker al inicio: `systemctl enable --now docker`.

---
*Actualizado: lunes, 10 de agosto de 2026*

## Actualización: Stack Docker Funcional End-to-End (lunes, 10 de agosto de 2026)

### Servicios en Docker quedaron todos HEALTHY
| Servicio | Contenedor | Estado | Puerto |
|---|---|---|---|
| **db** | `postgres:15-alpine` | ✅ healthy | 5433→5432 (host 5432 ocupado por postgres nativo) |
| **backend** | FastAPI | ✅ healthy | 8000 |
| **ai_service** | CUDA 12.1 | ✅ healthy | 8001 |
| **frontend** | nginx | ✅ healthy | 80 |
| **redis** | `redis:7-alpine` | ✅ Up | 6379 |

### Decisión tomada
- **Postgres vive en Docker**, recreado como servicio `db` en el `docker-compose.yml` (que antes NO existía).
- Se expone en puerto **5433** del host para no chocar con el PostgreSQL 16 nativo del sistema (systemd, 127.0.0.1:5432).
- `DATABASE_URL=postgresql://postgres:postgres@db:5432/vehicle_detection` (DNS interno de docker).

### Crash loops resueltos (causa raíz → fix)
1. **backend**: `email-validator` (requirements ya lo tenía, faltaba rebuild de imagen), luego `httpx`, luego `psutil` → se agregaron a `backend/requirements.txt`.
2. **ai_service**: `psutil` faltante → agregado a `ai/requirements.txt`.
3. **bcrypt 5.0.0 roto con passlib 1.7.4**: login daba "password cannot be longer than 72 bytes" → fijado `bcrypt==4.0.1`.
4. **numpy 2.x rompía cv2**: pinneado `numpy>=1.26,<2` en ambos requirements.

### Refactor grande: alinear ORM al esquema de `database/init.sql`
La BD en Docker (creada por init.sql) NO coincidía con los modelos ORM → 500 en todos los endpoints. Se alinearon **modelos, schemas y routers** al esquema canónico de init.sql:

- **IDs UUID** en todos los modelos (antes Integer).
- `zones` → **`parking_zones`**; `system_configs` → **`system_config`**.
- `DetectedVehicle`: `track_id` → **`vehicle_id`** (VARCHAR), `confidence` Float, `bbox` JSONB, `park_start_time`, `total_park_time` Interval.
- `cameras`: + `fps`, `width`, `height`, `owner_id` (FK users).
- `events`: `event_metadata` → **`metadata`** JSONB (atributo Python `meta` porque `metadata` es reservado en SQLAlchemy declarative), + `license_plate`. Se eliminó `user_id`.
- `SystemConfig`: `value` JSONB (antes Text).
- Se agregó tabla **`audit_logs`** a init.sql.
- Schemas pydantic v2: `orm_mode` → `model_config = ConfigDict(from_attributes=True)`.
- init.sql: + `owner_id` en cameras, + tabla `audit_logs`, hash de admin corregido a `admin123`.

### Bugs de routers corregidos
- **`utils.auth.get_current_active_user` era un stub que devolvía `None`** → todos los endpoints autenticados fallaban con `'NoneType' object has no attribute 'role'`. Ahora reexporta la implementación real de `utils.security`.
- **`zones` no estaba montado en `main.py`** y le faltaba import de `Camera`/`User`.
- **`vehicles.py` no tenía endpoint POST** (la IA no podría registrar vehículos) → agregado.
- Params de ruta `int` → `UUID` en cameras/users/vehicles/zones/events.
- **WebSocket daba 403 por ruta duplicada**: el router se monta con prefix `/api/ws` y la ruta interna era `/ws/{client_id}` → corregido a `/{client_id}`. Ahora responde.
- **`report_service.py` incompleto**: no tenía los métodos que usa `reports.py` → implementados (`generate_daily/weekly/monthly_report`, `generate_pdf/excel_report`, `get_statistics`). Se agregaron `reportlab` y `openpyxl` a requirements.

### Healthchecks y proxy
- **Causa raíz del "unhealthy"**: en los contenedores `localhost` resuelve a `::1` (IPv6) pero los servicios escuchan solo en IPv4 → "Connection refused". Y backend/ai no tenían `curl`.
- Backend y ai_service: healthcheck ahora usa `python3 -c urllib.request` contra `127.0.0.1`.
- Frontend: healthcheck usa `wget http://127.0.0.1/healthz`.
- **nginx.conf**: `proxy_pass http://backend:8000/` con slash final quitaba el prefijo `/api/` → 404. Corregido a `http://backend:8000` (sin slash).

### Pruebas finales end-to-end (todas OK)
- `POST /api/auth/login` (admin/admin123) → access_token ✅
- CRUD completo: crear cámara → zona → vehículo → evento, listar ✅
- `/api/reports/stats`, `/api/reports/daily` (PDF) ✅
- `/api/system/status`, `/api/config/`, `/api/users/` ✅
- WebSocket `/api/ws/42` → "Message received" ✅
- Proxy nginx: `/api/*` → backend, `/ai/*` → ai_service ✅
- Datos de prueba creados: cámara "Entrada Principal", zona "Zona A", vehículo T-101, evento vehicle_parked.

### Pendientes para próximas sesiones
1. **Conectar el AI service** (hoy solo sirve `/` y `/health`): mover `ai_service.py` a una API real, corregir imports (usa `backend.models.detected_vehicle` que no existe → debe usar el modelo alineado), eliminar dependencia del paquete `backend`.
2. **Conectar frontend a la API** (hoy 100% mock: `js/main.js`, `js/events.js`) y crear páginas de Cámaras/Estacionamiento/Reportes/Configuración/Usuarios (menú apunta a `#`).
3. **PaddleOCR** pendiente (requiere `swig`, `gcc`, `make`).
4. Verificar que `numpy<2` no rompe ultralytics dentro del contenedor al usarse la detección.

---
*Actualizado: lunes, 10 de agosto de 2026*

## Actualización: Fix de Deadlock en AI Service y Healthcheck de Redis (lunes, 10 de agosto de 2026)

### Problema: AI service "unhealthy" con evento bloqueado
- El contenedor `ai_service` quedó `unhealthy` (failing streak 36+): el healthcheck de Docker a `/health` daba timeout (5s) y el endpoint colgaba indefinidamente desde el host.
- Diagnóstico con `py-spy dump` → deadlock en dos partes:
  1. **Hilo de procesamiento de cámara** colgado en `BackendClient._request` → `_ensure_token`: `_request` tomaba `self._lock` y luego `_ensure_token` intentaba re-adquirir el **mismo `threading.Lock` no reentrante** → deadlock (primera vez que el token es `None`).
  2. **Bucle de eventos de FastAPI** colgado en `stop_camera_processing` → `frame_queues[camera_id].put(None)`: la cola acotada (maxsize=10) se llenaba porque `get_frame_for_display` nunca se llama y el hilo de procesamiento estaba muerto (no drenaba la cola) → `put()` bloquea para siempre y congela todos los endpoints (`/health` incluido).

### Fixes aplicados
1. **`ai/app/backend_client.py`**: `threading.Lock()` → `threading.RLock()` (reentrante) para evitar el auto-deadlock en el login inicial.
2. **`ai/services/ai_service.py`**:
   - `stop_camera_processing`: `put(None)` → `put_nowait(None)` + `try/except queue.Full` (no bloquea el event loop).
   - Nuevo `stop_events: Dict[str, threading.Event]` por cámara: `start_camera_processing` crea el evento, `stop_camera_processing` lo marca y el hilo sale limpiamente.
   - `_process_camera_stream`: el loop ahora itera mientras el stop event no esté marcado y drena la cola de frames una vez por iteración (después de tomar el frame lee el centinela `None` para terminar). Se eliminan los threads zombie que nunca salían.

### Fix: healthcheck de Redis en backend
- `/health/detailed` reportaba `redis: disconnected` aunque Redis respondía `PING → PONG`.
- Causa raíz: `backend/health.py` usaba `redis.from_string(...)` que **no existe** en redis-py 5.0.1 → la excepción se tragaba y reportaba "disconnected".
- Fix: `redis.Redis.from_url(settings.REDIS_URL)`. Ahora `/health/detailed` → `redis: connected`, `/ready` → 200.

### Pruebas end-to-end (todas OK)
- Todos los contenedores `healthy`: ai_service, frontend, backend, db; redis `Up`.
- `/health` del AI responde en ~8-11ms (antes colgaba >120s).
- Ciclos de start/stop de cámara (test_video.mp4) repetidos 3+ veces: sin congelamiento del event loop, sin threads zombie.
- Detección con UUID real de cámara → la IA detecta vehículos, hace login contra el backend y reporta `POST /api/vehicles/` correctamente (persistido en PostgreSQL).

### Pendientes para próximas sesiones
1. Conectar el **frontend a la API** (hoy 100% mock: `js/main.js`, `js/events.js`).
2. **PaddleOCR** pendiente (requiere `swig`, `gcc`, `make`); ultralytics/torch no instalado → fallback OpenCV.
3. `systemctl enable --now docker` para que Docker arranque solo en reinicio.
4. Advertencia menor: al terminar un archivo de video, `cap.read()` falla y el hilo loguea "Failed to read frame" cada 0.1s hasta el stop (spam de log).

---
*Actualizado: lunes, 10 de agosto de 2026*

## Sesión: Conexión del Frontend a la API — Plan Paso a Paso (lunes, 10 de agosto de 2026)

### Contexto
Se analizó el proyecto completo con apoyo de `chat_history.md` y `DEVELOPMENT_SETUP_SUMMARY.md`. El backend y el AI service ya están funcionales (todos los contenedores healthy). La deuda pendiente principal es el **frontend**: el menú apunta a `#`, hay funciones mock sin llamar a la API y faltan páginas de Cámaras/Estacionamiento/Reportes/Configuración/Usuarios.

### Metodología
Trabajo **paso a paso**: cada paso se documenta aquí y se sube a Git con un commit independiente.

- **Paso 1 — Baseline**: limpieza de archivos generados (logs, `.bak`, `test*.txt`, `prueba.txt`, `test_video.mp4`) que quedaron rastreados. Se añadieron a `.gitignore` (`*.bak`, `*.mp4`, `test.txt`, `test2.txt`, `prueba.txt`). Se hace commit de todo el refactor pendiente de hoy (modelos UUID, routers, healthchecks, login frontend, api.js, AI service API).
- **Paso 2 — Infraestructura frontend**: crear `js/common.js` (utilidades compartidas), enlaces reales en el sidebar, skeletons de páginas nuevas y fix del HTML inválido en `events.html`.
- **Paso 3 — Página Cámaras**: CRUD + control del AI service (start/stop por cámara).
- **Paso 4 — Página Estacionamiento**: zonas (conectar el dibujo a la API) + vehículos estacionados.
- **Paso 5 — Página Reportes**: estadísticas reales y descarga PDF/Excel.
- **Paso 6 — Página Configuración**: system config + WhatsApp.
- **Paso 7 — Página Usuarios**: CRUD de usuarios (admin).
- **Paso 8 — Eventos**: exportar, filtro dinámico por cámara, ver detalles.
- **Paso 9 — Documentación final**: README + historial + resumen.

### Paso 1 completado ✅ (commit `e6dfe6f`)
Limpieza de archivos generados y commit del refactor de la API. Detalle arriba.

### Paso 2 completado ✅ (infraestructura frontend)
- Creado `frontend/js/common.js`: `Common.requireAuth()`, `Common.initSidebar(activePage)` (toggle, logout, nombre de usuario, resaltado del menú), `Common.showNotification()`, `Common.escapeHtml()`, `Common.formatDateTime()`, `Common.formatDate()`, `Common.formatDuration()`.
- `main.js` y `events.js` refactorizados para usar `Common` (se eliminaron funciones duplicadas `escapeHtml`/`showNotification`).
- Sidebar de `index.html` y `events.html` ahora apunta a páginas reales: `pages/cameras.html`, `pages/parking.html`, `pages/events.html`, `pages/reports.html`, `pages/settings.html`, `pages/users.html` (con atributo `data-page`).
- Fix de HTML inválido en `events.html:64` (`data-bs-toggle="aria-expanded="false"` → `data-bs-toggle="dropdown" aria-expanded="false"`).
- Creados skeletons de las 5 páginas nuevas + sus JS (`cameras.js`, `parking.js`, `reports.js`, `settings.js`, `users.js`).
- Sintaxis verificada con `node --check` en todos los JS.

### Paso 3 completado ✅ (página Cámaras)
- `api.js`: nuevas funciones hacia el AI service a través del proxy `/ai/*`: `aiGetStatus()`, `aiStartCamera(cameraId, {rtsp_url, username, password})`, `aiStopCamera(cameraId)`, `aiGetCameraResults(cameraId)`.
- `pages/cameras.html`: tabla de cámaras (nombre, ubicación, stream, estado activa/inactiva, procesamiento IA, acciones), botón "Nueva Cámara", modal de crear/editar cámara (nombre, ubicación, RTSP, credenciales, FPS, resolución, activa) y modal "Estado IA".
- `js/cameras.js`: CRUD real contra `/api/cameras/`, control de IA (start/stop) contra `/ai/api/detection/...`, indicador "Procesando/Detenida" por cámara consultando `/ai/api/detection/status`, refresh automático (IA cada 10s, lista cada 30s).

### Paso 4 completado ✅ (página Estacionamiento)
- `api.js`: `createZone()`, `updateZone()`, `deleteZone()` contra `/api/zones/`.
- `pages/parking.html`: tabla de **vehículos estacionados** (ID de seguimiento, tipo, placa, cámara, primera/última vista) con botón de actualizar, y tabla de **zonas de estacionamiento** (nombre, cámara, nº de puntos, estado, acciones: dibujar/editar/eliminar).
- `js/parking.js`: 
  - Vehículos estacionados reales desde `/api/vehicles/parked/current` (refresh cada 30s).
  - CRUD de zonas real contra `/api/zones/` (modal crear/editar con selector de cámara).
  - Dibujo de coordenadas sobre canvas conectado a la API: clic para marcar vértices, deshacer, limpiar y guardar (`PUT /api/zones/{id}`). Se cargan las coordenadas existentes al editar.
- Eliminado `main.js` (funciones de zona antiguas que solo logueaban) y `js/zone-management.js` (archivo huérfano no referenciado).

### Paso 5 completado ✅ (página Reportes + dashboard real)
- `api.js`: `downloadReport(path, filename)` — descarga binaria autenticada (blob + objeto URL) para PDF/Excel.
- `pages/reports.html`: 4 tarjetas de estadísticas (eventos totales, eventos 30 días, vehículos detectados, estacionados ahora) y formulario de generación de reportes (tipo diario/semanal/mensual, formato PDF/Excel, fechas dinámicas).
- `js/reports.js`: estadísticas reales desde `/api/reports/stats?days=30` y descarga real de `/api/reports/{daily|weekly|monthly}?format=pdf|excel` (se genera el nombre del archivo según `Content-Disposition`).
- Dashboard (`index.html` + `main.js`): eliminadas las estadísticas hardcodeadas (12/5/4/2, 8/10/5) — ahora se calculan desde los vehículos reales: por tipo (`stat-type-*`) y por duración de estacionamiento (`stat-dur-*`) usando `park_start_time`/`first_seen`.

### Paso 6 completado ✅ (página Configuración)
- `api.js`: CRUD de configuración (`createConfig`, `updateConfig`, `deleteConfig`, `initializeDefaultConfigs`) y WhatsApp (`getWhatsAppStatus`, `configureWhatsApp`, `testWhatsApp`, `sendWhatsAppMessage`).
- `pages/settings.html`: 
  - Tabla de **configuración del sistema** (clave, valor, descripción, editar/eliminar) + botón "Nueva Configuración" y "Inicializar Defaults". Modal con valor JSON (acepta números, strings, booleanos y arrays).
  - Sección **WhatsApp**: estado actual, formulario de configuración (URL de Evolution, API Key, instancia), botón "Probar Conexión" y formulario para enviar mensaje de prueba.
- `js/settings.js`: CRUD real contra `/api/config/` y control real de WhatsApp contra `/api/whatsapp/*` con estado visible.

### Paso 7 completado ✅ (página Usuarios)
- `api.js`: `createUser()`, `updateUser()`, `deleteUser()` contra `/api/users/`.
- `pages/users.html`: tabla de usuarios (usuario, nombre, email, rol, estado, fecha de creación, acciones) + modal crear/editar con validaciones (email, contraseña mínima 8 caracteres, roles admin/operator/user, activo/inactivo).
- `js/users.js`: CRUD real contra `/api/users/`. Al editar se oculta el campo contraseña (el backend no soporta cambio de password por PUT).

### Paso 8 completado ✅ (página Eventos)
- `pages/events.html`:
  - Filtro de cámara (`#cameraFilter`) ahora es un select vacío que se **pobla dinámicamente** desde `/api/cameras/` (antes estaba hardcodeado).
  - Nuevo modal `#eventDetailsModal` para ver el detalle completo de un evento.
- `js/events.js`:
  - `loadCameraOptions()`: carga las cámaras y construye un `cameraMap {id → name}`; la tabla ahora muestra el **nombre de la cámara** en lugar del UUID.
  - Filtro por cámara **en el cliente** (el backend `GET /api/events/` no acepta `camera_id`).
  - Botón "Ver detalles": modal con fecha, tipo, descripción, cámara, placa, IDs (evento/vehículo/zona) y metadatos crudos (`event.meta` formateado).
  - Botón WhatsApp: pide el número por prompt y encola el envío vía `POST /api/whatsapp/send-message` con `{phone_number, message}` (payload validado contra `backend/routers/whatsapp.py`).
  - **Exportación CSV real**: descarga `eventos_YYYY-MM-DD.csv` desde los datos visibles en la DataTable (antes mostraba "en desarrollo"), con escape CSV correcto.
  - Event delegation para las acciones de la tabla, tooltips reinicializados tras cada redraw de la DataTable.
- Sintaxis verificada con `node --check`.

### Paso 9 completado ✅ (Documentación final)
- `README.md`: sección "Uso del Sistema" reescrita con las páginas reales del frontend (Panel Principal, Cámaras, Estacionamiento, Historial de Eventos, Reportes, Configuración del Sistema, Usuarios). La configuración de zonas de estacionamiento ahora referencia la página **Estacionamiento** (dibujo sobre canvas persistido en `/api/zones/`).
- `DEVELOPMENT_SETUP_SUMMARY.md`: se añadió el estado del frontend conectado a la API (todas las páginas), los fixes de deadlock/Redis, y los próximos pasos actualizados.
- `chat_history.md`: se documentó el Paso 8 (Eventos) y este cierre del plan.

### 🎯 PLAN COMPLETADO — Frontend 100% conectado a la API
El plan paso a paso quedó terminado: los 9 pasos fueron commitados de forma independiente.

**Historial de commits de esta sesión:**
- `e6dfe6f` Paso 1: baseline (limpieza + .gitignore)
- `272b51b` Paso 2: infraestructura frontend (common.js, sidebar, skeletons)
- `9da13e4` Paso 3: página Cámaras (CRUD + control IA)
- `531a357` Paso 4: página Estacionamiento (zonas + vehículos)
- `9ef9196` Paso 5: página Reportes + dashboard real
- `aee2128` Paso 6: página Configuración + WhatsApp
- `35eb1be` Paso 7: página Usuarios (CRUD admin)
- `eb7aca3` Paso 8: página Eventos (filtro cámara, detalles, CSV, WhatsApp)
- *(este commit)* Paso 9: documentación final

**Pendientes fuera de este plan** (de sesiones anteriores): PaddleOCR (requiere `swig`, `gcc`, `make`), `systemctl enable --now docker`, y el spam de log "Failed to read frame" al terminar videos de prueba.

---
*Actualizado: lunes, 10 de agosto de 2026*

## Sesión: PaddleOCR Real — Reconocimiento de Placas Habilitado (lunes, 10 de agosto de 2026)

### Objetivo (tarea pendiente #1)
Activar el reconocimiento de placas real con PaddleOCR. Hasta ahora el AI service usaba el fallback OpenCV y `paddleocr`/`paddlepaddle`/`torch`/`ultralytics` estaban comentados en `ai/requirements.txt` (requerían `swig`, `gcc`, `make` y sufrían incompatibilidades de numpy).

### Problemas encontrados y soluciones
1. **Falta `swig`**: no existe en BaseOS/AppStream/EPEL de CentOS Stream 10 → está en el repo **CRB**: `dnf install --enablerepo=crb swig` (SWIG 4.3.0).
2. **Stack PaddleOCR 2.x incompatible en 2026**: `paddleocr==2.7.3` sube `numpy` a 2.x (rompe `paddlepaddle==2.6.x`, que exige `numpy<2`) y arrastra decenas de dependencias viejas sin resolver limpiamente. Se migró a la línea mantenida: **`paddleocr==3.7.0` + `paddlepaddle==3.3.1`** (soporta numpy 1.26 y 2.x; `paddlex` pide `numpy>=1.24,<2.4`).
3. **La API de PaddleOCR v3 cambió**: ya no existen `use_gpu`/`use_angle_cls`/`show_log`; ahora se pasa `device` y `use_textline_orientation`, y `ocr.predict(img)` devuelve un objeto `PaddleOCRResult` (`result.json["res"]["rec_texts"/"rec_scores"]`), no la lista de líneas de v2. Se reescribió `ai/services/license_plate_recognizer.py` para la API v3 con fallback a v2.
4. **Crash de paddlepaddle 3.3.1 en CPU con oneDNN**: `NotImplementedError: ConvertPirAttribute2RuntimeAttribute ... onednn_instruction.cc:116` al inferir PP-OCRv6. Solución: `PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=False` (fijado por defecto en el código del recognizer).
5. **Modelos**: PP-OCRv6 (det + rec) y PP-LCNet_x1_0_textline_ori se descargan automáticamente al primer uso en `~/.paddlex/official_models/`.

### Cambios de código
- `ai/services/license_plate_recognizer.py`: soporte de API v3 (principal) y v2 (fallback); preprocesado de placa en 3 canales (ya no binario) para el modelo neuronal; parsing de `rec_texts`/`rec_scores`.
- `ai/requirements.txt`: habilitado el stack ML — `ultralytics==8.2.103`, `torch==2.4.0`, `paddleocr==3.7.0`, `paddlepaddle==3.3.1` (se mantiene `numpy>=1.26,<2`).
- `ai/Dockerfile`: herramientas de build (`swig`, `build-essential`, `python3-dev`), librerías de PaddleOCR (`libgomp1`, `libsm6`, `libxext6`, `libxrender1`), torch CPU desde el índice de PyTorch y se eliminó `--only-binary=:all:`.
- `ai/services/vehicle_detector.py`: si se pide `DEVICE=cuda` sin GPU → cae a `cpu` (antes caía al detector OpenCV).
- `docker-compose.yml`: `DEVICE=cpu` (este servidor no tiene GPU).

### Verificación (venv local `ai/.venv`, Python 3.12, CPU)
- `pip install "paddleocr==3.7.0" "paddlepaddle==3.3.1" "numpy>=1.26,<2"` resuelve e instala limpio (verificado también por `pip install --dry-run`).
- OCR real sobre placas sintéticas: `ABC1234` → ok (conf 1.0), `XYZ-789` → `XYZ789` (conf 0.9999), `PGR5480` → ok.
- Escenario con placa en la parte baja del vehículo (recorte por regiones) → placa detectada correctamente.
- `ai_service.get_status()` → `ocr_available: true`, `api_version: 3`.

### Documentación
- `README.md`: nota de configuración de PaddleOCR (descarga de modelos, oneDNN) y nuevo punto de troubleshooting.
- `DEVELOPMENT_SETUP_SUMMARY.md`: PaddleOCR movido de pendientes a resueltos.
- Este historial.

### Pendientes restantes
- Build completo de la imagen `ai_service` con Docker Compose (stack ML) y prueba end-to-end con una cámara real.
- `systemctl enable --now docker`.
- Spam de log "Failed to read frame" al terminar videos de prueba (menor).

---
*Actualizado: lunes, 10 de agosto de 2026*


---

## Sesión: lunes, 10 de agosto de 2026 (continuación) — Stack ML en Docker + fixes de robustez

### Resumen
Se completaron las tareas pendientes de la sesión anterior: se habilitó Docker, se construyó la imagen `ai_service` con el stack ML completo (YOLOv8 + PaddleOCR), se verificó la detección real end-to-end dentro del contenedor y se corrigieron varios bugs que impedían la operación continua.

### Problemas resueltos
1. **Docker apagado y deshabilitado**: `systemctl enable --now docker` → queda activo y arranca solo tras reinicios.
2. **`torchvision::nms does not exist` en el contenedor**: torch 2.4.0 se instalaba desde el índice CPU, pero `torchvision==0.19.0` se resolvía desde PyPI (wheel CUDA). Al correr YOLO, NMS fallaba. Fix: instalar `torch==2.4.0` + `torchvision==0.19.0` desde `--index-url https://download.pytorch.org/whl/cpu` en el `Dockerfile`.
3. **Contexto de build gigante**: no existía `ai/.dockerignore`; el `.venv` de 1.3 GB se subía a cada build. Se creó `.dockerignore` (excluye `.venv/`, caches, modelos, logs, videos de prueba).
4. **Backend caído mataba la detección**: `backend_client.login()` lanzaba excepción de red que se propagaba por `post_vehicle`/`post_event` y el `try/except` de `_process_frame_for_vehicles` descartaba el frame completo (detección perdida en silencio). Fix en `app/backend_client.py`: `login()` devuelve `None` en fallo y `_request` nunca lanza; además `_report_if_due` envuelve los envíos al backend en `try/except`.
5. **`UniqueViolation` al reportar vehículos**: tras reiniciar el AI service, los track IDs se reusan (T-1, T-2...) y `POST /api/vehicles/` fallaba con `detected_vehicles_vehicle_id_key`. Fix en `backend/routers/vehicles.py`: upsert por `vehicle_id` + `camera_id`, gestionando `last_seen`, `park_start_time` y `total_park_time`.
6. **Handler global de excepciones roto** (`backend/main.py`): devolvía un `dict` en vez de `JSONResponse` → `TypeError: 'dict' object is not callable` y respuestas 500 vacías. Fix: retorna `JSONResponse(status_code=500, content=...)`.
7. **Umbral de estacionamiento ignorado**: los singletons `parking_detector`, `object_tracker` y `vehicle_detector` se instanciaban con valores por defecto ignorando `settings` (el threshold de parking quedaba en 300s aunque se configurara otro). Fix: se instancian con `settings.PARKING_TIME_THRESHOLD`, `settings.CONFIDENCE_THRESHOLD` y `settings.DEVICE`.
8. **Spam "Failed to read frame"**: al terminar un archivo de video, `cap.read()` fallaba para siempre y el hilo logueaba cada 0.1s. Fix en `services/ai_service.py`: al detectar EOF en fuente tipo archivo el hilo termina con estado `stopped: video ended` y un solo log; en streams RTSP se reintenta con backoff de 0.5s y log acotado.

### Verificación end-to-end (Docker Compose, CPU)
- Stack completo arriba: `db`, `redis`, `backend`, `ai_service`, `frontend` — todos `healthy`.
- Imagen `ai_service`: YOLOv8 cargado (`/app/models/yolov8n.pt` incluido en el repo) + PaddleOCR disponible; `yolo_model_loaded` y OCR verificados en el contenedor.
- OCR real en el contenedor: `ABC1234` y `PGR5480` → conf ≈ 0.9999.
- Pipeline completo en el contenedor (backend alcanzable): detección (bus + car en frame 225 del video de prueba) → ByteTrack (confirmación a los 3 hits) → ParkingDetector (`is_parked=true` con `PARKING_TIME_THRESHOLD=5`) → upsert en `detected_vehicles` → evento `vehicle_parked` en `events`.
- Fin de video: un solo log "End of video reached" y el hilo termina (0 mensajes "Failed to read frame" tras la corrección).
- Nota: el video de tráfico de prueba (`ai/test_video.mp4`, descartado por `.gitignore`) no produce eventos de estacionamiento por sí solo porque los vehículos pasan de largo (tracks de <3 hits); es el comportamiento esperado del tracker.

### Cambios de código
- `ai/Dockerfile`: torchvision CPU desde el índice de PyTorch.
- `ai/.dockerignore`: nuevo (excluye `.venv/`, caches, modelos, logs).
- `ai/models/yolov8n.pt`: modelo YOLOv8n incluido para que compose funcione sin descargas.
- `ai/app/backend_client.py`: `login()` no lanza; `_request` tolerante a fallos.
- `ai/services/ai_service.py`: envíos al backend a prueba de fallos + manejo de EOF/backoff de lectura.
- `ai/services/parking_detector.py`, `object_tracker.py`, `vehicle_detector.py`: singletons con `settings`.
- `backend/main.py`: handler global devuelve `JSONResponse`.
- `backend/routers/vehicles.py`: upsert de vehículos por `vehicle_id`+`camera_id`.

### Pendientes restantes
- Prueba end-to-end con cámara RTSP real (Hikvision) y placas legibles.
- Ajustar `PARKING_TIME_THRESHOLD` a los tiempos reales de estacionamiento.
- Evaluar `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` para acelerar el primer arranque.

---

## Sesión: lunes, 11 de agosto de 2026 — Puerto 4001 y documentación de WhatsApp

### Puerto del frontend cambiado a 4001
- `docker-compose.yml`: mapeo del frontend de `"80:80"` a `"4001:80"`. El puerto **interno del contenedor sigue siendo 80**; solo cambia el expuesto en el host.
- Motivo: evitar colisiones con otros servicios (Apache/nginx) que ya usen el puerto 80 al desplegar el proyecto en otro servidor. Si el destino ya ocupa el 4001, se cambia el lado host de una línea.
- Verificado: `http://localhost:4001/` responde 200 y el puerto 80 queda libre.
- Contenedor `frontend` recreado con `docker compose up -d frontend` (sin afectar al resto del stack).
- Docs: `DEVELOPMENT_SETUP_SUMMARY.md` actualizado (acceso en `http://localhost:4001`).

### Documentación de WhatsApp/Evolution API
- Estado real: los envíos son **manuales** — desde un evento del Historial (botón WhatsApp) y desde Configuración (mensaje de prueba). No hay aún auto-envío al detectar estacionamiento (`whatsapp_enabled`/`default_whatsapp_numbers` existen en BD pero nadie los lee para notificar automáticamente).
- La configuración (api_url, api_key, instance_name) vive en un singleton **en memoria** (`backend/routers/whatsapp.py:50`), no en la BD → se pierde al reiniciar el backend.
- Los envíos se encolan con `BackgroundTasks`; el número se normaliza (solo dígitos, +1 implícito para números US de 10 dígitos) en `backend/services/whatsapp_service.py`.
- README: nueva sección "Notificaciones WhatsApp" con arquitectura (Evolution API), cómo levantar una instancia de prueba con Docker, pasos de configuración desde la UI, prueba rápida y las limitaciones actuales (config en memoria, sin auto-envío).

### Commits
- (pendiente de commitear/pushear en esta sesión)

---

## Sesión: lunes, 11 de agosto de 2026 — WhatsApp corregido para Evolution API v2 (prueba real lista)

### Qué descubrimos (pregunta del usuario: "¿de dónde sale la clave atomikos?")
- La imagen que mencioné antes (`atomikos/evolution-api`) era un error de memoria: la imagen oficial es **`atendai/evolution-api`**.
- La **API Key no se "saca" de ningún lado**: la genera el propio usuario (`openssl rand -hex 32`), se le pasa a Evolution API como `AUTHENTICATION_API_KEY` al arrancar el contenedor, y es la misma que se pega en la Configuración del sistema. Evolution valida esa clave en el header `apikey` de cada petición.
- Flujo real completo: levantar Evolution → crear instancia (`POST /instance/create` con `qrcode:true`) → escanear el QR con WhatsApp (Ajustes > Dispositivos vinculados) → verificar `GET /instance/connectionState/{instancia}` = `open` → configurar los 3 datos en el sistema → enviar.

### Bug encontrado: el backend hablaba API v1, Evolution actual es v2
- `backend/services/whatsapp_service.py` usaba endpoints de la **v1**:
  - envío: `POST {api_url}/instance/{instancia}/sendMessage` con body `{number, textMessage:{text}}`
  - prueba: `GET {api_url}/instance/{instancia}/fetchInstances` (endpoint inexistente)
- Con `atendai/evolution-api` 2.x ambos devolvían 404 → la prueba real habría fallado.
- **Corregido a v2** (verificado contra el quickstart oficial):
  - envío: `POST {api_url}/message/sendText/{instancia}` con body `{number, text}`
  - prueba: `GET {api_url}/instance/connectionState/{instancia}`
- Se eliminó `self.base_url` (quedaba sin uso). `py_compile` OK; backend reiniciado y `/health` OK (el código va por bind mount `./backend:/app`).
- **Alcance desde el contenedor**: las llamadas a Evolution las hace el contenedor `backend`, no el navegador. Se añadió `extra_hosts: host.docker.internal:host-gateway` al servicio backend para que alcance Evolution cuando corre en el mismo host (`http://host.docker.internal:8080`). Verificado: `getent hosts host.docker.internal` → `172.17.0.1`.
- README: imagen corregida a `atendai/evolution-api`, pasos reales con QR, verificación de estado y uso de `host.docker.internal`.

### Commits
- (pendiente de commitear/pushear en esta sesión)

*Actualizado: lunes, 11 de agosto de 2026*
