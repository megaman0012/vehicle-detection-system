# Vehicle Detection System

## Sistema Inteligente de Detección de Vehículos Estacionados con IA

Un sistema completo para la detección inteligente de vehículos estacionados utilizando cámaras Hikvision, reconocimiento de placas y notificaciones por WhatsApp.

### Características Principales

- 🎯 **Detección de Vehículos**: Utiliza YOLOv8 para detección precisa de vehículos
- 🔄 **Seguimiento de Objetos**: Implementa ByteTrack para asignación consistente de IDs
- 🚗 **Detección de Estacionamiento**: Identifica vehículos estacionados por tiempo excesivo
- 🔖 **Reconocimiento de Placas**: Utiliza PaddleOCR para lectura de placas de vehículos
- 📱 **Notificaciones por WhatsApp**: Envía alertas en tiempo real mediante Evolution API
- 📊 **Panel Web Interfaz**: Dashboard moderno con Bootstrap 5 para monitoreo y control
- 📈 **Historial de Eventos**: Búsqueda y filtrado avanzado de eventos detectados
- 📋 **Generación de Reportes**: Reportes en PDF y Excel para análisis histórico
- 🔒 **Seguridad Robusta**: Autenticación JWT, roles de usuario, auditoría y rate limiting
- 🐳 **Despliegue con Docker**: Arquitectura de microservicios completamente contenedorizada
- ⚡ **Alto Rendimiento**: Optimizado para GPU NVIDIA con fallback a CPU

### Arquitectura del Sistema

El sistema sigue una arquitectura de microservicios con los siguientes componentes:

1. **Backend API** (FastAPI): REST API y WebSockets para comunicación
2. **Servicio de IA**: Procesamiento de video, detección y reconocimiento
3. **Frontend**: Interfaz web responsive con Bootstrap 5
4. **Base de Datos**: PostgreSQL para almacenamiento persistente
5. **Redis**: Caching y gestión de colas
6. **Nginx**: Proxy inverso y terminación SSL (opcional)

### Requisitos del Sistema

- **Sistema Operativo**: CentOS 10 o compatible
- **Hardware**: 
  - CPU: 4+ núcleos recomendados
  - RAM: 8GB+ recomendados
  - GPU: NVIDIA con CUDA 12.1+ (opcional, pero recomendado para rendimiento)
  - Almacenamiento: 20GB+ disponible
- **Software**:
  - Docker 20.10+
  - Docker Compose 2.0+
  - NVIDIA Driver 525+ (para uso de GPU)
  - CUDA Toolkit 12.1+ (para uso de GPU)

### Instalación

#### Opción 1: Script de Instalación Automática (Recomendado)

```bash
# Descargar el script de instalación
wget https://raw.githubusercontent.com/your-repo/vehicle-detection-system/main/scripts/install.sh

# Hacerlo ejecutable
chmod +x install.sh

# Ejecutar como root
sudo ./install.sh
```

#### Opción 2: Instalación Manual

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/your-repo/vehicle-detection-system.git
   cd vehicle-detection-system
   ```

2. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con sus configuraciones
   ```

3. **Construir y iniciar los servicios**:
   ```bash
   docker-compose up -d --build
   ```

4. **Esperar a que los servicios se inicien** (aproximadamente 2-3 minutos)

5. **Acceder al sistema**:
   - URL: http://your-server-ip
   - Usuario: admin@vehicle-detection.com
   - Contraseña: admin123 (cambiar inmediatamente después del primer inicio)

### Configuración

#### Variables de Entorno (.env)

El archivo `.env` contiene todas las configuraciones necesarias:

