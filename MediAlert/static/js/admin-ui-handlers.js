// static/js/admin-ui-handlers.js

function showView(viewId) {
    document.querySelectorAll('.view-content').forEach(view => view.style.display = 'none');
    const currentView = document.getElementById(viewId);
    if (currentView) {
        currentView.style.display = 'block';
    }

    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.view === viewId) link.classList.add('active');
    });

    // Cargar datos según la vista
    // Estas funciones deben estar definidas globalmente (desde admin-data-handlers.js)
    switch (viewId) {
        case 'view-clientes': if(typeof loadClientes === 'function') loadClientes(); break;
        case 'view-medicamentos': if(typeof loadMedicamentos === 'function') loadMedicamentos(); break;
        case 'view-alertas': if(typeof loadAlertas === 'function') loadAlertas(); break;
        case 'view-auditoria': if(typeof loadAuditoria === 'function') loadAuditoria(); break;
    }
}

async function openClienteModal(id = null) {
    const form = document.getElementById('clienteForm');
    form.reset();
    document.getElementById('clienteId').value = '';
    
    if (id) { // Modo Editar
        try {
            const res = await fetch(`/api/admin/clientes/${id}`);
            if (!res.ok) throw new Error(`Error al obtener datos del cliente: ${res.statusText}`);
            const cliente = await res.json();
            document.getElementById('clienteModalTitle').textContent = 'Editar Cliente';
            document.getElementById('clienteId').value = cliente.id;
            document.getElementById('clienteNombre').value = cliente.nombre;
            document.getElementById('clienteCedula').value = cliente.cedula;
            document.getElementById('clienteEmail').value = cliente.email;
            document.getElementById('password-field-container').style.display = 'none';
            document.getElementById('clienteContrasena').required = false;
        } catch(error) {
            console.error("Error en openClienteModal (edit):", error);
            alert("No se pudieron cargar los datos del cliente para editar.");
            return;
        }
    } else { // Modo Agregar
        document.getElementById('clienteModalTitle').textContent = 'Agregar Cliente';
        document.getElementById('password-field-container').style.display = 'block';
        document.getElementById('clienteContrasena').required = true;
    }
    // Asume que window.clienteModal está disponible globalmente desde admin-main.js
    if (window.clienteModal && typeof window.clienteModal.show === 'function') {
        window.clienteModal.show();
    } else {
        console.error("clienteModal no está disponible o no tiene el método show.");
    }
}

function openMedicamentoModal(id = null, data = {}) {
    const form = document.getElementById('medicamentoForm');
    form.reset();
    document.getElementById('medicamentoId').value = '';
    
    if (id) { // Modo Editar
        document.getElementById('medicamentoModalTitle').textContent = 'Editar Medicamento';
        document.getElementById('medicamentoId').value = id;
        document.getElementById('medicamentoNombre').value = data.nombre || ''; // Asegurar que data.nombre exista
        document.getElementById('medicamentoDescripcion').value = data.descripcion || ''; // Asegurar que data.descripcion exista
    } else { // Modo Agregar
        document.getElementById('medicamentoModalTitle').textContent = 'Agregar Medicamento';
    }
    // Asume que window.medicamentoModal está disponible globalmente desde admin-main.js
    if (window.medicamentoModal && typeof window.medicamentoModal.show === 'function') {
        window.medicamentoModal.show();
    } else {
        console.error("medicamentoModal no está disponible o no tiene el método show.");
    }
}

async function openAlertaModal(alertaId = null) { // alertaId para futura edición
    const form = document.getElementById('alertaForm');
    form.reset();
    document.getElementById('alertaId').value = ''; 

    const modalTitle = document.getElementById('alertaModalLabel');
    const usuarioSelect = document.getElementById('alertaUsuario');
    const medicamentoSelect = document.getElementById('alertaMedicamento');

    modalTitle.textContent = 'Asignar Nueva Alerta';
    // Limpiar selectores manteniendo la opción por defecto
    usuarioSelect.innerHTML = '<option value="" disabled selected>Seleccione un cliente...</option>';
    medicamentoSelect.innerHTML = '<option value="" disabled selected>Seleccione un medicamento...</option>';

    try {
        // Cargar Clientes
        const clientesResponse = await fetch('/api/admin/clientes');
        if (!clientesResponse.ok) throw new Error('No se pudieron cargar los clientes.');
        const clientes = await clientesResponse.json();
        clientes.forEach(cliente => {
            const option = new Option(`${cliente.nombre} (C.C: ${cliente.cedula})`, cliente.id);
            usuarioSelect.add(option);
        });

        // Cargar Medicamentos
        const medicamentosResponse = await fetch('/api/admin/medicamentos');
        if (!medicamentosResponse.ok) throw new Error('No se pudieron cargar los medicamentos.');
        const medicamentos = await medicamentosResponse.json();
        medicamentos.forEach(medicamento => {
            const option = new Option(medicamento.nombre, medicamento.id);
            medicamentoSelect.add(option);
        });

        if (alertaId) {
            // Lógica para cargar datos de una alerta existente para editar (FUTURO)
            // modalTitle.textContent = 'Editar Alerta';
            // const alertDataResponse = await fetch(`/api/admin/alertas/${alertaId}`);
            // const alertData = await alertDataResponse.json();
            // Llenar campos del formulario...
        }

        if (window.alertaModal && typeof window.alertaModal.show === 'function') {
            window.alertaModal.show();
        } else {
            console.error("La instancia del modal 'alertaModal' no está disponible.");
        }

    } catch (error) {
        console.error("Error al preparar el modal de alerta:", error);
        alert(`Error al cargar datos para el formulario de alerta: ${error.message}`);
    }
}