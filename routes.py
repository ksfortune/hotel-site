from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import main
from ..models import Room, Client, Booking, db
from datetime import datetime
from functools import wraps

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.role in roles:
                flash('У вас нет прав для доступа к этой странице.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@main.route('/')
@login_required
def index():
    rooms = Room.query.all()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    return render_template('main/index.html', rooms=rooms, recent_bookings=recent_bookings)

@main.route('/rooms')
@login_required
def rooms():
    rooms = Room.query.all()
    return render_template('main/rooms.html', rooms=rooms)

@main.route('/room/<int:id>')
@login_required
def room_detail(id):
    room = Room.query.get_or_404(id)
    return render_template('main/room_detail.html', room=room)

@main.route('/clients')
@login_required
def clients():
    clients = Client.query.all()
    return render_template('main/clients.html', clients=clients)

@main.route('/bookings')
@login_required
def bookings():
    if current_user.role == 'manager':
        bookings = Booking.query.filter_by(created_by=current_user.id).all()
    else:
        bookings = Booking.query.all()
    return render_template('main/bookings.html', bookings=bookings)

@main.route('/hotel')
def hotel():
    return render_template('main/hotel.html')

@main.route('/reports')
@login_required
@role_required('supervisor', 'admin')
def reports():
    return render_template('main/reports.html')
