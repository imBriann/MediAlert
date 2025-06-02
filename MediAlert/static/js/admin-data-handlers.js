// static/js/admin-data-handlers.js

async function fetchData(url, errorMessagePrefix) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            let errorText = response.statusText;
            try {
                const errorData = await response.json();
                errorText = errorData.error || errorText;
            } catch (e) { /* Ignore if response is not JSON */ }
            throw new Error(`${errorMessagePrefix}: ${errorText} (${response.status})`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error in fetchData for ${url}:`, error);
        throw error; // Re-throw to be caught by caller
    }
}

function renderErrorRow(tableBody, colspan, error) {
    if (tableBody) {
        tableBody.innerHTML = `<tr><td colspan="${colspan}" class="text-center text-danger">Error al cargar los datos: ${error.message}</td></tr>`;
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        return new Date(dateString).toLocaleDateString();
    } catch (e) {
        return dateString; // Return original if parsing fails
    }
}

function formatTime(timeString) {
    if (!timeString) return 'N/A';
    // Assuming timeString is in "HH:MM:SS" or "HH:MM" format
    const [hours, minutes] = timeString.split(':');
    if (hours && minutes) {
        const d = new Date();
        d.setHours(parseInt(hours, 10), parseInt(minutes, 10), 0);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    }
    return timeString;
}


async function loadClientes() {
    const tableBody = document.getElementById('clientes-table-body');
    if (!tableBody) {
        console.error("Elemento 'clientes-table-body' no encontrado.");
        return;
    }
    try {
        const clientes = await fetchData('/api/admin/clientes?estado=todos', 'Error al cargar clientes');
        tableBody.innerHTML = '';
        if (!clientes || clientes.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No hay clientes registrados.</td></tr>';
        } else {
            clientes.forEach(c => {
                const estadoBadgeClass = c.estado_usuario === 'activo' ? 'bg-success' : 'bg-danger';
                tableBody.innerHTML += `
                    <tr>
                        <td>${c.nombre || 'N/A'}</td>
                        <td>${c.cedula || 'N/A'}</td>
                        <td>${c.email || 'N/A'}</td>
                        <td><span class="badge ${estadoBadgeClass}">${c.estado_usuario || 'N/A'}</span></td>
                        <td>
                            <button class="btn btn-sm btn-info btn-edit-cliente" data-id="${c.id}" title="Editar Cliente"><i class="bi bi-pencil-square"></i></button>
                            <button class="btn btn-sm btn-warning btn-delete-cliente" data-id="${c.id}" data-nombre="${c.nombre}" title="${c.estado_usuario === 'activo' ? 'Desactivar' : 'Reactivar'} Cliente">
                                <i class="bi ${c.estado_usuario === 'activo' ? 'bi-person-slash' : 'bi-person-check'}"></i>
                            </button>
                        </td>
                    </tr>`;
            });
        }
    } catch (error) {
        renderErrorRow(tableBody, 5, error);
    }
}

async function loadMedicamentos() {
    const tableBody = document.getElementById('medicamentos-table-body');
     if (!tableBody) {
        console.error("Elemento 'medicamentos-table-body' no encontrado.");
        return;
    }
    try {
        const medicamentos = await fetchData('/api/admin/medicamentos?estado=todos', 'Error al cargar medicamentos');
        tableBody.innerHTML = '';
        if (!medicamentos || medicamentos.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No hay medicamentos registrados.</td></tr>';
        } else {
            medicamentos.forEach(m => {
                const estadoBadgeClass = m.estado_medicamento === 'disponible' ? 'bg-success' : 'bg-danger';
                tableBody.innerHTML += `
                    <tr>
                        <td>${m.nombre || 'N/A'}</td>
                        <td class="text-truncate" style="max-width: 200px;">${m.descripcion || 'N/A'}</td>
                        <td class="text-truncate" style="max-width: 200px;">${m.composicion || 'N/A'}</td>
                        <td><span class="badge ${estadoBadgeClass}">${m.estado_medicamento || 'N/A'}</span></td>
                        <td>
                            <button class="btn btn-sm btn-info btn-edit-medicamento" data-id="${m.id}" title="Editar Medicamento">
                                <i class="bi bi-pencil-square"></i>
                            </button>
                            <button class="btn btn-sm btn-warning btn-delete-medicamento" data-id="${m.id}" data-nombre="${m.nombre}" title="${m.estado_medicamento === 'disponible' ? 'Discontinuar' : 'Reactivar'} Medicamento">
                                <i class="bi ${m.estado_medicamento === 'disponible' ? 'bi-capsule-pill' : 'bi-capsule'}"></i> </button>
                        </td>
                    </tr>`;
            });
        }
    } catch (error) {
        renderErrorRow(tableBody, 5, error);
    }
}

async function loadAlertas() {
    const tableBody = document.getElementById('alertas-table-body');
    if (!tableBody) {
        console.error("Elemento 'alertas-table-body' no encontrado.");
        return;
    }
    try {
        const alertas = await fetchData('/api/admin/alertas', 'Error al cargar alertas');
        tableBody.innerHTML = ''; 

        if (!alertas || alertas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9" class="text-center">No hay alertas registradas.</td></tr>';
            return;
        }

        alertas.forEach(a => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = a.cliente_nombre || 'N/A';
            row.insertCell().textContent = a.medicamento_nombre || 'N/A';
            row.insertCell().textContent = a.dosis || 'N/A';
            row.insertCell().textContent = a.frecuencia || 'N/A';
            row.insertCell().textContent = formatDate(a.fecha_inicio);
            row.insertCell().textContent = formatDate(a.fecha_fin);
            row.insertCell().textContent = formatTime(a.hora_preferida);
            
            const estadoCell = row.insertCell();
            const estadoBadge = document.createElement('span');
            let estadoClass = 'bg-secondary'; 
            if (a.estado_alerta === 'activa') estadoClass = 'bg-success';
            else if (a.estado_alerta === 'completada') estadoClass = 'bg-info';
            else if (a.estado_alerta === 'inactiva') estadoClass = 'bg-warning';
            else if (a.estado_alerta === 'fallida') estadoClass = 'bg-danger';
            estadoBadge.className = `badge ${estadoClass}`;
            estadoBadge.textContent = a.estado_alerta || 'N/A';
            estadoCell.appendChild(estadoBadge);
            
            row.insertCell().innerHTML = `
                <button class="btn btn-sm btn-info btn-edit-alerta" data-id="${a.id}" title="Editar Alerta"><i class="bi bi-pencil-square"></i></button>
                <button class="btn btn-sm btn-danger btn-delete-alerta" data-id="${a.id}" title="Eliminar Alerta"><i class="bi bi-trash"></i></button>
            `;
        });
    } catch (error) {
         renderErrorRow(tableBody, 9, error);
    }
}

function formatJsonForDisplay(jsonData) {
    if (jsonData === null || typeof jsonData === 'undefined') return 'N/A';
    if (typeof jsonData === 'string') {
        try { jsonData = JSON.parse(jsonData); } catch (e) { return jsonData; }
    }
    if (typeof jsonData === 'object') {
        return Object.entries(jsonData)
            .map(([key, value]) => `${key}: ${value}`)
            .join('; ') || 'Vacío';
    }
    return String(jsonData);
}


async function loadAuditoria(filter = '') {
    const tableBody = document.getElementById('auditoria-table-body');
    if (!tableBody) {
        console.error("Elemento 'auditoria-table-body' no encontrado.");
        return;
    }
    try {
        const url = filter ? `/api/admin/auditoria?tabla=${filter}` : '/api/admin/auditoria';
        const logs = await fetchData(url, 'Error al cargar auditoría');
        tableBody.innerHTML = ''; 

        if (!logs || logs.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9" class="text-center">No hay registros de auditoría.</td></tr>';
            return;
        }

        logs.forEach((log, index) => {
            const row = tableBody.insertRow();
            row.className = index % 2 === 0 ? 'table-light' : 'table-secondary';
            row.insertCell().textContent = log.fecha_hora ? new Date(log.fecha_hora).toLocaleString() : 'N/A';
            row.insertCell().textContent = log.nombre_usuario_app || 'Sistema';
            row.insertCell().textContent = log.usuario_postgres || 'N/A';
            row.insertCell().textContent = log.accion || 'N/A';
            row.insertCell().textContent = log.tabla_afectada || 'N/A';
            row.insertCell().textContent = log.registro_id_afectado !== null ? log.registro_id_afectado : 'N/A';
            
            const datosAnterioresCell = row.insertCell();
            datosAnterioresCell.innerHTML = `<small>${formatJsonForDisplay(log.datos_anteriores)}</small>`;
            
            const datosNuevosCell = row.insertCell();
            datosNuevosCell.innerHTML = `<small>${formatJsonForDisplay(log.datos_nuevos)}</small>`;

            const detallesAdicionalesCell = row.insertCell();
            detallesAdicionalesCell.innerHTML = `<small>${formatJsonForDisplay(log.detalles_adicionales)}</small>`;
        });
    } catch (error) {
        renderErrorRow(tableBody, 9, error);
    }
}