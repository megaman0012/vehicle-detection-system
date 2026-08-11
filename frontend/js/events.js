// Events Page JavaScript for Vehicle Detection System

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
    // Initialize DataTable
    initEventsTable();

    // Set up filter functionality
    setupEventFilters();

    // Load real events from backend
    loadEvents();
}

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
        responsive: true
    });

    window.eventsTable = table;
}

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
}

function loadEvents() {
    console.log('Loading events from backend...');

    const params = {
        limit: 100,
        skip: 0
    };

    const eventType = document.getElementById('eventTypeFilter') ? document.getElementById('eventTypeFilter').value : '';
    const startDate = document.getElementById('startDateFilter') ? document.getElementById('startDateFilter').value : '';
    const endDate = document.getElementById('endDateFilter') ? document.getElementById('endDateFilter').value : '';

    if (eventType) params.event_type = eventType;
    if (startDate) params.start_date = new Date(startDate + 'T00:00:00').toISOString();
    if (endDate) params.end_date = new Date(endDate + 'T23:59:59').toISOString();

    API.getEvents(params).then(function(events) {
        if (window.eventsTable) {
            window.eventsTable.clear().rows.add(events.map(formatEventForDataTable)).draw();
        } else {
            populateEventsTable(events);
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

const EVENT_TYPE_STYLES = {
    'vehicle_parked': { icon: 'fas fa-parking', color: 'success', text: 'Vehículo Estacionado' },
    'vehicle_left': { icon: 'fas fa-car-rear', color: 'info', text: 'Vehículo Retirado' },
    'plate_detected': { icon: 'fas fa-license', color: 'warning', text: 'Placa Detectada' },
    'camera_offline': { icon: 'fas fa-video-slash', color: 'danger', text: 'Cámara Desconectada' },
    'system_alert': { icon: 'fas fa-exclamation-triangle', color: 'warning', text: 'Alerta del Sistema' }
};

function formatEventForDataTable(event) {
    const date = new Date(event.timestamp);
    const formattedDate = date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    const style = EVENT_TYPE_STYLES[event.event_type] || { icon: 'fas fa-bell', color: 'secondary', text: event.event_type };
    const typeBadge = `<span class="badge bg-${style.color}">${style.text}</span>`;

    const plateDisplay = event.license_plate ? `<span class="badge bg-info">${Common.escapeHtml(event.license_plate)}</span>` : '-';

    const actions = `
        <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-secondary" data-bs-toggle="tooltip" data-bs-placement="top" title="Ver detalles">
                <i class="fas fa-eye"></i>
            </button>
            <button type="button" class="btn btn-outline-success" data-bs-toggle="tooltip" data-bs-placement="top" title="Enviar por WhatsApp">
                <i class="fas fa-whatsapp"></i>
            </button>
        </div>
    `;

    return [
        formattedDate,
        typeBadge,
        event.description || '-',
        event.camera_id || '-',
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

    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Utilities (escapeHtml and showNotification are provided by js/common.js)

// Export functionality
document.getElementById('exportBtn').addEventListener('click', function() {
    Common.showNotification('Funcionalidad de exportación en desarrollo', 'info');
});

// Refresh button functionality
document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-refresh')) {
        e.preventDefault();
        loadEvents();
        Common.showNotification('Eventos actualizados', 'success');
    }
});
