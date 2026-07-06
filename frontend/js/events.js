// Events Page JavaScript for Vehicle Detection System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize events page functionality
    initializeEventsPage();
});

function initializeEventsPage() {
    // Initialize DataTable
    initEventsTable();
    
    // Set up filter functionality
    setupEventFilters();
    
    // Load initial events
    loadEvents();
}

function initEventsTable() {
    // Initialize DataTable with Spanish language
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
        order: [[0, 'desc']], // Sort by date descending by default
        responsive: true
    });
    
    // Store table instance for later use
    window.eventsTable = table;
}

function setupEventFilters() {
    // Filter button
    const filterBtn = document.getElementById('filterBtn');
    const filtersCollapse = document.getElementById('filtersCollapse');
    
    if (filterBtn && filtersCollapse) {
        filterBtn.addEventListener('click', function() {
            const bsCollapse = new bootstrap.Collapse(filtersCollapse);
            bsCollapse.toggle();
        });
    }
    
    // Reset filters button
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            // Reset form
            document.getElementById('eventFiltersForm').reset();
            // Apply empty filters
            applyEventFilters();
        });
    }
    
    // Apply filters button
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            applyEventFilters();
        });
    }
    
    // Enter key to apply filters
    const filtersForm = document.getElementById('eventFiltersForm');
    if (filtersForm) {
        filtersForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyEventFilters();
        });
    }
}

function applyEventFilters() {
    // Get filter values
    const eventType = document.getElementById('eventTypeFilter').value;
    const startDate = document.getElementById('startDateFilter').value;
    const endDate = document.getElementById('endDateFilter').value;
    const cameraId = document.getElementById('cameraFilter').value;
    const textSearch = document.getElementById('textSearchFilter').value.trim();
    
    // Build filter string for DataTables
    let filterStr = '';
    
    if (eventType) {
        filterStr += `eventType:${eventType}|`;
    }
    if (startDate) {
        filterStr += `startDate:${startDate}|`;
    }
    if (endDate) {
        filterStr += `endDate:${endDate}|`;
    }
    if (cameraId) {
        filterStr += `cameraId:${cameraId}|`;
    }
    if (textSearch) {
        filterStr += `textSearch:${textSearch}|`;
    }
    
    // Apply filter to DataTable
    if (window.eventsTable) {
        window.eventsTable.search(filterStr, true, false).draw();
    }
    
    // Close collapse if open
    const filtersCollapse = document.getElementById('filtersCollapse');
    if (filtersCollapse && !filtersCollapse.classList.contains('show')) {
        const bsCollapse = new bootstrap.Collapse(filtersCollapse);
        bsCollapse.show();
    }
}

function loadEvents() {
    // In a real implementation, this would fetch events from the backend API
    // For demo purposes, we'll generate mock events
    
    console.log('Loading events...');
    
    // Show loading state
    const tbody = document.querySelector('#eventsTable tbody');
    tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2">Cargando eventos...</p>
            </td>
        </tr>
    `;
    
    // Simulate API delay
    setTimeout(() => {
        // Generate mock events
        const mockEvents = generateMockEvents();
        
        // Populate table
        populateEventsTable(mockEvents);
        
        // Update DataTable
        if (window.eventsTable) {
            window.eventsTable.clear().rows.add(mockEvents.map(formatEventForDataTable)).draw();
        }
    }, 1500);
}

function generateMockEvents() {
    const eventTypes = [
        { type: 'vehicle_parked', icon: 'fas fa-parking', color: 'success', text: 'Vehículo Estacionado' },
        { type: 'vehicle_left', icon: 'fas fa-car-rear', color: 'info', text: 'Vehículo Retirado' },
        { type: 'plate_detected', icon: 'fas fa-license', color: 'warning', text: 'Placa Detectada' },
        { type: 'camera_offline', icon: 'fas fa-video-slash', color: 'danger', text: 'Cámara Desconectada' },
        { type: 'system_alert', icon: 'fas fa-exclamation-triangle', color: 'warning', text: 'Alerta del Sistema' }
    ];
    
    const cameras = [
        { id: 1, name: 'Entrada Principal' },
        { id: 2, name: 'Parqueo Norte' },
        { id: 3, name: 'Parqueo Sur' },
        { id: 4, name: 'Salida Principal' }
    ];
    
    const descriptions = [
        'Vehículo detectado estacionado por más de 30 minutos',
        'Vehículo detectado saliendo del área de estacionamiento',
        'Placa de vehículo leída correctamente',
        'Cámara no responde a las solicitudes de conexión',
        'Temperatura del servidor por encima del umbral',
        'Movimiento detectado fuera del horario laboral',
        'Intento de acceso no autorizado detectado',
        'Error en el algoritmo de detección de placas'
    ];
    
    const plates = ['ABC-123', 'XYZ-789', 'DEF-456', 'GHI-012', 'JKL-345', 'MNO-678'];
    
    const events = [];
    const now = new Date();
    
    // Generate 50 random events from the last 7 days
    for (let i = 0; i < 50; i++) {
        const daysAgo = Math.floor(Math.random() * 7);
        const hoursAgo = Math.floor(Math.random() * 24);
        const minutesAgo = Math.floor(Math.random() * 60);
        
        const eventDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000) - (hoursAgo * 60 * 60 * 1000) - (minutesAgo * 60 * 1000));
        
        const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
        const camera = cameras[Math.floor(Math.random() * cameras.length)];
        const description = descriptions[Math.floor(Math.random() * descriptions.length)];
        const plate = eventType.type === 'plate_detected' ? plates[Math.floor(Math.random() * plates.length)] : null;
        
        events.push({
            id: i + 1,
            timestamp: eventDate,
            type: eventType.type,
            typeIcon: eventType.icon,
            typeColor: eventType.color,
            typeText: eventType.text,
            description: description,
            cameraId: camera.id,
            cameraName: camera.name,
            licensePlate: plate,
            userId: Math.floor(Math.random() * 5) + 1,
            userName: `Usuario ${Math.floor(Math.random() * 5) + 1}`
        });
    }
    
    // Sort by date descending
    events.sort((a, b) => b.timestamp - a.timestamp);
    
    return events;
}

function formatEventForDataTable(event) {
    // Format date for display
    const date = new Date(event.timestamp);
    const formattedDate = date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    // Format type badge
    const typeBadge = `<span class="badge bg-${event.typeColor}">${event.typeText}</span>`;
    
    // Format license plate
    const plateDisplay = event.licensePlate ? `<span class="badge bg-info">${event.licensePlate}</span>` : '-';
    
    // Format actions
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
        event.description,
        event.cameraName,
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
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Function to show notifications
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '1050';
    notification.innerHTML = `
        <i class="fas fa-info-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Change icon based on type
    if (type === 'success') {
        notification.querySelector('i').className = 'fas fa-check-circle me-2';
    } else if (type === 'danger') {
        notification.querySelector('i').className = 'fas fa-exclamation-triangle me-2';
    } else if (type === 'warning') {
        notification.querySelector('i').className = 'fas fa-exclamation-circle me-2';
    }
    
    // Add to document
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Export functionality
document.getElementById('exportBtn').addEventListener('click', function() {
    showNotification('Funcionalidad de exportación en desarrollo', 'info');
    
    // In a real implementation, this would:
    // 1. Get current filtered data from DataTable
    // 2. Generate CSV or Excel file
    // 3. Trigger download
});

// Refresh button functionality
document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-refresh')) {
        e.preventDefault();
        loadEvents();
        showNotification('Eventos actualizados', 'success');
    }
});