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

# --- Firebase Configuration ---
SERVICE_ACCOUNT_KEY_PATH = "firebase_key.json"
DATABASE_URL = 'https://receipt-generator-95b80-default-rtdb.asia-southeast1.firebasedatabase.app/'
ADMIN_PASSWORD = "admin123" # Change this to a more secure password

def initialize_firebase():
    try:
        if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            print(f"Firebase key not found at {SERVICE_ACCOUNT_KEY_PATH}")
            return False
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        return True
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        return False

firebase_initialized = initialize_firebase()

# --- Font Registration ---

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

# --- Font Registration ---
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_PATH))
except Exception as e:
    print(f"Warning: Could not register font. Error: {e}")
    print("PDF generation might fail or use a default font.")

# --- User Authentication ---
USERS = {
    'mousui': 'pass1',
    'prabal': 'pass2',
    'rahul': 'pass3'
}

# --- Helper Functions ---
def get_next_receipt_number():
    """Gets the next receipt number from a local file."""
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
    except (IOError, ValueError) as e:
        print(f"Error with receipt counter file: {e}")
        # Fallback in case of file issues
        return "ERR"

def save_receipt_to_firebase(data):
    """Saves a receipt dictionary to Firebase using receipt_no as the key."""
    if not firebase_initialized:
        print("Firebase not initialized. Skipping save.")
        return
    try:
        ref = db.reference('receipts')
        # Use the receipt number as the key for the new entry
        ref.child(data['receipt_no']).set(data)
        print(f"Successfully saved receipt {data['receipt_no']} to Firebase.")
    except Exception as e:
        print(f"Error saving to Firebase: {e}")

