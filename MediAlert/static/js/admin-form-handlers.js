// static/js/admin-form-handlers.js

async function handleClienteSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('clienteId').value;
    const url = id ? `/api/admin/clientes/${id}` : '/api/admin/clientes';
    const method = id ? 'PUT' : 'POST';

    const body = {
        nombre: document.getElementById('clienteNombre').value,
        cedula: document.getElementById('clienteCedula').value,
        email: document.getElementById('clienteEmail').value,
    };
    if (!id || document.getElementById('clienteContrasena').value) { // Solo enviar contraseña si es nuevo o se ha escrito una
        if (!id) body.contrasena = document.getElementById('clienteContrasena').value;
        // Si es edición y se quiere cambiar contraseña, se necesitaría un campo diferente o lógica adicional
    }
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error al guardar cliente: ${response.statusText}`);
        }
        // Asume que window.clienteModal y loadClientes están disponibles globalmente
        if (window.clienteModal) window.clienteModal.hide();
        if (typeof loadClientes === 'function') loadClientes();
    } catch (error) {
        console.error("Error en handleClienteSubmit:", error);
        alert(`Error al guardar cliente: ${error.message}`);
    }
}

async function handleMedicamentoSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('medicamentoId').value;
    const url = id ? `/api/admin/medicamentos/${id}` : '/api/admin/medicamentos';
    const method = id ? 'PUT' : 'POST';
    
    const body = {
        nombre: document.getElementById('medicamentoNombre').value,
        descripcion: document.getElementById('medicamentoDescripcion').value,
    };

    try {
        const response = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
         if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error al guardar medicamento: ${response.statusText}`);
        }
        // Asume que window.medicamentoModal y loadMedicamentos están disponibles globalmente
        if (window.medicamentoModal) window.medicamentoModal.hide();
        if (typeof loadMedicamentos === 'function') loadMedicamentos();
    } catch (error) {
        console.error("Error en handleMedicamentoSubmit:", error);
        alert(`Error al guardar medicamento: ${error.message}`);
    }
}

async function handleAlertaSubmit(e) {
    e.preventDefault();
    const alertaId = document.getElementById('alertaId').value; // Para futura edición

    const method = alertaId ? 'PUT' : 'POST';
    const url = alertaId ? `/api/admin/alertas/${alertaId}` : '/api/admin/alertas';

    const fechaFinValue = document.getElementById('alertaFechaFin').value;

    const body = {
        usuario_id: document.getElementById('alertaUsuario').value,
        medicamento_id: document.getElementById('alertaMedicamento').value,
        dosis: document.getElementById('alertaDosis').value.trim(),
        frecuencia: document.getElementById('alertaFrecuencia').value.trim(),
        fecha_inicio: document.getElementById('alertaFechaInicio').value,
        fecha_fin: fechaFinValue ? fechaFinValue : null, // Enviar null si está vacío
    };

    if (!body.usuario_id || !body.medicamento_id || !body.fecha_inicio) {
        alert('Por favor, complete todos los campos obligatorios (Cliente, Medicamento, Fecha de Inicio).');
        return;
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const responseData = await response.json(); // Siempre intentar parsear JSON

        if (!response.ok) {
            throw new Error(responseData.error || `Error (${response.status}) al guardar la alerta.`);
        }

        if (window.alertaModal) window.alertaModal.hide();
        if (typeof loadAlertas === 'function') loadAlertas();
        alert(responseData.message || 'Alerta guardada con éxito.');

    } catch (error) {
        console.error('Error al enviar formulario de alerta:', error);
        alert(`Error: ${error.message}`);
    }
}