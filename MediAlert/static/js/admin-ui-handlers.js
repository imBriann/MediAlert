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

    switch (viewId) {
        case 'view-clientes': if(typeof loadClientes === 'function') loadClientes(); break;
        case 'view-medicamentos': if(typeof loadMedicamentos === 'function') loadMedicamentos(); break;
        case 'view-alertas': if(typeof loadAlertas === 'function') loadAlertas(); break;
        case 'view-auditoria': if(typeof loadAuditoria === 'function') loadAuditoria(); break;
        case 'view-reportes': if(typeof loadReportesLog === 'function') loadReportesLog(); break; // NUEVO
    }
}

async function openClienteModal(id = null) {
    const form = document.getElementById('clienteForm');
    form.reset();
    document.getElementById('clienteId').value = '';
    const modalTitle = document.getElementById('clienteModalTitle');
    const contrasenaInput = document.getElementById('clienteContrasena');
    const contrasenaLabel = document.getElementById('clienteContrasenaLabel');
    const contrasenaHelp = document.getElementById('clienteContrasenaHelp');
    
    const estadoUsuarioSelect = document.getElementById('clienteEstadoUsuario');
    const estadoUsuarioDiv = document.getElementById('clienteEstadoUsuarioDiv'); // Contenedor del select
    
    if (id) { // Modo Editar
        modalTitle.textContent = 'Editar Cliente';
        if(estadoUsuarioDiv) estadoUsuarioDiv.style.display = 'block'; // Mostrar campo de estado
        try {
            const res = await fetch(`/api/admin/clientes/${id}`);
            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.error || `Error al obtener datos del cliente: ${res.statusText}`);
            }
            const cliente = await res.json();
            document.getElementById('clienteId').value = cliente.id;
            document.getElementById('clienteNombre').value = cliente.nombre;
            document.getElementById('clienteCedula').value = cliente.cedula;
            document.getElementById('clienteEmail').value = cliente.email;
            estadoUsuarioSelect.value = cliente.estado_usuario;

            contrasenaLabel.innerHTML = 'Nueva Contraseña (Opcional)';
            contrasenaInput.required = false;
            contrasenaInput.placeholder = 'Dejar en blanco para no cambiar';
            contrasenaHelp.textContent = 'Solo ingrese un valor si desea cambiar la contraseña actual.';

        } catch(error) {
            console.error("Error en openClienteModal (edit):", error);
            alert(`No se pudieron cargar los datos del cliente: ${error.message}`);
            return;
        }
    } else { // Modo Agregar
        modalTitle.textContent = 'Agregar Cliente';
        if(estadoUsuarioDiv) estadoUsuarioDiv.style.display = 'none'; // Ocultar campo de estado
        estadoUsuarioSelect.value = 'activo'; // Establecer valor por defecto aunque esté oculto

        contrasenaLabel.innerHTML = 'Contraseña <span class="text-danger">*</span>';
        contrasenaInput.required = true;
        contrasenaInput.placeholder = 'Ingrese la contraseña';
        contrasenaHelp.textContent = 'Requerida para nuevos clientes.';
    }
    if (window.clienteModal) window.clienteModal.show();
}

async function openMedicamentoModal(id = null) {
    const form = document.getElementById('medicamentoForm');
    form.reset();
    document.getElementById('medicamentoId').value = '';
    const modalTitle = document.getElementById('medicamentoModalTitle');

    const estadoSelect = document.getElementById('medicamentoEstado');
    const estadoMedicamentoDiv = document.getElementById('medicamentoEstadoDiv'); // Contenedor del select

    if (id) { // Modo Editar
        modalTitle.textContent = 'Editar Medicamento';
        if(estadoMedicamentoDiv) estadoMedicamentoDiv.style.display = 'block'; // Mostrar campo de estado
        try {
            const res = await fetch(`/api/admin/medicamentos/${id}`);
            if (!res.ok) {
                 const errorData = await res.json();
                 throw new Error(errorData.error || `Error al obtener datos del medicamento: ${res.statusText}`);
            }
            const med = await res.json();
            document.getElementById('medicamentoId').value = med.id;
            document.getElementById('medicamentoNombre').value = med.nombre || '';
            document.getElementById('medicamentoDescripcion').value = med.descripcion || '';
            document.getElementById('medicamentoComposicion').value = med.composicion || '';
            document.getElementById('medicamentoSintomasSecundarios').value = med.sintomas_secundarios || '';
            document.getElementById('medicamentoIndicaciones').value = med.indicaciones || '';
            document.getElementById('medicamentoRangoEdad').value = med.rango_edad || '';
            estadoSelect.value = med.estado_medicamento || 'disponible';
        } catch(error) {
            console.error("Error en openMedicamentoModal (edit):", error);
            alert(`No se pudieron cargar los datos del medicamento: ${error.message}`);
            return;
        }
    } else { // Modo Agregar
        modalTitle.textContent = 'Agregar Medicamento';
        if(estadoMedicamentoDiv) estadoMedicamentoDiv.style.display = 'none'; // Ocultar campo de estado
        estadoSelect.value = 'disponible'; // Establecer valor por defecto aunque esté oculto
    }
    if (window.medicamentoModal) window.medicamentoModal.show();
}

