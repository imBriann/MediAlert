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
                 resetOriginalData();
                showView('view-clientes');
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

    // --- Search Event Listeners ---
    const searchClientesInput = document.getElementById('search-clientes');
    if (searchClientesInput) {
        searchClientesInput.addEventListener('input', () => {
            if (typeof loadClientes === 'function') loadClientes(searchClientesInput.value);
        });
    }

    const searchMedicamentosInput = document.getElementById('search-medicamentos');
    if (searchMedicamentosInput) {
        searchMedicamentosInput.addEventListener('input', () => {
            if (typeof loadMedicamentos === 'function') loadMedicamentos(searchMedicamentosInput.value);
        });
    }

    const searchAlertasInput = document.getElementById('search-alertas-input');
    if (searchAlertasInput) {
        searchAlertasInput.addEventListener('input', () => {
            if (typeof loadAlertas === 'function') {
                loadAlertas(searchAlertasInput.value);
            }
        });
    }

    const searchAuditoriaInput = document.getElementById('search-auditoria');
    const auditoriaModuleFilter = document.getElementById('auditoria-filter-module');

    function triggerAuditoriaLoad() {
        const moduleFilterValue = auditoriaModuleFilter ? auditoriaModuleFilter.value : '';
        const userSearchTermValue = searchAuditoriaInput ? searchAuditoriaInput.value : '';
        if (typeof loadAuditoria === 'function') {
            loadAuditoria(moduleFilterValue, userSearchTermValue);
        }
    }

    if (searchAuditoriaInput) {
        searchAuditoriaInput.addEventListener('input', triggerAuditoriaLoad);
    }
    if (auditoriaModuleFilter) {
        auditoriaModuleFilter.removeEventListener('change', window.handleAuditoriaModuleFilterChange);
        window.handleAuditoriaModuleFilterChange = triggerAuditoriaLoad;
        auditoriaModuleFilter.addEventListener('change', window.handleAuditoriaModuleFilterChange);
    }


    // --- Delegación de Eventos Principal ---
    document.body.addEventListener('click', async (e) => {
        const targetElement = e.target.closest('button, a, div.report-option-card');
        if (!targetElement) return;

        // Navegación Sidebar
        if (targetElement.matches('.sidebar .nav-link')) {
            e.preventDefault();
            const viewId = targetElement.dataset.view;
            if (viewId && typeof showView === 'function') {
                if (searchClientesInput) searchClientesInput.value = '';
                if (searchMedicamentosInput) searchMedicamentosInput.value = '';
                if (searchAlertasInput) searchAlertasInput.value = '';
                if (searchAuditoriaInput) searchAuditoriaInput.value = '';
                if (auditoriaModuleFilter) auditoriaModuleFilter.value = '';

                resetOriginalData();
                showView(viewId);
            }
        }

        // Cierre de Sesión
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

        // Botones "Agregar"
        if (targetElement.matches('#btn-add-cliente') && typeof openClienteModal === 'function') openClienteModal();
        if (targetElement.matches('#btn-add-medicamento') && typeof openMedicamentoModal === 'function') openMedicamentoModal();
        if (targetElement.matches('#btn-add-alerta') && typeof openAlertaModal === 'function') openAlertaModal();

        // --- Client Card Actions ---
        if (targetElement.matches('.btn-edit-cliente') && typeof openClienteModal === 'function') {
            openClienteModal(targetElement.dataset.id);
        }

        if (targetElement.matches('.btn-toggle-status-cliente')) {
            const id = targetElement.dataset.id;
            const nombre = targetElement.dataset.nombre || 'este cliente';
            const currentStatus = targetElement.dataset.status;
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

                    showGlobalNotification('Actualización de Cliente', responseData.message || `Cliente ${actionText} con éxito.`, 'success');

                    if (typeof loadClientes === 'function') loadClientes();
                } catch (error) {
                    console.error(`Error al ${actionText} cliente:`, error);
                    showGlobalNotification('Error de Actualización', `Error al ${actionText} cliente: ${error.message}`, 'error');
                }
            }
        }

        if (targetElement.matches('.btn-view-cliente') && typeof openClientDetailModal === 'function') {
            openClientDetailModal(targetElement.dataset.id);
        }

        if (targetElement.matches('.btn-view-cliente-alerts') && typeof openClientDetailModal === 'function') {
            openClientDetailModal(targetElement.dataset.id);
        }

        const clickableCardArea = targetElement.closest('.client-card-clickable-area');
        if (clickableCardArea) {
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
        if (targetElement.matches('.btn-delete-medicamento')) {
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

                    showGlobalNotification('Actualización de Medicamento', responseData.message || `Medicamento ${actionText} con éxito.`, 'success');

                    originalMedicamentosData = [];
                    if(typeof loadMedicamentos === 'function') loadMedicamentos(searchMedicamentosInput ? searchMedicamentosInput.value : '');
                    originalAlertasData = [];
                    if(typeof loadAlertas === 'function') loadAlertas(searchAlertasInput ? searchAlertasInput.value : '');
                } catch (error) {
                    console.error(`Error al ${actionText} medicamento:`, error);
                    showGlobalNotification('Error de Actualización', `Error al ${actionText} medicamento: ${error.message}`, 'error');
                }
            }
        }

        // Botones de generación de reportes (general, en la vista de reportes)
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
        // Consolidated Admin Report button (in the general reports view)
        if (targetElement.matches('#btn-report-recetas-consolidadas-admin') && typeof generateConsolidatedRecetaPdfForAdmin === 'function') {
            generateConsolidatedRecetaPdfForAdmin();
        }
    });

    // Listener for individual prescription print buttons (both for admin as part of client detail modal)
    document.body.addEventListener('click', async (e) => {
        const targetElement = e.target.closest('.btn-print-receta');
        if (targetElement) {
            const alertaId = targetElement.dataset.alertaId;
            // AHORA LLAMA A LA NUEVA FUNCIÓN
            if (typeof generatePlanDeManejoPdf === 'function') {
                generatePlanDeManejoPdf(alertaId);
            } else {
                showGlobalNotification('Error', 'La función de generación de PDF no está disponible.', 'error');
            }
        }

        // NEW: Listener for "Download Consolidated Active Prescriptions" button within client detail modal
        const consolidatedClientRecetaBtn = e.target.closest('#btn-download-client-consolidated-receta');
        if (consolidatedClientRecetaBtn) {
            const clientId = consolidatedClientRecetaBtn.dataset.clientId;
            const clientName = consolidatedClientRecetaBtn.dataset.clientName;
            if (typeof generateConsolidatedRecetaPdf === 'function') {
                // Pass client ID and name to the reusable function
                generateConsolidatedRecetaPdf(clientId, clientName);
            } else {
                showGlobalNotification('Error', 'La función de generación de PDF consolidado no está disponible.', 'error');
            }
        }
    });


    // --- Manejo de Formularios ---
    const clienteFormEl = document.getElementById('clienteForm');
    if (clienteFormEl && typeof handleClienteSubmit === 'function') {
        clienteFormEl.addEventListener('submit', (e) => {
            handleClienteSubmit(e).then(() => {
                originalClientesData = [];
                if (typeof loadClientes === 'function') loadClientes(searchClientesInput ? searchClientesInput.value : '');
            });
        });
    }

    const medicamentoFormEl = document.getElementById('medicamentoForm');
    if (medicamentoFormEl && typeof handleMedicamentoSubmit === 'function') {
        medicamentoFormEl.addEventListener('submit', (e) => {
            handleMedicamentoSubmit(e).then(() => {
                originalMedicamentosData = [];
                if (typeof loadMedicamentos === 'function') loadMedicamentos(searchMedicamentosInput ? searchMedicamentosInput.value : '');
            });
        });
    }

    const alertaFormEl = document.getElementById('alertaForm');
    if (alertaFormEl && typeof handleAlertaSubmit === 'function') {
        alertaFormEl.addEventListener('submit', (e) => {
            handleAlertaSubmit(e).then(() => {
                originalAlertasData = [];
                if (typeof loadAlertas === 'function') loadAlertas(searchAlertasInput ? searchAlertasInput.value : '');
            });
        });
    }
});