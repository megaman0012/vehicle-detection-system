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

        renderParkingStats(vehicles);
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

function renderParkingStats(vehicles) {
    const types = { car: 0, motorcycle: 0, truck: 0, bus: 0 };
    const durations = { under1h: 0, between: 0, over4h: 0 };
    const now = Date.now();

    (vehicles || []).forEach(function(v) {
        if (types[v.vehicle_type] !== undefined) {
            types[v.vehicle_type]++;
        }

        const start = v.park_start_time ? new Date(v.park_start_time).getTime() : new Date(v.first_seen).getTime();
        if (isNaN(start)) return;
        const hours = (now - start) / 3600000;
        if (hours < 1) {
            durations.under1h++;
        } else if (hours <= 4) {
            durations.between++;
        } else {
            durations.over4h++;
        }
    });

    setStat('stat-type-car', types.car);
    setStat('stat-type-motorcycle', types.motorcycle);
    setStat('stat-type-truck', types.truck);
    setStat('stat-type-bus', types.bus);
    setStat('stat-dur-under1h', durations.under1h);
    setStat('stat-dur-1to4h', durations.between);
    setStat('stat-dur-over4h', durations.over4h);
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
