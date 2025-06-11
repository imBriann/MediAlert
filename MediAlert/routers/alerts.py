# medialert/routers/alerts.py

from flask import Blueprint, request, jsonify, session
from services.alert_service import (
    get_alerts, get_alert_by_id, create_alert, update_alert, delete_alert,
    get_client_alerts, get_consolidated_client_recipes, get_recipe_data
)
from utils.decorators import admin_required, login_required

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/admin/alertas', methods=['GET', 'POST'])
@admin_required
def manage_alertas_admin():
    admin_id_actual = session.get('user_id')

    if request.method == 'GET':
        usuario_id_filtro = request.args.get('usuario_id', type=int)
        group_by_client = request.args.get('group_by_client', 'false').lower() == 'true'
        try:
            alertas = get_alerts(usuario_id_filtro, group_by_client)
            return jsonify(alertas)
        except Exception as e:
            return jsonify({'error': f'Error al obtener alertas: {e}'}), 500

    if request.method == 'POST':
        data = request.json
        try:
            new_id = create_alert(data, admin_id_actual)
            return jsonify({'message': 'Alerta creada con éxito.', 'id': new_id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error al crear alerta: {e}'}), 500

@alerts_bp.route('/admin/alertas/<int:alerta_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def manage_single_alerta_admin(alerta_id):
    admin_id_actual = session.get('user_id')

    try:
        alerta = get_alert_by_id(alerta_id)
        if not alerta:
            return jsonify({'error': 'Alerta no encontrada.'}), 404

        if request.method == 'GET':
            if isinstance(alerta.get('hora_preferida'), (type(None),)):
                alerta['hora_preferida'] = None
            else:
                 alerta['hora_preferida'] = str(alerta['hora_preferida'])
            return jsonify(alerta)

        if request.method == 'PUT':
            data = request.json
            update_alert(alerta_id, data, alerta, admin_id_actual)
            return jsonify({'message': f'Alerta {alerta_id} actualizada con éxito.'})

        if request.method == 'DELETE':
            delete_alert(alerta_id, alerta, admin_id_actual)
            return jsonify({'message': f'Alerta {alerta_id} eliminada con éxito.'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error al gestionar alerta {alerta_id}: {e}'}), 500

@alerts_bp.route('/cliente/mis_alertas', methods=['GET'])
@login_required
def get_mis_alertas_cliente():
    if session.get('rol') != 'cliente':
        return jsonify({'error': 'Acceso denegado. Esta vista es solo para clientes.'}), 403
    
    cliente_id = session['user_id']
    try:
        alertas = get_client_alerts(cliente_id)
        return jsonify(alertas)
    except Exception as e:
        return jsonify({'error': f'Error al cargar tus alertas: {e}'}), 500

@alerts_bp.route('/cliente/recetas_consolidadas', methods=['GET'])
@login_required
def get_consolidated_recetas_cliente():
    """
    Endpoint para que un cliente obtenga una lista consolidada de sus alertas activas
    para generar una receta médica. También permite a un admin solicitar la receta de un cliente específico.
    """
    user_id_param = request.args.get('user_id', type=int)

    # Determine which client_id to use based on role and parameters
    if session.get('rol') == 'cliente':
        # Clients can only request their own data
        if user_id_param and user_id_param != session.get('user_id'):
            return jsonify({'error': 'Acceso denegado. Un cliente solo puede ver sus propias recetas consolidadas.'}), 403
        cliente_id = session.get('user_id')
    elif session.get('rol') == 'admin':
        # Admins can request data for any client, so user_id_param is mandatory
        if not user_id_param:
            return jsonify({'error': 'Se requiere user_id para que un administrador solicite recetas consolidadas de un cliente específico.'}), 400
        cliente_id = user_id_param
    else:
        # Neither client nor admin role, or invalid scenario
        return jsonify({'error': 'Acceso denegado. Rol de usuario no válido para esta operación.'}), 403

    try:
        recetas_data = get_consolidated_client_recipes(cliente_id)
        if not recetas_data:
            return jsonify({'message': 'No hay alertas activas para generar una receta consolidada.'}), 200
        return jsonify(recetas_data)
    except Exception as e:
        return jsonify({'error': f'Error al cargar las recetas consolidadas: {e}'}), 500

@alerts_bp.route('/receta_medica/<int:alerta_id>', methods=['GET'])
@login_required 
def get_receta_data_route(alerta_id):
    try:
        receta_data = get_recipe_data(alerta_id)
        if not receta_data:
            return jsonify({'error': 'Alerta o receta no encontrada.'}), 404
        
        # Permite que el cliente vea solo sus propias recetas, y el admin vea cualquiera
        if session.get('rol') == 'cliente' and receta_data['usuario_id'] != session.get('user_id'):
            return jsonify({'error': 'No autorizado para ver esta receta.'}), 403
            
        return jsonify(receta_data)
    except Exception as e:
        return jsonify({'error': f'Error al cargar los datos de la receta: {e}'}), 500