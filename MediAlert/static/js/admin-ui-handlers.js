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
        case 'view-reportes': if(typeof loadReportesLog === 'function') loadReportesLog(); break;
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
    const estadoUsuarioDiv = document.getElementById('clienteEstadoUsuarioDiv');

    const telefonoInput = document.getElementById('clienteTelefono');
    const ciudadInput = document.getElementById('clienteCiudad');
    const fechaNacimientoInput = document.getElementById('clienteFechaNacimiento');
    const epsSelect = document.getElementById('clienteEps');

    // FIX: Change API URL from '/api/eps' to '/api/admin/eps'
    await populateSelect(epsSelect, '/api/admin/eps', 'id', ['nombre'], 'Seleccione una EPS...', 'No se pudieron cargar las EPS.');

    if (id) { // Modo Editar
        modalTitle.textContent = 'Editar Cliente';
        if(estadoUsuarioDiv) estadoUsuarioDiv.style.display = 'block';
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

            telefonoInput.value = cliente.telefono || '';
            ciudadInput.value = cliente.ciudad || '';
            fechaNacimientoInput.value = cliente.fecha_nacimiento ? cliente.fecha_nacimiento.split('T')[0] : '';
            epsSelect.value = cliente.eps_id || '';

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
        if(estadoUsuarioDiv) estadoUsuarioDiv.style.display = 'none';
        estadoUsuarioSelect.value = 'activo';

        telefonoInput.value = '';
        ciudadInput.value = '';
        fechaNacimientoInput.value = '';
        epsSelect.value = '';

        contrasenaLabel.innerHTML = 'Contraseña <span class="text-danger">*</span>';
        contrasenaInput.required = true;
        contrasenaInput.placeholder = 'Ingrese la contraseña';
        contrasenaHelp.textContent = 'Requerida para nuevos clientes.';
    }
    if (window.clienteModal) window.clienteModal.show();
}

