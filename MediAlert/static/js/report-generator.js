// MediAlert/static/js/report-generator.js

async function getLogoBase64DataUrl(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Respuesta de red no fue OK para el logo: ${response.statusText}`);
        }
        const blob = await response.blob();
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = (error) => {
                console.error("Error del FileReader:", error);
                reject(null);
            };
            reader.readAsDataURL(blob);
        });
    } catch (error) {
        console.error("Error al obtener o convertir el logo:", error);
        return null;
    }
}

async function addPdfHeader(doc, title) {
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 35;
    const topMargin = 30;

    const logoUrl = '/static/img/logo1.png';
    const logoBase64 = await getLogoBase64DataUrl(logoUrl);

    if (logoBase64) {
        try {
            const logoImgProps = doc.getImageProperties(logoBase64);
            const aspectRatio = logoImgProps.width / logoImgProps.height;
            const logoHeightPdf = 28;
            const logoWidthPdf = logoHeightPdf * aspectRatio;
            doc.addImage(logoBase64, logoImgProps.fileType.toUpperCase(), margin, topMargin, logoWidthPdf, logoHeightPdf);
        } catch (e) {
            console.error("Error al añadir el logo (obtenido dinámicamente) al PDF:", e);
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(12);
            doc.setTextColor(44, 62, 80);
            doc.text("MediAlert", margin, topMargin + 15);
        }
    } else {
        console.warn("El logo no pudo ser cargado. Usando texto de fallback.");
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.setTextColor(44, 62, 80);
        doc.text("MediAlert", margin, topMargin + 15);
    }

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(18);
    doc.setTextColor(40, 40, 40);
    const titleWidth = doc.getTextWidth(title);
    doc.text(title, (pageWidth - titleWidth) / 2, topMargin + 20);

    doc.setDrawColor(180, 180, 180);
    doc.line(margin, topMargin + 35, pageWidth - margin, topMargin + 35);
}

function addPdfFooter(doc, data) {
    const pageCount = doc.internal.getNumberOfPages();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 35;
    const footerY = pageHeight - 30;

    doc.setFont('helvetica', 'italic');
    doc.setFontSize(8);
    doc.setTextColor(100, 100, 100);

    const generationText = `Generado: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`;
    doc.text(generationText, margin, footerY);

    const companyText = "MediAlert - Reporte Interno";
    const companyTextWidth = doc.getTextWidth(companyText);
    doc.text(companyText, (pageWidth - companyTextWidth) / 2, footerY);

    const pageNumText = `Página ${data.pageNumber} de ${pageCount}`;
    const pageNumTextWidth = doc.getTextWidth(pageNumText);
    doc.text(pageNumText, pageWidth - margin - pageNumTextWidth, footerY);
}


async function uploadPdfAndLog(pdfBlob, originalFilename, reportTypeForLog, reportTitleForLog) {
    const formData = new FormData();
    formData.append('report_pdf', pdfBlob, originalFilename + ".pdf");

    try {
        const uploadResponse = await fetch('/api/admin/reportes/upload_pdf', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const errorData = await uploadResponse.json();
            throw new Error(`Error al subir PDF: ${errorData.error || uploadResponse.statusText}`);
        }
        const uploadResult = await uploadResponse.json();
        const serverFilename = uploadResult.filename;

        const logResponse = await fetch('/api/admin/reportes_log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tipo_reporte: reportTypeForLog,
                nombre_reporte: reportTitleForLog,
                pdf_filename: serverFilename
            })
        });

        if (!logResponse.ok) {
            const logErrorData = await logResponse.json();
            console.error('Error al registrar la generación del reporte (después de subir PDF):', logErrorData.error || logResponse.statusText);
        } else {
            console.log("Reporte subido y logueado exitosamente.");
        }

        if (document.getElementById('view-reportes')?.style.display === 'block' && typeof loadReportesLog === 'function') {
            loadReportesLog();
        }

    } catch (error) {
        console.error('Error en el proceso de subir y loguear PDF:', error);
        showGlobalNotification('Error de Reporte', `Error al procesar el reporte: ${error.message}`, 'error');
    }
}

async function generatePdfAndUpload(reportConfig) {
    const { title, headers, data, filename, columnStyles = {}, bodyStyles = {}, tipo_reporte_log, orientation = 'p', format = 'a4' } = reportConfig;
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF(orientation, 'pt', format);
    const margin = 35;

    await addPdfHeader(doc, title);

    const tableStartY = 75;

    const headForTable = [headers.map(h => h.text)];
    const bodyForTable = data.map(row => headers.map(header => {
        const value = row[header.key];
        return value !== undefined && value !== null ? String(value) : '';
    }));

    doc.autoTable({
        startY: tableStartY,
        head: headForTable,
        body: bodyForTable,
        theme: 'striped',
        styles: {
            font: 'helvetica',
            fontSize: 8,
            cellPadding: { top: 4, right: 5, bottom: 4, left: 5 },
            overflow: 'linebreak',
            valign: 'middle',
            ...bodyStyles
        },
        headStyles: {
            fillColor: [44, 62, 80],
            textColor: 255,
            fontStyle: 'bold',
            halign: 'center',
            fontSize: 9,
            lineWidth: 0.1,
            lineColor: [44, 62, 80]
        },
        alternateRowStyles: {
            fillColor: [240, 245, 250]
        },
        columnStyles: columnStyles,
        margin: { top: tableStartY, right: margin, bottom: 45, left: margin },
        didDrawPage: function (data) {
            addPdfFooter(doc, data);
        }
    });

    doc.save(`${filename}_${new Date().toISOString().slice(0, 10)}.pdf`);
    const pdfBlob = doc.output('blob');

    if (tipo_reporte_log) {
        await uploadPdfAndLog(pdfBlob, filename, tipo_reporte_log, title);
    }
}

async function generateUsuariosReport() {
    try {
        const clientesPromise = fetchData('/api/admin/clientes?estado=todos&rol=cliente', 'Error al obtener datos de clientes');
        const adminsPromise = fetchData('/api/admin/clientes?estado=todos&rol=admin', 'Error al obtener datos de administradores');
        const [clientes, admins] = await Promise.all([clientesPromise, adminsPromise]);

        const allUsers = [...(clientes || []), ...(admins || [])];

        if (!allUsers.length) { showGlobalNotification('Reporte Vacío', 'No hay datos de usuarios para generar el reporte.', 'info'); return; }

        const dataForPdf = allUsers.map(user => ({
            nombre: user.nombre || 'N/A',
            cedula: user.cedula || 'N/A',
            email: user.email || 'N/A',
            rol: user.rol ? user.rol.charAt(0).toUpperCase() + user.rol.slice(1) : 'N/A',
            estado_usuario: user.estado_usuario ? user.estado_usuario.charAt(0).toUpperCase() + user.estado_usuario.slice(1) : "N/A" // Removed extra space
        }));

        const reportConfig = {
            title: 'Reporte de Usuarios del Sistema', filename: 'Reporte_Usuarios', tipo_reporte_log: 'usuarios',
            headers: [
                { text: "Nombre", key: "nombre" }, { text: "Cédula", key: "cedula" },
                { text: "Email", key: "email" }, { text: "Rol", key: "rol" },
                { text: "Estado", key: "estado_usuario" }
            ],
            data: dataForPdf,
            columnStyles: {
                nombre: { cellWidth: 110 },
                cedula: { cellWidth: 70 },
                email: { cellWidth: 130 },
                rol: { cellWidth: 60 },
                estado_usuario: { cellWidth: 60 }
            }
        };
        await generatePdfAndUpload(reportConfig);
        showGlobalNotification('Reporte Generado', 'El reporte de usuarios se ha generado y descargado con éxito.', 'success');
    } catch (error) { console.error('Error generando reporte de usuarios:', error); showGlobalNotification('Error', 'No se pudo generar el reporte de usuarios: ' + error.message, 'error'); }
}

async function generateMedicamentosReport() {
    try {
        const medicamentos = await fetchData('/api/admin/medicamentos?estado=todos', 'Error al obtener datos de medicamentos');
        if (!medicamentos || !medicamentos.length) { showGlobalNotification('Reporte Vacío', 'No hay datos de medicamentos para generar el reporte.', 'info'); return; }

        const dataForPdf = medicamentos.map(m => ({
            nombre: m.nombre || "N/A", descripcion: m.descripcion || "N/A",
            composicion: m.composicion || "N/A", indicaciones: m.indicaciones || "N/A",
            rango_edad: m.rango_edad || "N/A",
            estado_medicamento: m.estado_medicamento ? m.estado_medicamento.charAt(0).toUpperCase() + m.estado_medicamento.slice(1) : "N/A"
        }));

        const reportConfig = {
            title: 'Reporte de Catálogo de Medicamentos', filename: 'Reporte_Medicamentos', tipo_reporte_log: 'medicamentos', orientation: 'l',
            headers: [
                { text: "Nombre", key: "nombre" }, { text: "Descripción", key: "descripcion" },
                { text: "Composición", key: "composicion" }, { text: "Indicaciones", key: "indicaciones" },
                { text: "Rango Edad", key: "rango_edad" }, { text: "Estado", key: "estado_medicamento" }
            ],
            data: dataForPdf,
            columnStyles: {
                nombre: { cellWidth: 120 },
                descripcion: { cellWidth: 180 },
                composicion: { cellWidth: 180 },
                indicaciones: { cellWidth: 180 },
                rango_edad: {cellWidth: 70},
                estado_medicamento: {cellWidth: 70}
            }
        };
        await generatePdfAndUpload(reportConfig);
        showGlobalNotification('Reporte Generado', 'El reporte de medicamentos se ha generado y descargado con éxito.', 'success');
    } catch (error) { console.error('Error generando reporte de medicamentos:', error); showGlobalNotification('Error', 'No se pudo generar el reporte de medicamentos: ' + error.message, 'error'); }
}

async function generateAlertasActivasReport() {
    try {
        const alertas = await fetchData('/api/admin/alertas', 'Error al obtener datos de alertas');
        const activas = alertas.filter(a => a.estado_alerta === 'activa');
        if (!activas.length) { showGlobalNotification('Reporte Vacío', 'No hay alertas activas para generar el reporte.', 'info'); return; }

        const dataForPdf = activas.map(a => ({
            cliente_nombre: a.cliente_nombre || "N/A", medicamento_nombre: a.medicamento_nombre || "N/A",
            dosis: a.dosis || "N/A", frecuencia: a.frecuencia || "N/A",
            fecha_inicio_f: a.fecha_inicio ? formatDate(a.fecha_inicio) : "N/A",
            fecha_fin_f: a.fecha_fin ? formatDate(a.fecha_fin) : "Indefinido",
            hora_preferida_f: a.hora_preferida ? formatTime(a.hora_preferida) : "N/A"
        }));

        const reportConfig = {
            title: 'Reporte de Alertas Activas', filename: 'Reporte_Alertas_Activas', tipo_reporte_log: 'alertas_activas', orientation: 'l',
            headers: [
                { text: "Cliente", key: "cliente_nombre" }, { text: "Medicamento", key: "medicamento_nombre" },
                { text: "Dosis", key: "dosis" }, { text: "Frecuencia", key: "frecuencia" },
                { text: "Inicio", key: "fecha_inicio_f" }, { text: "Fin", key: "fecha_fin_f" },
                { text: "Hora Pref.", key: "hora_preferida_f" }
            ],
            data: dataForPdf,
             columnStyles: {
                cliente_nombre: { cellWidth: 120 },
                medicamento_nombre: { cellWidth: 120 }
            }
        };
        await generatePdfAndUpload(reportConfig);
        showGlobalNotification('Reporte Generado', 'El reporte de alertas activas se ha generado y descargado con éxito.', 'success');
    } catch (error) { console.error('Error generando reporte de alertas activas:', error); showGlobalNotification('Error', 'No se pudo generar el reporte de alertas activas: ' + error.message, 'error'); }
}

async function generateAuditoriaReport() {
    try {
        const logs = await fetchData('/api/admin/auditoria?limit=100', 'Error al obtener datos de auditoría');
        if (!logs || !logs.length) { showGlobalNotification('Reporte Vacío', 'No hay datos de auditoría para generar el reporte.', 'info'); return; }

        const dataForPdf = logs.slice(0, 100).map(log => {
            let detallesSummary = '';
             if (log.datos_nuevos && typeof log.datos_nuevos === 'object') {
                detallesSummary = Object.entries(log.datos_nuevos)
                    .filter(([key]) => !['contrasena', 'hashed_password'].includes(key))
                    .map(([key, value]) => `${key}: ${String(value).substring(0,30)}`)
                    .join('; ');
            } else if (log.detalles_adicionales && typeof log.detalles_adicionales === 'object') {
                 detallesSummary = Object.entries(log.detalles_adicionales)
                    .map(([key, value]) => `${key}: ${String(value).substring(0,30)}`)
                    .join('; ');
            } else if(typeof log.detalles_adicionales === 'string') {
                 detallesSummary = log.detalles_adicionales.substring(0,100);
            }


            return {
                fecha_hora_f: log.fecha_hora ? new Date(log.fecha_hora).toLocaleString() : "N/A",
                nombre_usuario_app: log.nombre_usuario_app || "Sistema",
                accion_f: log.accion ? log.accion.replace(/_/g, ' ') : "N/A",
                tabla_afectada_f: typeof getFriendlyTableName === 'function' ? getFriendlyTableName(log.tabla_afectada) : (log.tabla_afectada || 'N/A'),
                registro_id_afectado: log.registro_id_afectado !== null && log.registro_id_afectado !== undefined ? String(log.registro_id_afectado) : "N/A",
                detalles_f: detallesSummary || "N/A"
            };
        });

        const reportConfig = {
            title: 'Reporte de Auditoría del Sistema (Últimos 100)', filename: 'Reporte_Auditoria', tipo_reporte_log: 'auditoria',
            orientation: 'l', format: 'a3',
            headers: [
                { text: "Fecha y Hora", key: "fecha_hora_f" }, { text: "Usuario", key: "nombre_usuario_app" },
                { text: "Acción", key: "accion_f" }, { text: "Módulo", key: "tabla_afectada_f" },
                { text: "ID Afectado", key: "registro_id_afectado" }, { text: "Detalles Resumidos", key: "detalles_f" }
            ],
            data: dataForPdf,
            columnStyles: {
                fecha_hora_f: { cellWidth: 110 },
                nombre_usuario_app: {cellWidth: 80},
                accion_f: {cellWidth: 120},
                tabla_afectada_f: {cellWidth: 80},
                registro_id_afectado: {cellWidth: 60},
                detalles_f: { cellWidth: 'auto' }
            },
            bodyStyles: { fontSize: 7, cellPadding: {top: 2, right: 3, bottom: 2, left: 3} }
        };
        await generatePdfAndUpload(reportConfig);
        showGlobalNotification('Reporte Generado', 'El reporte de auditoría se ha generado y descargado con éxito.', 'success');
    } catch (error) { console.error('Error generando reporte de auditoría:', error); showGlobalNotification('Error', 'No se pudo generar el reporte de auditoría: ' + error.message, 'error'); }
}

function formatDateOfBirth(dateString) {
    if (!dateString || String(dateString).trim() === '') {
        return 'N/A';
    }
    try {
        const birthDate = new Date(dateString + 'T00:00:00Z');
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

async function generateRecetaMedicaPdf(alertaId) {
    showGlobalNotification('Generando Receta', 'Preparando la receta médica, por favor espere...', 'info');
    try {
        const recetaData = await fetchData(`/api/receta_medica/${alertaId}`, 'Error al obtener datos de la receta');

        if (!recetaData) {
            showGlobalNotification('Receta No Encontrada', 'No se encontraron datos para la receta.', 'error');
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'pt', 'a4');
        const margin = 40;
        let currentY = 40;
        const lineHeight = 14;

        await addPdfHeader(doc, `Receta Médica - Alerta #${recetaData.alerta_id}`);
        currentY = 100;

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(50, 50, 50);

        // Información del Cliente
        doc.setFont('helvetica', 'bold');
        doc.text('Información del Paciente:', margin, currentY);
        currentY += lineHeight;
        doc.setFont('helvetica', 'normal');
        doc.text(`Nombre: ${recetaData.cliente_nombre || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Cédula: ${recetaData.cliente_cedula || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Fecha Nacimiento: ${formatDateOfBirth(recetaData.cliente_fecha_nacimiento)}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Teléfono: ${recetaData.cliente_telefono || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Ciudad: ${recetaData.cliente_ciudad || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`EPS: ${recetaData.eps_nombre || 'N/A'}`, margin, currentY);
        currentY += lineHeight * 2;

        // Información del Medicamento Recetado
        doc.setFont('helvetica', 'bold');
        doc.text('Medicamento Recetado:', margin, currentY);
        currentY += lineHeight;
        doc.setFont('helvetica', 'normal');
        doc.text(`Nombre: ${recetaData.medicamento_nombre || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        let splitDescription = doc.splitTextToSize(`Descripción: ${recetaData.medicamento_descripcion || 'N/A'}`, doc.internal.pageSize.getWidth() - 2 * margin);
        doc.text(splitDescription, margin, currentY);
        currentY += (splitDescription.length * lineHeight);

        let splitComposicion = doc.splitTextToSize(`Composición: ${recetaData.medicamento_composicion || 'N/A'}`, doc.internal.pageSize.getWidth() - 2 * margin);
        doc.text(splitComposicion, margin, currentY);
        currentY += (splitComposicion.length * lineHeight);

        let splitIndicaciones = doc.splitTextToSize(`Indicaciones: ${recetaData.medicamento_indicaciones || 'N/A'}`, doc.internal.pageSize.getWidth() - 2 * margin);
        doc.text(splitIndicaciones, margin, currentY);
        currentY += (splitIndicaciones.length * lineHeight);

        doc.text(`Dosis: ${recetaData.dosis || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Frecuencia: ${recetaData.frecuencia || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Rango de Edad: ${recetaData.medicamento_rango_edad || 'N/A'}`, margin, currentY);
        currentY += lineHeight;

        // Displaying alert status
        doc.text(`Estado de la Alerta: ${recetaData.estado_alerta.charAt(0).toUpperCase() + recetaData.estado_alerta.slice(1) || 'N/A'}`, margin, currentY);
        currentY += lineHeight * 2;


        // Período de Administración
        doc.setFont('helvetica', 'bold');
        doc.text('Período de Administración:', margin, currentY);
        currentY += lineHeight;
        doc.setFont('helvetica', 'normal');
        doc.text(`Fecha de Inicio: ${formatDate(recetaData.fecha_inicio)}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Fecha de Fin: ${recetaData.fecha_fin ? formatDate(recetaData.fecha_fin) : 'Indefinido'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Hora Preferida: ${recetaData.hora_preferida ? formatTime(recetaData.hora_preferida) : 'Cualquier hora / N/A'}`, margin, currentY);
        currentY += lineHeight * 3;

        // Firma del Asignador
        doc.setFont('helvetica', 'bold');
        doc.text('Asignado por:', margin, currentY);
        currentY += lineHeight;
        doc.setFont('helvetica', 'normal');
        doc.text(`_____________________________________`, margin, currentY);
        currentY += 5;
        doc.text(`${recetaData.asignador_nombre || 'Sistema MediAlert'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Cédula: ${recetaData.asignador_cedula || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Rol: ${recetaData.asignador_rol || 'N/A'}`, margin, currentY);
        currentY += lineHeight * 2;

        addPdfFooter(doc, { pageNumber: 1 });

        doc.save(`Receta_Medica_Alerta_${alertaId}_${new Date().toISOString().slice(0, 10)}.pdf`);
        const pdfBlob = doc.output('blob');
        await uploadPdfAndLog(pdfBlob, `Receta_Medica_Alerta_${alertaId}`, 'receta_medica', `Receta Médica Alerta #${alertaId}`);
        showGlobalNotification('Receta Generada', 'La receta médica se ha generado y descargado con éxito.', 'success');

    } catch (error) {
        console.error('Error generando receta médica:', error);
        showGlobalNotification('Error', `No se pudo generar la receta médica: ${error.message}`, 'error');
    }
}

// Re-factored generateConsolidatedRecetaPdf to accept optional client ID and name
async function generateConsolidatedRecetaPdf(clientId = null, clientName = null) {
    showGlobalNotification('Generando Receta Consolidada', 'Preparando la receta consolidada, por favor espere...', 'info');
    try {
        let apiUrl = '/api/cliente/recetas_consolidadas'; // Default for client's own view
        let filenamePrefix = 'Receta_Consolidada';
        let reportTitle = 'Receta Médica Consolidada';
        let clientInfoForReport = {}; // To hold the client's static data for the report header

        if (clientId) {
            // Admin requesting for a specific client
            apiUrl = `/api/cliente/recetas_consolidadas?user_id=${clientId}`; // Now this will be allowed for admin
            filenamePrefix = `Receta_Consolidada_${(clientName || 'Cliente').replace(/ /g, '_')}_${clientId}`;
            reportTitle = `Receta Médica Consolidada de ${clientName || 'Cliente'} (ID: ${clientId})`;
        }

        const recetasData = await fetchData(apiUrl, 'Error al obtener datos de recetas consolidadas');

        if (!recetasData || recetasData.length === 0) {
            showGlobalNotification('Reporte Vacío', 'No hay alertas activas para generar una receta consolidada.', 'info');
            return;
        }

        // If clientId is provided (admin scenario), we fetch client data directly for the header
        // Otherwise (client's own panel), use first receta for client info
        if (clientId) {
            const clientDetails = await fetchData(`/api/admin/clientes/${clientId}`, `Error al obtener detalles del cliente ${clientId}`);
            clientInfoForReport = {
                cliente_nombre: clientDetails.nombre,
                cliente_cedula: clientDetails.cedula,
                cliente_fecha_nacimiento: clientDetails.fecha_nacimiento,
                cliente_telefono: clientDetails.telefono,
                cliente_ciudad: clientDetails.ciudad,
                eps_nombre: clientDetails.eps_nombre
            };
        } else {
            clientInfoForReport = {
                cliente_nombre: recetasData[0].cliente_nombre,
                cliente_cedula: recetasData[0].cliente_cedula,
                cliente_fecha_nacimiento: recetasData[0].cliente_fecha_nacimiento,
                cliente_telefono: recetasData[0].cliente_telefono,
                cliente_ciudad: recetasData[0].cliente_ciudad,
                eps_nombre: recetasData[0].eps_nombre
            };
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'pt', 'a4');
        const margin = 40;
        let currentY = 40;
        const lineHeight = 14;

        await addPdfHeader(doc, reportTitle);
        currentY = 100;

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(50, 50, 50);

        // Client Information Section
        doc.setFont('helvetica', 'bold');
        doc.text('Información del Paciente:', margin, currentY);
        currentY += lineHeight;
        doc.setFont('helvetica', 'normal');
        doc.text(`Nombre: ${clientInfoForReport.cliente_nombre || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Cédula: ${clientInfoForReport.cliente_cedula || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Fecha Nacimiento: ${formatDateOfBirth(clientInfoForReport.cliente_fecha_nacimiento)}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Teléfono: ${clientInfoForReport.cliente_telefono || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Ciudad: ${clientInfoForReport.cliente_ciudad || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`EPS: ${clientInfoForReport.eps_nombre || 'N/A'}`, margin, currentY);
        currentY += lineHeight * 2;

        doc.setFont('helvetica', 'bold');
        doc.text('Medicamentos Recetados Activos:', margin, currentY);
        currentY += lineHeight;

        recetasData.forEach((receta, index) => {
            if (currentY + 150 > doc.internal.pageSize.getHeight() - 40) {
                doc.addPage();
                currentY = 40;
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(12);
                doc.setTextColor(40, 40, 40);
                doc.text(`${reportTitle} - Continuación (Página ${doc.internal.getNumberOfPages()})`, margin, currentY);
                currentY += lineHeight * 2;
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(10);
                doc.setTextColor(50, 50, 50);
            }

            doc.setFont('helvetica', 'bold');
            doc.text(`${index + 1}. ${receta.medicamento_nombre || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.setFont('helvetica', 'normal');

            let splitDescription = doc.splitTextToSize(`Descripción: ${receta.medicamento_descripcion || 'N/A'}`, doc.internal.pageSize.getWidth() - 2 * margin);
            doc.text(splitDescription, margin, currentY);
            currentY += (splitDescription.length * lineHeight);

            doc.text(`Dosis: ${receta.dosis || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Frecuencia: ${receta.frecuencia || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Fecha Inicio: ${formatDate(receta.fecha_inicio)}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Fecha Fin: ${receta.fecha_fin ? formatDate(receta.fecha_fin) : 'Indefinido'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Hora Preferida: ${receta.hora_preferida ? formatTime(receta.hora_preferida) : 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Estado de la Alerta: ${receta.estado_alerta.charAt(0).toUpperCase() + receta.estado_alerta.slice(1) || 'N/A'}`, margin, currentY);
            currentY += lineHeight * 1.5;
        });

        currentY += lineHeight * 2;

        doc.setFont('helvetica', 'bold');
        doc.text('Asignado por:', margin, currentY);
        currentY += lineHeight;
        doc.setFont('helvetica', 'normal');
        doc.text(`_____________________________________`, margin, currentY);
        currentY += 5;
        doc.text(`${recetasData[0].asignador_nombre || 'Sistema MediAlert'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Cédula: ${recetasData[0].asignador_cedula || 'N/A'}`, margin, currentY);
        currentY += lineHeight;
        doc.text(`Rol: ${recetasData[0].asignador_rol || 'N/A'}`, margin, currentY);

        const totalPages = doc.internal.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            doc.setPage(i);
            addPdfFooter(doc, { pageNumber: i, pageCount: totalPages });
        }


        doc.save(`${filenamePrefix}_${new Date().toISOString().slice(0, 10)}.pdf`);
        const pdfBlob = doc.output('blob');
        await uploadPdfAndLog(pdfBlob, filenamePrefix, 'receta_consolidada_cliente', reportTitle);
        showGlobalNotification('Receta Consolidada Generada', 'La receta médica consolidada se ha generado y descargado con éxito.', 'success');

    } catch (error) {
        console.error('Error generando receta médica consolidada:', error);
        showGlobalNotification('Error', `No se pudo generar la receta médica consolidada: ${error.message}`, 'error');
    }
}


