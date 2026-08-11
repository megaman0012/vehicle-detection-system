// Parking Page JavaScript for Vehicle Detection System

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('parking');
    initParkingPage();
});

function initParkingPage() {
    // Implemented in step 4 (zones + parked vehicles)
}
