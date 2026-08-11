// Events Page JavaScript for Vehicle Detection System

let eventsCache = [];
let cameraMap = {};

document.addEventListener('DOMContentLoaded', function() {
    // Auth guard: require a valid session before rendering
    if (!Common.requireAuth()) {
        return;
    }

    // Sidebar, logout, user name and active page
    Common.initSidebar('events');

    // Initialize events page functionality
    initializeEventsPage();
});

function initializeEventsPage() {
    initEventsTable();
    setupEventFilters();
    setupEventActions();
    loadCameraOptions();
    loadEvents();
}

// ---- DataTable ----

function initEventsTable() {
    const table = $('#eventsTable').DataTable({
        language: {
            "sProcessing": "Procesando...",
            "sLengthMenu": "Mostrar _MENU_ registros",
            "sZeroRecords": "No se encontraron resultados",
            "sEmptyTable": "Ningún dato disponible en esta tabla",
            "sInfo": "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
            "sInfoEmpty": "Mostrando registros del 0 al 0 de un total de 0 registros",
            "sInfoFiltered": "(filtrado de un total de _MAX_ registros)",
            "sInfoPostFix": "",
            "sSearch": "Buscar:",
            "sUrl": "",
            "sInfoThousands": ",",
            "sLoadingRecords": "Cargando...",
            "oPaginate": {
                "sFirst": "Primero",
                "sLast": "Último",
                "sNext": "Siguiente",
                "sPrevious": "Anterior"
            },
            "oAria": {
                "sSortAscending": ": Activar para ordenar la columna de manera ascendente",
                "sSortDescending": ": Activar para ordenar la columna de manera descendente"
            }
        },
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        order: [[0, 'desc']],
        responsive: true,
        drawCallback: function() {
            // Reinitialize tooltips after table redraw
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    });

    window.eventsTable = table;
}

// ---- Filters ----

function setupEventFilters() {
    const filterBtn = document.getElementById('filterBtn');
    const filtersCollapse = document.getElementById('filtersCollapse');

    if (filterBtn && filtersCollapse) {
        filterBtn.addEventListener('click', function() {
            const bsCollapse = new bootstrap.Collapse(filtersCollapse);
            bsCollapse.toggle();
        });
    }

    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            document.getElementById('eventFiltersForm').reset();
            loadEvents();
        });
    }

    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            loadEvents();
        });
    }

    const filtersForm = document.getElementById('eventFiltersForm');
    if (filtersForm) {
        filtersForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadEvents();
        });
    }

    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportEventsCsv();
        });
    }
}

function loadCameraOptions() {
    API.getCameras({ limit: 100 }).then(function(cameras) {
        const select = document.getElementById('cameraFilter');
        if (!select) return;
        cameraMap = {};
        let options = '<option value="">Todas las cámaras</option>';
        cameras.forEach(function(cam) {
            cameraMap[cam.id] = cam.name;
            options += `<option value="${cam.id}">${Common.escapeHtml(cam.name)}</option>`;
        });
        select.innerHTML = options;
    }).catch(function(err) {
        console.error('Failed to load camera options:', err);
    });
}

