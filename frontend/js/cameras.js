// Cameras Page JavaScript for Vehicle Detection System

let camerasPageState = {
    cameras: [],
    aiActive: {},      // camera_id -> true while AI processes it
    aiStatus: null
};

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('cameras');
    initCamerasPage();
});

function initCamerasPage() {
    setupCameraForm();
    setupAiStatusModal();

    document.getElementById('newCameraBtn').addEventListener('click', function() {
        openCameraModal();
    });
    document.getElementById('aiStatusBtn').addEventListener('click', function() {
        showAiStatusModal();
    });

    loadCameras();

    setInterval(loadAiStatus, 10000);
    setInterval(loadCameras, 30000);
}

// ---- Loading ----

function loadCameras() {
    API.getCameras({ limit: 100 }).then(function(cameras) {
        camerasPageState.cameras = cameras;
        renderCameras();
        loadAiStatus();
    }).catch(function(err) {
        console.error('Failed to load cameras:', err);
        renderCamerasError(err.message || err);
    });
}

function loadAiStatus() {
    API.aiGetStatus().then(function(status) {
        camerasPageState.aiStatus = status;
        const active = {};
        (status.active_cameras || []).forEach(function(c) {
            active[c.camera_id] = c.thread_alive;
        });
        camerasPageState.aiActive = active;
        renderCameras();
    }).catch(function(err) {
        console.error('Failed to load AI status:', err);
        camerasPageState.aiActive = {};
    });
}

// ---- Rendering ----

function renderCamerasError(message) {
    const tbody = document.querySelector('#camerasTable tbody');
    if (!tbody) return;
    tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-muted mb-3"></i>
                <p class="text-muted">Error al cargar las cámaras: ${Common.escapeHtml(message)}</p>
            </td>
        </tr>
    `;
}

function renderCameras() {
    const tbody = document.querySelector('#camerasTable tbody');
    if (!tbody) return;

    const cameras = camerasPageState.cameras;

    if (!cameras || cameras.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="fas fa-video-slash fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay cámaras registradas. Haga clic en "Nueva Cámara".</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    cameras.forEach(function(camera) {
        const statusBadge = camera.is_active
            ? '<span class="badge bg-success">Activa</span>'
            : '<span class="badge bg-danger">Inactiva</span>';

        const aiProcessing = !!camerasPageState.aiActive[camera.id];
        const aiBadge = aiProcessing
            ? '<span class="badge bg-primary">Procesando</span>'
            : '<span class="badge bg-secondary">Detenida</span>';

        const aiAction = aiProcessing
            ? `<button type="button" class="btn btn-sm btn-outline-danger btn-ai-stop" data-id="${camera.id}" title="Detener procesamiento IA"><i class="fas fa-stop"></i></button>`
            : `<button type="button" class="btn btn-sm btn-outline-primary btn-ai-start" data-id="${camera.id}" title="Iniciar procesamiento IA"><i class="fas fa-play"></i></button>`;

        html += `
            <tr>
                <td><i class="fas fa-video me-2 text-primary"></i>${Common.escapeHtml(camera.name)}</td>
                <td>${Common.escapeHtml(camera.location || '-')}</td>
                <td class="text-muted small">${Common.escapeHtml(camera.rtsp_url)}</td>
                <td>${statusBadge}</td>
                <td>${aiBadge}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        ${aiAction}
                        <button type="button" class="btn btn-outline-secondary btn-edit" data-id="${camera.id}" title="Editar"><i class="fas fa-edit"></i></button>
                        <button type="button" class="btn btn-outline-danger btn-delete" data-id="${camera.id}" title="Eliminar"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    tbody.querySelectorAll('.btn-ai-start').forEach(function(btn) {
        btn.addEventListener('click', function() {
            startAiProcessing(this.getAttribute('data-id'));
        });
    });
    tbody.querySelectorAll('.btn-ai-stop').forEach(function(btn) {
        btn.addEventListener('click', function() {
            stopAiProcessing(this.getAttribute('data-id'));
        });
    });
    tbody.querySelectorAll('.btn-edit').forEach(function(btn) {
        btn.addEventListener('click', function() {
            openCameraModal(this.getAttribute('data-id'));
        });
    });
    tbody.querySelectorAll('.btn-delete').forEach(function(btn) {
        btn.addEventListener('click', function() {
            deleteCamera(this.getAttribute('data-id'));
        });
    });
}

// ---- Camera CRUD ----

function setupCameraForm() {
    const form = document.getElementById('cameraForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveCamera();
        });
    }
}

function openCameraModal(cameraId) {
    const title = document.getElementById('cameraModalTitle');
    const form = document.getElementById('cameraForm');

    form.reset();
    document.getElementById('cameraActive').checked = true;
    document.getElementById('cameraFps').value = 30;
    document.getElementById('cameraWidth').value = 1920;
    document.getElementById('cameraHeight').value = 1080;

    if (cameraId) {
        const camera = camerasPageState.cameras.find(function(c) { return c.id === cameraId; });
        if (camera) {
            title.textContent = 'Editar Cámara';
            document.getElementById('cameraId').value = camera.id;
            document.getElementById('cameraName').value = camera.name;
            document.getElementById('cameraLocation').value = camera.location || '';
            document.getElementById('cameraRtsp').value = camera.rtsp_url || '';
            document.getElementById('cameraUsername').value = camera.username || '';
            document.getElementById('cameraPassword').value = camera.password || '';
            document.getElementById('cameraFps').value = camera.fps || 30;
            document.getElementById('cameraWidth').value = camera.width || 1920;
            document.getElementById('cameraHeight').value = camera.height || 1080;
            document.getElementById('cameraActive').checked = !!camera.is_active;
        }
    } else {
        title.textContent = 'Nueva Cámara';
        document.getElementById('cameraId').value = '';
    }

    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('cameraModal'));
    modal.show();
}

