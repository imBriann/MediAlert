# medialert/services/alert_service.py

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app, session
from datetime import time

from database import get_db_connection, registrar_auditoria_aplicacion

def get_alerts(usuario_id_filtro=None, group_by_client=False):
    """Obtiene alertas o un conteo de alertas agrupado por cliente."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if group_by_client:
            query = """
                SELECT
                    u.id as usuario_id,
                    u.nombre as cliente_nombre,
                    u.cedula,
                    u.estado_usuario,
                    COUNT(CASE WHEN a.estado = 'activa' THEN 1 ELSE NULL END) as alertas_activas_count,
                    COUNT(a.id) as total_alertas_count
                FROM usuarios u
                LEFT JOIN alertas a ON u.id = a.usuario_id
                WHERE u.rol = 'cliente'
                GROUP BY u.id, u.nombre, u.cedula, u.estado_usuario
                ORDER BY u.nombre;
            """
            cur.execute(query)
            clientes_con_alertas = cur.fetchall()
            return clientes_con_alertas
        else:
            query_parts = ["""
                SELECT
                    a.id, a.usuario_id, u.nombre as cliente_nombre, u.estado_usuario,
                    a.medicamento_id, m.nombre as medicamento_nombre, m.estado_medicamento,
                    a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida, 
                    a.estado as estado_alerta, a.asignado_por_usuario_id, ap.nombre as asignador_nombre
                FROM alertas a
                JOIN usuarios u ON a.usuario_id = u.id
                JOIN medicamentos m ON a.medicamento_id = m.id
                LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
            """]
            conditions = []
            params = []

            if usuario_id_filtro:
                conditions.append("a.usuario_id = %s")
                params.append(usuario_id_filtro)

            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            query_parts.append("ORDER BY u.nombre, m.nombre, a.fecha_inicio")

            final_query = " ".join(query_parts)
            cur.execute(final_query, tuple(params))
            alertas = cur.fetchall()

            for alerta in alertas:
                if isinstance(alerta.get('hora_preferida'), (time,)):
                    alerta['hora_preferida'] = alerta['hora_preferida'].strftime('%H:%M:%S')
            return alertas
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener alertas: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_alert_by_id(alerta_id):
    """Obtiene una alerta por su ID."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM alertas WHERE id = %s", (alerta_id,))
        alerta = cur.fetchone()
        return alerta
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener alerta {alerta_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_alert(alert_data, admin_id_actual):
    """Crea una nueva alerta."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        usuario_id = alert_data.get('usuario_id')
        medicamento_id = alert_data.get('medicamento_id')
        fecha_inicio = alert_data.get('fecha_inicio')

        if not all([usuario_id, medicamento_id, fecha_inicio]):
            raise ValueError('ID de usuario, ID de medicamento y fecha de inicio son requeridos.')

        cur.execute("SELECT estado_usuario FROM usuarios WHERE id = %s AND rol = 'cliente'", (usuario_id,))
        user_check = cur.fetchone()
        if not user_check or user_check['estado_usuario'] != 'activo':
            raise ValueError('El usuario seleccionado no es un cliente activo.')

        cur.execute("SELECT estado_medicamento FROM medicamentos WHERE id = %s", (medicamento_id,))
        med_check = cur.fetchone()
        if not med_check or med_check['estado_medicamento'] != 'disponible':
            raise ValueError('El medicamento seleccionado no está disponible.')

        dosis = alert_data.get('dosis')
        frecuencia = alert_data.get('frecuencia')
        fecha_fin = alert_data.get('fecha_fin') if alert_data.get('fecha_fin') else None
        hora_preferida = alert_data.get('hora_preferida') if alert_data.get('hora_preferida') else None
        estado_alerta = alert_data.get('estado', 'activa')

        if estado_alerta not in ['activa', 'inactiva', 'completada', 'fallida']:
            raise ValueError('Valor de estado de alerta no válido.')

        cur.execute(
            """
            INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, asignado_por_usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado_alerta, admin_id_actual)
        )
        new_id = cur.fetchone()['id']
        conn.commit()
        registrar_auditoria_aplicacion(
            'CREACION_ALERTA',
            tabla_afectada='alertas',
            registro_id=str(new_id),
            datos_nuevos=alert_data,
            detalles_adicionales={'creado_por_admin_id': admin_id_actual}
        )
        return new_id
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al crear alerta: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_alert(alerta_id, alert_data, old_alerta_data, admin_id_actual):
    """Actualiza una alerta existente."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        usuario_id = alert_data.get('usuario_id', old_alerta_data['usuario_id'])
        medicamento_id = alert_data.get('medicamento_id', old_alerta_data['medicamento_id'])
        dosis = alert_data.get('dosis', old_alerta_data['dosis'])
        frecuencia = alert_data.get('frecuencia', old_alerta_data['frecuencia'])
        fecha_inicio = alert_data.get('fecha_inicio', old_alerta_data['fecha_inicio'])
        fecha_fin = alert_data.get('fecha_fin', old_alerta_data['fecha_fin'])
        if fecha_fin == '': fecha_fin = None
        hora_preferida = alert_data.get('hora_preferida', old_alerta_data['hora_preferida'])
        if hora_preferida == '': hora_preferida = None
        estado = alert_data.get('estado', old_alerta_data['estado'])

        if estado not in ['activa', 'inactiva', 'completada', 'fallida']:
            raise ValueError('Valor de estado de alerta no válido.')
        
        cur.execute(
            """
            UPDATE alertas SET usuario_id=%s, medicamento_id=%s, dosis=%s, frecuencia=%s, 
            fecha_inicio=%s, fecha_fin=%s, hora_preferida=%s, estado=%s, asignado_por_usuario_id=%s
            WHERE id=%s
            """,
            (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, admin_id_actual, alerta_id)
        )
        conn.commit()
        registrar_auditoria_aplicacion(
            'EDICION_ALERTA', 
            tabla_afectada='alertas', 
            registro_id=str(alerta_id),
            datos_anteriores=dict(old_alerta_data),
            datos_nuevos=alert_data,
            detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
        )
        return True
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al actualizar alerta {alerta_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def delete_alert(alerta_id, old_alerta_data, admin_id_actual):
    """Elimina una alerta."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("DELETE FROM alertas WHERE id = %s", (alerta_id,))
        conn.commit()
        registrar_auditoria_aplicacion(
            'ELIMINACION_ALERTA', 
            tabla_afectada='alertas', 
            registro_id=str(alerta_id),
            datos_anteriores=dict(old_alerta_data),
            detalles_adicionales={'eliminado_por_admin_id': admin_id_actual}
        )
        return True
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al eliminar alerta {alerta_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_client_alerts(client_id):
    """Obtiene todas las alertas para un cliente específico."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                a.id, m.nombre as medicamento_nombre, a.dosis, a.frecuencia, 
                a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.usuario_id = %s 
            ORDER BY a.fecha_inicio DESC, a.hora_preferida DESC
        """, (client_id,))
        alertas = cur.fetchall()

        for alerta in alertas:
            if isinstance(alerta.get('hora_preferida'), time):
                alerta['hora_preferida'] = alerta['hora_preferida'].strftime('%H:%M:%S')
        return alertas
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener mis_alertas para cliente {client_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_consolidated_client_recipes(client_id):
    """Obtiene alertas activas de un cliente para una receta consolidada."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                a.id as alerta_id, a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado as estado_alerta,
                m.nombre as medicamento_nombre, m.descripcion as medicamento_descripcion, m.composicion as medicamento_composicion,
                m.indicaciones as medicamento_indicaciones, m.sintomas_secundarios as medicamento_sintomas_secundarios,
                m.rango_edad as medicamento_rango_edad,
                u.nombre as cliente_nombre, u.cedula as cliente_cedula, u.fecha_nacimiento as cliente_fecha_nacimiento,
                u.telefono as cliente_telefono, u.ciudad as cliente_ciudad,
                e.nombre as eps_nombre, e.nit as eps_nit,
                ap.nombre as asignador_nombre, ap.cedula as asignador_cedula, ap.rol as asignador_rol
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            LEFT JOIN eps e ON u.eps_id = e.id
            LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
            WHERE a.usuario_id = %s AND a.estado = 'activa' AND m.estado_medicamento = 'disponible'
            ORDER BY m.nombre;
        """, (client_id,))
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
        current_app.logger.error(f"Error de BD al obtener recetas consolidadas para cliente {client_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_recipe_data(alerta_id):
    """Obtiene datos de una alerta específica para generar una receta médica."""
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
            JOIN usuarios u ON a.usuario_id = u.id
            JOIN medicamentos m ON a.medicamento_id = m.id
            LEFT JOIN eps e ON u.eps_id = e.id
            LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
            WHERE a.id = %s
        """, (alerta_id,))
        
        receta_data = cur.fetchone()

        if receta_data:
            if receta_data.get('fecha_inicio'):
                receta_data['fecha_inicio'] = receta_data['fecha_inicio'].isoformat()
            if receta_data.get('fecha_fin'):
                receta_data['fecha_fin'] = receta_data['fecha_fin'].isoformat()
            if receta_data.get('hora_preferida'):
                receta_data['hora_preferida'] = str(receta_data['hora_preferida'])
            if receta_data.get('cliente_fecha_nacimiento'):
                receta_data['cliente_fecha_nacimiento'] = receta_data['cliente_fecha_nacimiento'].isoformat()

        return receta_data

    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener datos de receta {alerta_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()