function loadEvents() {
    const params = {
        limit: 100,
        skip: 0
    };

    const eventType = document.getElementById('eventTypeFilter') ? document.getElementById('eventTypeFilter').value : '';
    const startDate = document.getElementById('startDateFilter') ? document.getElementById('startDateFilter').value : '';
    const endDate = document.getElementById('endDateFilter') ? document.getElementById('endDateFilter').value : '';
    const cameraId = document.getElementById('cameraFilter') ? document.getElementById('cameraFilter').value : '';

    if (eventType) params.event_type = eventType;
    if (startDate) params.start_date = new Date(startDate + 'T00:00:00').toISOString();
    if (endDate) params.end_date = new Date(endDate + 'T23:59:59').toISOString();

    API.getEvents(params).then(function(events) {
        eventsCache = events || [];

        // Camera filter is applied client-side
        let filtered = eventsCache;
        if (cameraId) {
            filtered = filtered.filter(function(ev) {
                return String(ev.camera_id) === String(cameraId);
            });
        }

        if (window.eventsTable) {
            window.eventsTable.clear().rows.add(filtered.map(formatEventForDataTable)).draw();
        } else {
            populateEventsTable(filtered);
        }
    }).catch(function(err) {
        console.error('Failed to load events:', err);
        const tbody = document.querySelector('#eventsTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4">
                        <i class="fas fa-exclamation-triangle fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Error al cargar los eventos: ${Common.escapeHtml(err.message || err)}</p>
                    </td>
                </tr>
            `;
        }
    });
}

// ---- Rendering ----

const EVENT_TYPE_STYLES = {
    'vehicle_parked': { icon: 'fas fa-parking', color: 'success', text: 'Vehículo Estacionado' },
    'vehicle_left': { icon: 'fas fa-car-rear', color: 'info', text: 'Vehículo Retirado' },
    'plate_detected': { icon: 'fas fa-license', color: 'warning', text: 'Placa Detectada' },
    'camera_offline': { icon: 'fas fa-video-slash', color: 'danger', text: 'Cámara Desconectada' },
    'system_alert': { icon: 'fas fa-exclamation-triangle', color: 'warning', text: 'Alerta del Sistema' }
};

function formatEventForDataTable(event) {
    const formattedDate = Common.formatDateTime(event.timestamp);

    const style = EVENT_TYPE_STYLES[event.event_type] || { icon: 'fas fa-bell', color: 'secondary', text: event.event_type };
    const typeBadge = `<span class="badge bg-${style.color}">${style.text}</span>`;

    const plateDisplay = event.license_plate ? `<span class="badge bg-info">${Common.escapeHtml(event.license_plate)}</span>` : '-';

    const cameraDisplay = cameraMap[event.camera_id] ? cameraMap[event.camera_id] : (event.camera_id || '-');

    const actions = `
        <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-secondary btn-view-event" data-event-id="${event.id}" data-bs-toggle="tooltip" data-bs-placement="top" title="Ver detalles">
                <i class="fas fa-eye"></i>
            </button>
            <button type="button" class="btn btn-outline-success btn-whatsapp-event" data-event-id="${event.id}" data-bs-toggle="tooltip" data-bs-placement="top" title="Enviar por WhatsApp">
                <i class="fab fa-whatsapp"></i>
            </button>
        </div>
    `;

    return [
        formattedDate,
        typeBadge,
        event.description || '-',
        cameraDisplay,
        plateDisplay,
        actions
    ];
}

function populateEventsTable(events) {
    const tbody = document.querySelector('#eventsTable tbody');

    if (events.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No se encontraron eventos con los filtros aplicados</p>
                </td>
            </tr>
        `;
        return;
    }

    let rowsHtml = '';
    events.forEach(event => {
        const formatted = formatEventForDataTable(event);
        rowsHtml += `
            <tr>
                <td>${formatted[0]}</td>
                <td>${formatted[1]}</td>
                <td>${formatted[2]}</td>
                <td>${formatted[3]}</td>
                <td>${formatted[4]}</td>
                <td>${formatted[5]}</td>
            </tr>
        `;
    });

    tbody.innerHTML = rowsHtml;
}

// ---- Event actions (view details / WhatsApp) ----

function setupEventActions() {
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.btn-view-event');
        if (viewBtn) {
            showEventDetails(viewBtn.getAttribute('data-event-id'));
            return;
        }
        const waBtn = e.target.closest('.btn-whatsapp-event');
        if (waBtn) {
            sendEventWhatsApp(waBtn.getAttribute('data-event-id'));
            return;
        }
        if (e.target.closest('.btn-refresh')) {
            e.preventDefault();
            loadEvents();
            Common.showNotification('Eventos actualizados', 'success');
        }
    });
}

function getEventById(eventId) {
    return eventsCache.find(function(ev) { return String(ev.id) === String(eventId); });
}