```env
# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=False

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/vehicle_detection

# Redis Configuration
REDIS_URL=redis://redis:6379

# Security Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Service Configuration
AI_SERVICE_HOST=0.0.0.0
AI_SERVICE_PORT=8001
BACKEND_URL=http://backend:8000
MODEL_PATH=/app/models
DEVICE=cuda  # Cambiar a 'cpu' si no hay GPU disponible

# YOLO Model Configuration
YOLO_MODEL=yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.5
YOLO_IOU_THRESHOLD=0.45

# ByteTrack Configuration
BYTETRACK_THRESHOLD=0.5
BYTETRACK_MATCH_THRESHOLD=0.8

# PaddleOCR Configuration
OCR_LANG=en
OCR_USE_ANGLE_CLS=true
OCR_USE_GPU=true

# Parking Detection Configuration
PARKING_TIME_THRESHOLD_MINUTES=30
MOTION_THRESHOLD_PIXELS=50

# WhatsApp Configuration (Evolution API)
WHATSAPP_API_URL=http://evolution-api:8080
WHATSAPP_API_KEY=your-evolution-api-key
WHATSAPP_INSTANCE_NAME=vehicle-detection
WHATSAPP_ENABLED=false

# Report Generation Configuration
REPORTS_DIR=/app/reports
MAX_REPORT_EVENTS=10000

# File Upload Configuration
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760  # 10MB

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_DIR=/app/logs

# CORS Configuration
BACKEND_CORS_ORIGINS=["http://localhost","http://localhost:3000","http://localhost:80"]

# Email Configuration (for notifications)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=vehicle-detection@example.com
EMAILS_FROM_NAME=Vehicle Detection System
```

#### Configuración de Cámaras Hikvision

Para configurar sus cámaras Hikvision:

1. Acceder al panel de administración → Cámaras
2. Hacer clic en "Añadir Nueva Cámara"
3. Completar los campos:
   - Nombre: Nombre descriptivo de la cámara
   - URL RTSP: `rtsp://[usuario]:[contraseña]@[ip]:[puerto]/Streaming/Channels/101`
   - Usuario: Usuario de la cámara Hikvision
   - Contraseña: Contraseña de la cámara Hikvision
   - Ubicación: Descripción de la ubicación física
   - FPS: Fotogramas por segundo (recomendado: 25-30)
   - Resolución: Ancho y alto de la transmisión

#### Configuración de Zonas de Estacionamiento

Para definir zonas de estacionamiento:

1. Acceder al panel → Estacionamiento
2. En la tabla de zonas, hacer clic en "Dibujar" o "Nueva Zona"
3. Seleccionar la cámara sobre la que se dibuja el área
4. Hacer clic en el canvas para marcar los vértices del polígono que representa el área de estacionamiento
5. Usar "Deshacer"/"Limpiar" si es necesario y luego "Guardar Zona" (los puntos se persisten en `/api/zones/`)
6. Repetir para todas las zonas necesarias

### Uso del Sistema

#### Panel Principal

El dashboard muestra:
- Estado de todas las cámaras (en línea/fuera de línea)
- Estadísticas de detección en tiempo real
- Número de vehículos actualmente estacionados
- Alertas recientes
- Gráficos de tendencias

Las estadísticas del dashboard se calculan desde los datos reales de vehículos (por tipo y por duración de estacionamiento), no son valores fijos.

#### Cámaras

Página de administración de cámaras (CRUD completo contra `/api/cameras/`):
- Crear, editar y eliminar cámaras (nombre, ubicación, URL RTSP, credenciales, FPS, resolución, activa)
- Control del servicio de IA por cámara: iniciar/detener el procesamiento (`/ai/api/detection/start` / `stop`)
- Modal de "Estado IA" y refresco automático del estado de procesamiento

#### Estacionamiento

- **Vehículos estacionados**: lista en vivo de los vehículos detectados y estacionados (ID de seguimiento, tipo, placa, cámara, primera/última vista) con refresco automático
- **Zonas de estacionamiento**: CRUD de zonas con dibujo de polígono sobre canvas, persistido en la API

#### Historial de Eventos

Accesible desde el menú lateral, permite:
- Filtrar por tipo de evento (estacionamiento, placa detectada, cámara desconectada, etc.)
- Filtrar por rango de fechas
- Filtrar por cámara específica (el select se llena dinámicamente desde la API)
- Búsqueda de texto en descripciones y placas
- Exportar resultados a CSV
- Ver detalles de cada evento (fecha, tipo, descripción, cámara, placa, metadatos)
- Enviar notificaciones por WhatsApp para eventos específicos

