// static/js/admin-form-handlers.js

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
        alert(responseData.message || `${entityName} guardado con éxito.`);

    } catch (error) {
        console.error(`Error en handle${entityName}Submit:`, error);
        alert(`Error al guardar ${entityName}: ${error.message}`);
    }
}


async function handleClienteSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('clienteId').value;
    const url = id ? `/api/admin/clientes/${id}` : '/api/admin/clientes';
    const method = id ? 'PUT' : 'POST';

    const fechaNacimientoValue = document.getElementById('clienteFechaNacimiento').value;
    const telefonoValue = document.getElementById('clienteTelefono').value;
    const ciudadValue = document.getElementById('clienteCiudad').value;

    const body = {
        nombre: document.getElementById('clienteNombre').value,
        cedula: document.getElementById('clienteCedula').value,
        email: document.getElementById('clienteEmail').value,
        estado_usuario: document.getElementById('clienteEstadoUsuario').value,
        // Nuevos campos
        fecha_nacimiento: fechaNacimientoValue ? fechaNacimientoValue : null, // Enviar null si está vacío
        telefono: telefonoValue ? telefonoValue : null, // Enviar null si está vacío
        ciudad: ciudadValue ? ciudadValue : null // Enviar null si está vacío
    };

    const contrasena = document.getElementById('clienteContrasena').value;
    if (method === 'POST') { // Nuevo cliente
        if (!contrasena) {
            alert('La contraseña es requerida para nuevos clientes.');
            return;
        }
        body.contrasena = contrasena; 
    } else if (method === 'PUT' && contrasena) { // Editando y se proveyó nueva contraseña
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

    const fechaFinValue = document.getElementById('alertaFechaFin').value;
    const horaPreferidaValue = document.getElementById('alertaHoraPreferida').value;

    const body = {
        usuario_id: parseInt(document.getElementById('alertaUsuario').value, 10),
        medicamento_id: parseInt(document.getElementById('alertaMedicamento').value, 10),
        dosis: document.getElementById('alertaDosis').value.trim() || null,
        frecuencia: document.getElementById('alertaFrecuencia').value.trim() || null,
        fecha_inicio: document.getElementById('alertaFechaInicio').value,
        fecha_fin: fechaFinValue ? fechaFinValue : null,
        hora_preferida: horaPreferidaValue ? horaPreferidaValue : null,
        estado: document.getElementById('alertaEstado').value
    };

    if (!body.usuario_id || !body.medicamento_id || !body.fecha_inicio || !body.estado) {
        alert('Por favor, complete todos los campos obligatorios (Cliente, Medicamento, Fecha de Inicio, Estado).');
        return;
    }
    await handleFormSubmit(url, method, body, loadAlertas, window.alertaModal, 'Alerta');
}
