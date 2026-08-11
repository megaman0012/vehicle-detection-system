// Main JavaScript for Vehicle Detection System Frontend

document.addEventListener('DOMContentLoaded', function() {
    // Auth guard: require a valid session before rendering
    if (!Common.requireAuth()) {
        return;
    }

    // Sidebar, logout, user name and active page
    Common.initSidebar('dashboard');

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Load real data
    loadDashboard();

    // Set up periodic updates
    setInterval(updateDashboardStats, 10000); // Update stats every 10 seconds
    setInterval(updateCameraFeeds, 5000);     // Update camera feeds every 5 seconds
});

// Zone management functions (kept from original implementation)
function initializeZoneManagement() {
    const drawZoneButtons = document.querySelectorAll('[data-action="draw-zone"]');
    drawZoneButtons.forEach(button => {
        button.addEventListener('click', function() {
            const cameraId = this.getAttribute('data-camera-id');
            startZoneDrawing(cameraId);
        });
    });

    const editZoneButtons = document.querySelectorAll('[data-action="edit-zone"]');
    editZoneButtons.forEach(button => {
        button.addEventListener('click', function() {
            const zoneId = this.getAttribute('data-zone-id');
            editZone(zoneId);
        });
    });

    const deleteZoneButtons = document.querySelectorAll('[data-action="delete-zone"]');
    deleteZoneButtons.forEach(button => {
        button.addEventListener('click', function() {
            const zoneId = this.getAttribute('data-zone-id');
            deleteZone(zoneId);
        });
    });
}

function startZoneDrawing(cameraId) {
    console.log(`Starting zone drawing for camera ${cameraId}`);
    showZoneDrawingModal(cameraId);
}