def create_receipt_pdf(receipt_no, name, amount, mode, cheque_details, purpose, issued_by):
    """Creates the receipt PDF."""
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")
    time_str = now.strftime("%I:%M %p")

    name = name.strip()[:100] if name else "Anonymous"
    try:
        amount_num = int(float(amount))
        if amount_num <= 0:
            raise ValueError
        amount_words = num2words(amount_num, lang='en_IN').title() + " Rupees Only"
        amount_display = f"₹ {amount_num:,}"
    except (ValueError, TypeError):
        amount_words = "Invalid Amount"
        amount_display = "₹ 0"
        amount_num = 0

    mode = mode.strip()[:50] or "Cash"
    cheque_details = cheque_details.strip()[:200] or ""
    purpose = purpose.strip()[:50] or "Donation"

    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    pdf_path = os.path.join(RECEIPTS_DIR, f"receipt_{receipt_no}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4

    # --- PDF Styling ---
    primary_color = colors.HexColor('#d95f02')
    secondary_color = colors.HexColor('#7570b3')
    text_color = colors.HexColor('#333333')
    light_bg_color = colors.HexColor('#f7f7f7')
    white_color = colors.white

    # --- PDF Content ---
    # Border
    c.setStrokeColor(primary_color)
    c.setLineWidth(5)
    c.rect(15, 15, w - 30, h - 30, stroke=1, fill=0)

    # Header
    c.setFillColor(primary_color)
    c.rect(20, h - 115, w - 40, 95, stroke=0, fill=1)
    c.setFillColor(white_color)
    c.setFont("DejaVuSans-Bold", 24)
    c.drawCentredString(w / 2, h - 55, "NASHIK BANGIYA PARISHAD")
    c.setFont("DejaVuSans-Bold", 11)
    c.drawCentredString(w / 2, h - 75, "Flat No.203, Sakhar Symphony, Damodar Chowk, Opposite GST Bhavan,")
    c.drawCentredString(w / 2, h - 90, "Pathardi Phata, Nashik-422010.")
    c.drawCentredString(w / 2, h - 105, "Reg. No.F-13, 873 NSK")

    # Metadata
    c.setFont("DejaVuSans-Bold", 14)
    c.setFillColor(text_color)
    c.drawString(40, h - 130, f"Receipt No: {receipt_no}")
    c.drawRightString(w - 40, h - 130, f"Date: {date_str} {time_str}")

    # Watermark
    c.saveState()
    try:
        if os.path.exists(LOGO_PATH):
            img = ImageReader(LOGO_PATH)
            img_w, img_h = img.getSize()
            aspect = img_h / float(img_w)
            watermark_width = 400
            watermark_height = watermark_width * aspect
            x = (w - watermark_width) / 2
            y = (h - watermark_height) / 2
            c.setFillAlpha(0.05)
            c.drawImage(LOGO_PATH, x, y, width=watermark_width, height=watermark_height, mask='auto')
    except Exception as e:
        print(f"Could not draw watermark: {e}")
    finally:
        c.restoreState()

    # Body
    y_pos = h - 200
    left_margin, right_margin = 50, w - 50

    c.setFont("DejaVuSans-Bold", 12)
    c.drawString(left_margin, y_pos, "Received with thanks from")
    c.setFont("DejaVuSans-Bold", 26)
    c.drawString(left_margin, y_pos - 35, name)

    # Amount Box
    amount_box_x = right_margin - 200
    amount_box_y = y_pos - 15
    c.setFillColor(light_bg_color)
    c.roundRect(amount_box_x, amount_box_y, 200, 60, 10, fill=1, stroke=0)
    c.setStrokeColor(secondary_color)
    c.setLineWidth(2)
    c.roundRect(amount_box_x, amount_box_y, 200, 60, 10, fill=0, stroke=1)
    c.setFont("DejaVuSans-Bold", 14)
    c.setFillColor(text_color)
    c.drawCentredString(amount_box_x + 100, amount_box_y + 40, "AMOUNT")
    c.setFont("DejaVuSans-Bold", 28)
    c.setFillColor(secondary_color)
    c.drawCentredString(amount_box_x + 100, amount_box_y + 12, amount_display)

    y_pos -= 80
    c.setFont("DejaVuSans-Bold", 12)
    c.drawString(left_margin, y_pos, "The sum of Rupees")

    # Amount in words (with wrapping)
    text_obj = c.beginText(left_margin, y_pos - 25)
    text_obj.setFont("DejaVuSans-Bold", 16)
    max_width = (amount_box_x - left_margin - 10)
    line = ""
    for word in amount_words.split():
        if c.stringWidth(line + word + ' ', "DejaVuSans-Bold", 16) < max_width:
            line += word + ' '
        else:
            text_obj.textLine(line.strip())
            line = word + ' '
    text_obj.textLine(line.strip())
    c.drawText(text_obj)

    # Payment Details
    y_pos -= 90
    c.setFont("DejaVuSans-Bold", 12)
    c.setFillColor(text_color)
    c.drawString(left_margin, y_pos, "Payment Details")
    c.setFont("DejaVuSans-Bold", 14)
    c.drawString(left_margin, y_pos - 25, f"Mode: {mode}")
    if cheque_details:
        c.setFont("DejaVuSans-Bold", 12)
        c.drawString(left_margin, y_pos - 45, f"Details: {cheque_details}")
    c.setFont("DejaVuSans-Bold", 14)
    c.drawRightString(right_margin, y_pos - 25, f"For: {purpose}")

    # Signatures
    sig_y = 150
    sig_w = 150
    spacing = (w - 2 * left_margin - 3 * sig_w) / 2
    for i, role in enumerate(["PRESIDENT", "TREASURER", "ISSUED BY"]):
        x = left_margin + i * (sig_w + spacing)
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(1)
        c.line(x, sig_y, x + sig_w, sig_y)
        c.setFont("DejaVuSans-Bold", 10)
        c.setFillColor(text_color)
        if role == "ISSUED BY":
            c.setFont("DejaVuSans-Bold", 12)
            c.drawCentredString(x + sig_w / 2, sig_y + 15, issued_by.upper())
            c.setFont("DejaVuSans-Bold", 10)
            c.drawCentredString(x + sig_w / 2, sig_y - 10, role)
        else:
            c.drawCentredString(x + sig_w / 2, sig_y - 15, role)

    # Footer
    c.setStrokeColor(primary_color)
    c.setLineWidth(2)
    c.line(left_margin, 80, right_margin, 80)
    c.setFont("DejaVuSans-Bold", 10)
    c.setFillColor(text_color)
    c.drawCentredString(w / 2, 60, "This is a computer-generated receipt and does not require a signature.")
    
    c.save()
    return pdf_path

# --- Routes ---
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
        # Collect form data
        name = request.form.get('name', '').strip()
        amount = request.form.get('amount', '').strip()
        mode = request.form.get('mode', '').strip()
        cheque_details = request.form.get('cheque_details', '').strip()
        purpose = request.form.get('purpose', '').strip()
        issued_by = session.get('username', 'Admin')

        # Basic Validation
        if not name:
            error = "Name is required."
        elif not amount or not re.match(r'^\d+(\.\d+)?$', amount) or float(amount) <= 0:
            error = "Amount must be a positive number."
        elif not mode:
            error = "Payment mode is required."
        elif mode.lower() in ['cheque', 'online'] and not cheque_details:
            error = "Cheque/Transaction details are required for this payment mode."
        elif not purpose:
            error = "Purpose is required."
        
        if not error:
            try:
                receipt_no = get_next_receipt_number()
                if receipt_no == "ERR":
                    error = "Could not generate receipt number. Check file permissions."
                else:
                    # Prepare data for Firebase and PDF
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
                    
                    # Save to Firebase first
                    save_receipt_to_firebase(receipt_data)

                    # Then, generate the PDF
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
                print(f"Error during PDF generation: {e}")
                error = f"An error occurred while generating the PDF: {e}"

    return render_template('index.html', error=error)

@app.route('/view_data', methods=['POST'])
def view_data():
    admin_password = request.form.get('admin_password')
    if admin_password != ADMIN_PASSWORD:
        return render_template('login.html', error="Invalid Admin Password.")

    if not firebase_initialized:
        return render_template('view_data.html', error="Firebase is not initialized. Check server logs.")

    try:
        ref = db.reference('receipts')
        data = ref.get()

        if not data:
            return render_template('view_data.html', error="No data found in Firebase.")

        # Handle both list and dict data structures from Firebase
        if isinstance(data, list):
            # Filter out any potential null/empty entries from Firebase arrays
            data = [item for item in data if item]
        elif isinstance(data, dict):
            data = [value for value in data.values() if value]

        return render_template('view_data.html', data=data)
    except Exception as e:
        return render_template('view_data.html', error=f"An error occurred: {e}")

if __name__ == '__main__':
    app.run(debug=True)