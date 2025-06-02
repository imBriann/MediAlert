// static/js/admin-main.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Verificación de Sesión ---
    (async () => {
        try {
            const response = await fetch('/api/session_check');
            if (!response.ok) {
                 let errorMsg = 'Sesión no válida o expirada.';
                try {
                    const data = await response.json();
                    if(data.error) errorMsg = data.error;
                } catch(e) { /* ignore if not json */ }
                throw new Error(errorMsg);
            }
            const data = await response.json();
            if (data.rol !== 'admin') {
                alert('Acceso denegado. Se requiere rol de administrador.');
                throw new Error('Acceso denegado.');
            }
            
            const adminNameEl = document.getElementById('admin-name');
            if(adminNameEl) adminNameEl.textContent = data.nombre || 'Admin';
            
            if(typeof showView === 'function') {
                showView('view-clientes'); // Carga la vista inicial
            } else {
                console.error("La función showView no está definida.");
            }

        } catch (e) {
            console.error("Error en la verificación de sesión:", e.message);
            window.location.href = '/login.html';
        }
    })();

    // --- Instancias de Modales ---
    window.clienteModal = document.getElementById('clienteModal') ? new bootstrap.Modal(document.getElementById('clienteModal')) : null;
    window.medicamentoModal = document.getElementById('medicamentoModal') ? new bootstrap.Modal(document.getElementById('medicamentoModal')) : null;
    window.alertaModal = document.getElementById('alertaModal') ? new bootstrap.Modal(document.getElementById('alertaModal')) : null;
    window.clientDetailModalInstance = document.getElementById('clientDetailModal') ? new bootstrap.Modal(document.getElementById('clientDetailModal')) : null;

    // --- Delegación de Eventos Principal ---
    document.body.addEventListener('click', async (e) => {
        const targetElement = e.target.closest('button, a, div.report-option-card'); // Incluir las cards de reporte
        if (!targetElement) return;

        // Navegación Sidebar
        if (targetElement.matches('.sidebar .nav-link')) {
            e.preventDefault();
            const viewId = targetElement.dataset.view;
            if (viewId && typeof showView === 'function') showView(viewId);
        }

        // Cierre de Sesión y Tema
        if (targetElement.matches('#logout-btn')) {
            e.preventDefault();
            try {
                await fetch('/api/logout', { method: 'POST' });
                window.location.href = '/login.html';
            } catch (logoutError) {
                console.error("Error al cerrar sesión:", logoutError);
                alert("Error al cerrar sesión.");
            }
        }
        if (targetElement.matches('#theme-toggler-admin')) { // Específico para admin si es necesario, o usa el global de theme.js
             // theme.js maneja el cambio de tema globalmente.
             // Si este botón tiene lógica específica adicional, agrégala aquí.
             // De lo contrario, asegúrate que theme.js esté funcionando.
        }


        // Botones "Agregar"
        if (targetElement.matches('#btn-add-cliente') && typeof openClienteModal === 'function') openClienteModal();
        if (targetElement.matches('#btn-add-medicamento') && typeof openMedicamentoModal === 'function') openMedicamentoModal();
        if (targetElement.matches('#btn-add-alerta') && typeof openAlertaModal === 'function') openAlertaModal();

        // --- Client Card Actions ---
        // Edit Cliente
        if (targetElement.matches('.btn-edit-cliente') && typeof openClienteModal === 'function') {
            openClienteModal(targetElement.dataset.id);
        }

        // Toggle Cliente Status
        if (targetElement.matches('.btn-toggle-status-cliente')) {
            const id = targetElement.dataset.id;
            const nombre = targetElement.dataset.nombre || 'este cliente';
            const currentStatus = targetElement.dataset.status; // Get status from data-status attribute
            const newStatus = currentStatus === 'activo' ? 'inactivo' : 'activo';
            const actionText = newStatus === 'inactivo' ? 'desactivar' : 'reactivar';

            if (confirm(`¿Estás seguro de que quieres ${actionText} a ${nombre}?`)) {
                try {
                    const response = await fetch(`/api/admin/clientes/${id}`, { 
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ estado_usuario: newStatus })
                    });
                    const responseData = await response.json();
                    if (!response.ok) throw new Error(responseData.error || `Error al ${actionText} cliente.`);
                    alert(responseData.message || `Cliente ${actionText} con éxito.`);
                    if (typeof loadClientes === 'function') loadClientes(); // Reload cards
                } catch (error) {
                    console.error(`Error al ${actionText} cliente:`, error);
                    alert(`Error al ${actionText} cliente: ${error.message}`);
                }
            }
        }

        // View Client Details
        if (targetElement.matches('.btn-view-cliente') && typeof openClientDetailModal === 'function') {
            openClientDetailModal(targetElement.dataset.id);
        }

        // Click on Card Body to View Details
        const clickableCardArea = targetElement.closest('.client-card-clickable-area');
        if (clickableCardArea) {
            // Check if the click was on a button inside this area, if so, let that button's handler work
            if (targetElement.closest('button')) {
                // Do nothing, let the button's specific handler take over
            } else if (clickableCardArea.dataset.id && typeof openClientDetailModal === 'function') {
                openClientDetailModal(clickableCardArea.dataset.id);
            }
        }

        // Botones de Acción en Tablas (Medicamentos)
        if (targetElement.matches('.btn-edit-medicamento') && typeof openMedicamentoModal === 'function') {
            openMedicamentoModal(targetElement.dataset.id);
        }
        if (targetElement.matches('.btn-delete-medicamento')) { // Ahora es Discontinuar/Reactivar
            const id = targetElement.dataset.id;
            const medNombre = targetElement.dataset.nombre || 'este medicamento';
            const currentStatusIcon = targetElement.querySelector('i.bi');
            const currentStatus = currentStatusIcon && currentStatusIcon.classList.contains('bi-capsule-pill') ? 'disponible' : 'discontinuado';
            const newStatus = currentStatus === 'disponible' ? 'discontinuado' : 'disponible';
            const actionText = newStatus === 'discontinuado' ? 'discontinuar' : 'reactivar';
            
            if (confirm(`¿Estás seguro de que quieres ${actionText} ${medNombre}? Las alertas asociadas podrían inactivarse/reactivarse.`)) {
                 try {
                    const response = await fetch(`/api/admin/medicamentos/${id}`, { 
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ estado_medicamento: newStatus })
                     });
                    const responseData = await response.json();
                    if (!response.ok) throw new Error(responseData.error || `Error al ${actionText} medicamento.`);
                    alert(responseData.message || `Medicamento ${actionText} con éxito.`);
                    if(typeof loadMedicamentos === 'function') loadMedicamentos();
                    if(typeof loadAlertas === 'function') loadAlertas(); // Recargar alertas por si cambiaron de estado
                } catch (error) {
                    console.error(`Error al ${actionText} medicamento:`, error);
                    alert(`Error al ${actionText} medicamento: ${error.message}`);
                }
            }
        }

        // Botones de Acción en Tablas (Alertas)
        if (targetElement.matches('.btn-edit-alerta') && typeof openAlertaModal === 'function') {
            openAlertaModal(targetElement.dataset.id);
        }
        if (targetElement.matches('.btn-delete-alerta')) {
            const alertaId = targetElement.dataset.id;
            const row = targetElement.closest('tr');
            const cliente = row ? row.cells[0].textContent : 'esta alerta';
            const medicamento = row ? row.cells[1].textContent : '';

            if (confirm(`¿Estás seguro de que quieres ELIMINAR la alerta para ${cliente} del medicamento ${medicamento}? Esta acción es irreversible.`)) {
                try {
                    const response = await fetch(`/api/admin/alertas/${alertaId}`, { method: 'DELETE' });
                    const responseData = await response.json();
                    if (!response.ok) throw new Error(responseData.error || 'Error al eliminar la alerta.');
                    alert(responseData.message || 'Alerta eliminada con éxito.');
                    if (typeof loadAlertas === 'function') loadAlertas();
                } catch (error) {
                    console.error("Error al eliminar alerta:", error);
                    alert(`Error al eliminar alerta: ${error.message}`);
                }
            }
        }

        // Botones de generación de reportes
        if (targetElement.matches('#btn-report-usuarios') && typeof generateUsuariosReport === 'function') {
            generateUsuariosReport();
        }
        if (targetElement.matches('#btn-report-medicamentos') && typeof generateMedicamentosReport === 'function') {
            generateMedicamentosReport();
        }
        if (targetElement.matches('#btn-report-alertas-activas') && typeof generateAlertasActivasReport === 'function') {
            generateAlertasActivasReport();
        }
        if (targetElement.matches('#btn-report-auditoria') && typeof generateAuditoriaReport === 'function') {
            generateAuditoriaReport();
        }
    });

    // --- Manejo de Formularios ---
    const clienteFormEl = document.getElementById('clienteForm');
    if (clienteFormEl && typeof handleClienteSubmit === 'function') {
        clienteFormEl.addEventListener('submit', handleClienteSubmit);
    }
    
    const medicamentoFormEl = document.getElementById('medicamentoForm');
    if (medicamentoFormEl && typeof handleMedicamentoSubmit === 'function') {
        medicamentoFormEl.addEventListener('submit', handleMedicamentoSubmit);
    }

    const alertaFormEl = document.getElementById('alertaForm');
    if (alertaFormEl && typeof handleAlertaSubmit === 'function') {
        alertaFormEl.addEventListener('submit', handleAlertaSubmit);
    }
});