function showZoneDrawingModal(cameraId) {
    const modalHtml = `
        <div class="modal fade" id="zoneDrawingModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-fullscreen">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Dibujar Zona de Estacionamiento</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="camera-feed-container">
                            <div id="zoneDrawingFeed" class="camera-feed bg-dark min-vh-75 d-flex align-items-center justify-content-center text-white position-relative">
                                <i class="fas fa-video-slash fa-3x opacity-25"></i>
                                <div>Cámara ${cameraId} - Dibuje la zona de estacionamiento</div>
                                <canvas id="zoneDrawingCanvas" class="position-absolute top-0 start-0 w-100 h-100"></canvas>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="button" class="btn btn-success me-2" id="saveZoneBtn">Guardar Zona</button>
                            <button type="button" class="btn btn-secondary" id="clearZoneBtn">Limpiar Dibujo</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);

    const zoneDrawingModal = new bootstrap.Modal(document.getElementById('zoneDrawingModal'));
    zoneDrawingModal.show();

    setupZoneDrawing(cameraId);

    const modalElement = document.getElementById('zoneDrawingModal');
    modalElement.addEventListener('hidden.bs.modal', function() {
        modalElement.remove();
    });
}

function setupZoneDrawing(cameraId) {
    const canvas = document.getElementById('zoneDrawingCanvas');
    const feedContainer = document.getElementById('zoneDrawingFeed');

    if (!canvas || !feedContainer) {
        console.error('Canvas or feed container not found');
        return;
    }

    function resizeCanvas() {
        canvas.width = feedContainer.clientWidth;
        canvas.height = feedContainer.clientHeight;
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    let isDrawing = false;
    let points = [];
    let lastPoint = null;

    const ctx = canvas.getContext('2d');
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';

    canvas.addEventListener('mousedown', function(e) {
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        points.push({x, y});
        lastPoint = {x, y};
        drawPoint(x, y);
    });

    canvas.addEventListener('mousemove', function(e) {
        if (!isDrawing) return;

        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        ctx.beginPath();
        ctx.moveTo(lastPoint.x, lastPoint.y);
        ctx.lineTo(x, y);
        ctx.stroke();

        lastPoint = {x, y};
        points.push({x, y});
    });

    canvas.addEventListener('mouseup', function(e) {
        if (!isDrawing) return;

        isDrawing = false;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        points.push({x, y});
        lastPoint = {x, y};

        if (points.length > 2) {
            ctx.beginPath();
            ctx.moveTo(points[points.length - 1].x, points[points.length - 1].y);
            ctx.lineTo(points[0].x, points[0].y);
            ctx.stroke();
            ctx.fill();
        }
    });

    canvas.addEventListener('touchstart', function(e) {
        e.preventDefault();
        if (e.touches.length === 1) {
            isDrawing = true;
            const touch = e.touches[0];
            const rect = canvas.getBoundingClientRect();
            const x = touch.clientX - rect.left;
            const y = touch.clientY - rect.top;
            points.push({x, y});
            lastPoint = {x, y};
            drawPoint(x, y);
        }
    });

    canvas.addEventListener('touchmove', function(e) {
        e.preventDefault();
        if (!isDrawing || e.touches.length !== 1) return;

        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;

        ctx.beginPath();
        ctx.moveTo(lastPoint.x, lastPoint.y);
        ctx.lineTo(x, y);
        ctx.stroke();

        lastPoint = {x, y};
        points.push({x, y});
    });

    canvas.addEventListener('touchend', function(e) {
        e.preventDefault();
        if (!isDrawing) return;

        isDrawing = false;
        if (e.touches.length === 0) {
            const touch = e.changedTouches[0];
            const rect = canvas.getBoundingClientRect();
            const x = touch.clientX - rect.left;
            const y = touch.clientY - rect.top;

            points.push({x, y});
            lastPoint = {x, y};

            if (points.length > 2) {
                ctx.beginPath();
                ctx.moveTo(points[points.length - 1].x, points[points.length - 1].y);
                ctx.lineTo(points[0].x, points[0].y);
                ctx.stroke();
                ctx.fill();
            }
        }
    });

    document.getElementById('clearZoneBtn').addEventListener('click', function() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        points = [];
        lastPoint = null;
    });

    document.getElementById('saveZoneBtn').addEventListener('click', function() {
        if (points.length < 3) {
            Common.showNotification('Se necesitan al menos 3 puntos para definir una zona', 'warning');
            return;
        }

        const coordinates = points.map(point => [Math.round(point.x), Math.round(point.y)]);
        console.log('Saving zone for camera', cameraId, 'with coordinates:', coordinates);
        Common.showNotification('Zona guardada correctamente', 'success');

        const zoneDrawingModal = bootstrap.Modal.getInstance(document.getElementById('zoneDrawingModal'));
        zoneDrawingModal.hide();
    });
}

function drawPoint(x, y) {
    const ctx = document.getElementById('zoneDrawingCanvas').getContext('2d');
    ctx.beginPath();
    ctx.arc(x, y, 2, 0, Math.PI * 2);
    ctx.fillStyle = '#00ff00';
    ctx.fill();
}

function editZone(zoneId) {
    console.log(`Editing zone ${zoneId}`);
    Common.showNotification(`Funcionalidad de edición de zona ${zoneId} en desarrollo`, 'info');
}

function deleteZone(zoneId) {
    if (confirm(`¿Está seguro de que desea eliminar la zona ${zoneId}?`)) {
        console.log(`Deleting zone ${zoneId}`);
        Common.showNotification(`Zona ${zoneId} eliminada correctamente`, 'success');
    }
}

// ---- Real data loading ----

function loadDashboard() {
    loadStats();
    loadCameras();
    loadRecentAlerts();
}

function loadStats() {
    API.getCameras({limit: 100}).then(function(cameras) {
        const activeCameras = cameras.filter(c => c.is_active).length;
        setStat('stat-active-cameras', activeCameras);
        return activeCameras;
    }).catch(function(err) {
        console.error('Failed to load cameras:', err);
    });

    API.getVehicles({limit: 1000}).then(function(vehicles) {
        const today = new Date();
        const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const vehiclesToday = vehicles.filter(function(v) {
            const seen = new Date(v.first_seen);
            return seen >= startOfDay;
        }).length;
        const parked = vehicles.filter(v => v.is_parked).length;
        const platesRead = vehicles.filter(v => v.license_plate).length;

        setStat('stat-vehicles-today', vehiclesToday);
        setStat('stat-parked-vehicles', parked);
        setStat('stat-plates-read', platesRead);
    }).catch(function(err) {
        console.error('Failed to load vehicles:', err);
    });

    // Also load parked vehicles from dedicated endpoint as fallback
    API.getParkedVehicles().then(function(parked) {
        setStat('stat-parked-vehicles', parked.length);
    }).catch(function() {
        // Ignore: main vehicles call already covers this
    });
}

function setStat(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    }
}

function loadCameras() {
    API.getCameras({limit: 100}).then(function(cameras) {
        renderCameras(cameras);
    }).catch(function(err) {
        console.error('Failed to load cameras:', err);
        const placeholder = document.getElementById('camera-grid-placeholder');
        if (placeholder) {
            placeholder.textContent = 'No se pudieron cargar las cámaras: ' + (err.message || err);
        }
    });
}

function renderCameras(cameras) {
    const grid = document.getElementById('camera-grid');
    if (!grid) return;

    if (!cameras || cameras.length === 0) {
        grid.innerHTML = `
            <div class="col-12 py-5 text-center text-muted">
                <i class="fas fa-video-slash fa-3x opacity-25 mb-3"></i>
                <p class="mb-0">No hay cámaras registradas. Agregue una cámara en Configuración.</p>
            </div>
        `;
        return;
    }

    let html = '';
    cameras.forEach(function(camera, index) {
        const statusClass = camera.is_active ? 'bg-success' : 'bg-danger';
        const statusText = camera.is_active ? 'EN VIVO' : 'DESCONECTADA';
        const lastRow = (index + 1) % 2 === 0 ? '' : 'border-end';
        const borderClass = (index + 1) === cameras.length ? '' : 'border-bottom';

        html += `
            <div class="col-md-6">
                <div class="camera-item ${lastRow} ${borderClass}">
                    <div class="position-relative">
                        <div class="camera-feed bg-dark min-vh-50 d-flex align-items-center justify-content-center text-white">
                            <i class="fas fa-video-slash fa-3x opacity-25"></i>
                            <div>${Common.escapeHtml(camera.name || camera.id)}</div>
                        </div>
                        <div class="camera-status position-absolute top-0 end-0 ${statusClass} p-2" data-camera-id="${camera.id}">
                            <small>${statusText}</small>
                        </div>
                    </div>
                    <div class="camera-info p-3">
                        <div class="d-flex justify-content-between">
                            <span>${Common.escapeHtml(camera.location || camera.name || camera.id)}</span>
                            <span class="badge ${camera.is_active ? 'bg-success' : 'bg-danger'}">${camera.is_active ? 'Activa' : 'Inactiva'}</span>
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">${Common.escapeHtml(camera.rtsp_url || 'Sin stream configurado')}</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    grid.innerHTML = html;
}

