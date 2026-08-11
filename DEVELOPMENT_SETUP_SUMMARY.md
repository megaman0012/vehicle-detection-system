# Resumen de la Configuración de Desarrollo

## ✅ COMPLETADO
- Backend (FastAPI): Dependencias instaladas y verificadas
- Servicio de IA: Dependencias principales instaladas (opencv, ultralytics) + **PaddleOCR 3.x habilitado y verificado**
- Frontend: Servidor HTTP funcionando en puerto 8080
- **Frontend conectado a la API real** (páginas Cámaras, Estacionamiento, Eventos, Reportes, Configuración y Usuarios): ya no hay funciones mock, todo el CRUD e integraciones se ejecutan contra los endpoints del backend y del servicio de IA a través del proxy nginx (`/api/*` y `/ai/*`)

## 🛠️ MEJORAS REALIZADAS

### Backend (FastAPI)
- Mejorado el endpoint de salud (/health/detailed) para incluir verificaciones de conectividad con base de datos y Redis
- Agregado endpoints de readiness (/ready) y liveness (/live) para entornos de orquestación
- Verificado que el módulo de salud se importa correctamente
- Fix de deadlock en el AI service: `threading.Lock` → `RLock` y `stop_camera_processing` no bloquea el event loop (`put_nowait` + stop events por cámara)
- Fix del healthcheck de Redis: `redis.from_string` → `redis.Redis.from_url`

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
- `systemctl enable --now docker` para que Docker arranque solo tras un reinicio.
- Spam de log "Failed to read frame" al terminar un video de prueba (menor).
- Verificación del build completo de la imagen `ai_service` con Docker (stack ML habilitado).

## ✅ PROBLEMAS RESUELTOS
- **PaddleOCR 3.x habilitado y verificado**: reconocimiento de placas real con `paddleocr==3.7.0` + `paddlepaddle==3.3.1` (CPU). Se reescribió `ai/services/license_plate_recognizer.py` para la API v3 (con fallback a v2), se desactiva oneDNN/MKLDNN en CPU (`PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=False`) para evitar un crash conocido de paddlepaddle, y se fijó `numpy>=1.26,<2` compatible con todo el stack (torch/ultralytics/paddle). Los modelos PP-OCRv6 se descargan automáticamente en el primer uso.
- **Docker**: Resuelto instalando `kernel-modules-extra` correspondiente al kernel en ejecución. En CentOS Stream 10 con kernel 6.12.x, el módulo `xt_addrtype.ko` necesario para que Docker cree correctamente sus reglas de NAT se encuentra en este paquete. Solución: `sudo dnf install kernel-modules-extra-$(uname -r)`
- **AI service unhealthy/deadlock**: hilos zombie y event loop congelado corregidos; todos los contenedores quedaron `healthy` con detección end-to-end funcionando
- **Healthcheck de Redis**: reportaba `disconnected` sin estarlo; corregido el constructor de la conexión

## 🚀 PRÓXIMOS PASOS
1. Build completo de la imagen `ai_service` con Docker Compose (stack ML habilitado: YOLOv8 + PaddleOCR) y prueba end-to-end con una cámara real
2. `systemctl enable --now docker` para que Docker arranque solo
3. Ajustar `PARKING_TIME_THRESHOLD` (default 300s vs 30 min del README) si aplica

## 📍 ACCESO
- Frontend: http://localhost:8080
- Backend: Disponible para desarrollo en /backend
- IA: Disponible para desarrollo en /ai

*Actualizado: lunes, 10 de agosto de 2026*
