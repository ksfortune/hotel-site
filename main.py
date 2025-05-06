import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, send_file, url_for, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash  
from flask_session import Session  
import os
from datetime import datetime, timedelta
import csv
import io


app = Flask(__name__)

# Настройки сессий
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'hotel.db')

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  
    return db

def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            schema_path = os.path.join(BASE_DIR, 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                db.cursor().executescript(f.read())
            db.commit()
    else:
        
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Reviews'")
            if cursor.fetchone() is None:
                cursor.execute('''
                    CREATE TABLE Reviews (
                        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        name TEXT NOT NULL,
                        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                        comment TEXT NOT NULL,
                        date_posted DATE DEFAULT CURRENT_DATE,
                        FOREIGN KEY (user_id) REFERENCES Users(user_id)
                    )
                ''')
            db.commit()
init_db()

# Главная страница
@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('index.html', logged_in=True)
    return render_template('index.html', logged_in=False)

# Страница бронирования
@app.route('/booking')
def booking():
    return render_template('booking.html')


@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """Возвращает список номеров с их комфортностью для выпадающего списка."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT room_number, comfort_level, price FROM Rooms")

        rooms = [
            {
                "room_number": row[0],
                "comfort_level": row[1],
                "price": float(row[2])
            }
            for row in cursor.fetchall()
        ]
        
        return jsonify(rooms)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


# Страница номеров
@app.route('/rooms', methods=['GET'])
def rooms():
    """Загружает список номеров из базы и передаёт в шаблон rooms.html."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        comfort_level = request.args.get('comfort_level')

        if comfort_level:
            cursor.execute("""
                SELECT room_number, capacity, comfort_level, price, image_url 
                FROM Rooms 
                WHERE comfort_level = ?
            """, (comfort_level,))
        else:
            cursor.execute("""
                SELECT room_number, capacity, comfort_level, price, image_url 
                FROM Rooms
            """)

        rooms = [
            {
                "room_number": row[0],
                "capacity": row[1],
                "comfort_level": row[2],
                "price": float(row[3]),
                "image_url": row[4]
            }
            for row in cursor.fetchall()
        ]

        return render_template('rooms.html', rooms=rooms)
    except Exception as e:
        return f"Ошибка при загрузке данных: {e}", 500
    finally:
        if 'conn' in locals():
            conn.close()
