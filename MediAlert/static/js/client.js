// static/js/client.js

document.addEventListener('DOMContentLoaded', async () => {
    const clientNameElement = document.getElementById('client-name');
    const alertasTableBody = document.getElementById('alertas-table-body');
    const logoutButton = document.getElementById('logout-btn-client');
    const consolidatedReportButton = document.getElementById('btn-report-consolidado');

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
            const alertas = await fetchData('/api/cliente/mis_alertas', 'Error al cargar mis alertas');

            alertasTableBody.innerHTML = '';
            if (alertas.length > 0) {
                alertas.forEach(a => {
                    let estadoBadgeClass = 'bg-secondary';
                    if (a.estado === 'activa') {
                        estadoBadgeClass = 'bg-success';
                    } else if (a.estado === 'completada') {
                        estadoBadgeClass = 'bg-info text-dark';
                    } else if (a.estado === 'inactiva') {
                        estadoBadgeClass = 'bg-warning text-dark';
                    } else if (a.estado === 'fallida') {
                        estadoBadgeClass = 'bg-danger';
                    }

                    const printButtonHtml = `<button class="btn btn-sm btn-outline-secondary ms-2 btn-print-receta" data-alerta-id="${a.id}" title="Imprimir Receta Médica">
                                                <i class="bi bi-printer"></i> Receta
                                            </button>`;

                    alertasTableBody.innerHTML += `<tr>
                        <td>${a.medicamento_nombre || 'N/A'}</td>
                        <td>${a.dosis || 'N/A'}</td>
                        <td>${a.frecuencia || 'N/A'}</td>
                        <td>${formatDate(a.fecha_inicio)}</td>
                        <td>${formatDate(a.fecha_fin)}</td>
                        <td>${formatTime(a.hora_preferida)}</td>
                        <td><span class="badge ${estadoBadgeClass}">${a.estado || 'N/A'}</span></td>
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

    document.body.addEventListener('click', async (e) => {
        const targetElement = e.target.closest('.btn-print-receta');
        if (targetElement) {
            const alertaId = targetElement.dataset.alertaId;
            if (typeof generateRecetaMedicaPdf === 'function') {
                generateRecetaMedicaPdf(alertaId);
            } else {
                showGlobalNotification('Error', 'La función de generación de PDF no está disponible. Asegúrate de que el script report-generator.js esté cargado.', 'error');
            }
        }
    });

    if (consolidatedReportButton) {
        consolidatedReportButton.addEventListener('click', () => {
            if (typeof generateConsolidatedRecetaPdf === 'function') {
                generateConsolidatedRecetaPdf();
            } else {
                showGlobalNotification('Error', 'La función de generación de PDF consolidado no está disponible.', 'error');
            }
        });
    }
});