async function openClientDetailModal(clientId) {
    const clientDetailContent = document.getElementById('clientDetailContent');
    const clientAlertsTableBody = document.getElementById('clientDetailAlertasTableBody');
    const modalLabel = document.getElementById('clientDetailModalLabel');

    if (!clientDetailContent || !clientAlertsTableBody || !modalLabel) {
        console.error('Elementos del modal de detalle de cliente no encontrados.');
        return;
    }

    if (!window.clientDetailModalInstance) {
        const modalElement = document.getElementById('clientDetailModal');
        if (modalElement) {
            window.clientDetailModalInstance = new bootstrap.Modal(modalElement);
        } else {
            console.error("Modal element #clientDetailModal not found for instantiation.");
            return;
        }
    }

    clientDetailContent.innerHTML = '<div class="text-center p-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p>Cargando detalles del cliente...</p></div>';
    clientAlertsTableBody.innerHTML = '<tr><td colspan="8" class="text-center"><div class="spinner-border spinner-border-sm" role="status"></div> Cargando alertas...</td></tr>';
    modalLabel.textContent = 'Detalles del Cliente';

    try {
        const clientRes = await fetch(`/api/admin/clientes/${clientId}`);
        if (!clientRes.ok) {
            const errData = await clientRes.json();
            throw new Error(errData.error || 'Error al cargar datos del cliente.');
        }
        const client = await clientRes.json();
        modalLabel.textContent = `Detalles de: ${client.nombre}`;

        clientDetailContent.innerHTML = `
            <dl class="row">
                <dt class="col-sm-3">Nombre:</dt><dd class="col-sm-9">${client.nombre || 'N/A'}</dd>
                <dt class="col-sm-3">Cédula:</dt><dd class="col-sm-9">${client.cedula || 'N/A'}</dd>
                <dt class="col-sm-3">Email:</dt><dd class="col-sm-9">${client.email || 'N/A'}</dd>
                <dt class="col-sm-3">Teléfono:</dt><dd class="col-sm-9">${client.telefono || 'N/A'}</dd>
                <dt class="col-sm-3">Ciudad:</dt><dd class="col-sm-9">${client.ciudad || 'N/A'}</dd>
                <dt class="col-sm-3">EPS:</dt><dd class="col-sm-9">${client.eps_nombre || 'N/A'}</dd>
                <dt class="col-sm-3">Fec. Nacimiento:</dt><dd class="col-sm-9">${formatDate(client.fecha_nacimiento)}</dd>
                <dt class="col-sm-3">Fec. Registro:</dt><dd class="col-sm-9">${formatDate(client.fecha_registro)}</dd>
                <dt class="col-sm-3">Estado:</dt><dd class="col-sm-9"><span class="badge ${client.estado_usuario === 'activo' ? 'bg-success' : 'bg-danger'}">${client.estado_usuario || 'N/A'}</span></dd>
                <dt class="col-sm-3">Rol:</dt><dd class="col-sm-9">${client.rol || 'N/A'}</dd>
            </dl>
            <div class="d-flex justify-content-center mt-3">
                <button class="btn btn-primary btn-sm" id="btn-download-client-consolidated-receta" data-client-id="${client.id}" data-client-name="${client.nombre}">
                    <i class="bi bi-file-earmark-medical-fill"></i> Descargar Receta Consolidada Activa
                </button>
            </div>
        `;

        const alertasRes = await fetch(`/api/admin/alertas?usuario_id=${clientId}`);
        if (!alertasRes.ok) {
             const errAlertData = await alertasRes.json();
            throw new Error(errAlertData.error || 'Error al cargar alertas del cliente.');
        }
        const clientAlertas = await alertasRes.json();

        clientAlertsTableBody.innerHTML = '';
        if (clientAlertas.length === 0) {
            clientAlertsTableBody.innerHTML = '<tr><td colspan="8" class="text-center fst-italic">Este cliente no tiene alertas asignadas.</td></tr>';
        } else {
            clientAlertas.forEach(a => {
                const estadoAlertBadgeClass = a.estado_alerta === 'activa' ? 'bg-success' :
                                       a.estado_alerta === 'completada' ? 'bg-info text-dark' :
                                       a.estado_alerta === 'inactiva' ? 'bg-warning text-dark' :
                                       a.estado_alerta === 'fallida' ? 'bg-danger' : 'bg-secondary';

                const printButtonHtml = `<button class="btn btn-sm btn-outline-secondary ms-2 btn-print-receta" data-alerta-id="${a.id}" title="Imprimir Receta Médica">
                                            <i class="bi bi-printer"></i> Receta
                                        </button>`;

                clientAlertsTableBody.innerHTML += `
                    <tr>
                        <td>${a.medicamento_nombre || 'N/A'}</td>
                        <td>${a.dosis || 'N/A'}</td>
                        <td>${a.frecuencia || 'N/A'}</td>
                        <td>${formatDate(a.fecha_inicio)}</td>
                        <td>${formatDate(a.fecha_fin)}</td>
                        <td>${formatTime(a.hora_preferida)}</td>
                        <td><span class="badge ${estadoAlertBadgeClass}">${a.estado_alerta || 'N/A'}</span></td>
                        <td>${printButtonHtml}</td> </tr>`;
            });
        }
        if (window.clientDetailModalInstance) window.clientDetailModalInstance.show();

    } catch (error) {
        console.error('Error en openClientDetailModal:', error);
        modalLabel.textContent = 'Error al Cargar Detalles';
        clientDetailContent.innerHTML = `<div class="alert alert-danger">No se pudieron cargar los detalles del cliente: ${error.message}</div>`;
        clientAlertsTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error al cargar alertas.</td></tr>`;
        if (window.clientDetailModalInstance) window.clientDetailModalInstance.show();
    }
}

async function openMedicamentoModal(id = null) {
    const form = document.getElementById('medicamentoForm');
    form.reset();
    document.getElementById('medicamentoId').value = '';
    const modalTitle = document.getElementById('medicamentoModalTitle');

    const estadoSelect = document.getElementById('medicamentoEstado');
    const estadoMedicamentoDiv = document.getElementById('medicamentoEstadoDiv');

    if (id) { // Modo Editar
        modalTitle.textContent = 'Editar Medicamento';
        if(estadoMedicamentoDiv) estadoMedicamentoDiv.style.display = 'block';
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
        if(estadoMedicamentoDiv) estadoMedicamentoDiv.style.display = 'none';
        estadoSelect.value = 'disponible';
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
            const text = textFieldParts.map(part => item[part]).filter(Boolean).join(' - ');
            const option = new Option(text, item[valueField]);
            selectElement.add(option);
        });
    }
     catch (error) {
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
    // FIX: Change API URL from '/api/admin/clientes?estado=activo&rol=cliente' to '/api/admin/clientes?estado=activo&rol=cliente' (already correct from previous fix)
    await populateSelect(usuarioSelect, '/api/admin/clientes?estado=activo&rol=cliente', 'id', ['nombre', 'cedula'], 'Seleccione un cliente activo...', 'No se pudieron cargar los clientes.');
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
        estadoSelect.value = 'activa';
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