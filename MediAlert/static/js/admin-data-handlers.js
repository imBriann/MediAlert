// static/js/admin-data-handlers.js

// originalData arrays and formatters are now in shared-utils.js

async function loadClientes(searchTerm = '') {
    const cardContainer = document.getElementById('clientes-card-container');
    if (!cardContainer) {
        console.error("Elemento 'clientes-card-container' no encontrado.");
        return;
    }
    try {
        if (originalClientesData.length === 0) { // Fetch only if not already fetched
            originalClientesData = await fetchData('/api/admin/clientes?rol=cliente&estado=todos', 'Error al cargar clientes');
            
            // NEW: Sort data after fetching
            originalClientesData.sort((a, b) => {
                // Primary sort: 'activo' users first
                const statusA = a.estado_usuario === 'activo' ? 0 : 1;
                const statusB = b.estado_usuario === 'activo' ? 0 : 1;
                if (statusA !== statusB) {
                    return statusA - statusB;
                }
                // Secondary sort: alphabetically by name
                return (a.nombre || '').localeCompare(b.nombre || '');
            });
        }
        
        const normalizedSearchTerm = searchTerm.toLowerCase().trim();
        const filteredClientes = originalClientesData.filter(c => {
            const nombre = c.nombre ? c.nombre.toLowerCase() : '';
            const cedula = c.cedula ? c.cedula.toLowerCase() : '';
            return nombre.includes(normalizedSearchTerm) || cedula.includes(normalizedSearchTerm);
        });

        cardContainer.innerHTML = ''; 

        if (!filteredClientes || filteredClientes.length === 0) {
            cardContainer.innerHTML = `<div class="col-12"><p class="text-center">No hay clientes ${normalizedSearchTerm ? 'que coincidan con la búsqueda' : 'registrados'}.</p></div>`;
        } else {
            filteredClientes.forEach(c => {
                const estadoBadgeClass = c.estado_usuario === 'activo' ? 'bg-success' : 'bg-danger';
                const toggleButtonIcon = c.estado_usuario === 'activo' ? 'bi-person-slash' : 'bi-person-check';
                const toggleButtonText = c.estado_usuario === 'activo' ? 'Desactivar' : 'Reactivar';
                const toggleButtonTitle = c.estado_usuario === 'activo' ? 'Desactivar Cliente' : 'Reactivar Cliente';

                cardContainer.innerHTML += `
                    <div class="col">
                        <div class="card h-100 shadow-sm">
                            <div class="card-body client-card-clickable-area" data-id="${c.id}">
                                <h5 class="card-title mb-2">${c.nombre || 'N/A'}</h5>
                                <p class="card-text mb-1">
                                    <small class="text-muted">CC: ${c.cedula || 'N/A'}</small>
                                </p>
                                <p class="card-text mb-2">
                                    <span class="badge ${estadoBadgeClass}">${c.estado_usuario || 'N/A'}</span>
                                </p>
                            </div>
                            <div class="card-footer">
                                <div class="d-flex justify-content-start flex-wrap">
                                    <button class="btn btn-sm btn-info btn-edit-cliente me-2 mb-1" data-id="${c.id}" title="Editar Cliente">
                                        <i class="bi bi-pencil-square"></i> Editar
                                    </button>
                                    <button class="btn btn-sm btn-warning btn-toggle-status-cliente me-2 mb-1" data-id="${c.id}" data-nombre="${c.nombre}" data-status="${c.estado_usuario}" title="${toggleButtonTitle}">
                                        <i class="bi ${toggleButtonIcon}"></i> ${toggleButtonText}
                                    </button>
                                    <button class="btn btn-sm btn-primary btn-view-cliente mb-1" data-id="${c.id}" title="Ver Detalles Completos">
                                        <i class="bi bi-eye-fill"></i> Ver
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>`;
            });
        }
    } catch (error) {
        if (cardContainer) {
            cardContainer.innerHTML = `<div class="col-12"><p class="text-center text-danger">Error al cargar los datos de clientes: ${error.message}</p></div>`;
        }
        console.error("Error en loadClientes:", error);
    }
}

