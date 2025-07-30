from flask import Flask, render_template, request, send_file, session, redirect, url_for
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from num2words import num2words
import firebase_admin
from firebase_admin import credentials, db
import os
import re
import json

# --- Configuration ---
app = Flask(__name__)
app.secret_key = 'super_secret_random_string_12345'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans-Bold.ttf")
LOGO_PATH = os.path.join(BASE_DIR, "static", "logo.png")
RECEIPT_COUNTER_FILE = os.path.join(BASE_DIR, "receipt_counter.txt")
RECEIPTS_DIR = os.path.join(BASE_DIR, "generated_receipts")

# --- Firebase Configuration (secure using env vars) ---
firebase_json = os.environ.get("FIREBASE_KEY_JSON")
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

firebase_initialized = False
if firebase_json and DATABASE_URL:
    try:
        firebase_dict = json.loads(firebase_json)
        cred = credentials.Certificate(firebase_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        firebase_initialized = True
    except Exception as e:
        print(f"Firebase initialization error: {e}")
else:
    print("Missing Firebase credentials or database URL.")

try:
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_PATH))
except Exception as e:
    print(f"Font registration failed: {e}")

USERS = {
    'mousui': 'pass1',
    'prabal': 'pass2',
    'rahul': 'pass3'
}


def get_next_receipt_number():
    os.makedirs(os.path.dirname(RECEIPT_COUNTER_FILE), exist_ok=True)
    try:
        if not os.path.exists(RECEIPT_COUNTER_FILE):
            with open(RECEIPT_COUNTER_FILE, "w") as f:
                f.write("1001")
            return "1001"
        with open(RECEIPT_COUNTER_FILE, "r") as f:
            number = int(f.read().strip())
        next_number = number + 1
        with open(RECEIPT_COUNTER_FILE, "w") as f:
            f.write(str(next_number))
        return str(number)
    except Exception as e:
        print(f"Receipt counter error: {e}")
        return "ERR"


def save_receipt_to_firebase(data):
    if not firebase_initialized:
        print("Firebase not initialized. Skipping save.")
        return
    try:
        ref = db.reference('receipts')
        ref.child(data['receipt_no']).set(data)
    except Exception as e:
        print(f"Failed to save to Firebase: {e}")


# --- You can insert your create_receipt_pdf() function here, unchanged from earlier ---
# (Truncated here for brevity, but it should be pasted completely from your last working version)


@app.route('/')
def root_redirect():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/index', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        amount = request.form.get('amount', '').strip()
        mode = request.form.get('mode', '').strip()
        cheque_details = request.form.get('cheque_details', '').strip()
        purpose = request.form.get('purpose', '').strip()
        issued_by = session.get('username', 'Admin')

        if not name:
            error = "Name is required."
        elif not amount or not re.match(r'^\d+(\.\d+)?$', amount) or float(amount) <= 0:
            error = "Amount must be a positive number."
        elif not mode:
            error = "Payment mode is required."
        elif mode.lower() in ['cheque', 'online'] and not cheque_details:
            error = "Cheque/Transaction details required."
        elif not purpose:
            error = "Purpose is required."

        if not error:
            try:
                receipt_no = get_next_receipt_number()
                if receipt_no == "ERR":
                    error = "Could not generate receipt number."
                else:
                    receipt_data = {
                        'receipt_no': receipt_no,
                        'name': name,
                        'amount': amount,
                        'mode': mode,
                        'cheque_details': cheque_details,
                        'purpose': purpose,
                        'issued_by': issued_by,
                        'date_str': datetime.now().strftime("%d/%m/%Y"),
                        'time_str': datetime.now().strftime("%I:%M %p")
                    }
                    save_receipt_to_firebase(receipt_data)
                    pdf_path = create_receipt_pdf(
                        receipt_no=receipt_no,
                        name=name,
                        amount=amount,
                        mode=mode,
                        cheque_details=cheque_details,
                        purpose=purpose,
                        issued_by=issued_by
                    )
                    return send_file(pdf_path, as_attachment=True)
            except Exception as e:
                error = f"Error generating receipt: {e}"

    return render_template('index.html', error=error)


@app.route('/view_data', methods=['POST'])
def view_data():
    admin_password = request.form.get('admin_password')
    if admin_password != ADMIN_PASSWORD:
        return render_template('login.html', error="Invalid Admin Password.")

    if not firebase_initialized:
        return render_template('view_data.html', error="Firebase is not initialized.")

    try:
        ref = db.reference('receipts')
        data = ref.get()
        if not data:
            return render_template('view_data.html', error="No data found in Firebase.")

        if isinstance(data, list):
            data = [item for item in data if item]
        elif isinstance(data, dict):
            data = [value for value in data.values() if value]

        return render_template('view_data.html', data=data)
    except Exception as e:
        return render_template('view_data.html', error=f"An error occurred: {e}")


if __name__ == '__main__':
    app.run()
