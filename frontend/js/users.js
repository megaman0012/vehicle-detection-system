// Users Page JavaScript for Vehicle Detection System

let usersState = {
    users: []
};

document.addEventListener('DOMContentLoaded', function() {
    if (!Common.requireAuth()) {
        return;
    }
    Common.initSidebar('users');
    initUsersPage();
});

function initUsersPage() {
    setupUserModal();

    document.getElementById('newUserBtn').addEventListener('click', function() {
        openUserModal();
    });

    loadUsers();
}

// ---- Loading ----

function loadUsers() {
    API.getUsers().then(function(users) {
        usersState.users = users;
        renderUsers();
    }).catch(function(err) {
        console.error('Failed to load users:', err);
        renderUsersError(err.message || err);
    });
}

function renderUsersError(message) {
    const tbody = document.querySelector('#usersTable tbody');
    if (!tbody) return;
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-muted mb-3"></i>
                <p class="text-muted">Error al cargar los usuarios: ${Common.escapeHtml(message)}</p>
            </td>
        </tr>
    `;
}

const ROLE_BADGES = {
    admin: { badge: 'bg-danger', text: 'Administrador' },
    operator: { badge: 'bg-info', text: 'Operador' },
    user: { badge: 'bg-secondary', text: 'Usuario' }
};

function renderUsers() {
    const tbody = document.querySelector('#usersTable tbody');
    if (!tbody) return;

    const users = usersState.users;

    if (!users || users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay usuarios registrados.</p>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    users.forEach(function(user) {
        const r = ROLE_BADGES[user.role] || ROLE_BADGES.user;
        const activeBadge = user.is_active
            ? '<span class="badge bg-success">Activo</span>'
            : '<span class="badge bg-danger">Inactivo</span>';

        html += `
            <tr>
                <td><i class="fas fa-user me-2 text-primary"></i>${Common.escapeHtml(user.username)}</td>
                <td>${Common.escapeHtml(user.full_name || '-')}</td>
                <td>${Common.escapeHtml(user.email)}</td>
                <td><span class="badge ${r.badge}">${r.text}</span></td>
                <td>${activeBadge}</td>
                <td class="text-muted">${Common.formatDate(user.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-secondary btn-edit-user" data-id="${user.id}" title="Editar"><i class="fas fa-edit"></i></button>
                        <button type="button" class="btn btn-outline-danger btn-delete-user" data-id="${user.id}" title="Eliminar"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    tbody.querySelectorAll('.btn-edit-user').forEach(function(btn) {
        btn.addEventListener('click', function() {
            openUserModal(this.getAttribute('data-id'));
        });
    });
    tbody.querySelectorAll('.btn-delete-user').forEach(function(btn) {
        btn.addEventListener('click', function() {
            deleteUser(this.getAttribute('data-id'));
        });
    });
}

// ---- Modal (create/edit) ----

function setupUserModal() {
    const form = document.getElementById('userForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveUser();
        });
    }
}

function openUserModal(userId) {
    const title = document.getElementById('userModalTitle');
    const form = document.getElementById('userForm');
    form.reset();
    document.getElementById('userActive').checked = true;
    document.getElementById('userRole').value = 'user';

    if (userId) {
        const user = usersState.users.find(function(u) { return u.id === userId; });
        if (user) {
            title.textContent = 'Editar Usuario';
            document.getElementById('userId').value = user.id;
            document.getElementById('userUsername').value = user.username;
            document.getElementById('userUsername').disabled = true;
            document.getElementById('userFullName').value = user.full_name || '';
            document.getElementById('userEmail').value = user.email;
            document.getElementById('userRole').value = user.role || 'user';
            document.getElementById('userActive').checked = !!user.is_active;
            document.getElementById('userPasswordField').style.display = 'none';
            document.getElementById('userPassword').removeAttribute('required');
        }
    } else {
        title.textContent = 'Nuevo Usuario';
        document.getElementById('userId').value = '';
        document.getElementById('userUsername').disabled = false;
        document.getElementById('userPasswordField').style.display = '';
        document.getElementById('userPassword').setAttribute('required', 'required');
    }

    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('userModal'));
    modal.show();
}

function saveUser() {
    const userId = document.getElementById('userId').value;
    const data = {
        username: document.getElementById('userUsername').value.trim(),
        full_name: document.getElementById('userFullName').value.trim() || null,
        email: document.getElementById('userEmail').value.trim(),
        role: document.getElementById('userRole').value,
        is_active: document.getElementById('userActive').checked
    };

    if (!data.username || !data.email) {
        Common.showNotification('Usuario y email son obligatorios', 'warning');
        return;
    }

    const saveBtn = document.getElementById('saveUserBtn');
    saveBtn.disabled = true;

    const promise = userId
        ? API.updateUser(userId, data)
        : API.createUser(Object.assign({}, data, { password: document.getElementById('userPassword').value }));

    promise.then(function() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('userModal'));
        if (modal) modal.hide();
        Common.showNotification(userId ? 'Usuario actualizado' : 'Usuario creado', 'success');
        loadUsers();
    }).catch(function(err) {
        Common.showNotification('Error al guardar: ' + (err.message || err), 'danger');
    }).finally(function() {
        saveBtn.disabled = false;
    });
}

function deleteUser(userId) {
    const user = usersState.users.find(function(u) { return u.id === userId; });
    const name = user ? user.username : userId;
    if (!confirm('¿Está seguro de que desea eliminar el usuario "' + name + '"?')) return;

    API.deleteUser(userId).then(function() {
        Common.showNotification('Usuario eliminado', 'success');
        loadUsers();
    }).catch(function(err) {
        Common.showNotification('Error al eliminar: ' + (err.message || err), 'danger');
    });
}
