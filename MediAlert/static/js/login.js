document.addEventListener('DOMContentLoaded', () => { // Es una buena práctica envolverlo para asegurar que el DOM esté listo, aunque para un script al final del body puede no ser estrictamente necesario para este caso específico.
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const cedula = document.getElementById('cedula').value;
            const contrasena = document.getElementById('contrasena').value;

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cedula, contrasena })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Error desconocido al intentar iniciar sesión.');
                }

                // Login exitoso
                showGlobalNotification('Inicio de Sesión Exitoso', 'Será redirigido en unos momentos...', 'success');
                setTimeout(() => {
                    if (data.rol === 'admin') {
                        window.location.href = '/admin.html';
                    } else if (data.rol === 'cliente') {
                        window.location.href = '/client.html';
                    } else {
                        showGlobalNotification('Error de Redirección', 'Rol de usuario no reconocido.', 'error');
                    }
                }, 1500);
            } catch (error) {
                // Error en el inicio de sesión
                showGlobalNotification('Error de Inicio de Sesión', error.message, 'error');
            }
        });
    }
});