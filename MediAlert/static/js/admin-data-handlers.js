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
    if (!dateString || String(dateString).trim() === '') {
        return 'N/A';
    }
    try {
        // Asume que dateString es YYYY-MM-DD. Interpretar como UTC.
        const dateObj = new Date(dateString + 'T00:00:00Z');
        if (isNaN(dateObj.getTime())) {
            console.warn("formatDate creó una fecha inválida para el string:", dateString);
            return dateString; 
        }
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            timeZone: 'UTC'
        };
        return dateObj.toLocaleDateString('es-CO', options);
    } catch (e) {
        console.error("Error en formatDate para el string:", dateString, e);
        return dateString; 
    }
}

function formatTimestamp(timestampString) {
    if (!timestampString || String(timestampString).trim() === '') {
        return 'N/A';
    }
    try {
        // Asume que timestampString es un formato ISO completo que new Date() puede parsear.
        const dateObj = new Date(timestampString);
        if (isNaN(dateObj.getTime())) {
            console.warn("formatTimestamp creó una fecha inválida para el string:", timestampString);
            return timestampString;
        }
        const options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'UTC' // O la zona horaria que prefieras para mostrar. Si los timestamps son UTC en BD.
                           // Si quieres mostrar en la zona local del usuario, puedes omitir timeZone
                           // o usar Intl.DateTimeFormat().resolvedOptions().timeZone
        };
        return dateObj.toLocaleString('es-CO', options);
    } catch (e) {
        console.error("Error en formatTimestamp para el string:", timestampString, e);
        return timestampString;
    }
}

