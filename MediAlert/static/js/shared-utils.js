// MediAlert/static/js/shared-utils.js

let globalNotificationModal; // To store the Bootstrap Modal instance

/**
 * Displays a notification modal.
 * @param {string} title - The title of the modal.
 * @param {string} message - The message to display in the modal body.
 * @param {string} type - The type of notification ('success', 'error', 'info'). Default is 'info'.
 */
function showGlobalNotification(title, message, type = 'info') {
    const modalElement = document.getElementById('notificationModal');
    if (!modalElement) {
        console.error('Notification modal element (#notificationModal) not found.');
        // Fallback to a simple alert if the modal isn't in the DOM
        alert(title + "\n\n" + message);
        return;
    }

    const modalTitleElement = document.getElementById('notificationModalLabel');
    const modalBodyElement = document.getElementById('notificationModalBody');
    const modalHeaderElement = document.getElementById('notificationModalHeader');

    if (modalTitleElement) modalTitleElement.textContent = title;
    if (modalBodyElement) modalBodyElement.innerHTML = message; // Use innerHTML if message can contain HTML

    // Set header color based on type
    if (modalHeaderElement) {
        modalHeaderElement.classList.remove('bg-success', 'bg-danger', 'bg-info', 'bg-primary', 'text-white', 'text-dark');
        let headerBgClass = 'bg-primary'; // Default
        let headerTextClass = 'text-white';

        switch (type.toLowerCase()) {
            case 'success':
                headerBgClass = 'bg-success';
                break;
            case 'error':
                headerBgClass = 'bg-danger';
                break;
            case 'info':
                headerBgClass = 'bg-info';
                headerTextClass = 'text-dark'; // Dark text is often more readable on info bg
                break;
        }
        modalHeaderElement.classList.add(headerBgClass, headerTextClass);
    }

    if (!globalNotificationModal) {
        globalNotificationModal = new bootstrap.Modal(modalElement);
    }
    globalNotificationModal.show();
}

/**
 * Fetches data from a given URL.
 * @param {string} url The API endpoint to fetch from.
 * @param {string} errorMessagePrefix A prefix for error messages.
 * @returns {Promise<Array>} A promise that resolves with the JSON data.
 * @throws {Error} If the network response is not OK or parsing fails.
 */
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

/**
 * Renders an error row in a table body.
 * @param {HTMLElement} tableBody The tbody element to insert the error row into.
 * @param {number} colspan The number of columns the error cell should span.
 * @param {Error} error The error object.
 */
function renderErrorRow(tableBody, colspan, error) {
    if (tableBody) {
        tableBody.innerHTML = `<tr><td colspan="${colspan}" class="text-center text-danger">Error al cargar los datos: ${error.message}</td></tr>`;
    }
}

/**
 * Formats a date string into a localized date format (e.g., "Jan 1, 2023").
 * Assumes ISO-8601 date string (YYYY-MM-DD).
 * @param {string} dateString The date string to format.
 * @returns {string} The formatted date string or 'N/A' if invalid/empty.
 */
function formatDate(dateString) {
    if (!dateString || String(dateString).trim() === '') {
        return 'N/A';
    }
    try {
        // Asume que dateString es YYYY-MM-DD. Interpretar como UTC para evitar problemas de zona horaria.
        const dateObj = new Date(dateString + 'T00:00:00Z');
        if (isNaN(dateObj.getTime())) {
            console.warn("formatDate creó una fecha inválida para el string:", dateString);
            return dateString; 
        }
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            timeZone: 'UTC' // O la zona horaria que prefieras para mostrar.
        };
        return dateObj.toLocaleDateString('es-CO', options);
    } catch (e) {
        console.error("Error en formatDate para el string:", dateString, e);
        return dateString; 
    }
}

/**
 * Formats a timestamp string into a localized date and time format.
 * Assumes ISO-8601 timestamp string.
 * @param {string} timestampString The timestamp string to format.
 * @returns {string} The formatted timestamp string or 'N/A' if invalid/empty.
 */
function formatTimestamp(timestampString) {
    if (!timestampString || String(timestampString).trim() === '') {
        return 'N/A';
    }
    try {
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
            timeZone: 'UTC' // O la zona horaria que prefieras para mostrar.
        };
        return dateObj.toLocaleString('es-CO', options);
    } catch (e) {
        console.error("Error en formatTimestamp para el string:", timestampString, e);
        return timestampString;
    }
}

/**
 * Formats a time string (HH:MM:SS) into a localized time format (e.g., "08:00 AM").
 * @param {string} timeString The time string to format.
 * @returns {string} The formatted time string or 'N/A' if invalid/empty.
 */
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

/**
 * Provides a user-friendly name for database table names.
 * @param {string} tableName The internal database table name.
 * @returns {string} A user-friendly name for the table.
 */
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

/**
 * Generates a summary of changes between two JSONB objects for audit logs.
 * @param {string} accion The action performed (e.g., 'INSERT', 'UPDATE', 'DELETE').
 * @param {object} datosAnteriores The old data as a JSONB object.
 * @param {object} datosNuevos The new data as a JSONB object.
 * @returns {string} An HTML string summarizing the changes.
 */
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

/**
 * Formats a JSON object for display in audit logs.
 * @param {object|string} jsonData The JSON data to format.
 * @returns {string} An HTML string representation of the JSON data.
 */
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

/**
 * Helper for formatting individual audit values.
 * @param {*} value The value to format.
 * @returns {string} The formatted value.
 */
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

/**
 * Helper para formatear fechas de nacimiento específicamente para recetas y calcular edad.
 * @param {string} dateString La fecha de nacimiento en formato YYYY-MM-DD.
 * @returns {string} La fecha formateada con la edad, o 'N/A'.
 */
function formatDateOfBirth(dateString) {
    if (!dateString || String(dateString).trim() === '') {
        return 'N/A';
    }
    try {
        const birthDate = new Date(dateString + 'T00:00:00Z'); // Tratar como UTC
        if (isNaN(birthDate.getTime())) {
            return dateString;
        }
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        const m = today.getMonth() - birthDate.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        
        return `${birthDate.toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC' })} (Edad: ${age})`;
    } catch (e) {
        console.error("Error en formatDateOfBirth:", e);
        return dateString;
    }
}

// Global data stores (can be used for client-side filtering/caching)
let originalClientesData = [];
let originalMedicamentosData = [];
let originalAlertasData = []; // This is for the detailed alerts, not the grouped view
let originalClientesConAlertasData = []; // For the grouped alerts view
let originalAuditoriaData = [];

// Function to reset all original data stores (useful on logout or full refresh)
function resetOriginalData() {
    originalClientesData = [];
    originalMedicamentosData = [];
    originalAlertasData = [];
    originalClientesConAlertasData = [];
    originalAuditoriaData = [];
}