# medialert/services/medication_service.py

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app, session

from database import get_db_connection, registrar_auditoria_aplicacion

def get_medications(estado_filtro='disponible'):
    """Obtiene una lista de medicamentos basada en el estado."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = "SELECT id, nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento FROM medicamentos"
        params = []
        if estado_filtro != 'todos':
            query += " WHERE estado_medicamento = %s"
            params.append(estado_filtro)
        query += " ORDER BY nombre"

        cur.execute(query, tuple(params))
        medicamentos = cur.fetchall()
        return medicamentos
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener medicamentos: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_medication_by_id(mid):
    """Obtiene un medicamento por su ID."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM medicamentos WHERE id = %s", (mid,))
        medicamento = cur.fetchone()
        return medicamento
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener medicamento {mid}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_medication(med_data, admin_id_actual):
    """Crea un nuevo medicamento."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        nombre = med_data.get('nombre')
        descripcion = med_data.get('descripcion')
        composicion = med_data.get('composicion')
        sintomas_secundarios = med_data.get('sintomas_secundarios')
        indicaciones = med_data.get('indicaciones')
        rango_edad = med_data.get('rango_edad')

        if not nombre:
            raise ValueError('El nombre del medicamento es requerido.')
        
        cur.execute(
            """
            INSERT INTO medicamentos (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento) 
            VALUES (%s, %s, %s, %s, %s, %s, 'disponible') RETURNING id
            """,
            (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad)
        )
        new_id = cur.fetchone()['id']
        conn.commit()
        registrar_auditoria_aplicacion(
            'CREACION_MEDICAMENTO', 
            tabla_afectada='medicamentos', 
            registro_id=str(new_id),
            datos_nuevos=med_data,
            detalles_adicionales={'creado_por_admin_id': admin_id_actual}
        )
        return new_id
    except psycopg2.IntegrityError as e:
        conn.rollback()
        raise ValueError(f'El medicamento "{nombre}" ya existe.')
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al crear medicamento: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_medication(mid, med_data, old_med_data, admin_id_actual):
    """Actualiza la información de un medicamento existente."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        nombre = med_data.get('nombre', old_med_data['nombre'])
        descripcion = med_data.get('descripcion', old_med_data['descripcion'])
        composicion = med_data.get('composicion', old_med_data['composicion'])
        sintomas_secundarios = med_data.get('sintomas_secundarios', old_med_data['sintomas_secundarios'])
        indicaciones = med_data.get('indicaciones', old_med_data['indicaciones'])
        rango_edad = med_data.get('rango_edad', old_med_data['rango_edad'])
        estado_medicamento = med_data.get('estado_medicamento', old_med_data['estado_medicamento'])

        if estado_medicamento not in ['disponible', 'discontinuado']:
             raise ValueError('Valor de estado_medicamento no válido.')
        
        cur.execute(
            """
            UPDATE medicamentos SET nombre=%s, descripcion=%s, composicion=%s, 
            sintomas_secundarios=%s, indicaciones=%s, rango_edad=%s, estado_medicamento=%s 
            WHERE id=%s
            """,
            (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento, mid)
        )
        conn.commit()
        
        accion_audit = 'EDICION_MEDICAMENTO'
        if old_med_data['estado_medicamento'] == 'disponible' and estado_medicamento == 'discontinuado':
            accion_audit = 'DISCONTINUACION_MEDICAMENTO'
        elif old_med_data['estado_medicamento'] == 'discontinuado' and estado_medicamento == 'disponible':
            accion_audit = 'REACTIVACION_MEDICAMENTO'
        
        registrar_auditoria_aplicacion(
            accion_audit, 
            tabla_afectada='medicamentos', 
            registro_id=str(mid),
            datos_anteriores=dict(old_med_data),
            datos_nuevos=med_data,
            detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
        )
        return True
    except psycopg2.IntegrityError as e:
        conn.rollback()
        raise ValueError(f'El nombre de medicamento "{nombre}" ya existe para otro ID.')
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al actualizar medicamento {mid}: {e}")
        raise
    finally:
        if conn:
            conn.close()