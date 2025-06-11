// static/js/client.js

// formatDateClient and formatTimeClient are now redundant as formatters are in shared-utils.js
// They are kept here for historical context if needed, but the calls will now use the global ones.

document.addEventListener('DOMContentLoaded', async () => {
    const clientNameElement = document.getElementById('client-name');
    const alertasTableBody = document.getElementById('alertas-table-body');
    const logoutButton = document.getElementById('logout-btn-client');

    // Make sure globalNotificationModal is initialized
    if (!window.globalNotificationModal) {
        const modalElement = document.getElementById('notificationModal');
        if (modalElement) {
            window.globalNotificationModal = new bootstrap.Modal(modalElement);
        } else {
            console.error("Modal element #notificationModal not found for instantiation in client.js.");
        }
    }

    try {
        const sessionResponse = await fetch('/api/session_check');
        const sessionData = await sessionResponse.json();
        if (!sessionResponse.ok || sessionData.rol !== 'cliente') {
            showGlobalNotification('Acceso Denegado', sessionData.error || 'Acceso denegado o sesión expirada. Por favor, inicie sesión.', 'error');
            setTimeout(() => { window.location.href = '/login.html'; }, 1500);
            return;
        }
        if (clientNameElement) {
            clientNameElement.textContent = sessionData.nombre;
        }
    } catch (e) {
        console.error("Error verificando sesión:", e);
        showGlobalNotification('Error de Conexión', 'Error de conexión al verificar la sesión. Serás redirigido al login.', 'error');
        setTimeout(() => { window.location.href = '/login.html'; }, 1500);
        return;
    }

    if (alertasTableBody) {
        try {
            // Using the globally available fetchData
            const alertas = await fetchData('/api/cliente/mis_alertas', 'Error al cargar mis alertas');
            
            alertasTableBody.innerHTML = '';
            if (alertas.length > 0) {
                alertas.forEach(a => {
                    let estadoBadgeClass = 'bg-secondary'; // Default
                    if (a.estado === 'activa') {
                        estadoBadgeClass = 'bg-success';
                    } else if (a.estado === 'completada') {
                        estadoBadgeClass = 'bg-info text-dark';
                    } else if (a.estado === 'inactiva') {
                        // Check if the alert is expired based on fecha_fin
                        const today = new Date();
                        today.setHours(0,0,0,0); // Normalize to start of day
                        // Use the shared formatDate to safely parse and compare
                        const fechaFin = a.fecha_fin ? new Date(a.fin + 'T00:00:00Z') : null; // Ensure 'fin' property is correct
                        if (fechaFin && fechaFin.getTime() < today.getTime()) {
                             estadoBadgeClass = 'bg-danger'; // Expired
                        } else {
                            estadoBadgeClass = 'bg-warning text-dark'; // Inactive but not expired
                        }
                    } else if (a.estado === 'fallida') {
                        estadoBadgeClass = 'bg-danger';
                    }

                    // Botón de imprimir receta solo si la alerta no está 'fallida'
                    const printButtonHtml = (a.estado !== 'fallida') ? 
                                            `<button class="btn btn-sm btn-outline-secondary ms-2 btn-print-receta" data-alerta-id="${a.id}" title="Imprimir Receta Médica">
                                                <i class="bi bi-printer"></i> Receta
                                            </button>` : '';

                    alertasTableBody.innerHTML += `<tr>
                        <td>${a.medicamento_nombre || 'N/A'}</td>
                        <td>${a.dosis || 'N/A'}</td>
                        <td>${a.frecuencia || 'N/A'}</td>
                        <td>${formatDate(a.fecha_inicio)}</td> <td>${formatDate(a.fecha_fin)}</td> <td>${formatTime(a.hora_preferida)}</td> <td><span class="badge ${estadoBadgeClass}">${a.estado || 'N/A'}</span></td>
                        <td>${printButtonHtml}</td>
                    </tr>`;
                });
            } else {
                alertasTableBody.innerHTML = '<tr><td colspan="8" class="text-center">No tienes alertas asignadas.</td></tr>';
            }
        } catch (e) {
            console.error("Error cargando alertas:", e);
            alertasTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error al cargar tus alertas: ${e.message}</td></tr>`;
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
                    showGlobalNotification('Error al Cerrar Sesión', errorData.error || 'Error desconocido al cerrar sesión.', 'error');
                }
            } catch (e) {
                console.error("Error en logout:", e);
                showGlobalNotification('Error de Conexión', 'Error de conexión al cerrar sesión.', 'error');
            }
        });
    }

    // Listener para los botones de imprimir receta (tanto para admin como cliente)
    document.body.addEventListener('click', async (e) => {
        const targetElement = e.target.closest('.btn-print-receta');
        if (targetElement) {
            const alertaId = targetElement.dataset.alertaId;
            // generateRecetaMedicaPdf está definida en report-generator.js y ahora disponible globalmente
            if (typeof generateRecetaMedicaPdf === 'function') {
                generateRecetaMedicaPdf(alertaId);
            } else {
                showGlobalNotification('Error', 'La función de generación de PDF no está disponible. Asegúrate de que el script report-generator.js esté cargado.', 'error');
            }
        }
    });
});