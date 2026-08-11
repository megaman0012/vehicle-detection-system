// Shared utilities for Vehicle Detection System frontend
// Loaded in every page. Requires js/api.js to be loaded first.

const Common = (function() {

    function requireAuth() {
        return API.requireAuth();
    }

    function initSidebar(activePage) {
        const menuToggle = document.getElementById('menu-toggle');
        const wrapper = document.getElementById('wrapper');

        if (menuToggle && wrapper) {
            menuToggle.addEventListener('click', function(e) {
                e.preventDefault();
                wrapper.classList.toggle('toggled');
            });
        }

        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                API.logout();
            });
        }

        const user = API.getStoredUser();
        const userFullName = document.getElementById('userFullName');
        if (userFullName) {
            userFullName.innerHTML = '<i class="fas fa-user me-2"></i>' +
                (user && user.full_name ? escapeHtml(user.full_name) : 'Administrador');
        }

        if (activePage) {
            document.querySelectorAll('[data-page]').forEach(function(el) {
                el.classList.remove('active');
                if (el.getAttribute('data-page') === activePage) {
                    el.classList.add('active');
                }
            });
        }
    }

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '1050';
        notification.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            ${escapeHtml(message)}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        if (type === 'success') {
            notification.querySelector('i').className = 'fas fa-check-circle me-2';
        } else if (type === 'danger') {
            notification.querySelector('i').className = 'fas fa-exclamation-triangle me-2';
        } else if (type === 'warning') {
            notification.querySelector('i').className = 'fas fa-exclamation-circle me-2';
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    function escapeHtml(value) {
        if (value === undefined || value === null) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatDateTime(iso) {
        if (!iso) return '-';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '-';
        return d.toLocaleString('es-ES', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
    }

    function formatDate(iso) {
        if (!iso) return '-';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '-';
        return d.toLocaleDateString('es-ES', {
            year: 'numeric', month: '2-digit', day: '2-digit'
        });
    }

    function formatDuration(seconds) {
        if (seconds === null || seconds === undefined) return '-';
        seconds = Math.round(seconds);
        if (isNaN(seconds)) return '-';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (h > 0) return `${h}h ${m}m`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    }

    return {
        requireAuth: requireAuth,
        initSidebar: initSidebar,
        showNotification: showNotification,
        escapeHtml: escapeHtml,
        formatDateTime: formatDateTime,
        formatDate: formatDate,
        formatDuration: formatDuration
    };
})();