#### Gestión de Reportes

Permite generar:
- Reportes de eventos de estacionamiento (PDF/Excel) en formato diario, semanal o mensual
- Las descargas son binarias autenticadas (blob) y el archivo se nombra según `Content-Disposition`
- El dashboard de estadísticas muestra los datos reales desde `/api/reports/stats`

#### Configuración del Sistema

Incluye:
- CRUD de configuración del sistema (clave/valor JSON: números, strings, booleanos y arrays) con botón "Inicializar Defaults"
- Configuración de WhatsApp/Evolution API: estado, URL de Evolution, API Key, instancia, prueba de conexión y envío de mensajes de prueba

#### Usuarios

- Gestión de usuarios y roles (admin/operator/user) contra `/api/users/`
- Al editar un usuario no se permite cambiar la contraseña (el backend no la soporta por PUT); la creación de usuarios solicita contraseña

### API REST

El sistema proporciona una API REST completa documentada en:
- Swagger UI: http://your-server-ip/docs
- ReDoc: http://your-server-ip/redoc

Los principales endpoints incluyen:
- `/api/auth`: Autenticación (login, registro, refresh token)
- `/api/users`: Gestión de usuarios
- `/api/cameras`: Gestión de cámaras y conexiones RTSP
- `/api/vehicles`: Gestión de vehículos detectados
- `/api/events`: Historial y filtrado de eventos
- `/api/reports`: Generación de reportes
- `/api/config`: Configuración del sistema
- `/api/whatsapp`: Envío de notificaciones por WhatsApp
- `/api/system`: Información y control del sistema
- `/api/ws`: WebSockets para actualizaciones en tiempo real

### Mantenimiento

#### Actualización del Sistema

```bash
# Descargar el script de actualización
wget https://raw.githubusercontent.com/your-repo/vehicle-detection-system/main/scripts/update.sh

# Hacerlo ejecutable
chmod +x update.sh

# Ejecutar como root
sudo ./update.sh
```

#### Copias de Seguridad

```bash
# Descargar el script de respaldo
wget https://raw.githubusercontent.com/your-repo/vehicle-detection-system/main/scripts/backup.sh

# Hacerlo ejecutable
chmod +x backup.sh

# Ejecutar como root
sudo ./backup.sh
```

#### Restauración desde Copia de Seguridad

```bash
# Descargar el script de restauración
wget https://raw.githubusercontent.com/your-repo/vehicle-detection-system/main/scripts/restore.sh

# Hacerlo ejecutable
chmod +x restore.sh

# Ejecutar como root (especificar el archivo de backup)
sudo ./restore.sh /path/to/backup.tar.gz
```

#### Logs y Monitoreo

- Ver logs en tiempo real: `docker-compose logs -f`
- Ver logs de un servicio específico: `docker-compose logs -f backend`
- Monitorear uso de recursos: `docker stats`
- Ver estado de los servicios: `docker-compose ps`

### Escalabilidad y Rendimiento

#### Optimización para GPU

El sistema está optimizado para aprovechar GPUs NVIDIA cuando están disponibles:
- El servicio de IA detecta automáticamente la disponibilidad de GPU
- YOLOv8 y PaddleOCR se ejecutan en GPU para máximo rendimiento
- Se puede forzar el uso de CPU estableciendo `DEVICE=cpu` en el archivo .env

#### Escalado Horizontal

Para manejar múltiples cámaras de alta resolución:
- Aumentar el número de workers en el servicio de IA
- Distribuir las cámaras entre múltiples instancias del servicio de IA
- Utilizar un balanceador de carga frente a las instancias de IA
- Aumentar los recursos de la base de datos y Redis según sea necesario

### Seguridad

#### Autenticación y Autorización

