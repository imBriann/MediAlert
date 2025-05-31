// static/js/client.js
document.addEventListener('DOMContentLoaded', async () => {
    const clientNameElement = document.getElementById('client-name');
    const alertasTableBody = document.getElementById('alertas-table-body');
    const logoutButton = document.getElementById('logout-btn-client');

    // Verificar sesión y cargar nombre del cliente
    try {
        const sessionResponse = await fetch('/api/session_check');
        const sessionData = await sessionResponse.json();
        if (!sessionResponse.ok || sessionData.rol !== 'cliente') {
            window.location.href = '/login.html';
            return;
        }
        if (clientNameElement) {
            clientNameElement.textContent = sessionData.nombre;
        }
    } catch (e) {
        console.error("Error verificando sesión:", e);
        window.location.href = '/login.html';
        return; // Salir si hay error de sesión
    }

    // Cargar alertas del cliente
    if (alertasTableBody) {
        try {
            const alertResponse = await fetch('/api/cliente/mis_alertas');
            if (!alertResponse.ok) {
                throw new Error(`Error al cargar alertas: ${alertResponse.statusText}`);
            }
            const alertas = await alertResponse.json();
            
            alertasTableBody.innerHTML = ''; // Limpiar tabla
            if (alertas.length > 0) {
                alertas.forEach(a => {
                    alertasTableBody.innerHTML += `<tr>
                        <td>${a.medicamento || 'N/A'}</td>
                        <td>${a.dosis || 'N/A'}</td>
                        <td>${a.frecuencia || 'N/A'}</td>
                        <td><span class="badge bg-success">${a.estado || 'N/A'}</span></td>
                    </tr>`;
                });
            } else {
                alertasTableBody.innerHTML = '<tr><td colspan="4" class="text-center">No tienes alertas asignadas.</td></tr>';
            }
        } catch (e) {
            console.error("Error cargando alertas:", e);
            alertasTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Error al cargar tus alertas.</td></tr>';
        }
    }

    // Manejador para el botón de Logout
    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.href = '/login.html';
                } else {
                    const errorData = await response.json();
                    alert(`Error al cerrar sesión: ${errorData.error || 'Desconocido'}`);
                }
            } catch (e) {
                console.error("Error en logout:", e);
                alert('Error de conexión al cerrar sesión.');
            }
        });
    }
});