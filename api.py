from flask import jsonify, request
from flask_login import login_required, current_user
from . import main
from ..models import Room, Client, Booking, db
from datetime import datetime
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.role in ['admin', 'supervisor']:
            return jsonify({'error': 'Недостаточно прав'}), 403
        return f(*args, **kwargs)
    return decorated_function

def supervisor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'supervisor':
            return jsonify({'error': 'Недостаточно прав'}), 403
        return f(*args, **kwargs)
    return decorated_function

# API для номеров
@main.route('/api/rooms', methods=['GET'])
@login_required
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{
        'id': room.id,
        'room_number': room.room_number,
        'room_type': room.room_type,
        'category': room.category,
        'price': room.price,
        'status': room.status
    } for room in rooms])

@main.route('/api/rooms', methods=['POST'])
@login_required
@admin_required
def create_room():
    data = request.get_json()
    
    # Проверяем, не существует ли уже номер с таким номером
    existing_room = Room.query.filter_by(room_number=data['room_number']).first()
    if existing_room:
        return jsonify({'error': 'Номер с таким номером уже существует'}), 400
    
    room = Room(
        room_number=data['room_number'],
        room_type=data['room_type'],
        category=data['category'],
        price=data['price'],
        status='available'
    )
    
    db.session.add(room)
    try:
        db.session.commit()
        return jsonify({'message': 'Номер успешно создан'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/api/rooms/<int:id>', methods=['GET'])
@login_required
def get_room(id):
    room = Room.query.get_or_404(id)
    return jsonify({
        'id': room.id,
        'room_number': room.room_number,
        'room_type': room.room_type,
        'category': room.category,
        'price': room.price
    })

@main.route('/api/rooms/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_room(id):
    try:
        data = request.json
        room = Room.query.get_or_404(id)

        # Проверка уникальности номера комнаты
        if Room.query.filter(Room.room_number == data['room_number'], Room.id != id).first():
            return jsonify({'error': 'Номер с таким номером уже существует'}), 400

        room.room_number = data['room_number']
        room.room_type = data['room_type']
        room.category = data['category']
        room.price = data['price']

        db.session.commit()
        return jsonify({'message': 'Номер обновлен успешно'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/api/rooms/<int:id>', methods=['DELETE'])
@login_required
@supervisor_required
def delete_room(id):
    room = Room.query.get_or_404(id)
    
    # Проверяем, нет ли активных бронирований
    active_bookings = Booking.query.filter(
        Booking.room_id == id,
        Booking.status.in_(['pending', 'confirmed'])
    ).first()
    
    if active_bookings:
        return jsonify({'error': 'Невозможно удалить номер с активными бронированиями'}), 400
    
    db.session.delete(room)
    try:
        db.session.commit()
        return jsonify({'message': 'Номер успешно удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# API для клиентов
@main.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    clients = Client.query.all()
    return jsonify([{
        'id': client.id,
        'first_name': client.first_name,
        'last_name': client.last_name,
        'email': client.email,
        'phone': client.phone,
        'passport_number': client.passport_number,
        'bookings_count': client.bookings.count()
    } for client in clients])

@main.route('/api/clients', methods=['POST'])
@login_required
@admin_required
def create_client():
    data = request.get_json()
    
    # Проверяем, не существует ли клиент с таким email или паспортом
    existing_client = Client.query.filter(
        (Client.email == data['email']) |
        (Client.passport_number == data['passport_number'])
    ).first()
    
    if existing_client:
        return jsonify({'error': 'Клиент с таким email или паспортом уже существует'}), 400
    
    client = Client(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        passport_number=data['passport_number']
    )
    
    db.session.add(client)
    try:
        db.session.commit()
        return jsonify({'message': 'Клиент успешно создан'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/api/clients/<int:id>', methods=['GET'])
@login_required
def get_client(id):
    client = Client.query.get_or_404(id)
    return jsonify({
        'id': client.id,
        'first_name': client.first_name,
        'last_name': client.last_name,
        'email': client.email,
        'phone': client.phone,
        'passport_number': client.passport_number
    })

@main.route('/api/clients/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_client(id):
    client = Client.query.get_or_404(id)
    data = request.get_json()
    
    if 'email' in data:
        # Проверяем уникальность email
        existing_client = Client.query.filter(
            Client.email == data['email'],
            Client.id != id
        ).first()
        if existing_client:
            return jsonify({'error': 'Клиент с таким email уже существует'}), 400
        client.email = data['email']
    
    if 'passport_number' in data:
        # Проверяем уникальность паспорта
        existing_client = Client.query.filter(
            Client.passport_number == data['passport_number'],
            Client.id != id
        ).first()
        if existing_client:
            return jsonify({'error': 'Клиент с таким паспортом уже существует'}), 400
        client.passport_number = data['passport_number']
    
    if 'first_name' in data:
        client.first_name = data['first_name']
    if 'last_name' in data:
        client.last_name = data['last_name']
    if 'phone' in data:
        client.phone = data['phone']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Данные клиента успешно обновлены'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

