// Reports Page JavaScript for Vehicle Detection System

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('reports');
    initReportsPage();
});

function initReportsPage() {
    loadStats();
    setupReportForm();
    setInterval(loadStats, 30000);
}

// ---- Statistics ----

function loadStats() {
    API.getStats(30).then(function(stats) {
        setText('stat-total-events', stats.total_events);
        setText('stat-events-30d', stats.events_last_30_days);
        setText('stat-total-vehicles', stats.total_vehicles_detected);
        setText('stat-parked-now', stats.currently_parked);
    }).catch(function(err) {
        console.error('Failed to load stats:', err);
    });
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value === null || value === undefined ? '-' : value;
    }
}

// ---- Report generation ----

function setupReportForm() {
    const typeSelect = document.getElementById('reportType');
    if (typeSelect) {
        typeSelect.addEventListener('change', function() {
            toggleReportFields(this.value);
        });
    }

    const form = document.getElementById('reportForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            generateReport();
        });
    }

    // Default to today / current month
    const today = new Date();
    const iso = today.toISOString().split('T')[0];
    document.getElementById('reportDailyDate').value = iso;
    document.getElementById('reportWeeklyDate').value = iso;
    document.getElementById('reportMonthlyDate').value = iso.slice(0, 7);
}

function toggleReportFields(type) {
    document.getElementById('reportDailyField').style.display = type === 'daily' ? '' : 'none';
    document.getElementById('reportWeeklyField').style.display = type === 'weekly' ? '' : 'none';
    document.getElementById('reportMonthlyField').style.display = type === 'monthly' ? '' : 'none';
}

function generateReport() {
    const type = document.getElementById('reportType').value;
    const format = document.getElementById('reportFormat').value;

    let path = '';
    let filename = '';

    if (type === 'daily') {
        const date = document.getElementById('reportDailyDate').value;
        if (!date) {
            Common.showNotification('Seleccione una fecha', 'warning');
            return;
        }
        path = '/api/reports/daily?date=' + date + '&format=' + format;
        filename = 'daily_report_' + date + '.' + (format === 'excel' ? 'xlsx' : 'pdf');
    } else if (type === 'weekly') {
        const date = document.getElementById('reportWeeklyDate').value;
        if (!date) {
            Common.showNotification('Seleccione la fecha de inicio de la semana', 'warning');
            return;
        }
        path = '/api/reports/weekly?start_date=' + date + '&format=' + format;
        filename = 'weekly_report_' + date + '.' + (format === 'excel' ? 'xlsx' : 'pdf');
    } else {
        const month = document.getElementById('reportMonthlyDate').value;
        if (!month) {
            Common.showNotification('Seleccione un mes', 'warning');
            return;
        }
        const parts = month.split('-');
        path = '/api/reports/monthly?year=' + parts[0] + '&month=' + parts[1] + '&format=' + format;
        filename = 'monthly_report_' + month + '.' + (format === 'excel' ? 'xlsx' : 'pdf');
    }

    const btn = document.getElementById('generateReportBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando...';

    API.downloadReport(path, filename).then(function() {
        Common.showNotification('Reporte generado correctamente', 'success');
    }).catch(function(err) {
        Common.showNotification('Error al generar el reporte: ' + (err.message || err), 'danger');
    }).finally(function() {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-download me-1"></i> Generar y Descargar';
    });
}
