// Settings Page JavaScript for Vehicle Detection System

let settingsState = {
    configs: []
};

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('settings');
    initSettingsPage();
});

function initSettingsPage() {
    setupConfigModal();
    setupWhatsAppForms();

    document.getElementById('newConfigBtn').addEventListener('click', function() {
        openConfigModal();
    });
    document.getElementById('initDefaultsBtn').addEventListener('click', function() {
        initializeDefaults();
    });

    loadConfigs();
    loadWhatsAppStatus();
}

// ---- System config ----

function loadConfigs() {
    API.getConfigs().then(function(configs) {
        settingsState.configs = configs;
        renderConfigs();
    }).catch(function(err) {
        console.error('Failed to load configs:', err);
        renderConfigsError(err.message || err);
    });
}

function renderConfigsError(message) {
    const tbody = document.querySelector('#configsTable tbody');
    if (!tbody) return;
    tbody.innerHTML = `
        <tr>
            <td colspan="4" class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-muted mb-3"></i>
                <p class="text-muted">Error al cargar la configuración: ${Common.escapeHtml(message)}</p>
            </td>
        </tr>
    `;
}

function renderConfigs() {
    const tbody = document.querySelector('#configsTable tbody');
    if (!tbody) return;

    const configs = settingsState.configs;

    if (!configs || configs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-4">
                    <i class="fas fa-cog fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay configuraciones. Haga clic en "Inicializar Defaults".</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    configs.forEach(function(config) {
        const value = typeof config.value === 'object' && config.value !== null
            ? JSON.stringify(config.value)
            : String(config.value);

        html += `
            <tr>
                <td><code>${Common.escapeHtml(config.key)}</code></td>
                <td>${Common.escapeHtml(value)}</td>
                <td class="text-muted">${Common.escapeHtml(config.description || '-')}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-secondary btn-edit-config" data-id="${config.id}" title="Editar"><i class="fas fa-edit"></i></button>
                        <button type="button" class="btn btn-outline-danger btn-delete-config" data-id="${config.id}" title="Eliminar"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    tbody.querySelectorAll('.btn-edit-config').forEach(function(btn) {
        btn.addEventListener('click', function() {
            openConfigModal(this.getAttribute('data-id'));
        });
    });
    tbody.querySelectorAll('.btn-delete-config').forEach(function(btn) {
        btn.addEventListener('click', function() {
            deleteConfig(this.getAttribute('data-id'));
        });
    });
}

function setupConfigModal() {
    const form = document.getElementById('configForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveConfig();
        });
    }
}

function openConfigModal(configId) {
    const title = document.getElementById('configModalTitle');
    const form = document.getElementById('configForm');
    form.reset();

    if (configId) {
        const config = settingsState.configs.find(function(c) { return c.id === configId; });
        if (config) {
            title.textContent = 'Editar Configuración';
            document.getElementById('configId').value = config.id;
            document.getElementById('configKey').value = config.key;
            document.getElementById('configKey').disabled = true;
            document.getElementById('configValue').value = typeof config.value === 'object'
                ? JSON.stringify(config.value)
                : String(config.value);
            document.getElementById('configDescription').value = config.description || '';
        }
    } else {
        title.textContent = 'Nueva Configuración';
        document.getElementById('configId').value = '';
        document.getElementById('configKey').disabled = false;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('configModal'));
    modal.show();
}

function parseConfigValue(raw) {
    const trimmed = raw.trim();
    try {
        return JSON.parse(trimmed);
    } catch (e) {
        // Not valid JSON: keep as string (numbers/booleans remain strings)
        return trimmed;
    }
}

function saveConfig() {
    const configId = document.getElementById('configId').value;
    const key = document.getElementById('configKey').value.trim();
    const value = parseConfigValue(document.getElementById('configValue').value);

    if (!key) {
        Common.showNotification('La clave es obligatoria', 'warning');
        return;
    }

    const saveBtn = document.getElementById('saveConfigBtn');
    saveBtn.disabled = true;

    const promise = configId
        ? API.updateConfig(configId, { value: value, description: document.getElementById('configDescription').value.trim() || null })
        : API.createConfig({ key: key, value: value, description: document.getElementById('configDescription').value.trim() || null });

    promise.then(function() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('configModal'));
        if (modal) modal.hide();
        Common.showNotification(configId ? 'Configuración actualizada' : 'Configuración creada', 'success');
        loadConfigs();
    }).catch(function(err) {
        Common.showNotification('Error al guardar: ' + (err.message || err), 'danger');
    }).finally(function() {
        saveBtn.disabled = false;
    });
}

function deleteConfig(configId) {
    const config = settingsState.configs.find(function(c) { return c.id === configId; });
    const key = config ? config.key : configId;
    if (!confirm('¿Está seguro de que desea eliminar la configuración "' + key + '"?')) return;

    API.deleteConfig(configId).then(function() {
        Common.showNotification('Configuración eliminada', 'success');
        loadConfigs();
    }).catch(function(err) {
        Common.showNotification('Error al eliminar: ' + (err.message || err), 'danger');
    });
}

function initializeDefaults() {
    if (!confirm('¿Inicializar las configuraciones por defecto? (no sobrescribe las existentes)')) return;

    API.initializeDefaultConfigs().then(function(result) {
        Common.showNotification(result.message || 'Configuraciones por defecto inicializadas', 'success');
        loadConfigs();
    }).catch(function(err) {
        Common.showNotification('Error al inicializar: ' + (err.message || err), 'danger');
    });
}

// ---- WhatsApp ----

function setupWhatsAppForms() {
    const configForm = document.getElementById('whatsappConfigForm');
    if (configForm) {
        configForm.addEventListener('submit', function(e) {
            e.preventDefault();
            configureWhatsApp();
        });
    }

    const sendForm = document.getElementById('whatsappSendForm');
    if (sendForm) {
        sendForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendWhatsAppMessage();
        });
    }

    document.getElementById('testWhatsAppBtn').addEventListener('click', function() {
        testWhatsAppConnection();
    });
}

function loadWhatsAppStatus() {
    API.getWhatsAppStatus().then(function(status) {
        const el = document.getElementById('whatsappStatus');
        if (!el) return;
        if (status.configured) {
            const state = status.connection_state || 'desconocido';
            const stateBadge = status.connected
                ? '<span class="badge bg-success">Conectado</span>'
                : `<span class="badge bg-secondary">${Common.escapeHtml(String(state).toUpperCase())}</span>`;
            el.className = 'alert alert-success';
            el.innerHTML = `<i class="fas fa-check-circle me-2"></i>
                WhatsApp configurado — Instancia: <strong>${Common.escapeHtml(status.instance_name)}</strong> · API: <code>${Common.escapeHtml(status.api_url)}</code> ${stateBadge}`;
            document.getElementById('whatsappApiUrl').value = status.api_url || '';
            document.getElementById('whatsappInstance').value = status.instance_name || '';
        } else {
            el.className = 'alert alert-warning';
            el.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>' +
                Common.escapeHtml(status.message || 'WhatsApp no configurado');
        }
    }).catch(function(err) {
        const el = document.getElementById('whatsappStatus');
        if (el) {
            el.className = 'alert alert-danger';
            el.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error al consultar el estado: ' + Common.escapeHtml(err.message || err);
        }
    });
}

function configureWhatsApp() {
    const data = {
        api_url: document.getElementById('whatsappApiUrl').value.trim(),
        api_key: document.getElementById('whatsappApiKey').value.trim(),
        instance_name: document.getElementById('whatsappInstance').value.trim()
    };

    if (!data.api_url || !data.api_key || !data.instance_name) {
        Common.showNotification('Todos los campos de WhatsApp son obligatorios', 'warning');
        return;
    }

    const btn = document.getElementById('configureWhatsAppBtn');
    btn.disabled = true;

    API.configureWhatsApp(data).then(function(result) {
        Common.showNotification(result.message || 'Configuración de WhatsApp guardada', 'success');
        loadWhatsAppStatus();
    }).catch(function(err) {
        Common.showNotification('Error al configurar: ' + (err.message || err), 'danger');
    }).finally(function() {
        btn.disabled = false;
    });
}

function testWhatsAppConnection() {
    const btn = document.getElementById('testWhatsAppBtn');
    btn.disabled = true;

    API.testWhatsApp().then(function(result) {
        if (result && result.success) {
            Common.showNotification('Conexión a WhatsApp exitosa', 'success');
        } else {
            Common.showNotification((result && result.error) || 'La conexión no fue exitosa', 'warning');
        }
    }).catch(function(err) {
        Common.showNotification('Error en la prueba: ' + (err.message || err), 'danger');
    }).finally(function() {
        btn.disabled = false;
    });
}

function sendWhatsAppMessage() {
    const data = {
        phone_number: document.getElementById('whatsappPhone').value.trim(),
        message: document.getElementById('whatsappMessage').value.trim() || 'Mensaje de prueba desde Vehicle Detection System'
    };

    if (!data.phone_number) {
        Common.showNotification('Ingrese un número de teléfono', 'warning');
        return;
    }

    const btn = document.getElementById('sendWhatsAppBtn');
    btn.disabled = true;

    API.sendWhatsAppMessage(data).then(function() {
        Common.showNotification('Mensaje encolado para envío', 'success');
        document.getElementById('whatsappMessage').value = '';
    }).catch(function(err) {
        Common.showNotification('Error al enviar: ' + (err.message || err), 'danger');
    }).finally(function() {
        btn.disabled = false;
    });
}
