// static/js/admin-data-handlers.js

async function loadClientes() {
    const response = await fetch('/api/admin/clientes');
    const clientes = await response.json();
    const tableBody = document.getElementById('clientes-table-body');
    tableBody.innerHTML = '';
    if (clientes.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No hay clientes registrados.</td></tr>';
    } else {
        clientes.forEach(c => {
            tableBody.innerHTML += `
                <tr>
                    <td>${c.nombre}</td>
                    <td>${c.cedula}</td>
                    <td>${c.email}</td>
                    <td>
                        <button class="btn btn-sm btn-info btn-edit-cliente" data-id="${c.id}"><i class="bi bi-pencil-square"></i> Editar</button>
                        <button class="btn btn-sm btn-danger btn-delete-cliente" data-id="${c.id}"><i class="bi bi-trash"></i> Eliminar</button>
                    </td>
                </tr>`;
        });
    }
}

async function loadMedicamentos() {
    const response = await fetch('/api/admin/medicamentos');
    const medicamentos = await response.json();
    const tableBody = document.getElementById('medicamentos-table-body');
    tableBody.innerHTML = '';
    medicamentos.forEach(m => {
        tableBody.innerHTML += `
            <tr>
                <td>${m.nombre}</td>
                <td>${m.descripcion || 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-info btn-edit-medicamento" 
                            data-id="${m.id}" 
                            data-nombre="${m.nombre}" 
                            data-descripcion="${m.descripcion || ''}">
                        <i class="bi bi-pencil-square"></i> Editar
                    </button>
                    <button class="btn btn-sm btn-danger btn-delete-medicamento" data-id="${m.id}">
                        <i class="bi bi-trash"></i> Eliminar
                    </button>
                </td>
            </tr>`;
    });
}

async function loadAlertas() {
    try {
        const response = await fetch('/api/admin/alertas');
        if (!response.ok) {
            throw new Error(`Error al cargar las alertas: ${response.statusText} (${response.status})`);
        }
        const alertas = await response.json();
        const tableBody = document.getElementById('alertas-table-body');
        tableBody.innerHTML = ''; // Limpiar tabla anterior

        if (!alertas || alertas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No hay alertas registradas.</td></tr>';
            return;
        }

        alertas.forEach(a => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = a.cliente_nombre || 'N/A';
            row.insertCell().textContent = a.medicamento_nombre || 'N/A';
            row.insertCell().textContent = a.dosis || 'N/A';
            row.insertCell().textContent = a.frecuencia || 'N/A';
            
            const estadoCell = row.insertCell();
            const estadoBadge = document.createElement('span');
            estadoBadge.className = `badge bg-${a.estado === 'activa' ? 'success' : 'secondary'}`;
            estadoBadge.textContent = a.estado || 'N/A';
            estadoCell.appendChild(estadoBadge);
            
            // Celda de acciones (puedes agregar botones aquí si es necesario en el futuro)
            row.insertCell().innerHTML = ``;
        });
    } catch (error) {
        console.error("Error en loadAlertas:", error);
        const tableBody = document.getElementById('alertas-table-body');
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error al cargar los datos de alertas: ${error.message}</td></tr>`;
        }
    }
}

async function loadAuditoria() {
    try {
        const response = await fetch('/api/admin/auditoria');
        if (!response.ok) {
            throw new Error(`Error al cargar la auditoría: ${response.statusText} (${response.status})`);
        }
        const logs = await response.json();
        const tableBody = document.getElementById('auditoria-table-body');
        tableBody.innerHTML = ''; // Limpiar tabla anterior

        if (!logs || logs.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No hay registros de auditoría.</td></tr>';
            return;
        }

        logs.forEach(log => {
            const row = tableBody.insertRow();
            const fechaHora = log.fecha_hora ? new Date(log.fecha_hora).toLocaleString() : 'N/A';
            row.insertCell().textContent = fechaHora;
            row.insertCell().textContent = log.admin_nombre || 'N/A';
            row.insertCell().textContent = log.accion || 'N/A';
            row.insertCell().textContent = log.tabla_afectada || 'N/A';
            row.insertCell().textContent = log.registro_id !== null ? log.registro_id : 'N/A';
            
            let detallesFormateados = 'N/A';
            if (log.detalles) {
                try {
                    const detallesObj = (typeof log.detalles === 'string') ? JSON.parse(log.detalles) : log.detalles;
                    if (typeof detallesObj === 'object' && detallesObj !== null) {
                        detallesFormateados = Object.entries(detallesObj)
                            .map(([key, value]) => `${key}: ${value}`)
                            .join('; ');
                    } else {
                        detallesFormateados = log.detalles;
                    }
                } catch (e) {
                    detallesFormateados = log.detalles; 
                }
            }
            row.insertCell().textContent = detallesFormateados;
        });
    } catch (error) {
        console.error("Error en loadAuditoria:", error);
        const tableBody = document.getElementById('auditoria-table-body');
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error al cargar los datos de auditoría: ${error.message}</td></tr>`;
        }
    }
}