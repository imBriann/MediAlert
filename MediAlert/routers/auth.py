# medialert/routers/auth.py

from flask import Blueprint, request, jsonify, session
from services.auth_service import verify_and_login_user, logout_user, get_current_user_session_info
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    cedula = data.get('cedula')
    password_ingresada = data.get('contrasena')

    if not cedula or not password_ingresada:
        return jsonify({'error': 'Cédula y contraseña son requeridas.'}), 400

    try:
        user_info = verify_and_login_user(cedula, password_ingresada)
        if user_info:
            return jsonify(user_info)
        else:
            return jsonify({'error': 'Credenciales inválidas o usuario inactivo.'}), 401
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor al intentar iniciar sesión: {e}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required 
def logout():
    try:
        logout_user()
        return jsonify({'message': 'Cierre de sesión exitoso.'}), 200
    except Exception as e:
        return jsonify({'error': f'Error interno al cerrar sesión: {e}'}), 500

@auth_bp.route('/session_check', methods=['GET'])
@login_required
def session_check():
    return jsonify(get_current_user_session_info())

@auth_bp.route('/configuracion/usuario', methods=['GET'])
@login_required
def get_configuracion_usuario():
    user_id = session.get('user_id')
    try:
        from services.user_service import get_user_by_id # Importar aquí para evitar circular imports
        user_data = get_user_by_id(user_id)
        if not user_data:
            return jsonify({'error': 'Usuario no encontrado.'}), 404
        return jsonify(user_data)
    except Exception as e:
        return jsonify({'error': f'Error al cargar datos de configuración: {e}'}), 500

@auth_bp.route('/configuracion/cambiar_contrasena', methods=['POST'])
@login_required
def cambiar_contrasena_usuario():
    user_id = session.get('user_id')
    data = request.json
    contrasena_actual = data.get('contrasena_actual')
    contrasena_nueva = data.get('contrasena_nueva')
    contrasena_nueva_confirmacion = data.get('contrasena_nueva_confirmacion')

    if not all([contrasena_actual, contrasena_nueva, contrasena_nueva_confirmacion]):
        return jsonify({'error': 'Todos los campos de contraseña son requeridos.'}), 400
    
    if contrasena_nueva != contrasena_nueva_confirmacion:
        return jsonify({'error': 'La nueva contraseña y su confirmación no coinciden.'}), 400
    
    if len(contrasena_nueva) < 6: 
        return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres.'}), 400

    try:
        success, message = verify_user_password_and_update(user_id, contrasena_actual, contrasena_nueva)
        if success:
            return jsonify({'message': message})
        else:
            return jsonify({'error': message}), 401
    except Exception as e:
        return jsonify({'error': f'Error interno del servidor al cambiar la contraseña: {e}'}), 500