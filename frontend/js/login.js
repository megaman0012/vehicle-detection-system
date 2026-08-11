// Login page JavaScript for Vehicle Detection System

document.addEventListener('DOMContentLoaded', function() {
    // If already authenticated, go straight to dashboard
    if (API.isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    const form = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const alertBox = document.getElementById('loginAlert');
    const loginBtn = document.getElementById('loginBtn');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        alertBox.classList.add('d-none');

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            showError('Por favor ingrese usuario y contraseña');
            return;
        }

        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Ingresando...';

        try {
            await API.login(username, password);
            window.location.href = 'index.html';
        } catch (err) {
            let message = 'Error de autenticación';
            if (err && err.message) {
                message = err.message;
            }
            if (err && err.status === 401) {
                message = 'Usuario o contraseña incorrectos';
            }
            showError(message);
        } finally {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>Ingresar';
        }
    });

    function showError(message) {
        alertBox.textContent = message;
        alertBox.classList.remove('d-none');
    }
});
