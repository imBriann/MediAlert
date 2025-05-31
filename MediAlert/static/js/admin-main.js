// static/js/admin-main.js

document.addEventListener('DOMContentLoaded', () => {

    // --- Verificación de Sesión ---
    (async () => {
        try {
            const response = await fetch('/api/session_check');
            if (!response.ok) throw new Error('Sesión no válida o expirada.');
            const data = await response.json();
            if (data.rol !== 'admin') throw new Error('Acceso denegado.');
            
            const adminNameEl = document.getElementById('admin-name');
            if(adminNameEl) adminNameEl.textContent = data.nombre;
            
            // Si la sesión es válida, carga la vista inicial
            // showView debe estar definida (desde admin-ui-handlers.js)
            if(typeof showView === 'function') showView('view-clientes');

        } catch (e) {
            console.error("Error en la verificación de sesión:", e.message);
            window.location.href = '/login.html';
        }
    })();

    // --- Instancias de Modales (disponibles globalmente mediante window) ---
    const clienteModalEl = document.getElementById('clienteModal');
    window.clienteModal = clienteModalEl ? new bootstrap.Modal(clienteModalEl) : null;
    
    const medicamentoModalEl = document.getElementById('medicamentoModal');
    window.medicamentoModal = medicamentoModalEl ? new bootstrap.Modal(medicamentoModalEl) : null;

    // --- Delegación de Eventos Principal ---
    document.body.addEventListener('click', async (e) => {
        const target = e.target;
        const button = target.closest('button, a'); 

        if (!button) return; 

        // Navegación Sidebar
        if (button.matches('.sidebar .nav-link')) {
            e.preventDefault();
            const viewId = button.dataset.view;
            if (viewId && typeof showView === 'function') showView(viewId);
        }

        // Cierre de Sesión
        if (button.matches('#logout-btn')) {
            try {
                await fetch('/api/logout', { method: 'POST' });
                window.location.href = '/login.html';
            } catch (logoutError) {
                console.error("Error al cerrar sesión:", logoutError);
                alert("Error al cerrar sesión.");
            }
        }

        // Botones "Agregar"
        if (button.matches('#btn-add-cliente')) {
            if(typeof openClienteModal === 'function') openClienteModal();
        }
        if (button.matches('#btn-add-medicamento')) {
            if(typeof openMedicamentoModal === 'function') openMedicamentoModal();
        }

        // Botones de Acción en Tablas (Editar/Eliminar Cliente)
        if (button.matches('.btn-edit-cliente')) {
            const id = button.dataset.id;
            if(typeof openClienteModal === 'function') openClienteModal(id);
        }
        if (button.matches('.btn-delete-cliente')) {
            const id = button.dataset.id;
            if (confirm('¿Estás seguro de que quieres eliminar este cliente?')) {
                try {
                    const response = await fetch(`/api/admin/clientes/${id}`, { method: 'DELETE' });
                    if (!response.ok) throw new Error("Error al eliminar cliente.");
                    if(typeof loadClientes === 'function') loadClientes();
                } catch (deleteError) {
                    console.error("Error al eliminar cliente:", deleteError);
                    alert("Error al eliminar cliente.");
                }
            }
        }

        // Botones de Acción en Tablas (Editar/Eliminar Medicamento)
        if (button.matches('.btn-edit-medicamento')) {
            const id = button.dataset.id;
            const nombre = button.dataset.nombre;
            const descripcion = button.dataset.descripcion;
            if(typeof openMedicamentoModal === 'function') openMedicamentoModal(id, { nombre, descripcion });
        }
        if (button.matches('.btn-delete-medicamento')) {
            const id = button.dataset.id;
            if (confirm('¿Estás seguro de que quieres eliminar este medicamento? Se eliminarán las alertas asociadas.')) {
                 try {
                    const response = await fetch(`/api/admin/medicamentos/${id}`, { method: 'DELETE' });
                    if (!response.ok) throw new Error("Error al eliminar medicamento.");
                    if(typeof loadMedicamentos === 'function') loadMedicamentos();
                } catch (deleteError) {
                    console.error("Error al eliminar medicamento:", deleteError);
                    alert("Error al eliminar medicamento.");
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
});