// MediAlert/static/js/report-generator.js

/**
 * Obtiene una imagen desde una URL y la convierte a una cadena Data URL (Base64).
 * @param {string} url La URL de la imagen.
 * @returns {Promise<string|null>} Una promesa que resuelve con la cadena Data URL o null si hay error.
 */
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

/**
 * Agrega un encabezado personalizado al documento PDF, incluyendo el logo.
 * @param {jsPDF} doc Instancia del documento jsPDF.
 * @param {string} title Título del reporte.
 */
async function addPdfHeader(doc, title) {
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 35;
    const topMargin = 30;

    const logoUrl = '/static/img/logo1.png'; // Ruta a tu logo en la carpeta static
    const logoBase64 = await getLogoBase64DataUrl(logoUrl);

    if (logoBase64) {
        try {
            const logoImgProps = doc.getImageProperties(logoBase64);
            const aspectRatio = logoImgProps.width / logoImgProps.height;
            const logoHeightPdf = 28; // Altura deseada del logo en el PDF (en puntos)
            const logoWidthPdf = logoHeightPdf * aspectRatio;
            doc.addImage(logoBase64, logoImgProps.fileType.toUpperCase(), margin, topMargin, logoWidthPdf, logoHeightPdf);
        } catch (e) {
            console.error("Error al añadir el logo (obtenido dinámicamente) al PDF:", e);
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(12);
            doc.setTextColor(44, 62, 80);
            doc.text("MediAlert", margin, topMargin + 15); // Fallback si el logo falla
        }
    } else {
        console.warn("El logo no pudo ser cargado. Usando texto de fallback.");
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(14);
        doc.setTextColor(44, 62, 80);
        doc.text("MediAlert", margin, topMargin + 15);
    }

    // Título del Reporte
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(18);
    doc.setTextColor(40, 40, 40); // Gris oscuro
    const titleWidth = doc.getTextWidth(title);
    doc.text(title, (pageWidth - titleWidth) / 2, topMargin + 20);

    // Línea horizontal
    doc.setDrawColor(180, 180, 180);
    doc.line(margin, topMargin + 35, pageWidth - margin, topMargin + 35);
}

/**
 * Agrega un pie de página personalizado al documento PDF.
 * Se llama para cada página a través de didDrawPage en autoTable.
 * @param {jsPDF} doc Instancia del documento jsPDF.
 * @param {object} data Información de la página actual de autoTable.
 */
function addPdfFooter(doc, data) {
    const pageCount = doc.internal.getNumberOfPages();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 35;
    const footerY = pageHeight - 30;

    doc.setFont('helvetica', 'italic');
    doc.setFontSize(8);
    doc.setTextColor(100, 100, 100); // Gris medio

    // Fecha de generación (puedes ponerla una vez o en cada página)
    const generationText = `Generado: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`;
    doc.text(generationText, margin, footerY);

    // Texto central (ej. nombre de la compañía)
    const companyText = "MediAlert - Reporte Interno";
    const companyTextWidth = doc.getTextWidth(companyText);
    doc.text(companyText, (pageWidth - companyTextWidth) / 2, footerY);


    // Numeración de página
    const pageNumText = `Página ${data.pageNumber} de ${pageCount}`;
    const pageNumTextWidth = doc.getTextWidth(pageNumText);
    doc.text(pageNumText, pageWidth - margin - pageNumTextWidth, footerY);
}


