// static/js/admin-form-handlers.js

/**
 * Función genérica para manejar el envío de formularios mediante Fetch.
 * @param {string} url - La URL del endpoint.
 * @param {string} method - El método HTTP (POST o PUT).
 * @param {object} body - El cuerpo de la solicitud en formato de objeto JS.
 * @param {function} successCallback - Función a ejecutar si la solicitud es exitosa.
 * @param {object} modalToHide - La instancia del modal de Bootstrap para ocultar al éxito.
 * @param {string} entityName - El nombre de la entidad para los mensajes (ej. "Cliente").
 */
async function handleFormSubmit(url, method, body, successCallback, modalToHide, entityName) {
    try {
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        const responseData = await response.json();
        if (!response.ok) {
            throw new Error(responseData.error || `Error al guardar ${entityName}: ${response.statusText}`);
        }
        if (modalToHide) modalToHide.hide();
        if (successCallback) successCallback();

        // Usa tu modal de notificación global
        showGlobalNotification(`${entityName} Guardado`, responseData.message || `${entityName} guardado con éxito.`, 'success');
    } catch (error) {
        console.error(`Error en handle${entityName}Submit:`, error);
        // Usa tu modal de notificación global para el error
        showGlobalNotification(`Error al Guardar ${entityName}`, error.message, 'error');
    }
}

async function handleClienteSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('clienteId').value;
    const url = id ? `/api/admin/clientes/${id}` : '/api/admin/clientes';
    const method = id ? 'PUT' : 'POST';

    // Se asume que los nuevos campos en tu HTML tienen estos IDs
    const generoValue = document.getElementById('clienteGenero').value;
    const tipoRegimenValue = document.getElementById('clienteTipoRegimen').value;
    const epsIdValue = document.getElementById('clienteEps').value;

    const body = {
        nombre: document.getElementById('clienteNombre').value,
        cedula: document.getElementById('clienteCedula').value,
        email: document.getElementById('clienteEmail').value,
        estado_usuario: document.getElementById('clienteEstadoUsuario').value,
        fecha_nacimiento: document.getElementById('clienteFechaNacimiento').value || null,
        telefono: document.getElementById('clienteTelefono').value || null,
        ciudad: document.getElementById('clienteCiudad').value || null,
        // CORRECCIÓN: Se añaden los nuevos campos al cuerpo de la solicitud
        genero: generoValue || null,
        tipo_regimen: tipoRegimenValue || null,
        eps_id: epsIdValue ? parseInt(epsIdValue, 10) : null
    };

    const contrasena = document.getElementById('clienteContrasena').value;
    if (method === 'POST') {
        if (!contrasena) {
            // CORRECCIÓN: Se reemplaza alert() con tu función de notificación
            showGlobalNotification('Error de Validación', 'La contraseña es requerida para nuevos clientes.', 'error');
            return;
        }
        body.contrasena = contrasena; 
    } else if (method === 'PUT' && contrasena) {
        body.contrasena_nueva = contrasena; 
    }

    await handleFormSubmit(url, method, body, loadClientes, window.clienteModal, 'Cliente');
}

async function handleMedicamentoSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('medicamentoId').value;
    const url = id ? `/api/admin/medicamentos/${id}` : '/api/admin/medicamentos';
    const method = id ? 'PUT' : 'POST';
    
    const body = {
        nombre: document.getElementById('medicamentoNombre').value,
        descripcion: document.getElementById('medicamentoDescripcion').value,
        composicion: document.getElementById('medicamentoComposicion').value,
        sintomas_secundarios: document.getElementById('medicamentoSintomasSecundarios').value,
        indicaciones: document.getElementById('medicamentoIndicaciones').value,
        rango_edad: document.getElementById('medicamentoRangoEdad').value,
        estado_medicamento: document.getElementById('medicamentoEstado').value
    };

    await handleFormSubmit(url, method, body, loadMedicamentos, window.medicamentoModal, 'Medicamento');
}

async function handleAlertaSubmit(e) {
    e.preventDefault();
    const alertaId = document.getElementById('alertaId').value;
    const method = alertaId ? 'PUT' : 'POST';
    const url = alertaId ? `/api/admin/alertas/${alertaId}` : '/api/admin/alertas';

    const body = {
        usuario_id: parseInt(document.getElementById('alertaUsuario').value, 10),
        medicamento_id: parseInt(document.getElementById('alertaMedicamento').value, 10),
        dosis: document.getElementById('alertaDosis').value.trim() || null,
        frecuencia: document.getElementById('alertaFrecuencia').value.trim() || null,
        fecha_inicio: document.getElementById('alertaFechaInicio').value,
        fecha_fin: document.getElementById('alertaFechaFin').value || null,
        hora_preferida: document.getElementById('alertaHoraPreferida').value || null,
        estado: document.getElementById('alertaEstado').value
    };

    if (!body.usuario_id || !body.medicamento_id || !body.fecha_inicio || !body.estado) {
        showGlobalNotification('Error de Validación', 'Por favor, complete todos los campos obligatorios (Cliente, Medicamento, Fecha de Inicio, Estado).', 'error');
        return;
    }
    await handleFormSubmit(url, method, body, loadAlertas, window.alertaModal, 'Alerta');
}