async function populateSelect(selectElement, apiUrl, valueField, textFieldParts, defaultOptionText, errorMessage) {
    selectElement.innerHTML = `<option value="" disabled selected>${defaultOptionText}</option>`;
    try {
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(errorMessage);
        const items = await response.json();
        items.forEach(item => {
            const text = textFieldParts.map(part => item[part]).join(' - ');
            const option = new Option(text, item[valueField]);
            selectElement.add(option);
        });
    } catch (error) {
        console.error(error);
        alert(error.message);
    }
}

async function openAlertaModal(alertaId = null) {
    const form = document.getElementById('alertaForm');
    form.reset();
    document.getElementById('alertaId').value = ''; 
    const modalTitle = document.getElementById('alertaModalLabel');
    const usuarioSelect = document.getElementById('alertaUsuario');
    const medicamentoSelect = document.getElementById('alertaMedicamento');
    const estadoSelect = document.getElementById('alertaEstado');

    // Populate dropdowns
    await populateSelect(usuarioSelect, '/api/admin/clientes?estado=activo', 'id', ['nombre', 'cedula'], 'Seleccione un cliente activo...', 'No se pudieron cargar los clientes.');
    await populateSelect(medicamentoSelect, '/api/admin/medicamentos?estado=disponible', 'id', ['nombre'], 'Seleccione un medicamento disponible...', 'No se pudieron cargar los medicamentos.');

    if (alertaId) {
        modalTitle.textContent = 'Editar Alerta';
        try {
            const res = await fetch(`/api/admin/alertas/${alertaId}`);
            if (!res.ok) {
                 const errorData = await res.json();
                 throw new Error(errorData.error || `Error al obtener datos de la alerta: ${res.statusText}`);
            }
            const alerta = await res.json();
            document.getElementById('alertaId').value = alerta.id;
            usuarioSelect.value = alerta.usuario_id;
            medicamentoSelect.value = alerta.medicamento_id;
            document.getElementById('alertaDosis').value = alerta.dosis || '';
            document.getElementById('alertaFrecuencia').value = alerta.frecuencia || '';
            document.getElementById('alertaFechaInicio').value = alerta.fecha_inicio ? alerta.fecha_inicio.split('T')[0] : '';
            document.getElementById('alertaFechaFin').value = alerta.fecha_fin ? alerta.fecha_fin.split('T')[0] : '';
            document.getElementById('alertaHoraPreferida').value = alerta.hora_preferida || '';
            estadoSelect.value = alerta.estado || 'activa';

        } catch (error) {
            console.error("Error al cargar datos de la alerta para editar:", error);
            alert(`No se pudieron cargar los datos de la alerta: ${error.message}`);
            return;
        }
    } else {
        modalTitle.textContent = 'Asignar Nueva Alerta';
        estadoSelect.value = 'activa'; // Default para nueva alerta
    }

    if (window.alertaModal) window.alertaModal.show();
}

document.addEventListener('DOMContentLoaded', () => {
    const auditoriaFilter = document.getElementById('auditoria-filter');
    if (auditoriaFilter) {
        auditoriaFilter.addEventListener('change', (e) => {
            const filter = e.target.value;
            if (typeof loadAuditoria === 'function') loadAuditoria(filter);
        });
    }
});