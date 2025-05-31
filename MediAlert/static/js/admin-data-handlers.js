// static/js/admin-data-handlers.js

async function loadClientes() {
    try {
        const response = await fetch('/api/admin/clientes');
        if (!response.ok) {
            throw new Error(`Error al cargar clientes: ${response.statusText} (${response.status})`);
        }
        const clientes = await response.json();
        const tableBody = document.getElementById('clientes-table-body');
        if (!tableBody) {
            console.error("Elemento 'clientes-table-body' no encontrado.");
            return;
        }
        tableBody.innerHTML = '';
        if (!clientes || clientes.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No hay clientes registrados.</td></tr>';
        } else {
            clientes.forEach(c => {
                tableBody.innerHTML += `
                    <tr>
                        <td>${c.nombre || 'N/A'}</td>
                        <td>${c.cedula || 'N/A'}</td>
                        <td>${c.email || 'N/A'}</td>
                        <td>
                            <button class="btn btn-sm btn-info btn-edit-cliente" data-id="${c.id}"><i class="bi bi-pencil-square"></i> Editar</button>
                            <button class="btn btn-sm btn-danger btn-delete-cliente" data-id="${c.id}"><i class="bi bi-trash"></i> Eliminar</button>
                        </td>
                    </tr>`;
            });
        }
    } catch (error) {
        console.error("Error en loadClientes:", error);
        const tableBody = document.getElementById('clientes-table-body');
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error al cargar los datos de clientes: ${error.message}</td></tr>`;
        }
    }
}

async function loadMedicamentos() {
    try {
        const response = await fetch('/api/admin/medicamentos');
        if (!response.ok) {
            throw new Error(`Error al cargar medicamentos: ${response.statusText} (${response.status})`);
        }
        const medicamentos = await response.json();
        const tableBody = document.getElementById('medicamentos-table-body');
        if (!tableBody) {
            console.error("Elemento 'medicamentos-table-body' no encontrado.");
            return;
        }
        tableBody.innerHTML = '';
        if (!medicamentos || medicamentos.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="3" class="text-center">No hay medicamentos registrados.</td></tr>';
        } else {
            medicamentos.forEach(m => {
                tableBody.innerHTML += `
                    <tr>
                        <td>${m.nombre || 'N/A'}</td>
                        <td>${m.descripcion || 'N/A'}</td>
                        <td>
                            <button class="btn btn-sm btn-info btn-edit-medicamento" 
                                    data-id="${m.id}" 
                                    data-nombre="${m.nombre || ''}" 
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
    } catch (error) {
        console.error("Error en loadMedicamentos:", error);
        const tableBody = document.getElementById('medicamentos-table-body');
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="3" class="text-center text-danger">Error al cargar los datos de medicamentos: ${error.message}</td></tr>`;
        }
    }
}

async function loadAlertas() {
    try {
        const response = await fetch('/api/admin/alertas');
        if (!response.ok) {
            throw new Error(`Error al cargar las alertas: ${response.statusText} (${response.status})`);
        }
        const alertas = await response.json();
        const tableBody = document.getElementById('alertas-table-body');
        if (!tableBody) {
            console.error("Elemento 'alertas-table-body' no encontrado.");
            return;
        }
        tableBody.innerHTML = ''; 

        if (!alertas || alertas.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" class="text-center">No hay alertas registradas.</td></tr>';
            return;
        }

        alertas.forEach(a => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = a.cliente_nombre || 'N/A';
            row.insertCell().textContent = a.medicamento_nombre || 'N/A';
            row.insertCell().textContent = a.dosis || 'N/A';
            row.insertCell().textContent = a.frecuencia || 'N/A';
            
            // Corrección para formato de fecha
            row.insertCell().textContent = a.fecha_inicio ? new Date(a.fecha_inicio).toLocaleDateString() : 'N/A';
            row.insertCell().textContent = a.fecha_fin ? new Date(a.fecha_fin).toLocaleDateString() : 'N/A';
            
            const estadoCell = row.insertCell();
            const estadoBadge = document.createElement('span');
            let estadoClass = 'bg-secondary'; 
            if (a.estado === 'activa') {
                estadoClass = 'bg-success';
            } else if (a.estado === 'completada') {
                estadoClass = 'bg-info'; // Cambiado a info para diferenciar de inactiva
            } else if (a.estado === 'inactiva') { 
                estadoClass = 'bg-warning';
            }
            estadoBadge.className = `badge ${estadoClass}`;
            estadoBadge.textContent = a.estado || 'N/A';
            estadoCell.appendChild(estadoBadge);
            
            // Botones de acciones para alertas (habilitados)
            row.insertCell().innerHTML = `
                <button class="btn btn-sm btn-info btn-edit-alerta" data-id="${a.id}" title="Editar Alerta"><i class="bi bi-pencil-square"></i></button>
                <button class="btn btn-sm btn-danger btn-delete-alerta" data-id="${a.id}" title="Eliminar Alerta"><i class="bi bi-trash"></i></button>
            `;
        });
    } catch (error) {
        console.error("Error en loadAlertas:", error);
        const tableBody = document.getElementById('alertas-table-body');
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error al cargar los datos de alertas: ${error.message}</td></tr>`;
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
        if (!tableBody) {
            console.error("Elemento 'auditoria-table-body' no encontrado.");
            return;
        }
        tableBody.innerHTML = ''; 

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
                    // Intenta parsear si es un string JSON, sino lo muestra tal cual
                    const detallesObj = (typeof log.detalles === 'string') ? JSON.parse(log.detalles) : log.detalles;
                    if (typeof detallesObj === 'object' && detallesObj !== null) {
                        detallesFormateados = Object.entries(detallesObj)
                            .map(([key, value]) => `${key}: ${value}`)
                            .join('; ');
                    } else {
                        detallesFormateados = String(log.detalles); // Si no es objeto, lo convierte a string
                    }
                } catch (e) {
                    // Si hay error al parsear (ej. no es JSON válido), mostrar como string original.
                    detallesFormateados = String(log.detalles); 
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