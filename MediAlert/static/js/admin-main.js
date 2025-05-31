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
            if(typeof showView === 'function') {
                showView('view-clientes');
            } else {
                console.error("La función showView no está definida. Asegúrate que admin-ui-handlers.js se carga antes que admin-main.js");
            }

        } catch (e) {
            console.error("Error en la verificación de sesión:", e.message);
            window.location.href = '/login.html';
        }
    })();

    // --- Instancias de Modales (disponibles globalmente mediante window para acceso desde otros archivos) ---
    const clienteModalEl = document.getElementById('clienteModal');
    window.clienteModal = clienteModalEl ? new bootstrap.Modal(clienteModalEl) : null;
    
    const medicamentoModalEl = document.getElementById('medicamentoModal');
    window.medicamentoModal = medicamentoModalEl ? new bootstrap.Modal(medicamentoModalEl) : null;

    const alertaModalEl = document.getElementById('alertaModal');
    window.alertaModal = alertaModalEl ? new bootstrap.Modal(alertaModalEl) : null;


    // --- Delegación de Eventos Principal ---
    document.body.addEventListener('click', async (e) => {
        const target = e.target;
        // Busca el botón o enlace más cercano, incluyendo aquellos dentro de otros elementos (como íconos dentro de botones)
        const button = target.closest('button, a'); 

        if (!button) return; // Si no se hizo clic en un botón o enlace, o algo que lo contenga, no hace nada

        // Navegación Sidebar
        if (button.matches('.sidebar .nav-link')) {
            e.preventDefault();
            const viewId = button.dataset.view;
            if (viewId && typeof showView === 'function') showView(viewId);
        }

        // Cierre de Sesión
        if (button.matches('#logout-btn')) {
            e.preventDefault(); // Si es un <a>
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
        if (button.matches('#btn-add-alerta')) { // Botón para agregar alerta
            if(typeof openAlertaModal === 'function') openAlertaModal(); // Llama sin ID para crear
        }

        // Botones de Acción en Tablas (Clientes)
        if (button.matches('.btn-edit-cliente')) {
            const id = button.dataset.id;
            if(typeof openClienteModal === 'function') openClienteModal(id);
        }
        if (button.matches('.btn-delete-cliente')) {
            const id = button.dataset.id;
            const clienteNombre = button.closest('tr')?.cells[0]?.textContent || 'este cliente';
            if (confirm(`¿Estás seguro de que quieres eliminar a ${clienteNombre}?`)) {
                try {
                    const response = await fetch(`/api/admin/clientes/${id}`, { method: 'DELETE' });
                    if (!response.ok) {
                         const errorData = await response.json();
                         throw new Error(errorData.error || "Error al eliminar cliente.");
                    }
                    if(typeof loadClientes === 'function') loadClientes(); // Recargar
                } catch (deleteError) {
                    console.error("Error al eliminar cliente:", deleteError);
                    alert(`Error al eliminar cliente: ${deleteError.message}`);
                }
            }
        }

        // Botones de Acción en Tablas (Medicamentos)
        if (button.matches('.btn-edit-medicamento')) {
            const id = button.dataset.id;
            const nombre = button.dataset.nombre;
            const descripcion = button.dataset.descripcion;
            if(typeof openMedicamentoModal === 'function') openMedicamentoModal(id, { nombre, descripcion });
        }
        if (button.matches('.btn-delete-medicamento')) {
            const id = button.dataset.id;
            const medNombre = button.closest('tr')?.cells[0]?.textContent || 'este medicamento';
            if (confirm(`¿Estás seguro de que quieres eliminar ${medNombre}? Se eliminarán las alertas asociadas.`)) {
                 try {
                    const response = await fetch(`/api/admin/medicamentos/${id}`, { method: 'DELETE' });
                     if (!response.ok) {
                         const errorData = await response.json();
                         throw new Error(errorData.error || "Error al eliminar medicamento.");
                    }
                    if(typeof loadMedicamentos === 'function') loadMedicamentos(); // Recargar
                } catch (deleteError) {
                    console.error("Error al eliminar medicamento:", deleteError);
                    alert(`Error al eliminar medicamento: ${deleteError.message}`);
                }
            }
        }

        // Botones de Acción en Tablas (Alertas)
        if (button.matches('.btn-edit-alerta')) {
            const alertaId = button.dataset.id;
            if(typeof openAlertaModal === 'function') openAlertaModal(alertaId); // Llama con ID para editar
        }
        if (button.matches('.btn-delete-alerta')) {
            const alertaId = button.dataset.id;
            const row = button.closest('tr');
            const cliente = row ? row.cells[0].textContent : 'esta alerta';
            const medicamento = row ? row.cells[1].textContent : '';

            if (confirm(`¿Estás seguro de que quieres eliminar la alerta para ${cliente} del medicamento ${medicamento}?`)) {
                try {
                    const response = await fetch(`/api/admin/alertas/${alertaId}`, { method: 'DELETE' });
                    const responseData = await response.json();
                    if (!response.ok) {
                        throw new Error(responseData.error || 'Error al eliminar la alerta.');
                    }
                    alert(responseData.message || 'Alerta eliminada con éxito.');
                    if (typeof loadAlertas === 'function') loadAlertas(); // Recargar la tabla
                } catch (error) {
                    console.error("Error al eliminar alerta:", error);
                    alert(`Error: ${error.message}`);
                }
            }
        }
    });

    // --- Manejo de Formularios ---
    const clienteFormEl = document.getElementById('clienteForm');
    if (clienteFormEl && typeof handleClienteSubmit === 'function') {
        clienteFormEl.addEventListener('submit', handleClienteSubmit);
    } else if (clienteFormEl) {
        console.error("handleClienteSubmit no está definido. Asegúrate que admin-form-handlers.js se carga correctamente.");
    }
    
    const medicamentoFormEl = document.getElementById('medicamentoForm');
    if (medicamentoFormEl && typeof handleMedicamentoSubmit === 'function') {
        medicamentoFormEl.addEventListener('submit', handleMedicamentoSubmit);
    } else if (medicamentoFormEl) {
        console.error("handleMedicamentoSubmit no está definido. Asegúrate que admin-form-handlers.js se carga correctamente.");
    }

    const alertaFormEl = document.getElementById('alertaForm');
    if (alertaFormEl && typeof handleAlertaSubmit === 'function') {
        alertaFormEl.addEventListener('submit', handleAlertaSubmit);
    } else if (alertaFormEl) {
        console.error("handleAlertaSubmit no está definido. Asegúrate que admin-form-handlers.js se carga correctamente.");
    }
});