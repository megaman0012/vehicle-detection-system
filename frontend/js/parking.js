// Parking Page JavaScript for Vehicle Detection System

let parkingState = {
    zones: [],
    parkedVehicles: [],
    cameras: []
};

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('parking');
    initParkingPage();
});

function initParkingPage() {
    setupZoneModal();
    setupZoneDrawingModal();

    document.getElementById('newZoneBtn').addEventListener('click', function() {
        openZoneModal();
    });
    document.querySelector('.btn-refresh-parking').addEventListener('click', function() {
        loadParkingPage();
        Common.showNotification('Datos actualizados', 'success');
    });

    loadParkingPage();
    setInterval(loadParkingPage, 30000);
}

function loadParkingPage() {
    loadCameras();
    loadZones();
    loadParkedVehicles();
}

// ---- Loading ----

function loadCameras() {
    API.getCameras({ limit: 100 }).then(function(cameras) {
        parkingState.cameras = cameras;
        populateCameraSelect();
    }).catch(function(err) {
        console.error('Failed to load cameras:', err);
    });
}

function populateCameraSelect() {
    const select = document.getElementById('zoneCamera');
    if (!select) return;
    const current = select.value;
    const options = ['<option value="">Seleccione una cámara...</option>'];
    parkingState.cameras.forEach(function(cam) {
        options.push(`<option value="${cam.id}">${Common.escapeHtml(cam.name)}</option>`);
    });
    select.innerHTML = options.join('');
    if (current) select.value = current;
}

function loadZones() {
    API.getZones().then(function(zones) {
        parkingState.zones = zones;
        renderZones();
    }).catch(function(err) {
        console.error('Failed to load zones:', err);
        renderZonesError(err.message || err);
    });
}

function loadParkedVehicles() {
    API.getParkedVehicles().then(function(vehicles) {
        parkingState.parkedVehicles = vehicles;
        renderParkedVehicles();
    }).catch(function(err) {
        console.error('Failed to load parked vehicles:', err);
        renderParkedVehiclesError(err.message || err);
    });
}

function getCameraName(cameraId) {
    const cam = parkingState.cameras.find(function(c) { return c.id === cameraId; });
    return cam ? cam.name : (cameraId || '-');
}

// ---- Zones rendering ----

function renderZonesError(message) {
    const tbody = document.querySelector('#zonesTable tbody');
    if (!tbody) return;
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-muted mb-3"></i>
                <p class="text-muted">Error al cargar las zonas: ${Common.escapeHtml(message)}</p>
            </td>
        </tr>
    `;
}

function renderZones() {
    const tbody = document.querySelector('#zonesTable tbody');
    if (!tbody) return;

    const zones = parkingState.zones;

    if (!zones || zones.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <i class="fas fa-draw-polygon fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay zonas registradas. Haga clic en "Nueva Zona".</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    zones.forEach(function(zone) {
        const pointsCount = Array.isArray(zone.coordinates) ? zone.coordinates.length : 0;
        const activeBadge = zone.is_active
            ? '<span class="badge bg-success">Activa</span>'
            : '<span class="badge bg-danger">Inactiva</span>';

        html += `
            <tr>
                <td><i class="fas fa-draw-polygon me-2 text-primary"></i>${Common.escapeHtml(zone.name)}</td>
                <td>${Common.escapeHtml(getCameraName(zone.camera_id))}</td>
                <td>${pointsCount}</td>
                <td>${activeBadge}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary btn-draw-zone" data-id="${zone.id}" title="Dibujar coordenadas"><i class="fas fa-edit"></i></button>
                        <button type="button" class="btn btn-outline-secondary btn-edit-zone" data-id="${zone.id}" title="Editar"><i class="fas fa-pencil-alt"></i></button>
                        <button type="button" class="btn btn-outline-danger btn-delete-zone" data-id="${zone.id}" title="Eliminar"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    tbody.querySelectorAll('.btn-draw-zone').forEach(function(btn) {
        btn.addEventListener('click', function() {
            openZoneDrawingModal(this.getAttribute('data-id'));
        });
    });
    tbody.querySelectorAll('.btn-edit-zone').forEach(function(btn) {
        btn.addEventListener('click', function() {
            openZoneModal(this.getAttribute('data-id'));
        });
    });
    tbody.querySelectorAll('.btn-delete-zone').forEach(function(btn) {
        btn.addEventListener('click', function() {
            deleteZone(this.getAttribute('data-id'));
        });
    });
}

