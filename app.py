from flask import Flask, request, send_file
from flask_cors import CORS
import qrcode
from io import BytesIO
from PIL import Image
import sqlite3

app = Flask(__name__)
CORS(app)

def create_table():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        qr_code BLOB
        )
    ''')
    conn.commit()
    conn.close()

def save_data(full_name, email, phone, qr_code_data):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    # Check if user with same email exists
    existing_user_email = cursor.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing_user_email:
        cursor.execute("DELETE FROM users WHERE email=?", (email,))
        conn.commit()

    # Check if user with same phone exists
    existing_user_phone = cursor.execute("SELECT id FROM users WHERE phone=?", (phone,)).fetchone()
    if existing_user_phone:
        cursor.execute("DELETE FROM users WHERE phone=?", (phone,))
        conn.commit()

    cursor.execute('''
        INSERT INTO users (full_name, email, phone, qr_code)
        VALUES (?, ?, ?, ?)
    ''', (full_name, email, phone, qr_code_data))
    conn.commit()
    conn.close()


@app.route('/verify_qr', methods=['POST'])
def verify_qr_code():
    try:
        data = request.get_json()
        scanned_data = data.get('scanned_data')  # Get the scanned QR code data

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        query = "SELECT id FROM users WHERE qr_code = ?"
        params = (scanned_data,)

        user_id = cursor.execute(query, params).fetchone()
        conn.close()

        if user_id:
            return "QR code verified."
        else:
            return "QR code not found.", 404

    except Exception as e:
        return "Error verifying QR code: " + str(e), 500




@app.route('/get_qr', methods=['GET'])
def get_qr_code():
    try:
        email = request.args.get('email')
        phone = request.args.get('phone')

        if email:
            query = "SELECT qr_code FROM users WHERE email = ?"
            params = (email,)
        elif phone:
            query = "SELECT qr_code FROM users WHERE phone = ?"
            params = (phone,)
        else:
            return "Invalid request parameters", 400

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        qr_code_data = cursor.execute(query, params).fetchone()
        conn.close()

        if qr_code_data:
            response = BytesIO(qr_code_data[0])
            return send_file(response, mimetype="image/png")
        else:
            return "User not found", 404

    except Exception as e:
        return "Error retrieving QR code: " + str(e), 500


@app.route('/generate_qr', methods=['POST'])
def generate_qr_code():
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')

        user_data = f"Name: {full_name}\nEmail: {email}\nPhone: {phone}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(user_data)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")

        image_stream = BytesIO()
        qr_image.save(image_stream, format="PNG")
        image_stream.seek(0)

        try:
            create_table()
            save_data(full_name, email, phone, image_stream.read())
        except Exception as e:
            print("Error saving data to the database:", e)
        

        if email:
            query = "SELECT qr_code FROM users WHERE email = ?"
            params = (email,)
        elif phone:
            query = "SELECT qr_code FROM users WHERE phone = ?"
            params = (phone,)
        else:
            return "Invalid request parameters", 400

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        qr_code_data = cursor.execute(query, params).fetchone()
        conn.close()


        if qr_code_data:
            response = BytesIO(qr_code_data[0])
            return send_file(response, mimetype="image/png")
        else:
            return "User not found", 404

    except Exception as e:
        return "Error generating QR code: " + str(e), 500

if __name__ == '__main__':
    app.run()



