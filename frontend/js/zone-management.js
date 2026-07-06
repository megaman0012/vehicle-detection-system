// Zone Management JavaScript for Vehicle Detection System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize zone management functionality
    initializeZoneManagement();
});

function initializeZoneManagement() {
    // Set up drawing tools for zones
    const drawZoneButtons = document.querySelectorAll('[data-action="draw-zone"]');
    drawZoneButtons.forEach(button => {
        button.addEventListener('click', function() {
            const cameraId = this.getAttribute('data-camera-id');
            startZoneDrawing(cameraId);
        });
    });
    
    // Set up edit zone buttons
    const editZoneButtons = document.querySelectorAll('[data-action="edit-zone"]');
    editZoneButtons.forEach(button => {
        button.addEventListener('click', function() {
            const zoneId = this.getAttribute('data-zone-id');
            editZone(zoneId);
        });
    });
    
    // Set up delete zone buttons
    const deleteZoneButtons = document.querySelectorAll('[data-action="delete-zone"]');
    deleteZoneButtons.forEach(button => {
        button.addEventListener('click', function() {
            const zoneId = this.getAttribute('data-zone-id');
            deleteZone(zoneId);
        });
    });
}

function startZoneDrawing(cameraId) {
    // In a real implementation, this would:
    // 1. Display the camera feed in a modal
    // 2. Allow user to draw a polygon on the video
    // 3. Save the coordinates to the database via API
    
    console.log(`Starting zone drawing for camera ${cameraId}`);
    
    // Show modal for drawing zone
    showZoneDrawingModal(cameraId);
}

function showZoneDrawingModal(cameraId) {
    // Create modal for drawing zone
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
    
    // Add modal to document
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // Initialize modal
    const zoneDrawingModal = new bootstrap.Modal(document.getElementById('zoneDrawingModal'));
    zoneDrawingModal.show();
    
    // Set up drawing functionality
    setupZoneDrawing(cameraId);
    
    // Clean up modal when hidden
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
    
    // Set canvas size to match container
    function resizeCanvas() {
        canvas.width = feedContainer.clientWidth;
        canvas.height = feedContainer.clientHeight;
    }
    
    // Initial resize
    resizeCanvas();
    
    // Resize on window resize
    window.addEventListener('resize', resizeCanvas);
    
    // Drawing state
    let isDrawing = false;
    let points = [];
    let lastPoint = null;
    
    // Get drawing context
    const ctx = canvas.getContext('2d');
    
    // Set up drawing style
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';
    
    // Mouse event handlers
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
        
        // Draw line from last point to current point
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
        
        // Add final point
        points.push({x, y});
        lastPoint = {x, y};
        
        // Complete the shape by connecting last point to first point
        if (points.length > 2) {
            ctx.beginPath();
            ctx.moveTo(points[points.length - 1].x, points[points.length - 1].y);
            ctx.lineTo(points[0].x, points[0].y);
            ctx.stroke();
            
            // Fill the polygon
            ctx.fill();
        }
    });
    
    // Touch event handlers for mobile
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
        
        // Draw line from last point to current point
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
            
            // Add final point
            points.push({x, y});
            lastPoint = {x, y};
            
            // Complete the shape by connecting last point to first point
            if (points.length > 2) {
                ctx.beginPath();
                ctx.moveTo(points[points.length - 1].x, points[points.length - 1].y);
                ctx.lineTo(points[0].x, points[0].y);
                ctx.stroke();
                
                // Fill the polygon
                ctx.fill();
            }
        }
    });
    
    // Clear drawing
    document.getElementById('clearZoneBtn').addEventListener('click', function() {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        points = [];
        lastPoint = null;
    });
    
    // Save zone
    document.getElementById('saveZoneBtn').addEventListener('click', function() {
        if (points.length < 3) {
            showNotification('Se necesitan al menos 3 puntos para definir una zona', 'warning');
            return;
        }
        
        // Convert points to coordinate format
        const coordinates = points.map(point => [Math.round(point.x), Math.round(point.y)]);
        
        // In a real implementation, this would send the data to the backend API
        console.log('Saving zone for camera', cameraId, 'with coordinates:', coordinates);
        
        // Show success message
        showNotification('Zona guardada correctamente', 'success');
        
        // Close modal
        const zoneDrawingModal = bootstrap.Modal.getInstance(document.getElementById('zoneDrawingModal'));
        zoneDrawingModal.hide();
        
        // In a real implementation, you would refresh the zone list here
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
    showNotification(`Funcionalidad de edición de zona ${zoneId} en desarrollo`, 'info');
}

function deleteZone(zoneId) {
    if (confirm(`¿Está seguro de que desea eliminar la zona ${zoneId}?`)) {
        console.log(`Deleting zone ${zoneId}`);
        // In a real implementation, this would send a DELETE request to the API
        showNotification(`Zona ${zoneId} eliminada correctamente`, 'success');
        
        // Remove zone from UI (in a real implementation, this would come from API response)
        const zoneElement = document.querySelector(`[data-zone-id="${zoneId}"]`);
        if (zoneElement) {
            const card = zoneElement.closest('.card');
            if (card) {
                card.remove();
            }
        }
    }
}

// Function to show notifications (reuse from main.js or define here)
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