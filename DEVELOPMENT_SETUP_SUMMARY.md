# Resumen de la Configuración de Desarrollo

## ✅ COMPLETADO
- Backend (FastAPI): Dependencias instaladas y verificadas
- Servicio de IA: Dependencias principales instaladas (opencv, ultralytics) + **PaddleOCR 3.x habilitado y verificado**
- **Docker habilitado y arrancando solo**: `systemctl enable --now docker`
- **Imagen `ai_service` construida con el stack ML completo** (torch CPU + torchvision CPU + YOLOv8 + PaddleOCR) y **prueba end-to-end verificada dentro del contenedor** (detección → tracking → estacionamiento → reporte al backend)
- Frontend: Servidor HTTP funcionando en puerto 8080
- **Frontend conectado a la API real** (páginas Cámaras, Estacionamiento, Eventos, Reportes, Configuración y Usuarios): ya no hay funciones mock, todo el CRUD e integraciones se ejecutan contra los endpoints del backend y del servicio de IA a través del proxy nginx (`/api/*` y `/ai/*`)

## 🛠️ MEJORAS REALIZADAS

### Backend (FastAPI)
- Mejorado el endpoint de salud (/health/detailed) para incluir verificaciones de conectividad con base de datos y Redis
- Agregado endpoints de readiness (/ready) y liveness (/live) para entornos de orquestación
- Verificado que el módulo de salud se importa correctamente
- Fix de deadlock en el AI service: `threading.Lock` → `RLock` y `stop_camera_processing` no bloquea el event loop (`put_nowait` + stop events por cámara)
- Fix del healthcheck de Redis: `redis.from_string` → `redis.Redis.from_url`
- **Upsert de vehículos** (`routers/vehicles.py`): al re-registrar un `vehicle_id` ya existente (típico tras reiniciar el AI service, que reusa track IDs T-1, T-2...) ahora se actualiza el registro en vez de fallar con `UniqueViolation`; gestiona `last_seen`, `park_start_time` y `total_park_time`
- **Fix handler global de excepciones** (`main.py`): devolvía un `dict` en vez de `JSONResponse`, provocando `TypeError: 'dict' object is not callable` y respuestas 500 vacías

### Servicio de IA
- Mejorado el endpoint de salud (/health/detailed) para incluir verificación de conectividad con el backend
- Agregado verificación de disponibilidad de GPU y uso de memoria
- Agregado endpoints de readiness (/ready) y liveness (/live) para entornos de orquestación
- Verificado que el módulo de salud se importa correctamente
- **Stack ML habilitado**: `ai/requirements.txt` con `ultralytics==8.2.103`, `torch==2.4.0`, `paddleocr==3.7.0` y `paddlepaddle==3.3.1`
- **`license_plate_recognizer.py` reescrito para PaddleOCR 3.x** (con fallback 2.x): usa `ocr.predict()` y los campos `rec_texts`/`rec_scores`; dispositivo gestionado por `device`; preprocesado de placa en 3 canales
- **Fix oneDNN en CPU**: `PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=False` (evita crash `ConvertPirAttribute2RuntimeAttribute` de paddlepaddle 3.3.1)
- **Fix detección en máquinas sin GPU**: `vehicle_detector.py` cae de `cuda` a `cpu` si no hay CUDA disponible
- **`ai/Dockerfile`**: herramientas de build (`swig`, `build-essential`, `python3-dev`), librerías de PaddleOCR (`libgomp1`, `libsm6`, `libxext6`, `libxrender1`) y torch CPU desde el índice de PyTorch
- **Fix torch/torchvision CPU** (`ai/Dockerfile`): `torchvision==0.19.0` ahora se instala desde el mismo índice CPU de PyTorch. Antes se resolvía el wheel CUDA de PyPI y YOLO fallaba con `operator torchvision::nms does not exist`
- **`ai/.dockerignore`**: excluye `.venv` (1.3 GB), caches y modelos del contexto de build (antes se enviaban todos a cada build)
- **Robustez ante fallos de red** (`app/backend_client.py`): `login()` ya no lanza excepción; una caída del backend no mata el procesamiento del frame (antes la excepción se propagaba y descartaba la detección completa)
- **Fin de video limpio** (`services/ai_service.py`): al terminar un archivo de video el hilo finaliza con estado `stopped: video ended` y un solo log, en lugar de loguear "Failed to read frame" cada 0.1s indefinidamente. En streams RTSP se reintenta con backoff (0.5s) y log acotado
- **Singletons alineados con `settings`**: `parking_detector`, `object_tracker` y `vehicle_detector` ahora se instancian con los valores de configuración (`PARKING_TIME_THRESHOLD`, `CONFIDENCE_THRESHOLD`, `DEVICE`). Antes el threshold de estacionamiento quedaba fijo en 300s ignorando la configuración
- **Modelo YOLOv8 incluido**: `ai/models/yolov8n.pt` (auto-descargado desde ultralytics) para que el compose funcione sin descargas

