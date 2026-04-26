from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Конфигурация
SYNAPSE_URL = os.getenv("SYNAPSE_URL", "http://synapse:8008")
MATRIX_SERVER_NAME = os.getenv("MATRIX_SERVER_NAME", "localhost")

@app.route('/')
def index():
    return render_template('register.html', server_name=MATRIX_SERVER_NAME)

@app.route('/api/register', methods=['POST'])
def register():
    """
    Регистрация пользователя через Matrix Client API с использованием registration_token.
    Коды создаются в synapse-admin (Awesometechnologies).
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')
    registration_token = data.get('token')

    if not all([username, password, registration_token]):
        return jsonify({"error": "Все поля обязательны: username, password, token"}), 400

    try:
        # Шаг 1: Начинаем регистрацию, чтобы получить session_id (если требуется)
        # Отправляем пустой запрос для получения flows и session_id
        start_resp = requests.post(f"{SYNAPSE_URL}/_matrix/client/v3/register", json={})
        
        session_id = None
        if start_resp.status_code == 401:
            session_id = start_resp.json().get("session")
        
        # Шаг 2: Формируем payload для регистрации
        payload = {
            "username": username,
            "password": password,
            "registration_token": registration_token,
            "kind": "user",
            "inhibit_login": False
        }
        
        if session_id:
            payload["session"] = session_id

        # Шаг 3: Отправляем запрос на регистрацию
        resp = requests.post(f"{SYNAPSE_URL}/_matrix/client/v3/register", json=payload)
        
        if resp.status_code == 200:
            return jsonify({"success": True, "message": "Регистрация успешна!"})
        elif resp.status_code == 401:
            err_data = resp.json()
            errcode = err_data.get("errcode", "M_UNKNOWN")
            
            if errcode == "M_INVALID_TOKEN":
                return jsonify({"error": "Неверный или истекший регистрационный код"}), 403
            elif errcode == "M_USER_IN_USE":
                return jsonify({"error": "Пользователь с таким именем уже существует"}), 409
            else:
                return jsonify({"error": f"Ошибка регистрации: {errcode}"}), 400
        else:
            err_data = resp.json() if resp.text else {}
            errcode = err_data.get("errcode", "M_UNKNOWN")
            return jsonify({"error": f"Ошибка сервера: {errcode}"}), resp.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Нет соединения с сервером Matrix"}), 503
    except Exception as e:
        return jsonify({"error": f"Внутренняя ошибка: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
