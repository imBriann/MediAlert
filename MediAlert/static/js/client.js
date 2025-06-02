// static/js/client.js

function formatDateClient(dateString) {
    if (!dateString) return 'N/A';
    try {
        // Asume que la fecha viene en formato ISO (YYYY-MM-DD) o similar parseable por Date
        return new Date(dateString).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (e) {
        return dateString;
    }
}

function formatTimeClient(timeString) {
    if (!timeString) return 'N/A';
    // Backend devuelve HH:MM:SS o HH:MM
    const parts = timeString.split(':');
    if (parts.length >= 2) {
        const date = new Date();
        date.setHours(parseInt(parts[0], 10));
        date.setMinutes(parseInt(parts[1], 10));
        date.setSeconds(parts.length > 2 ? parseInt(parts[2], 10) : 0);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    }
    return timeString; // Devuelve original si no es formato esperado
}


document.addEventListener('DOMContentLoaded', async () => {
    const clientNameElement = document.getElementById('client-name');
    const alertasTableBody = document.getElementById('alertas-table-body');
    const logoutButton = document.getElementById('logout-btn-client');

    try {
        const sessionResponse = await fetch('/api/session_check');
        const sessionData = await sessionResponse.json();
        if (!sessionResponse.ok || sessionData.rol !== 'cliente') {
            alert(sessionData.error || 'Acceso denegado o sesión expirada.');
            window.location.href = '/login.html';
            return;
        }
        if (clientNameElement) {
            clientNameElement.textContent = sessionData.nombre;
        }
    } catch (e) {
        console.error("Error verificando sesión:", e);
        alert("Error de conexión al verificar la sesión. Serás redirigido al login.");
        window.location.href = '/login.html';
        return;
    }

    if (alertasTableBody) {
        try {
            const alertResponse = await fetch('/api/cliente/mis_alertas');
            if (!alertResponse.ok) {
                const errorData = await alertResponse.json();
                throw new Error(errorData.error || `Error al cargar alertas: ${alertResponse.statusText}`);
            }
            const alertas = await alertResponse.json();
            
            alertasTableBody.innerHTML = '';
            if (alertas.length > 0) {
                alertas.forEach(a => {
                    const estadoBadgeClass = a.estado === 'activa' ? 'bg-success' : 
                                           a.estado === 'completada' ? 'bg-info' :
                                           a.estado === 'inactiva' ? 'bg-warning' : 'bg-secondary';
                    alertasTableBody.innerHTML += `<tr>
                        <td>${a.medicamento_nombre || 'N/A'}</td>
                        <td>${a.dosis || 'N/A'}</td>
                        <td>${a.frecuencia || 'N/A'}</td>
                        <td>${formatDateClient(a.fecha_inicio)}</td>
                        <td>${formatDateClient(a.fecha_fin)}</td>
                        <td>${formatTimeClient(a.hora_preferida)}</td>
                        <td><span class="badge ${estadoBadgeClass}">${a.estado || 'N/A'}</span></td>
                    </tr>`;
                });
            } else {
                alertasTableBody.innerHTML = '<tr><td colspan="7" class="text-center">No tienes alertas activas asignadas.</td></tr>';
            }
        } catch (e) {
            console.error("Error cargando alertas:", e);
            alertasTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">Error al cargar tus alertas: ${e.message}</td></tr>`;
        }
    }

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