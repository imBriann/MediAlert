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

    // --- Delegación de Eventos Principal ---
    document.body.addEventListener('click', async (e) => {
        const button = e.target.closest('button, a'); 
        if (!button) return;

        // Navegación Sidebar
        if (button.matches('.sidebar .nav-link')) {
            e.preventDefault();
            const viewId = button.dataset.view;
            if (viewId && typeof showView === 'function') showView(viewId);
        }

        // Cierre de Sesión y Tema
        if (button.matches('#logout-btn')) {
            e.preventDefault();
            try {
                await fetch('/api/logout', { method: 'POST' });
                window.location.href = '/login.html';
            } catch (logoutError) {
                console.error("Error al cerrar sesión:", logoutError);
                alert("Error al cerrar sesión.");
            }
        }
        if (button.matches('#theme-toggler-admin')) { // Específico para admin si es necesario, o usa el global de theme.js
             // theme.js maneja el cambio de tema globalmente.
             // Si este botón tiene lógica específica adicional, agrégala aquí.
             // De lo contrario, asegúrate que theme.js esté funcionando.
        }


        // Botones "Agregar"
        if (button.matches('#btn-add-cliente') && typeof openClienteModal === 'function') openClienteModal();
        if (button.matches('#btn-add-medicamento') && typeof openMedicamentoModal === 'function') openMedicamentoModal();
        if (button.matches('#btn-add-alerta') && typeof openAlertaModal === 'function') openAlertaModal();

        // Botones de Acción en Tablas (Clientes)
        if (button.matches('.btn-edit-cliente') && typeof openClienteModal === 'function') {
            openClienteModal(button.dataset.id);
        }
        if (button.matches('.btn-delete-cliente')) { // Ahora es Desactivar/Reactivar
            const id = button.dataset.id;
            const nombre = button.dataset.nombre || 'este cliente';
            const currentStatus = button.querySelector('i.bi').classList.contains('bi-person-slash') ? 'activo' : 'inactivo';
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
                    if(typeof loadClientes === 'function') loadClientes();
                } catch (error) {
                    console.error(`Error al ${actionText} cliente:`, error);
                    alert(`Error al ${actionText} cliente: ${error.message}`);
                }
            }
        }

        // Botones de Acción en Tablas (Medicamentos)
        if (button.matches('.btn-edit-medicamento') && typeof openMedicamentoModal === 'function') {
            openMedicamentoModal(button.dataset.id);
        }
        if (button.matches('.btn-delete-medicamento')) { // Ahora es Discontinuar/Reactivar
            const id = button.dataset.id;
            const medNombre = button.dataset.nombre || 'este medicamento';
            const currentStatusIcon = button.querySelector('i.bi');
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
        if (button.matches('.btn-edit-alerta') && typeof openAlertaModal === 'function') {
            openAlertaModal(button.dataset.id);
        }
        if (button.matches('.btn-delete-alerta')) {
            const alertaId = button.dataset.id;
            const row = button.closest('tr');
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