// ---- Parked vehicles rendering ----

const VEHICLE_TYPES = {
    car: { icon: 'fas fa-car', text: 'Automóvil', color: 'primary' },
    motorcycle: { icon: 'fas fa-motorcycle', text: 'Motocicleta', color: 'info' },
    truck: { icon: 'fas fa-truck', text: 'Camión', color: 'success' },
    bus: { icon: 'fas fa-bus', text: 'Bus', color: 'warning' },
    unknown: { icon: 'fas fa-question-circle', text: 'Desconocido', color: 'secondary' }
};

function renderParkedVehiclesError(message) {
    const tbody = document.querySelector('#parkedVehiclesTable tbody');
    if (!tbody) return;
    tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-muted mb-3"></i>
                <p class="text-muted">Error al cargar los vehículos: ${Common.escapeHtml(message)}</p>
            </td>
        </tr>
    `;
}

function renderParkedVehicles() {
    const tbody = document.querySelector('#parkedVehiclesTable tbody');
    if (!tbody) return;

    const vehicles = parkingState.parkedVehicles;

    if (!vehicles || vehicles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="fas fa-car fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay vehículos estacionados actualmente.</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    vehicles.forEach(function(v) {
        const t = VEHICLE_TYPES[v.vehicle_type] || VEHICLE_TYPES.unknown;
        const plate = v.license_plate
            ? `<span class="badge bg-info">${Common.escapeHtml(v.license_plate)}</span>`
            : '-';

        html += `
            <tr>
                <td><code>${Common.escapeHtml(v.vehicle_id)}</code></td>
                <td><span class="badge bg-${t.color}"><i class="${t.icon} me-1"></i>${t.text}</span></td>
                <td>${plate}</td>
                <td>${Common.escapeHtml(getCameraName(v.camera_id))}</td>
                <td>${Common.formatDateTime(v.first_seen)}</td>
                <td>${Common.formatDateTime(v.last_seen)}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// ---- Zone modal (create/edit) ----

function setupZoneModal() {
    const form = document.getElementById('zoneForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveZone();
        });
    }
}

function openZoneModal(zoneId) {
    const title = document.getElementById('zoneModalTitle');
    const form = document.getElementById('zoneForm');
    form.reset();
    document.getElementById('zoneActive').checked = true;

    if (zoneId) {
        const zone = parkingState.zones.find(function(z) { return z.id === zoneId; });
        if (zone) {
            title.textContent = 'Editar Zona';
            document.getElementById('zoneId').value = zone.id;
            document.getElementById('zoneName').value = zone.name;
            document.getElementById('zoneCamera').value = zone.camera_id || '';
            document.getElementById('zoneActive').checked = !!zone.is_active;
            document.getElementById('zoneCamera').disabled = true;
        }
    } else {
        title.textContent = 'Nueva Zona';
        document.getElementById('zoneId').value = '';
        document.getElementById('zoneCamera').disabled = false;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('zoneModal'));
    modal.show();
}

function saveZone() {
    const zoneId = document.getElementById('zoneId').value;
    const data = {
        name: document.getElementById('zoneName').value.trim(),
        camera_id: document.getElementById('zoneCamera').value,
        is_active: document.getElementById('zoneActive').checked
    };

    if (!data.name) {
        Common.showNotification('El nombre de la zona es obligatorio', 'warning');
        return;
    }
    if (!zoneId && !data.camera_id) {
        Common.showNotification('Seleccione una cámara', 'warning');
        return;
    }

    const saveBtn = document.getElementById('saveZoneBtn');
    saveBtn.disabled = true;

    const promise = zoneId
        ? API.updateZone(zoneId, { name: data.name, is_active: data.is_active })
        : API.createZone({ name: data.name, camera_id: data.camera_id, is_active: data.is_active });

    promise.then(function() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('zoneModal'));
        if (modal) modal.hide();
        Common.showNotification(zoneId ? 'Zona actualizada' : 'Zona creada', 'success');
        loadZones();
    }).catch(function(err) {
        Common.showNotification('Error al guardar la zona: ' + (err.message || err), 'danger');
    }).finally(function() {
        saveBtn.disabled = false;
    });
}

