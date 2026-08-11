// API client for Vehicle Detection System
// Talks to the backend through the nginx proxy (/api -> backend:8000).

const API = (function() {
    const TOKEN_KEY = 'vds_access_token';
    const REFRESH_KEY = 'vds_refresh_token';
    const USER_KEY = 'vds_user';

    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    function getRefreshToken() {
        return localStorage.getItem(REFRESH_KEY);
    }

    function getStoredUser() {
        const raw = localStorage.getItem(USER_KEY);
        if (!raw) return null;
        try {
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function storeSession(tokens, user) {
        localStorage.setItem(TOKEN_KEY, tokens.access_token);
        localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
        if (user) {
            localStorage.setItem(USER_KEY, JSON.stringify(user));
        }
    }

    function clearSession() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        localStorage.removeItem(USER_KEY);
    }

    function redirectToLogin() {
        const current = window.location.pathname;
        if (!current.endsWith('login.html')) {
            window.location.href = 'login.html';
        }
    }

    async function request(path, options) {
        options = options || {};
        const headers = Object.assign({}, options.headers || {});
        const token = getToken();
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }
        if (options.body && typeof options.body !== 'string' && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        const resp = await fetch(path, Object.assign({}, options, { headers: headers }));

        if (resp.status === 401) {
            // Try to refresh once
            const refreshed = await tryRefresh();
            if (!refreshed) {
                clearSession();
                redirectToLogin();
                throw new Error('No autenticado');
            }
            // Retry original request with new token
            headers['Authorization'] = 'Bearer ' + getToken();
            const retryResp = await fetch(path, Object.assign({}, options, { headers: headers }));
            return parseResponse(retryResp);
        }

        return parseResponse(resp);
    }

    async function tryRefresh() {
        const refreshToken = getRefreshToken();
        if (!refreshToken) return false;
        try {
            const resp = await fetch('/api/auth/refresh?refresh_token=' + encodeURIComponent(refreshToken), {
                method: 'POST'
            });
            if (!resp.ok) return false;
            const data = await resp.json();
            localStorage.setItem(TOKEN_KEY, data.access_token);
            localStorage.setItem(REFRESH_KEY, data.refresh_token);
            return true;
        } catch (e) {
            return false;
        }
    }

    async function parseResponse(resp) {
        if (resp.status === 204) {
            return null;
        }
        const contentType = resp.headers.get('Content-Type') || '';
        const isJson = contentType.indexOf('application/json') !== -1;
        const body = isJson ? await resp.json() : await resp.text();

        if (!resp.ok) {
            const detail = body && body.detail ? body.detail : 'Error de servidor';
            const error = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
            error.status = resp.status;
            throw error;
        }
        return body;
    }

    function qs(params) {
        const search = new URLSearchParams();
        Object.keys(params).forEach(function(key) {
            const value = params[key];
            if (value !== undefined && value !== null && value !== '') {
                search.append(key, value);
            }
        });
        const s = search.toString();
        return s ? '?' + s : '';
    }

    async function login(username, password) {
        const form = new URLSearchParams();
        form.append('username', username);
        form.append('password', password);

        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: form.toString()
        });

        const data = await parseResponse(resp);
        storeSession(data, null);

        // Load current user profile
        try {
            const me = await request('/api/auth/me');
            localStorage.setItem(USER_KEY, JSON.stringify(me));
        } catch (e) {
            // Non-fatal: token already stored
        }
        return data;
    }

    function logout() {
        clearSession();
        window.location.href = 'login.html';
    }

    function isAuthenticated() {
        return !!getToken();
    }

    function requireAuth() {
        if (!isAuthenticated()) {
            redirectToLogin();
            return false;
        }
        return true;
    }

    // ---- Endpoints ----

    function getCameras(params) {
        return request('/api/cameras/' + qs(params || {}));
    }

    function createCamera(data) {
        return request('/api/cameras/', { method: 'POST', body: data });
    }

    function updateCamera(cameraId, data) {
        return request('/api/cameras/' + cameraId, { method: 'PUT', body: data });
    }

    function deleteCamera(cameraId) {
        return request('/api/cameras/' + cameraId, { method: 'DELETE' });
    }

    function getVehicles(params) {
        return request('/api/vehicles/' + qs(params || {}));
    }

    function getParkedVehicles() {
        return request('/api/vehicles/parked/current');
    }

    function getEvents(params) {
        return request('/api/events/' + qs(params || {}));
    }

    function getRecentEvents(hours) {
        return request('/api/events/recent' + qs({ hours: hours || 24 }));
    }

    function getZones() {
        return request('/api/zones/');
    }

    function createZone(data) {
        return request('/api/zones/', { method: 'POST', body: data });
    }

    function updateZone(zoneId, data) {
        return request('/api/zones/' + zoneId, { method: 'PUT', body: data });
    }

    function deleteZone(zoneId) {
        return request('/api/zones/' + zoneId, { method: 'DELETE' });
    }

    function getSystemStatus() {
        return request('/api/system/status');
    }

    function getSystemMetrics() {
        return request('/api/system/metrics');
    }

    function getStats(days) {
        return request('/api/reports/stats' + qs({ days: days || 30 }));
    }

    function getConfigs() {
        return request('/api/config/');
    }

    function createConfig(data) {
        return request('/api/config/', { method: 'POST', body: data });
    }

    function updateConfig(configId, data) {
        return request('/api/config/' + configId, { method: 'PUT', body: data });
    }

    function deleteConfig(configId) {
        return request('/api/config/' + configId, { method: 'DELETE' });
    }

    function initializeDefaultConfigs() {
        return request('/api/config/initialize-defaults', { method: 'POST', body: {} });
    }

    function getWhatsAppStatus() {
        return request('/api/whatsapp/status');
    }

    function configureWhatsApp(data) {
        return request('/api/whatsapp/configure', { method: 'POST', body: data });
    }

    function testWhatsApp() {
        return request('/api/whatsapp/test', { method: 'POST', body: {} });
    }

    function sendWhatsAppMessage(data) {
        return request('/api/whatsapp/send-message', { method: 'POST', body: data });
    }

    function getUsers() {
        return request('/api/users/');
    }

    function createUser(data) {
        return request('/api/users/', { method: 'POST', body: data });
    }

    function updateUser(userId, data) {
        return request('/api/users/' + userId, { method: 'PUT', body: data });
    }

    function deleteUser(userId) {
        return request('/api/users/' + userId, { method: 'DELETE' });
    }

    function getCurrentUser() {
        return request('/api/auth/me');
    }

    // ---- Report downloads (binary) ----

    async function downloadReport(path, filename) {
        const headers = {};
        const token = getToken();
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }
        const resp = await fetch(path, { headers: headers });
        if (!resp.ok) {
            let detail = 'Error al descargar el archivo';
            try {
                const body = await resp.json();
                if (body && body.detail) detail = body.detail;
            } catch (e) { /* keep default */ }
            const error = new Error(detail);
            error.status = resp.status;
            throw error;
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    }

    // ---- AI service (proxied through /ai/*) ----

    function aiGetStatus() {
        return request('/ai/api/detection/status');
    }

    function aiStartCamera(cameraId, data) {
        return request('/ai/api/detection/cameras/' + cameraId + '/start', { method: 'POST', body: data });
    }

    function aiStopCamera(cameraId) {
        return request('/ai/api/detection/cameras/' + cameraId + '/stop', { method: 'POST', body: {} });
    }

    function aiGetCameraResults(cameraId) {
        return request('/ai/api/detection/cameras/' + cameraId + '/results');
    }

    return {
        getToken: getToken,
        getStoredUser: getStoredUser,
        login: login,
        logout: logout,
        isAuthenticated: isAuthenticated,
        requireAuth: requireAuth,
        getCameras: getCameras,
        createCamera: createCamera,
        updateCamera: updateCamera,
        deleteCamera: deleteCamera,
        getVehicles: getVehicles,
        getParkedVehicles: getParkedVehicles,
        getEvents: getEvents,
        getRecentEvents: getRecentEvents,
        getZones: getZones,
        createZone: createZone,
        updateZone: updateZone,
        deleteZone: deleteZone,
        getSystemStatus: getSystemStatus,
        getSystemMetrics: getSystemMetrics,
        getStats: getStats,
        getConfigs: getConfigs,
        createConfig: createConfig,
        updateConfig: updateConfig,
        deleteConfig: deleteConfig,
        initializeDefaultConfigs: initializeDefaultConfigs,
        getWhatsAppStatus: getWhatsAppStatus,
        configureWhatsApp: configureWhatsApp,
        testWhatsApp: testWhatsApp,
        sendWhatsAppMessage: sendWhatsAppMessage,
        getUsers: getUsers,
        createUser: createUser,
        updateUser: updateUser,
        deleteUser: deleteUser,
        getCurrentUser: getCurrentUser,
        aiGetStatus: aiGetStatus,
        aiStartCamera: aiStartCamera,
        aiStopCamera: aiStopCamera,
        aiGetCameraResults: aiGetCameraResults,
        downloadReport: downloadReport
    };
})();
