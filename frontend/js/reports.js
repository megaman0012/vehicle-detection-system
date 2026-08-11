// Reports Page JavaScript for Vehicle Detection System

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('reports');
    initReportsPage();
});

function initReportsPage() {
    // Implemented in step 5 (stats + PDF/Excel download)
}