function deleteZone(zoneId) {
    const zone = parkingState.zones.find(function(z) { return z.id === zoneId; });
    const name = zone ? zone.name : zoneId;
    if (!confirm('¿Está seguro de que desea eliminar la zona "' + name + '"?')) return;

    API.deleteZone(zoneId).then(function() {
        Common.showNotification('Zona eliminada', 'success');
        loadZones();
    }).catch(function(err) {
        Common.showNotification('Error al eliminar: ' + (err.message || err), 'danger');
    });
}

// ---- Zone drawing (canvas) ----

let drawingState = {
    zoneId: null,
    points: [],
    ctx: null,
    canvas: null
};

function setupZoneDrawingModal() {
    const modalEl = document.getElementById('zoneDrawingModal');
    if (!modalEl) return;

    modalEl.addEventListener('shown.bs.modal', function() {
        initDrawingCanvas();
    });
    modalEl.addEventListener('hidden.bs.modal', function() {
        drawingState.points = [];
        drawingState.zoneId = null;
    });

    document.getElementById('undoZoneBtn').addEventListener('click', function() {
        drawingState.points.pop();
        redrawCanvas();
    });
    document.getElementById('clearZoneBtn').addEventListener('click', function() {
        drawingState.points = [];
        redrawCanvas();
    });
    document.getElementById('saveZoneBtn').addEventListener('click', function() {
        saveZoneCoordinates();
    });
}

function openZoneDrawingModal(zoneId) {
    drawingState.zoneId = zoneId;
    const zone = parkingState.zones.find(function(z) { return z.id === zoneId; });
    if (zone && Array.isArray(zone.coordinates)) {
        drawingState.points = zone.coordinates.map(function(pt) {
            return { x: pt[0], y: pt[1] };
        });
    } else {
        drawingState.points = [];
    }
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('zoneDrawingModal'));
    modal.show();
}

function initDrawingCanvas() {
    const canvas = document.getElementById('zoneDrawingCanvas');
    const feedContainer = document.getElementById('zoneDrawingFeed');
    if (!canvas || !feedContainer) return;

    function resizeCanvas() {
        canvas.width = feedContainer.clientWidth;
        canvas.height = feedContainer.clientHeight;
        redrawCanvas();
    }

    drawingState.canvas = canvas;
    drawingState.ctx = canvas.getContext('2d');

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    canvas.onmousedown = function(e) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        drawingState.points.push({ x: Math.round(x), y: Math.round(y) });
        redrawCanvas();
    };

    canvas.ontouchstart = function(e) {
        e.preventDefault();
        if (e.touches.length !== 1) return;
        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;
        drawingState.points.push({ x: Math.round(x), y: Math.round(y) });
        redrawCanvas();
    };

    redrawCanvas();
}

function redrawCanvas() {
    if (!drawingState.ctx || !drawingState.canvas) return;
    const ctx = drawingState.ctx;
    const canvas = drawingState.canvas;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const points = drawingState.points;
    if (points.length === 0) return;

    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
    }
    if (points.length > 2) {
        ctx.closePath();
        ctx.stroke();
        ctx.fill();
    } else {
        ctx.stroke();
    }

    points.forEach(function(p, i) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#00ff00';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = '#00ff00';
        ctx.font = '12px monospace';
        ctx.fillText(String(i + 1), p.x + 6, p.y - 6);
    });
}

function saveZoneCoordinates() {
    if (!drawingState.zoneId) return;
    if (drawingState.points.length < 3) {
        Common.showNotification('Se necesitan al menos 3 puntos para definir una zona', 'warning');
        return;
    }

    const coordinates = drawingState.points.map(function(p) { return [p.x, p.y]; });

    API.updateZone(drawingState.zoneId, { coordinates: coordinates }).then(function() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('zoneDrawingModal'));
        if (modal) modal.hide();
        Common.showNotification('Coordenadas de la zona guardadas', 'success');
        loadZones();
    }).catch(function(err) {
        Common.showNotification('Error al guardar coordenadas: ' + (err.message || err), 'danger');
    });
}
