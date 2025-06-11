# medialert/routers/users.py

from flask import Blueprint, request, jsonify, session
from services.user_service import get_users, get_user_by_id, create_user, update_user, get_eps_list
from utils.decorators import admin_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/clientes', methods=['GET', 'POST'])
@admin_required
def manage_clientes():
    admin_id_actual = session.get('user_id')

    if request.method == 'GET':
        estado_filtro = request.args.get('estado', None)
        rol_filtro = request.args.get('rol', None)
        search_query = request.args.get('query', None)
        try:
            users = get_users(estado_filtro, rol_filtro, search_query)
            return jsonify(users)
        except Exception as e:
            return jsonify({'error': f'Error al obtener clientes: {e}'}), 500

    if request.method == 'POST':
        data = request.json
        try:
            new_id = create_user(data, admin_id_actual)
            return jsonify({'message': 'Cliente creado con éxito.', 'id': new_id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error al crear cliente: {e}'}), 500

@users_bp.route('/clientes/<int:uid>', methods=['GET', 'PUT'])
@admin_required
def manage_single_cliente(uid):
    admin_id_actual = session.get('user_id')

    try:
        current_user_data = get_user_by_id(uid)
        if not current_user_data:
            return jsonify({'error': 'Usuario no encontrado.'}), 404
        
        if current_user_data['rol'] != 'cliente':
            return jsonify({'error': 'Esta ruta es solo para gestionar clientes.'}), 403

        if request.method == 'GET':
            return jsonify(current_user_data)
            
        if request.method == 'PUT':
            data = request.json
            update_user(uid, data, current_user_data, admin_id_actual)
            return jsonify({'message': f'Cliente {uid} actualizado con éxito.'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error al gestionar cliente {uid}: {e}'}), 500

@users_bp.route('/eps', methods=['GET'])
@admin_required # O login_required si los clientes también necesitan esta lista
def get_eps():
    try:
        eps_list = get_eps_list()
        return jsonify(eps_list)
    except Exception as e:
        return jsonify({'error': f'Error al cargar las EPS: {e}'}), 500