### Frontend (páginas completas)
- `js/common.js`: utilidades compartidas (auth guard, sidebar, notificaciones, escape, formatos de fecha/hora)
- `js/api.js`: cliente API completo (auth, cámaras, vehículos, eventos, zonas, reportes, config, whatsapp, AI service)
- **Cámaras** (`pages/cameras.html`): CRUD real + control del AI service (start/stop por cámara) y modal de estado IA
- **Estacionamiento** (`pages/parking.html`): vehículos estacionados en vivo + CRUD de zonas con dibujo de polígono sobre canvas persistido en la API
- **Reportes** (`pages/reports.html`): estadísticas reales desde `/api/reports/stats` y descarga de PDF/Excel (binario autenticado)
- **Configuración** (`pages/settings.html`): CRUD de configuración (valores JSON) + WhatsApp (estado, configuración, prueba y envío)
- **Usuarios** (`pages/users.html`): CRUD de usuarios con roles (admin/operator/user)
- **Eventos** (`pages/events.html`): filtro dinámico por cámara, exportación CSV, modal de detalles y envío por WhatsApp
- Dashboard (`index.html`): estadísticas reales calculadas desde los vehículos detectados (por tipo y por duración)

## ⚠️ PROBLEMAS PENDIENTES
- Probar el despliegue con una **cámara RTSP real** (Hikvision) en vez de archivo de video
- Ajustar `PARKING_TIME_THRESHOLD` (default 300s vs 30 min del README) si aplica a las zonas de estacionamiento reales

## ✅ PROBLEMAS RESUELTOS
- **PaddleOCR 3.x habilitado y verificado**: reconocimiento de placas real con `paddleocr==3.7.0` + `paddlepaddle==3.3.1` (CPU). Se reescribió `ai/services/license_plate_recognizer.py` para la API v3 (con fallback a v2), se desactiva oneDNN/MKLDNN en CPU (`PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=False`) para evitar un crash conocido de paddlepaddle, y se fijó `numpy>=1.26,<2` compatible con todo el stack (torch/ultralytics/paddle). Los modelos PP-OCRv6 se descargan automáticamente en el primer uso.
- **Docker**: Resuelto instalando `kernel-modules-extra` correspondiente al kernel en ejecución. En CentOS Stream 10 con kernel 6.12.x, el módulo `xt_addrtype.ko` necesario para que Docker cree correctamente sus reglas de NAT se encuentra en este paquete. Solución: `sudo dnf install kernel-modules-extra-$(uname -r)`
- **AI service unhealthy/deadlock**: hilos zombie y event loop congelado corregidos; todos los contenedores quedaron `healthy` con detección end-to-end funcionando
- **Healthcheck de Redis**: reportaba `disconnected` sin estarlo; corregido el constructor de la conexión

## 🚀 PRÓXIMOS PASOS
1. Prueba end-to-end con una cámara RTSP real (Hikvision) y placas legibles
2. Verificar el reconocimiento de placas en condiciones reales (iluminación, ángulo) y ajustar `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` si el primer arranque tarda demasiado
3. Ajustar `PARKING_TIME_THRESHOLD` (default 300s vs 30 min del README) si aplica

## 📍 ACCESO
- Frontend: http://localhost:8080
- Backend: Disponible para desarrollo en /backend
- IA: Disponible para desarrollo en /ai

*Actualizado: lunes, 10 de agosto de 2026*