async function uploadPdfAndLog(pdfBlob, originalFilename, reportTypeForLog, reportTitleForLog) { //
    const formData = new FormData();
    formData.append('report_pdf', pdfBlob, originalFilename + ".pdf");

    try {
        const uploadResponse = await fetch('/api/admin/reportes/upload_pdf', { //
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const errorData = await uploadResponse.json();
            throw new Error(`Error al subir PDF: ${errorData.error || uploadResponse.statusText}`);
        }
        const uploadResult = await uploadResponse.json();
        const serverFilename = uploadResult.filename;

        const logResponse = await fetch('/api/admin/reportes_log', { //
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
        alert(`Error al procesar el reporte: ${error.message}`);
    }
}

// Hacer generatePdfAndUpload asíncrona para poder usar await con addPdfHeader
async function generatePdfAndUpload(reportConfig) {
    const { title, headers, data, filename, columnStyles = {}, bodyStyles = {}, tipo_reporte_log, orientation = 'p', format = 'a4' } = reportConfig;
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF(orientation, 'pt', format);
    const margin = 35;

    // Esperar a que el encabezado (que incluye el logo) se complete
    await addPdfHeader(doc, title);

    const tableStartY = 75; // Ajustar si la altura del encabezado cambia

    const headForTable = [headers.map(h => h.text)];
    const bodyForTable = data.map(row => headers.map(header => {
        const value = row[header.key];
        return value !== undefined && value !== null ? String(value) : '';
    }));

    console.log("generatePdfAndUpload - Datos para la tabla:", JSON.parse(JSON.stringify(data))); //
    console.log("generatePdfAndUpload - Cabeceras para la tabla:", JSON.parse(JSON.stringify(headForTable))); //
    console.log("generatePdfAndUpload - Cuerpo procesado para la tabla:", JSON.parse(JSON.stringify(bodyForTable))); //

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
        // uploadPdfAndLog ya es async, así que esperamos su finalización
        await uploadPdfAndLog(pdfBlob, filename, tipo_reporte_log, title);
    }
}

async function generateUsuariosReport() {
    try {
        const clientesPromise = fetchData('/api/admin/clientes?estado=todos&rol=cliente', 'Error al obtener datos de clientes'); //
        const adminsPromise = fetchData('/api/admin/clientes?estado=todos&rol=admin', 'Error al obtener datos de administradores'); //
        const [clientes, admins] = await Promise.all([clientesPromise, adminsPromise]);
        
        console.log("generateUsuariosReport - Clientes fetched:", JSON.parse(JSON.stringify(clientes || [])));
        console.log("generateUsuariosReport - Admins fetched:", JSON.parse(JSON.stringify(admins || [])));

        const allUsers = [...(clientes || []), ...(admins || [])];
        console.log("generateUsuariosReport - AllUsers combined:", JSON.parse(JSON.stringify(allUsers)));

        if (!allUsers.length) { alert('No hay datos de usuarios para generar el reporte.'); return; }
        
        const dataForPdf = allUsers.map(user => ({
            nombre: user.nombre || 'N/A',
            cedula: user.cedula || 'N/A',
            email: user.email || 'N/A',
            rol: user.rol ? user.rol.charAt(0).toUpperCase() + user.rol.slice(1) : 'N/A',
            estado_usuario: user.estado_usuario ? user.estado_usuario.charAt(0).toUpperCase() + user.estado_usuario.slice(1) : 'N/A'
        }));
        console.log("generateUsuariosReport - Data mapped for PDF (dataForPdf):", JSON.parse(JSON.stringify(dataForPdf)));
        
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
        generatePdfAndUpload(reportConfig);
    } catch (error) { console.error('Error generando reporte de usuarios:', error); alert('No se pudo generar el reporte de usuarios: ' + error.message); }
}

async function generateMedicamentosReport() {
    try {
        const medicamentos = await fetchData('/api/admin/medicamentos?estado=todos', 'Error al obtener datos de medicamentos'); //
        console.log("generateMedicamentosReport - Medicamentos fetched:", JSON.parse(JSON.stringify(medicamentos || [])));
        if (!medicamentos || !medicamentos.length) { alert('No hay datos de medicamentos para generar el reporte.'); return; }

        const dataForPdf = medicamentos.map(m => ({
            nombre: m.nombre || "N/A", descripcion: m.descripcion || "N/A",
            composicion: m.composicion || "N/A", indicaciones: m.indicaciones || "N/A",
            rango_edad: m.rango_edad || "N/A",
            estado_medicamento: m.estado_medicamento ? m.estado_medicamento.charAt(0).toUpperCase() + m.estado_medicamento.slice(1) : "N/A"
        }));
        console.log("generateMedicamentosReport - Data mapped for PDF (dataForPdf):", JSON.parse(JSON.stringify(dataForPdf)));

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
        generatePdfAndUpload(reportConfig);
    } catch (error) { console.error('Error generando reporte de medicamentos:', error); alert('No se pudo generar el reporte de medicamentos: ' + error.message); }
}

async function generateAlertasActivasReport() {
    try {
        const alertas = await fetchData('/api/admin/alertas', 'Error al obtener datos de alertas'); //
        console.log("generateAlertasActivasReport - Alertas fetched:", JSON.parse(JSON.stringify(alertas || [])));
        const activas = alertas.filter(a => a.estado_alerta === 'activa');
        if (!activas.length) { alert('No hay alertas activas para generar el reporte.'); return; }

        const dataForPdf = activas.map(a => ({
            cliente_nombre: a.cliente_nombre || "N/A", medicamento_nombre: a.medicamento_nombre || "N/A",
            dosis: a.dosis || "N/A", frecuencia: a.frecuencia || "N/A",
            fecha_inicio_f: a.fecha_inicio ? formatDate(a.fecha_inicio) : "N/A",
            fecha_fin_f: a.fecha_fin ? formatDate(a.fecha_fin) : "Indefinido",
            hora_preferida_f: a.hora_preferida ? formatTime(a.hora_preferida) : "N/A"
        }));
        console.log("generateAlertasActivasReport - Data mapped for PDF (dataForPdf):", JSON.parse(JSON.stringify(dataForPdf)));
        
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
        generatePdfAndUpload(reportConfig);
    } catch (error) { console.error('Error generando reporte de alertas activas:', error); alert('No se pudo generar el reporte de alertas activas: ' + error.message); }
}

async function generateAuditoriaReport() {
    try {
        const logs = await fetchData('/api/admin/auditoria?limit=100', 'Error al obtener datos de auditoría'); //
        console.log("generateAuditoriaReport - Logs fetched:", JSON.parse(JSON.stringify(logs || [])));
        if (!logs || !logs.length) { alert('No hay datos de auditoría para generar el reporte.'); return; }
        
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
        console.log("generateAuditoriaReport - Data mapped for PDF (dataForPdf):", JSON.parse(JSON.stringify(dataForPdf)));
        
        const reportConfig = {
            title: 'Reporte de Auditoría del Sistema (Últimos 100)', filename: 'Reporte_Auditoria', tipo_reporte_log: 'auditoria', 
            orientation: 'l', format: 'a3', // A3 para más espacio
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
                detalles_f: { cellWidth: 'auto' } // Permitir que esta columna tome el espacio restante
            },
            bodyStyles: { fontSize: 7, cellPadding: {top: 2, right: 3, bottom: 2, left: 3} }
        };
        generatePdfAndUpload(reportConfig);
    } catch (error) { console.error('Error generando reporte de auditoría:', error); alert('No se pudo generar el reporte de auditoría: ' + error.message); }
}

// Funciones formatDate, formatTime, getFriendlyTableName y fetchData se esperan
// desde admin-data-handlers.js, que debe cargarse ANTES de este script.