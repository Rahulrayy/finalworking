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
import os
import re
import firebase_admin
from firebase_admin import credentials, db
import json

app = Flask(__name__)
app.secret_key = 'super_secret_random_string_12345'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans-Bold.ttf")
LOGO_PATH = os.path.join(BASE_DIR, "static", "logo.png")
RECEIPT_COUNTER_FILE = os.path.join(BASE_DIR, "receipt_counter.txt")
RECEIPTS_DIR = os.path.join(BASE_DIR, "generated_receipts")

# --- Firebase Config ---
DATABASE_URL = 'https://receipt-generator-95b80-default-rtdb.asia-southeast1.firebasedatabase.app/'

def initialize_firebase():
    try:
        firebase_json = os.environ.get("FIREBASE_KEY_JSON")
        if not firebase_json:
            print("FIREBASE_KEY_JSON not set in environment")
            return False
        firebase_dict = json.loads(firebase_json)
        cred = credentials.Certificate(firebase_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        return True
    except Exception as e:
        print(f"Firebase init error: {e}")
        return False

firebase_initialized = initialize_firebase()

# --- Fonts ---
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_PATH))
except Exception as e:
    print(f"Font error: {e}")

# --- Auth Users ---
USERS = {
    'mousui': 'pass1',
    'prabal': 'pass2',
    'rahul': 'pass3'
}
ADMIN_PASSWORD = "admin123"

# --- Receipt Number ---
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
    except:
        return "ERR"

# --- Firebase Save ---
def save_receipt_to_firebase(data):
    if not firebase_initialized:
        return
    try:
        ref = db.reference('receipts')
        ref.child(data['receipt_no']).set(data)
    except Exception as e:
        print(f"Firebase save error: {e}")

# --- PDF Generator ---
def create_receipt_pdf(receipt_no, name, amount, mode, cheque_details, purpose, issued_by):
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")

    name = name.strip()[:100] or "Anonymous"
    try:
        amount_num = int(float(amount))
        amount_words = num2words(amount_num, lang='en_IN').title() + " Rupees Only"
        amount_display = f"₹ {amount_num:,}"
    except:
        amount_words = "Invalid Amount"
        amount_display = "₹ 0"

    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    pdf_path = os.path.join(RECEIPTS_DIR, f"receipt_{receipt_no}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4

    # Border
    c.setStrokeColor(colors.HexColor('#d95f02'))
    c.setLineWidth(5)
    c.rect(15, 15, w - 30, h - 30)

    # Header
    c.setFillColor(colors.HexColor('#d95f02'))
    c.rect(20, h - 115, w - 40, 95, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("DejaVuSans-Bold", 24)
    c.drawCentredString(w / 2, h - 55, "NASHIK BANGIYA PARISHAD")
    c.setFont("DejaVuSans-Bold", 11)
    c.drawCentredString(w / 2, h - 90, "Pathardi Phata, Nashik-422010.")

    # Metadata
    c.setFont("DejaVuSans-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(40, h - 130, f"Receipt No: {receipt_no}")
    c.drawRightString(w - 40, h - 130, f"Date: {date_str}")

    # Watermark
    try:
        if os.path.exists(LOGO_PATH):
            img = ImageReader(LOGO_PATH)
            img_w, img_h = img.getSize()
            ratio = img_h / img_w
            width = 400
            height = width * ratio
            x = (w - width) / 2
            y = (h - height) / 2
            c.saveState()
            c.setFillAlpha(0.05)
            c.drawImage(LOGO_PATH, x, y, width=width, height=height, mask='auto')
            c.restoreState()
    except Exception as e:
        print(f"Watermark error: {e}")

    # Body
    c.setFont("DejaVuSans-Bold", 12)
    c.drawString(50, h - 200, f"Received from: {name}")
    c.drawString(50, h - 230, f"Amount: {amount_display}")
    c.drawString(50, h - 260, f"In Words: {amount_words}")
    c.drawString(50, h - 290, f"Payment Mode: {mode}")
    if cheque_details:
        c.drawString(50, h - 320, f"Details: {cheque_details}")
    c.drawString(50, h - 350, f"For Purpose: {purpose}")
    c.drawString(50, h - 380, f"Issued By: {issued_by}")

    # Footer
    c.setFont("DejaVuSans-Bold", 10)
    c.drawCentredString(w / 2, 60, "This is a computer-generated receipt.")

    c.save()
    return pdf_path

# --- Routes ---
@app.route('/')
def root():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect('/index')
    error = None
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if u in USERS and USERS[u] == p:
            session['logged_in'] = True
            session['username'] = u
            return redirect('/index')
        error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect('/login')
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        amount = request.form.get('amount', '').strip()
        mode = request.form.get('mode', '').strip()
        cheque = request.form.get('cheque_details', '').strip()
        purpose = request.form.get('purpose', '').strip()
        issued_by = session.get('username')

        if not name:
            error = "Name required."
        elif not amount or not re.match(r'^\d+(\.\d+)?$', amount):
            error = "Valid amount required."
        elif not mode:
            error = "Payment mode required."
        elif mode.lower() in ['cheque', 'online'] and not cheque:
            error = "Details required for cheque/online."

        if not error:
            receipt_no = get_next_receipt_number()
            if receipt_no == "ERR":
                error = "Counter issue"
            else:
                data = {
                    'receipt_no': receipt_no,
                    'name': name,
                    'amount': amount,
                    'mode': mode,
                    'cheque_details': cheque,
                    'purpose': purpose,
                    'issued_by': issued_by,
                    'date': datetime.now().strftime("%d/%m/%Y")
                }
                save_receipt_to_firebase(data)
                pdf = create_receipt_pdf(receipt_no, name, amount, mode, cheque, purpose, issued_by)
                return send_file(pdf, as_attachment=True)
    return render_template("index.html", error=error)

@app.route('/view_data', methods=['POST'])
def view_data():
    pwd = request.form.get("admin_password")
    if pwd != ADMIN_PASSWORD:
        return render_template("login.html", error="Wrong admin password.")
    if not firebase_initialized:
        return render_template("view_data.html", error="Firebase not initialized")
    try:
        ref = db.reference("receipts")
        data = ref.get()
        if not data:
            return render_template("view_data.html", error="No data found")
        if isinstance(data, dict):
            data = [v for v in data.values()]
        return render_template("view_data.html", data=data)
    except Exception as e:
        return render_template("view_data.html", error=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