function saveCamera() {
    const cameraId = document.getElementById('cameraId').value;
    const data = {
        name: document.getElementById('cameraName').value.trim(),
        location: document.getElementById('cameraLocation').value.trim() || null,
        rtsp_url: document.getElementById('cameraRtsp').value.trim(),
        username: document.getElementById('cameraUsername').value.trim() || null,
        password: document.getElementById('cameraPassword').value.trim() || null,
        fps: parseInt(document.getElementById('cameraFps').value, 10) || 30,
        width: parseInt(document.getElementById('cameraWidth').value, 10) || 1920,
        height: parseInt(document.getElementById('cameraHeight').value, 10) || 1080,
        is_active: document.getElementById('cameraActive').checked
    };

    if (!data.name || !data.rtsp_url) {
        Common.showNotification('Nombre y URL RTSP son obligatorios', 'warning');
        return;
    }

    const saveBtn = document.getElementById('saveCameraBtn');
    saveBtn.disabled = true;

    const promise = cameraId
        ? API.updateCamera(cameraId, data)
        : API.createCamera(data);

    promise.then(function() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('cameraModal'));
        if (modal) modal.hide();
        Common.showNotification(cameraId ? 'Cámara actualizada' : 'Cámara creada', 'success');
        loadCameras();
    }).catch(function(err) {
        Common.showNotification('Error al guardar: ' + (err.message || err), 'danger');
    }).finally(function() {
        saveBtn.disabled = false;
    });
}

function deleteCamera(cameraId) {
    const camera = camerasPageState.cameras.find(function(c) { return c.id === cameraId; });
    const name = camera ? camera.name : cameraId;
    if (!confirm('¿Está seguro de que desea eliminar la cámara "' + name + '"?')) return;

    API.deleteCamera(cameraId).then(function() {
        Common.showNotification('Cámara eliminada', 'success');
        loadCameras();
    }).catch(function(err) {
        Common.showNotification('Error al eliminar: ' + (err.message || err), 'danger');
    });
}

// ---- AI control ----

function startAiProcessing(cameraId) {
    const camera = camerasPageState.cameras.find(function(c) { return c.id === cameraId; });
    if (!camera) return;
    if (!camera.rtsp_url) {
        Common.showNotification('La cámara no tiene URL RTSP configurada', 'warning');
        return;
    }

    API.aiStartCamera(cameraId, {
        rtsp_url: camera.rtsp_url,
        username: camera.username || null,
        password: camera.password || null
    }).then(function() {
        Common.showNotification('Procesamiento IA iniciado para ' + camera.name, 'success');
        loadAiStatus();
    }).catch(function(err) {
        Common.showNotification('Error al iniciar IA: ' + (err.message || err), 'danger');
    });
}

function stopAiProcessing(cameraId) {
    API.aiStopCamera(cameraId).then(function() {
        Common.showNotification('Procesamiento IA detenido', 'success');
        loadAiStatus();
    }).catch(function(err) {
        Common.showNotification('Error al detener IA: ' + (err.message || err), 'danger');
    });
}

// ---- AI status modal ----

function setupAiStatusModal() {
    const modalEl = document.getElementById('aiStatusModal');
    if (!modalEl) return;
    modalEl.addEventListener('shown.bs.modal', function() {
        renderAiStatusModal();
    });
}

function showAiStatusModal() {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('aiStatusModal'));
    modal.show();
}

function renderAiStatusModal() {
    const body = document.getElementById('aiStatusBody');
    if (!body) return;

    body.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Consultando estado...</p></div>';

    API.aiGetStatus().then(function(status) {
        const running = status.is_running;
        const active = status.active_cameras || [];
        const ocr = status.ocr_available;

        let rows = '';
        if (active.length === 0) {
            rows = '<tr><td colspan="2" class="text-center text-muted py-3">No hay cámaras en procesamiento</td></tr>';
        } else {
            active.forEach(function(c) {
                const cam = camerasPageState.cameras.find(function(x) { return x.id === c.camera_id; });
                const name = cam ? cam.name : c.camera_id;
                rows += `
                    <tr>
                        <td>${Common.escapeHtml(name)}</td>
                        <td>${c.thread_alive ? '<span class="badge bg-success">Activo</span>' : '<span class="badge bg-danger">Detenido</span>'}</td>
                    </tr>
                `;
            });
        }

        body.innerHTML = `
            <div class="mb-3">
                <span class="badge ${running ? 'bg-success' : 'bg-danger'} me-2">Servicio ${running ? 'Activo' : 'Detenido'}</span>
                <span class="badge ${ocr ? 'bg-success' : 'bg-warning'}">OCR ${ocr ? 'Disponible' : 'No disponible'}</span>
            </div>
            <table class="table table-sm table-hover mb-0">
                <thead class="table-light">
                    <tr><th>Cámara</th><th>Estado</th></tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    }).catch(function(err) {
        body.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-muted mb-3"></i>
                <p class="text-muted">No se pudo consultar el estado del servicio de IA.<br>${Common.escapeHtml(err.message || err)}</p>
            </div>
        `;
    });
}