function formatTime(timeString) {
    if (!timeString) return 'N/A';
    const parts = timeString.split(':');
    if (parts.length >= 2) {
        const hours = parseInt(parts[0], 10);
        const minutes = parseInt(parts[1], 10);
        if (isNaN(hours) || isNaN(minutes)) {
            return timeString;
        }
        const d = new Date();
        d.setHours(hours, minutes, 0);
        return d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: true });
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
        const clientes = await fetchData('/api/admin/clientes?estado=todos&rol=cliente', 'Error al cargar clientes');
        tableBody.innerHTML = '';
        if (!clientes || clientes.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9" class="text-center">No hay clientes registrados.</td></tr>';
        } else {
            clientes.forEach(c => {
                const estadoBadgeClass = c.estado_usuario === 'activo' ? 'bg-success' : 'bg-danger';
                tableBody.innerHTML += `
                    <tr>
                        <td>${c.nombre || 'N/A'}</td>
                        <td>${c.cedula || 'N/A'}</td>
                        <td>${c.email || 'N/A'}</td>
                        <td>${c.telefono || 'N/A'}</td>
                        <td>${c.ciudad || 'N/A'}</td>
                        <td>${formatDate(c.fecha_nacimiento)}</td>
                        <td>${formatDate(c.fecha_registro)}</td>
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
        renderErrorRow(tableBody, 9, error);
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

// --- Funciones para la Vista de Auditoría ---

function getFriendlyTableName(tableName) {
    if (!tableName) return 'N/A';
    switch (tableName.toLowerCase()) {
        case 'usuarios': return 'Usuarios/Clientes';
        case 'medicamentos': return 'Medicamentos';
        case 'alertas': return 'Alertas';
        case 'auditoria': return 'Auditoría'; 
        case 'reportes_log': return 'Log de Reportes';
        default: 
            if (tableName.includes('_SESION') || tableName.includes('_LOGIN')) return 'Sesión';
            return tableName.charAt(0).toUpperCase() + tableName.slice(1);
    }
}

function formatAuditValue(value) {
    if (value === null || typeof value === 'undefined') return '<em>N/A</em>';
    if (typeof value === 'boolean') return value ? 'Sí' : 'No';
    
    if (typeof value === 'string') {
        // Regex para fecha YYYY-MM-DD
        const dateOnlyRegex = /^\d{4}-\d{2}-\d{2}$/;
        // Regex para timestamp YYYY-MM-DDTHH:mm:ss o con Z o con offset
        const timestampRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|([+-]\d{2}:\d{2}))?$/;

        if (timestampRegex.test(value)) {
            return formatTimestamp(value);
        } else if (dateOnlyRegex.test(value)) {
            return formatDate(value);
        }
    }
    
    if (typeof value === 'object') return `<pre class="mb-0 small">${JSON.stringify(value, null, 2)}</pre>`;
    return value.toString();
}


function generateChangeSummary(accion, datosAnteriores, datosNuevos) {
    let pDatosAnteriores = datosAnteriores, pDatosNuevos = datosNuevos;
    if (typeof datosAnteriores === 'string') {
        try { pDatosAnteriores = JSON.parse(datosAnteriores); } catch (e) { /* ignore */ }
    }
    if (typeof datosNuevos === 'string') {
        try { pDatosNuevos = JSON.parse(datosNuevos); } catch (e) { /* ignore */ }
    }

    let summary = '<ul class="list-unstyled mb-0 small">';
    let changesFound = false;
    const excludedKeys = ['contrasena', 'hashed_password', 'contrasena_nueva', 'updated_at', 'created_at', 'last_login', 'usuario_id_app'];

    if (accion && (accion.toUpperCase().includes('CREACI') || accion.toUpperCase().includes('INSERT') || accion.toUpperCase().includes('NUEVO'))) {
        summary += '<li><strong>Registro Creado:</strong></li>';
        if (pDatosNuevos && typeof pDatosNuevos === 'object') {
            for (const key in pDatosNuevos) {
                if (pDatosNuevos.hasOwnProperty(key) && !excludedKeys.includes(key.toLowerCase())) {
                    summary += `<li><strong>${key}:</strong> ${formatAuditValue(pDatosNuevos[key])}</li>`;
                    changesFound = true;
                }
            }
        }
    } else if (accion && (accion.toUpperCase().includes('ELIMINA') || accion.toUpperCase().includes('DELETE') || accion.toUpperCase().includes('BORRADO'))) {
        summary += '<li><strong>Registro Eliminado. Datos Anteriores:</strong></li>';
        if (pDatosAnteriores && typeof pDatosAnteriores === 'object') {
             for (const key in pDatosAnteriores) {
                if (pDatosAnteriores.hasOwnProperty(key) && !excludedKeys.includes(key.toLowerCase())) {
                    summary += `<li><strong>${key}:</strong> ${formatAuditValue(pDatosAnteriores[key])}</li>`;
                    changesFound = true;
                }
            }
        }
    } else if (pDatosNuevos && typeof pDatosNuevos === 'object' && pDatosAnteriores && typeof pDatosAnteriores === 'object') {
        summary += '<li><strong>Cambios Detectados:</strong></li>';
        const allKeys = new Set([...Object.keys(pDatosAnteriores), ...Object.keys(pDatosNuevos)]);
        allKeys.forEach(key => {
            if (excludedKeys.includes(key.toLowerCase())) return;

            const oldValue = pDatosAnteriores[key];
            const newValue = pDatosNuevos[key];

            if (JSON.stringify(oldValue) !== JSON.stringify(newValue)) {
                summary += `<li><strong>${key}:</strong> 
                            <span class="text-danger" style="text-decoration: line-through;">${formatAuditValue(oldValue)}</span> &rarr; 
                            <span class="text-success">${formatAuditValue(newValue)}</span></li>`;
                changesFound = true;
            }
        });
    } else if (pDatosNuevos && typeof pDatosNuevos === 'object') { 
        summary += '<li><strong>Datos Actualizados:</strong></li>';
        for (const key in pDatosNuevos) {
            if (pDatosNuevos.hasOwnProperty(key) && !excludedKeys.includes(key.toLowerCase())) {
                summary += `<li><strong>${key}:</strong> ${formatAuditValue(pDatosNuevos[key])}</li>`;
                changesFound = true;
            }
        }
    }

    if (!changesFound) {
        if (accion && (accion.toUpperCase().includes('SESION') || accion.toUpperCase().includes('LOGIN'))) {
             summary += `<li><small>Evento de ${accion.toLowerCase().replace(/_/g, ' ')}.</small></li>`;
        } else {
            summary += '<li><small>No se detectaron cambios de datos o son eventos generales.</small></li>';
        }
    }
    summary += '</ul>';
    return summary;
}


function formatJsonForDisplay(jsonData) { 
    if (jsonData === null || typeof jsonData === 'undefined') return 'N/A';
    if (typeof jsonData === 'string') {
        try { jsonData = JSON.parse(jsonData); } catch (e) { return `<small>${jsonData}</small>`; }
    }
    if (typeof jsonData === 'object') {
        let content = '<ul class="list-unstyled mb-0 small">';
        for(const [key, value] of Object.entries(jsonData)) {
            content += `<li><strong>${key}:</strong> ${formatAuditValue(value)}</li>`;
        }
        content += '</ul>';
        return content;
    }
    return `<small>${String(jsonData)}</small>`;
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
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center">No hay registros de auditoría disponibles para este filtro.</td></tr>';
            return;
        }

        logs.forEach((log) => {
            const row = tableBody.insertRow();
            row.insertCell().innerHTML = `<small>${formatTimestamp(log.fecha_hora)}</small>`;
            row.insertCell().innerHTML = `<small>${log.nombre_usuario_app || 'Sistema'}</small>`;
            row.insertCell().innerHTML = `<small>${log.accion ? log.accion.replace(/_/g, ' ') : 'N/A'}</small>`;
            row.insertCell().innerHTML = `<small>${getFriendlyTableName(log.tabla_afectada)}</small>`;
            row.insertCell().innerHTML = `<small>${log.registro_id_afectado !== null ? log.registro_id_afectado : 'N/A'}</small>`;
            
            const cambiosCell = row.insertCell();
            cambiosCell.innerHTML = generateChangeSummary(log.accion, log.datos_anteriores, log.datos_nuevos);
            
            const detallesAdicionalesCell = row.insertCell();
            detallesAdicionalesCell.innerHTML = formatJsonForDisplay(log.detalles_adicionales);
        });
    } catch (error) {
        renderErrorRow(tableBody, 7, error); 
    }
}


async function loadReportesLog() {
    const tableBody = document.getElementById('reportes-log-table-body');
    if (!tableBody) {
        console.warn("Elemento 'reportes-log-table-body' no encontrado en la vista actual.");
        return;
    }

    try {
        const logs = await fetchData('/api/admin/reportes_log', 'Error al cargar historial de reportes'); 
        tableBody.innerHTML = '';

        if (!logs || logs.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No hay reportes generados en el historial.</td></tr>';
            return;
        }

        logs.forEach(log => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = formatTimestamp(log.fecha_generacion);
            row.insertCell().textContent = log.nombre_reporte || 'N/A';
            row.insertCell().textContent = log.tipo_reporte ? log.tipo_reporte.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'N/A';
            row.insertCell().textContent = log.generado_por_nombre || 'Desconocido';
            
            const actionsCell = row.insertCell();
            const downloadButton = document.createElement('a'); 
            downloadButton.className = 'btn btn-sm btn-outline-primary bi bi-cloud-download'; 
            downloadButton.title = 'Descargar Reporte Almacenado';
            downloadButton.href = `/api/admin/reportes/download/${log.id}`; 
            
            actionsCell.appendChild(downloadButton);
        });

    } catch (error) {
        renderErrorRow(tableBody, 5, error); 
    }
}
