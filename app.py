from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import requests
import secrets
import hashlib
import json
import os
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Конфигурация
SYNAPSE_ADMIN_URL = os.getenv('SYNAPSE_ADMIN_URL', 'http://localhost:8008')
SYNAPSE_ADMIN_ACCESS_TOKEN = os.getenv('SYNAPSE_ADMIN_ACCESS_TOKEN', '')
SERVER_NAME = os.getenv('MATRIX_SERVER_NAME', 'example.com')

# База данных для кодов регистрации
DB_PATH = 'registration_codes.db'

def init_db():
    """Инициализация базы данных для хранения кодов регистрации"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registration_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            max_uses INTEGER DEFAULT 1,
            current_uses INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_by TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            username TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_registration_code(length=16):
    """Генерация случайного кода регистрации"""
    return secrets.token_urlsafe(length)

def register_user_on_synapse(username, password, access_token):
    """Регистрация пользователя в Synapse через Admin API"""
    url = f"{SYNAPSE_ADMIN_URL}/_synapse/admin/v1/register"
    
    # Сначала получаем nonce
    response = requests.get(url)
    if response.status_code != 200:
        return False, "Не удалось получить nonce от сервера"
    
    data = response.json()
    nonce = data.get('nonce')
    
    # Вычисляем хеш
    mac = hashlib.sha256()
    mac.update(nonce.encode())
    mac.update(b"\x00")
    mac.update(username.encode())
    mac.update(b"\x00")
    mac.update(password.encode())
    mac.update(b"\x00")
    mac.update(b"admin")  # kind=admin для регистрации через админку
    
    hex_mac = mac.hexdigest()
    
    # Отправляем запрос на регистрацию
    payload = {
        "nonce": nonce,
        "username": username,
        "password": password,
        "kind": "user",
        "mac": hex_mac,
        "admin": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.text

@app.route('/')
def index():
    """Главная страница - форма регистрации"""
    return render_template('register.html')

@app.route('/admin')
def admin_panel():
    """Панель администратора"""
    return render_template('admin.html')

@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    """Генерация нового кода регистрации"""
    data = request.json
    max_uses = data.get('max_uses', 1)
    expires_in_hours = data.get('expires_in_hours', 24)
    created_by = data.get('created_by', 'admin')
    
    code = generate_registration_code()
    expires_at = datetime.now() + timedelta(hours=expires_in_hours)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO registration_codes 
            (code, expires_at, max_uses, created_by)
            VALUES (?, ?, ?, ?)
        ''', (code, expires_at, max_uses, created_by))
        conn.commit()
        
        return jsonify({
            'success': True,
            'code': code,
            'expires_at': expires_at.isoformat(),
            'max_uses': max_uses
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/validate-code', methods=['POST'])
def validate_code():
    """Проверка кода регистрации"""
    data = request.json
    code = data.get('code')
    
    if not code:
        return jsonify({'valid': False, 'error': 'Код не предоставлен'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM registration_codes 
        WHERE code = ? AND is_active = 1
    ''', (code,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'valid': False, 'error': 'Недействительный код'})
    
    # Проверка срока действия
    if row['expires_at']:
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            return jsonify({'valid': False, 'error': 'Срок действия кода истёк'})
    
    # Проверка количества использований
    if row['current_uses'] >= row['max_uses']:
        return jsonify({'valid': False, 'error': 'Код достиг лимита использований'})
    
    return jsonify({'valid': True})

@app.route('/api/register', methods=['POST'])
def register():
    """Регистрация пользователя с использованием кода"""
    data = request.json
    code = data.get('code')
    username = data.get('username')
    password = data.get('password')
    
    if not all([code, username, password]):
        return jsonify({'success': False, 'error': 'Все поля обязательны'}), 400
    
    # Проверяем код
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM registration_codes 
        WHERE code = ? AND is_active = 1
    ''', (code,))
    
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Недействительный код'}), 400
    
    # Проверка срока действия
    if row['expires_at']:
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            conn.close()
            return jsonify({'success': False, 'error': 'Срок действия кода истёк'}), 400
    
    # Проверка количества использований
    if row['current_uses'] >= row['max_uses']:
        conn.close()
        return jsonify({'success': False, 'error': 'Код достиг лимита использований'}), 400
    
    # Регистрируем пользователя в Synapse
    success, result = register_user_on_synapse(username, password, SYNAPSE_ADMIN_ACCESS_TOKEN)
    
    if success:
        # Увеличиваем счётчик использований
        cursor.execute('''
            UPDATE registration_codes 
            SET current_uses = current_uses + 1 
            WHERE code = ?
        ''', (code,))
        conn.commit()
        
        # Логируем успешную регистрацию
        cursor.execute('''
            INSERT INTO registration_logs (code, username, success)
            VALUES (?, ?, 1)
        ''', (code, username))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Регистрация успешна',
            'user_id': f'@{username}:{SERVER_NAME}'
        })
    else:
        # Логируем неудачную попытку
        cursor.execute('''
            INSERT INTO registration_logs (code, username, success)
            VALUES (?, ?, 0)
        ''', (code, username))
        conn.commit()
        
        return jsonify({'success': False, 'error': result}), 400
    finally:
        conn.close()

@app.route('/api/codes', methods=['GET'])
def get_codes():
    """Получение списка всех кодов (для админки)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM registration_codes 
        ORDER BY created_at DESC
    ''')
    
    codes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'codes': codes})

@app.route('/api/deactivate-code/<int:code_id>', methods=['POST'])
def deactivate_code(code_id):
    """Деактивация кода"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE registration_codes 
        SET is_active = 0 
        WHERE id = ?
    ''', (code_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Получение логов регистрации"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM registration_logs 
        ORDER BY registered_at DESC
        LIMIT 100
    ''')
    
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'logs': logs})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