async function generateConsolidatedRecetaPdfForAdmin() {
    showGlobalNotification('Generando Receta Consolidada (Admin)', 'Preparando la receta consolidada de todos los clientes, por favor espere...', 'info');
    try {
        const recetasData = await fetchData('/api/admin/recetas_consolidadas', 'Error al obtener datos de recetas consolidadas para admin');

        if (!recetasData || recetasData.length === 0) {
            showGlobalNotification('Reporte Vacío', 'No hay alertas activas de clientes para generar una receta consolidada.', 'info');
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('p', 'pt', 'a4');
        const margin = 40;
        let currentY = 40;
        const lineHeight = 14;

        // Group recipes by client for better readability
        const recetasByClient = recetasData.reduce((acc, receta) => {
            const clientName = receta.cliente_nombre;
            if (!acc[clientName]) {
                acc[clientName] = {
                    info: {
                        cliente_nombre: receta.cliente_nombre,
                        cliente_cedula: receta.cliente_cedula,
                        cliente_fecha_nacimiento: receta.cliente_fecha_nacimiento,
                        cliente_telefono: receta.cliente_telefono,
                        cliente_ciudad: receta.cliente_ciudad,
                        eps_nombre: receta.eps_nombre,
                    },
                    alerts: []
                };
            }
            acc[clientName].alerts.push(receta);
            return acc;
        }, {});

        const clientNames = Object.keys(recetasByClient).sort();

        for (let clientIndex = 0; clientIndex < clientNames.length; clientIndex++) {
            const clientName = clientNames[clientIndex];
            const clientData = recetasByClient[clientName];

            if (clientIndex > 0) {
                doc.addPage();
                currentY = 40;
            }

            await addPdfHeader(doc, `Receta Médica Consolidada (Admin)`);
            currentY = 100;

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(10);
            doc.setTextColor(50, 50, 50);

            doc.setFont('helvetica', 'bold');
            doc.text('Información del Paciente:', margin, currentY);
            currentY += lineHeight;
            doc.setFont('helvetica', 'normal');
            doc.text(`Nombre: ${clientData.info.cliente_nombre || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Cédula: ${clientData.info.cliente_cedula || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Fecha Nacimiento: ${formatDateOfBirth(clientData.info.cliente_fecha_nacimiento)}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Teléfono: ${clientData.info.cliente_telefono || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Ciudad: ${clientData.info.cliente_ciudad || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`EPS: ${clientData.info.eps_nombre || 'N/A'}`, margin, currentY);
            currentY += lineHeight * 2;

            doc.setFont('helvetica', 'bold');
            doc.text('Medicamentos Recetados Activos:', margin, currentY);
            currentY += lineHeight;

            clientData.alerts.forEach((receta, alertIndex) => {
                if (currentY + 150 > doc.internal.pageSize.getHeight() - 40) {
                    doc.addPage();
                    currentY = 40;
                    doc.setFont('helvetica', 'bold');
                    doc.setFontSize(12);
                    doc.setTextColor(40, 40, 40);
                    doc.text(`Receta Consolidada - Continuación (Página ${doc.internal.getNumberOfPages()})`, margin, currentY);
                    currentY += lineHeight * 2;
                    doc.setFont('helvetica', 'normal');
                    doc.setFontSize(10);
                    doc.setTextColor(50, 50, 50);
                }

                doc.setFont('helvetica', 'bold');
                doc.text(`${alertIndex + 1}. ${receta.medicamento_nombre || 'N/A'}`, margin, currentY);
                currentY += lineHeight;
                doc.setFont('helvetica', 'normal');

                let splitDescription = doc.splitTextToSize(`Descripción: ${receta.medicamento_descripcion || 'N/A'}`, doc.internal.pageSize.getWidth() - 2 * margin);
                doc.text(splitDescription, margin, currentY);
                currentY += (splitDescription.length * lineHeight);

                doc.text(`Dosis: ${receta.dosis || 'N/A'}`, margin, currentY);
                currentY += lineHeight;
                doc.text(`Frecuencia: ${receta.frecuencia || 'N/A'}`, margin, currentY);
                currentY += lineHeight;
                doc.text(`Fecha Inicio: ${formatDate(receta.fecha_inicio)}`, margin, currentY);
                currentY += lineHeight;
                doc.text(`Fecha Fin: ${receta.fecha_fin ? formatDate(receta.fecha_fin) : 'Indefinido'}`, margin, currentY);
                currentY += lineHeight;
                doc.text(`Hora Preferida: ${receta.hora_preferida ? formatTime(receta.hora_preferida) : 'N/A'}`, margin, currentY);
                currentY += lineHeight;
                doc.text(`Estado de la Alerta: ${receta.estado_alerta.charAt(0).toUpperCase() + receta.estado_alerta.slice(1) || 'N/A'}`, margin, currentY);
                currentY += lineHeight * 1.5;
            });

            currentY += lineHeight * 2;

            doc.setFont('helvetica', 'bold');
            doc.text('Asignado por:', margin, currentY);
            currentY += lineHeight;
            doc.setFont('helvetica', 'normal');
            doc.text(`_____________________________________`, margin, currentY);
            currentY += 5;
            doc.text(`${clientData.alerts[0].asignador_nombre || 'Sistema MediAlert'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Cédula: ${clientData.alerts[0].asignador_cedula || 'N/A'}`, margin, currentY);
            currentY += lineHeight;
            doc.text(`Rol: ${clientData.alerts[0].asignador_rol || 'N/A'}`, margin, currentY);

            addPdfFooter(doc, { pageNumber: doc.internal.getNumberOfPages(), pageCount: clientNames.length });
        }

        doc.save(`Receta_Consolidada_Admin_${new Date().toISOString().slice(0, 10)}.pdf`);
        const pdfBlob = doc.output('blob');
        await uploadPdfAndLog(pdfBlob, `Receta_Consolidada_Admin`, 'receta_consolidada_admin', `Receta Consolidada de Clientes (Admin)`);
        showGlobalNotification('Receta Consolidada Generada', 'La receta médica consolidada para todos los clientes se ha generado y descargado con éxito.', 'success');

    } catch (error) {
        console.error('Error generando receta médica consolidada para admin:', error);
        showGlobalNotification('Error', `No se pudo generar la receta médica consolidada para el administrador: ${error.message}`, 'error');
    }
}