function loadRecentAlerts() {
    API.getRecentEvents(24).then(function(events) {
        renderAlerts(events);
    }).catch(function(err) {
        console.error('Failed to load events:', err);
        const alerts = document.getElementById('recent-alerts');
        if (alerts) {
            alerts.innerHTML = `
                <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center text-muted">
                    <span>No se pudieron cargar las alertas</span>
                </a>
            `;
        }
    });
}

function renderAlerts(events) {
    const container = document.getElementById('recent-alerts');
    if (!container) return;

    if (!events || events.length === 0) {
        container.innerHTML = `
            <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center text-muted">
                <span>No hay alertas recientes</span>
            </a>
        `;
        return;
    }

    const types = {
        'vehicle_parked': { badge: 'bg-danger', text: 'Activa' },
        'vehicle_left': { badge: 'bg-info', text: 'Salida' },
        'plate_detected': { badge: 'bg-warning', text: 'Pendiente' },
        'camera_offline': { badge: 'bg-secondary', text: 'Inactiva' },
        'system_alert': { badge: 'bg-warning', text: 'Alerta' }
    };

    const maxEvents = 5;
    const shown = events.slice(0, maxEvents);
    let html = '';

    shown.forEach(function(event) {
        const t = types[event.event_type] || { badge: 'bg-secondary', text: event.event_type };
        const description = event.description || 'Evento del sistema';
        const plate = event.license_plate ? ` • Placa: ${event.license_plate}` : '';
        const time = event.timestamp ? new Date(event.timestamp).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '';

        html += `
            <a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${Common.escapeHtml(description)}</h6>
                    <p class="mb-0 text-small text-muted">${time}${plate}</p>
                </div>
                <span class="badge ${t.badge} rounded-pill">${t.text}</span>
            </a>
        `;
    });

    container.innerHTML = html;
}

// ---- Periodic updates (real data) ----

function updateDashboardStats() {
    loadStats();
}

function updateCameraFeeds() {
    API.getCameras({limit: 100}).then(function(cameras) {
        cameras.forEach(function(camera) {
            const statusEl = document.querySelector(`.camera-status[data-camera-id="${camera.id}"]`);
            if (statusEl) {
                const active = camera.is_active;
                statusEl.className = `camera-status position-absolute top-0 end-0 ${active ? 'bg-success' : 'bg-danger'} p-2`;
                statusEl.querySelector('small').textContent = active ? 'EN VIVO' : 'DESCONECTADA';
            }
        });
    }).catch(function(err) {
        console.error('Failed to refresh camera statuses:', err);
    });
}

// ---- Utilities ----
// escapeHtml() and showNotification() are provided by js/common.js (Common)