function showEventDetails(eventId) {
    const event = getEventById(eventId);
    if (!event) {
        Common.showNotification('No se encontró el evento', 'warning');
        return;
    }

    const style = EVENT_TYPE_STYLES[event.event_type] || { text: event.event_type };
    const cameraName = cameraMap[event.camera_id] || event.camera_id || '-';
    const meta = event.meta ? JSON.stringify(event.meta, null, 2) : '-';

    const body = document.getElementById('eventDetailsBody');
    body.innerHTML = `
        <table class="table table-sm">
            <tbody>
                <tr><th class="w-25">Fecha</th><td>${Common.formatDateTime(event.timestamp)}</td></tr>
                <tr><th>Tipo</th><td><span class="badge bg-success">${Common.escapeHtml(style.text)}</span></td></tr>
                <tr><th>Descripción</th><td>${Common.escapeHtml(event.description || '-')}</td></tr>
                <tr><th>Cámara</th><td>${Common.escapeHtml(cameraName)}</td></tr>
                <tr><th>Placa</th><td>${event.license_plate ? Common.escapeHtml(event.license_plate) : '-'}</td></tr>
                <tr><th>Evento ID</th><td><code>${Common.escapeHtml(event.id)}</code></td></tr>
                <tr><th>Vehículo ID</th><td>${event.vehicle_id ? '<code>' + Common.escapeHtml(event.vehicle_id) + '</code>' : '-'}</td></tr>
                <tr><th>Zona ID</th><td>${event.zone_id ? '<code>' + Common.escapeHtml(event.zone_id) + '</code>' : '-'}</td></tr>
                <tr><th>Metadatos</th><td><pre class="mb-0 small bg-light p-2 rounded">${Common.escapeHtml(meta)}</pre></td></tr>
            </tbody>
        </table>
    `;

    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('eventDetailsModal'));
    modal.show();
}

function sendEventWhatsApp(eventId) {
    const event = getEventById(eventId);
    if (!event) {
        Common.showNotification('No se encontró el evento', 'warning');
        return;
    }

    const phone = prompt('Ingrese el número de teléfono para enviar la notificación (ej: 584121234567):');
    if (!phone) return;

    const style = EVENT_TYPE_STYLES[event.event_type] || { text: event.event_type };
    const message = `[VDS] ${style.text}: ${event.description || ''}` +
        (event.license_plate ? ` · Placa: ${event.license_plate}` : '') +
        ` · ${Common.formatDateTime(event.timestamp)}`;

    API.sendWhatsAppMessage({ phone_number: phone.trim(), message: message }).then(function() {
        Common.showNotification('Notificación encolada para envío por WhatsApp', 'success');
    }).catch(function(err) {
        Common.showNotification('Error al enviar: ' + (err.message || err), 'danger');
    });
}

// ---- CSV export ----

function exportEventsCsv() {
    const rows = window.eventsTable ? window.eventsTable.data().toArray() : [];

    if (rows.length === 0) {
        Common.showNotification('No hay eventos para exportar', 'warning');
        return;
    }

    const headers = ['Fecha y Hora', 'Tipo', 'Descripción', 'Cámara', 'Placa'];
    const csvLines = [headers.join(',')];

    rows.forEach(function(row) {
        const cols = [
            stripHtml(row[0]),
            stripHtml(row[1]),
            stripHtml(row[2]),
            stripHtml(row[3]),
            stripHtml(row[4])
        ];
        csvLines.push(cols.map(csvEscape).join(','));
    });

    const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'eventos_' + new Date().toISOString().slice(0, 10) + '.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    Common.showNotification('Eventos exportados a CSV', 'success');
}

function stripHtml(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || '';
}

function csvEscape(value) {
    const s = String(value === null || value === undefined ? '' : value);
    if (s.indexOf(',') !== -1 || s.indexOf('"') !== -1 || s.indexOf('\n') !== -1) {
        return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
}
