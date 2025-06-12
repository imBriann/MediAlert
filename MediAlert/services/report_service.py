# medialert/services/report_service.py

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app, session
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime

from database import get_db_connection
import config # Importar el módulo config para allowed_file y rutas

def log_report_generation(tipo_reporte, nombre_reporte, pdf_filename):
    """Registra un evento de generación de reporte en la base de datos."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        cur.execute(
            """
            INSERT INTO reportes_log (tipo_reporte, nombre_reporte, pdf_filename, generado_por_usuario_id)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (tipo_reporte, nombre_reporte, pdf_filename, admin_id_actual)
        )
        conn.commit()
        log_id = cur.fetchone()['id']
        return log_id
    except psycopg2.IntegrityError as e:
        conn.rollback()
        current_app.logger.error(f"Error de integridad al registrar log de reporte: {e}")
        raise ValueError('Error de integridad al guardar el log del reporte.')
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al registrar generación de reporte: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_report_logs(limit=50):
    """Obtiene el historial de reportes generados."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT rl.id, rl.tipo_reporte, rl.nombre_reporte, rl.pdf_filename, 
                   rl.fecha_generacion, u.nombre as generado_por_nombre
            FROM reportes_log rl
            LEFT JOIN usuarios u ON rl.generado_por_usuario_id = u.id
            ORDER BY rl.fecha_generacion DESC
            LIMIT %s
        """, (limit,))
        logs = cur.fetchall()
        return logs
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener logs de auditoría: {e}")
        raise
    finally:
        if conn:
            conn.close()

def save_pdf_file(file):
    """Guarda un archivo PDF en el almacenamiento de reportes."""
    if file.filename == '':
        raise ValueError('No se seleccionó ningún archivo.')
        
    if not config.allowed_file(file.filename):
        raise ValueError('Tipo de archivo no permitido. Solo se aceptan PDFs.')
        
    unique_id = uuid.uuid4()
    extension = secure_filename(file.filename.rsplit('.', 1)[1].lower())
    storage_filename = f"{unique_id}.{extension}"
    
    # --- Correctly use REPORTS_STORAGE_PATH from app.config ---
    reports_dir = current_app.config['REPORTS_STORAGE_PATH']
    
    try:
        file.save(os.path.join(reports_dir, storage_filename))
        return storage_filename
    except Exception as e:
        current_app.logger.error(f"Error al guardar el archivo PDF subido: {e}")
        raise

def get_pdf_file_info(log_id):
    """Obtiene la información del archivo PDF de un reporte por su ID de log."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT pdf_filename, nombre_reporte FROM reportes_log WHERE id = %s", (log_id,))
        report_log = cur.fetchone()
        
        if not report_log:
            return None, None # No encontrado
            
        pdf_filename = report_log['pdf_filename']
        base_name = report_log['nombre_reporte'].replace(' ', '_').replace('/', '-')
        timestamp_part = pdf_filename.split('.')[0][:8]
        download_name = secure_filename(f"{base_name}_{timestamp_part}.pdf")

        return pdf_filename, download_name
                                   
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al intentar descargar reporte {log_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_all_active_consolidated_recipes():
    """Obtiene todas las alertas activas de todos los clientes para un reporte consolidado de admin."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                a.id as alerta_id, a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado as estado_alerta,
                u.nombre as cliente_nombre, u.cedula as cliente_cedula, u.fecha_nacimiento as cliente_fecha_nacimiento,
                u.telefono as cliente_telefono, u.ciudad as cliente_ciudad,
                m.nombre as medicamento_nombre, m.descripcion as medicamento_descripcion, m.composicion as medicamento_composicion,
                m.indicaciones as medicamento_indicaciones, m.sintomas_secundarios as medicamento_sintomas_secundarios,
                m.rango_edad as medicamento_rango_edad,
                e.nombre as eps_nombre, e.nit as eps_nit,
                ap.nombre as asignador_nombre, ap.cedula as asignador_cedula, ap.rol as asignador_rol
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            LEFT JOIN eps e ON u.eps_id = e.id
            LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
            WHERE a.estado = 'activa' AND m.estado_medicamento = 'disponible' AND u.rol = 'cliente'
            ORDER BY u.nombre, m.nombre;
        """)
        recetas_data = cur.fetchall()

        for receta in recetas_data:
            if receta.get('fecha_inicio'):
                receta['fecha_inicio'] = receta['fecha_inicio'].isoformat()
            if receta.get('fecha_fin'):
                receta['fecha_fin'] = receta['fecha_fin'].isoformat()
            if receta.get('hora_preferida'):
                receta['hora_preferida'] = str(receta['hora_preferida'])
            if receta.get('cliente_fecha_nacimiento'):
                receta['cliente_fecha_nacimiento'] = receta['cliente_fecha_nacimiento'].isoformat()

        return recetas_data
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener recetas consolidadas para admin: {e}")
        raise
    finally:
        if conn:
            conn.close()
            
def get_audit_logs(limit=100, tabla_filtro=None, user_search_term=None):
    """Obtiene el historial de auditoría del sistema con filtros."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query_parts = ["""
            SELECT
                aud.id, aud.fecha_hora, u_app.nombre as nombre_usuario_app,
                u_app.cedula as cedula_usuario_app,
                aud.usuario_db as usuario_postgres, aud.accion, aud.tabla_afectada,
                aud.registro_id_afectado, aud.datos_anteriores, aud.datos_nuevos,
                aud.detalles_adicionales
            FROM auditoria aud
            LEFT JOIN usuarios u_app ON aud.usuario_id_app = u_app.id
        """]
        conditions = []
        params = []

        if tabla_filtro:
            conditions.append("aud.tabla_afectada = %s")
            params.append(tabla_filtro)

        if user_search_term:
            conditions.append("(u_app.nombre ILIKE %s OR u_app.cedula ILIKE %s)")
            params.append(f"%{user_search_term}%")
            params.append(f"%{user_search_term}%")

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY aud.fecha_hora DESC")

        if limit:
            query_parts.append("LIMIT %s")
            params.append(limit)

        final_query = " ".join(query_parts)
        cur.execute(final_query, tuple(params))
        logs = cur.fetchall()
        return logs
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener logs de auditoría: {e}")
        raise
    finally:
        if conn:
            conn.close()