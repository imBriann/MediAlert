# medialert/routers/medications.py

from flask import Blueprint, request, jsonify, session
from services.medication_service import get_medications, get_medication_by_id, create_medication, update_medication
from utils.decorators import admin_required

medications_bp = Blueprint('medications', __name__)

@medications_bp.route('/medicamentos', methods=['GET', 'POST'])
@admin_required
def manage_medicamentos():
    admin_id_actual = session.get('user_id')

    if request.method == 'GET':
        estado_filtro = request.args.get('estado', 'disponible')
        try:
            medicamentos = get_medications(estado_filtro)
            return jsonify(medicamentos)
        except Exception as e:
            return jsonify({'error': f'Error al obtener medicamentos: {e}'}), 500
        
    if request.method == 'POST':
        data = request.json
        try:
            new_id = create_medication(data, admin_id_actual)
            return jsonify({'message': 'Medicamento creado con éxito.', 'id': new_id}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f'Error al crear medicamento: {e}'}), 500

@medications_bp.route('/medicamentos/<int:mid>', methods=['GET','PUT'])
@admin_required
def manage_single_medicamento(mid):
    admin_id_actual = session.get('user_id')

    try:
        medicamento = get_medication_by_id(mid)
        if not medicamento:
            return jsonify({'error': 'Medicamento no encontrado.'}), 404

        if request.method == 'GET':
            return jsonify(medicamento)

        if request.method == 'PUT':
            data = request.json
            update_medication(mid, data, medicamento, admin_id_actual)
            return jsonify({'message': f'Medicamento {mid} actualizado con éxito.'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Error al gestionar medicamento {mid}: {e}'}), 500