- Autenticación basada en JWT con tokens de acceso y refresh
- Contraseñas hasheadas utilizando bcrypt
- Roles de usuario: admin, operador, usuario
- Control de acceso basado en roles (RBAC)
- Protección contra fuerza bruta mediante rate limiting

#### Protección de Datos

- Comunicación encriptada entre componentes (opcional con TLS)
- Registro de auditoría para todas las acciones importantes
- Validación y sanitización de todas las entradas
- Protección contra inyección SQL mediante ORM
- Headers de seguridad HTTP implementados

#### Privacidad

- Los datos de video no se almacenan permanentemente, solo se procesan en tiempo real
- Las placas de vehículos se almacenan solo cuando es necesario para el caso de uso
- Posibilidad de anonimizar o eliminar datos según requerimientos legales
- Cumplimiento con regulaciones de protección de datos (GDPR, etc.)

### Solución de Problemas

#### Problemas Comunes

1. **Las cámaras no se conectan**:
   - Verificar la URL RTSP, usuario y contraseña
   - Probar la conexión con VLC o ffmpeg: `ffmpeg -i "rtsp://user:pass@ip:port/channel" -t 5 test.jpg`
   - Asegurarse de que la cámara permita conexiones remotas
   - Verificar reglas de firewall y NAT

2. **Rendimiento lento o alto uso de CPU**:
   - Verificar si se está utilizando GPU (debería mostrar "GPU available: True" en los logs)
   - Reducir la resolución o FPS de las cámaras si es necesario
   - Ajustar los umbrales de detección para reducir falsos positivos
   - Considerar agregar más recursos o distribuir la carga

3. **Problemas con WhatsApp/Evolution API**:
   - Verificar que la API de Evolution esté accesible desde el contenedor
   - Probar la conexión desde el endpoint de prueba en la configuración de WhatsApp
   - Verificar que el número de teléfono tenga el formato correcto (con código de país)
   - Revisar los logs del servicio de WhatsApp para errores específicos

4. **Problemas de base de datos**:
   - Verificar que el contenedor de PostgreSQL esté en ejecución
   - Revisar los logs de la base de datos para errores
   - Asegurarse de que haya suficiente espacio en disco
   - Considerar aumentar los recursos asignados a PostgreSQL

#### Logs de Depuración

Para habilitar logs más detallados:
```bash
# En el archivo .env, cambiar:
LOG_LEVEL=DEBUG

# Luego reiniciar los servicios:
docker-compose restart
```

Los logs se pueden ver con:
```bash
docker-compose logs -f [service-name]
```

### Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](LICENSE) para detalles.

### Contribuir

Las contribuciones son bienvenidas. Por favor, lea nuestras [pautas de contribución](CONTRIBUTING.md) para detalles sobre nuestro código de conducta y el proceso para enviar pull requests.

### Soporte

Para soporte técnico, por favor:
- Revise la documentación y los archivos de troubleshooting
- Consulte los issues existentes en el repositorio
- Abra un nuevo issue proporcionando detalles específicos del problema
- Para soporte comercial, contacte a [soporte@ejemplo.com]

### Agradecimientos

- [YOLOv8](https://github.com/ultralytics/ultralytics) por la excelente detección de objetos
- [ByteTrack](https://github.com/ifzhang/ByteTrack) por el seguimiento de objetos de alto rendimiento
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) por el reconocimiento de placas multilingüe
- [FastAPI](https://fastapi.tiangolo.com/) por el framework web moderno y rápido
- [PostgreSQL](https://www.postgresql.org/) por la base de datos confiable
- [Redis](https://redis.io/) por el caching y gestión de colas eficiente
- [Bootstrap 5](https://getbootstrap.com/) por el framework de interfaz responsive
- [Evolution API](https://github.com/EvolutionAPI/evolution) por la integración con WhatsApp

---

**Nota**: Este sistema está diseñado para cumplir con las regulaciones locales de privacidad y protección de datos. Es responsabilidad del operador asegurarse de que su uso cumpla con todas las leyes aplicables en su jurisdicción.