async function loadMedicamentos(searchTerm = '') {
    const tableBody = document.getElementById('medicamentos-table-body');
    if (!tableBody) {
        console.error("Elemento 'medicamentos-table-body' no encontrado.");
        return;
    }

    try {
        if (originalMedicamentosData.length === 0) {
            originalMedicamentosData = await fetchData('/api/admin/medicamentos?estado=todos', 'Error al cargar medicamentos');
            
            // NEW: Sort data after fetching
            originalMedicamentosData.sort((a, b) => {
                // Primary sort: 'disponible' medicines first
                const statusA = a.estado_medicamento === 'disponible' ? 0 : 1;
                const statusB = b.estado_medicamento === 'disponible' ? 0 : 1;
                if (statusA !== statusB) {
                    return statusA - statusB;
                }
                // Secondary sort: alphabetically by name
                return (a.nombre || '').localeCompare(b.nombre || '');
            });
        }

        const normalizedSearchTerm = searchTerm.toLowerCase().trim();
        const filteredMedicamentos = originalMedicamentosData.filter(m => {
            const nombre = m.nombre ? m.nombre.toLowerCase() : '';
            return nombre.includes(normalizedSearchTerm);
        });

        tableBody.innerHTML = '';
        if (!filteredMedicamentos || filteredMedicamentos.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="text-center">No hay medicamentos ${searchTerm ? 'que coincidan con la búsqueda' : 'registrados'}.</td></tr>`;
        } else {
            filteredMedicamentos.forEach(m => {
                const estadoBadgeClass = m.estado_medicamento === 'disponible' ? 'bg-success' : 'bg-danger';
                const toggleButtonIcon = m.estado_medicamento === 'disponible' ? 'bi-capsule' : 'bi-capsule-pill';
                const toggleButtonTitle = m.estado_medicamento === 'disponible' ? 'Discontinuar' : 'Reactivar';
                
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
                            <button class="btn btn-sm btn-warning btn-delete-medicamento" data-id="${m.id}" data-nombre="${m.nombre}" title="${toggleButtonTitle} Medicamento">
                                <i class="bi ${toggleButtonIcon}"></i>
                            </button>
                        </td>
                    </tr>`;
            });
        }
    } catch (error) {
        renderErrorRow(tableBody, 5, error);
    }
}

async function loadAlertas(searchQuery = '') {
    const tableBody = document.getElementById('clientes-con-alertas-table-body');
    if (!tableBody) {
        console.error("Elemento 'clientes-con-alertas-table-body' no encontrado.");
        return;
    }

    try {
        if (originalClientesConAlertasData.length === 0) {
            const url = '/api/admin/alertas?group_by_client=true';
            originalClientesConAlertasData = await fetchData(url, 'Error al cargar clientes con alertas');

            // NEW: Sort data after fetching
            originalClientesConAlertasData.sort((a, b) => {
                // Primary sort: 'activo' users first
                const statusA = a.estado_usuario === 'activo' ? 0 : 1;
                const statusB = b.estado_usuario === 'activo' ? 0 : 1;
                if (statusA !== statusB) {
                    return statusA - statusB;
                }
                // Secondary sort: alphabetically by client name
                return (a.cliente_nombre || '').localeCompare(b.cliente_nombre || '');
            });
        }

        const normalizedSearchTerm = searchQuery.toLowerCase().trim();
        const filteredData = originalClientesConAlertasData.filter(c => {
            const nombre = c.cliente_nombre ? c.cliente_nombre.toLowerCase() : '';
            const cedula = c.cedula ? c.cedula.toLowerCase() : '';
            return nombre.includes(normalizedSearchTerm) || cedula.includes(normalizedSearchTerm);
        });

        tableBody.innerHTML = '';
        if (!filteredData || filteredData.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="text-center">No hay clientes ${searchQuery ? 'que coincidan con la búsqueda' : 'con alertas registradas'}.</td></tr>`;
            return;
        }

        filteredData.forEach(c => {
            const estadoBadgeClass = c.estado_usuario === 'activo' ? 'bg-success' : 'bg-danger';
            const row = tableBody.insertRow();
            row.insertCell().textContent = c.cliente_nombre || 'N/A';
            row.insertCell().textContent = c.cedula || 'N/A';
            row.insertCell().innerHTML = `<span class="badge ${estadoBadgeClass}">${c.estado_usuario || 'N/A'}</span>`;
            row.insertCell().textContent = c.alertas_activas_count !== null ? c.alertas_activas_count : '0';

            const actionsCell = row.insertCell();
            actionsCell.innerHTML = `
                <button class="btn btn-sm btn-primary btn-view-cliente-alerts" data-id="${c.usuario_id}" title="Ver Alertas del Cliente">
                    <i class="bi bi-eye-fill"></i> Ver Alertas (${c.total_alertas_count})
                </button>
            `;
        });
    } catch (error) {
        renderErrorRow(tableBody, 5, error);
    }
}

// --- Funciones para la Vista de Auditoría --- (Now in shared-utils.js: getFriendlyTableName, formatAuditValue, generateChangeSummary, formatJsonForDisplay)

async function loadAuditoria(moduleFilter = '', userSearchTerm = '') {
    const tableBody = document.getElementById('auditoria-table-body');
    if (!tableBody) {
        console.error("Elemento 'auditoria-table-body' no encontrado.");
        return;
    }
    try {
        let url = '/api/admin/auditoria?limit=100'; // Default limit for display
        const params = new URLSearchParams();

        if (moduleFilter) {
            params.append('tabla', moduleFilter);
        }
        if (userSearchTerm) {
            params.append('search_user', userSearchTerm); // Assuming backend supports this param
        }
        if (params.toString()) {
            url += `&${params.toString()}`;
        }

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
            row.insertCell().innerHTML = `<small>${log.cedula_usuario_app || 'N/A'}</small>`; // Added cedula
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

// originalData reset function is now in shared-utils.js