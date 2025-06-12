# medialert/routers/reports.py

from flask import Blueprint, request, jsonify, send_from_directory
# 1. Actualiza la línea de importación
from services.report_service import (
    log_report_generation, get_report_logs, save_pdf_file, 
    get_pdf_file_info, get_all_active_consolidated_recipes, get_audit_logs
)
from utils.decorators import admin_required
import os

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reportes_log', methods=['GET', 'POST'])
@admin_required
def manage_reportes_log():
    if request.method == 'POST':
        data = request.json
        tipo_reporte = data.get('tipo_reporte')
        nombre_reporte = data.get('nombre_reporte')
        pdf_filename = data.get('pdf_filename')

        if not all([tipo_reporte, nombre_reporte, pdf_filename]):
            return jsonify({'error': 'Tipo, nombre del reporte y nombre del archivo PDF son requeridos.'}), 400
        
        try:
            log_id = log_report_generation(tipo_reporte, nombre_reporte, pdf_filename)
            return jsonify({'message': 'Generación de reporte registrada con éxito.', 'log_id': log_id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error al registrar generación de reporte: {e}'}), 500

    if request.method == 'GET':
        limit = request.args.get('limit', type=int, default=50)
        try:
            logs = get_report_logs(limit)
            return jsonify(logs)
        except Exception as e:
            return jsonify({'error': f'Error al cargar los registros de auditoría: {e}'}), 500

@reports_bp.route('/reportes/upload_pdf', methods=['POST'])
@admin_required
def upload_report_pdf():
    if 'report_pdf' not in request.files:
        return jsonify({'error': 'No se encontró el archivo PDF en la solicitud.'}), 400
    
    file = request.files['report_pdf']
    
    try:
        storage_filename = save_pdf_file(file)
        return jsonify({'message': 'Archivo PDF subido con éxito.', 'filename': storage_filename}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error interno al guardar el archivo PDF: {e}'}), 500

@reports_bp.route('/auditoria', methods=['GET'])
@admin_required
def get_auditoria_logs():
    limit = request.args.get('limit', type=int, default=100)
    module_filter = request.args.get('tabla')
    user_search = request.args.get('search_user') # El frontend usa 'search_user' en el query
    try:
        # Llama a la nueva y correcta función de servicio
        logs = get_audit_logs(limit=limit, tabla_filtro=module_filter, user_search_term=user_search)
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': f'Error al cargar los registros de auditoría: {e}'}), 500


@reports_bp.route('/reportes/download/<int:log_id>', methods=['GET'])
@admin_required
def download_report_pdf(log_id):
    try:
        pdf_filename, download_name = get_pdf_file_info(log_id)
        if not pdf_filename:
            return jsonify({'error': 'Registro de reporte no encontrado.'}), 404
        
        reports_dir = os.path.join(reports_bp.root_path, '..', '..', 'instance', 'generated_reports')
        
        if not os.path.exists(os.path.join(reports_dir, pdf_filename)):
            return jsonify({'error': 'Archivo PDF no encontrado en el servidor.'}), 404

        return send_from_directory(directory=reports_dir, 
                                   path=pdf_filename, 
                                   as_attachment=True, 
                                   download_name=download_name)
    except Exception as e:
        return jsonify({'error': f'Error al procesar la descarga del reporte: {e}'}), 500

@reports_bp.route('/recetas_consolidadas', methods=['GET'])
@admin_required
def get_consolidated_recetas_admin_route():
    try:
        recetas_data = get_all_active_consolidated_recipes()
        if not recetas_data:
            return jsonify({'message': 'No hay alertas activas de clientes para generar una receta consolidada.'}), 200
        return jsonify(recetas_data)
    except Exception as e:
        return jsonify({'error': f'Error al cargar las recetas consolidadas para el administrador: {e}'}), 500