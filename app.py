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
    """Creates an enhanced, more attractive receipt PDF."""
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y")

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

    # --- Enhanced Color Palette ---
    primary_color = colors.HexColor('#2E86AB')      # Modern blue
    secondary_color = colors.HexColor('#A23B72')    # Deep magenta
    accent_color = colors.HexColor('#F18F01')       # Vibrant orange
    success_color = colors.HexColor('#C73E1D')      # Elegant red
    text_color = colors.HexColor('#2D3748')         # Dark gray
    light_text = colors.HexColor('#718096')         # Medium gray
    bg_gradient_start = colors.HexColor('#EDF2F7')  # Light gray
    bg_gradient_end = colors.HexColor('#F7FAFC')    # Very light gray
    white_color = colors.white

    # --- Enhanced Border with Gradient Effect ---
    # Outer border with shadow effect
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.setLineWidth(8)
    c.rect(12, 12, w - 24, h - 24, stroke=1, fill=0)
    
    # Main border with gradient-like layering
    c.setStrokeColor(primary_color)
    c.setLineWidth(3)
    c.rect(18, 18, w - 36, h - 36, stroke=1, fill=0)
    
    # Inner accent line
    c.setStrokeColor(accent_color)
    c.setLineWidth(1)
    c.rect(22, 22, w - 44, h - 44, stroke=1, fill=0)

    # --- Modern Header with Gradient Background ---
    # Header background with layered effect
    c.setFillColor(bg_gradient_start)
    c.rect(25, h - 130, w - 50, 105, stroke=0, fill=1)
    
    # Primary header section
    c.setFillColor(primary_color)
    c.roundRect(30, h - 125, w - 60, 95, 8, fill=1, stroke=0)
    
    # Accent stripe
    c.setFillColor(accent_color)
    c.rect(30, h - 125, w - 60, 12, stroke=0, fill=1)
    
    # Organization name with enhanced typography
    c.setFillColor(white_color)
    c.setFont("DejaVuSans-Bold", 26)
    c.drawCentredString(w / 2, h - 55, "NASHIK BANGIYA PARISHAD")
    
    # Address with better spacing
    c.setFont("DejaVuSans", 11)
    c.drawCentredString(w / 2, h - 78, "Flat No.203, Sakhar Symphony, Damodar Chowk")
    c.drawCentredString(w / 2, h - 93, "Opposite GST Bhavan, Pathardi Phata, Nashik-422010")
    
    # Registration with accent color
    c.setFillColor(accent_color)
    c.setFont("DejaVuSans-Bold", 10)
    c.drawCentredString(w / 2, h - 108, "● Reg. No.F-13, 873 NSK ●")

    # --- Enhanced Metadata Section ---
    # Receipt info box
    c.setFillColor(bg_gradient_start)
    c.roundRect(35, h - 160, w - 70, 25, 6, fill=1, stroke=0)
    c.setStrokeColor(primary_color)
    c.setLineWidth(1)
    c.roundRect(35, h - 160, w - 70, 25, 6, fill=0, stroke=1)
    
    c.setFont("DejaVuSans-Bold", 14)
    c.setFillColor(primary_color)
    c.drawString(45, h - 150, f"Receipt No: {receipt_no}")
    c.drawRightString(w - 45, h - 150, f"Date: {date_str}")

    # --- Subtle Watermark ---
    c.saveState()
    try:
        if os.path.exists(LOGO_PATH):
            img = ImageReader(LOGO_PATH)
            img_w, img_h = img.getSize()
            aspect = img_h / float(img_w)
            watermark_width = 300
            watermark_height = watermark_width * aspect
            x = (w - watermark_width) / 2
            y = (h - watermark_height) / 2 - 50
            c.setFillAlpha(0.03)
            c.drawImage(LOGO_PATH, x, y, width=watermark_width, height=watermark_height, mask='auto')
    except Exception as e:
        print(f"Could not draw watermark: {e}")
    finally:
        c.restoreState()

    # --- Enhanced Body Section ---
    y_pos = h - 220
    left_margin, right_margin = 60, w - 60

    # "Received with thanks" section with modern styling
    c.setFillColor(light_text)
    c.setFont("DejaVuSans", 14)
    c.drawString(left_margin, y_pos, "Received with thanks from")

    # Name with emphasis
    c.setFont("DejaVuSans-Bold", 28)
    c.setFillColor(text_color)
    c.drawString(left_margin, y_pos - 40, name)
    
    # Decorative underline
    name_width = c.stringWidth(name, "DejaVuSans-Bold", 28)
    c.setStrokeColor(accent_color)
    c.setLineWidth(3)
    c.line(left_margin, y_pos - 48, left_margin + name_width, y_pos - 48)

    # --- Redesigned Amount Box ---
    amount_box_x = right_margin - 220
    amount_box_y = y_pos - 25
    amount_box_w = 220
    amount_box_h = 80
    
    # Shadow effect
    c.setFillColor(colors.HexColor('#E2E8F0'))
    c.roundRect(amount_box_x + 3, amount_box_y - 3, amount_box_w, amount_box_h, 15, fill=1, stroke=0)
    
    # Main amount box with gradient effect
    c.setFillColor(white_color)
    c.roundRect(amount_box_x, amount_box_y, amount_box_w, amount_box_h, 15, fill=1, stroke=0)
    
    # Border with primary color
    c.setStrokeColor(primary_color)
    c.setLineWidth(2)
    c.roundRect(amount_box_x, amount_box_y, amount_box_w, amount_box_h, 15, fill=0, stroke=1)
    
    # Amount header with accent background
    c.setFillColor(accent_color)
    c.roundRect(amount_box_x + 10, amount_box_y + 50, amount_box_w - 20, 20, 8, fill=1, stroke=0)
    c.setFont("DejaVuSans-Bold", 12)
    c.setFillColor(white_color)
    c.drawCentredString(amount_box_x + amount_box_w/2, amount_box_y + 56, "AMOUNT")
    
    # Amount value with enhanced styling
    c.setFont("DejaVuSans-Bold", 24)
    c.setFillColor(success_color)
    c.drawCentredString(amount_box_x + amount_box_w/2, amount_box_y + 20, amount_display)

    # --- Amount in Words Section ---
    y_pos -= 100
    c.setFont("DejaVuSans", 14)
    c.setFillColor(light_text)
    c.drawString(left_margin, y_pos, "The sum of Rupees")

    # Enhanced amount in words with background
    words_bg_y = y_pos - 50
    c.setFillColor(bg_gradient_end)
    c.roundRect(left_margin - 10, words_bg_y, (amount_box_x - left_margin), 40, 8, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor('#E2E8F0'))
    c.setLineWidth(1)
    c.roundRect(left_margin - 10, words_bg_y, (amount_box_x - left_margin), 40, 8, fill=0, stroke=1)

    # Amount in words with better typography
    text_obj = c.beginText(left_margin, y_pos - 30)
    text_obj.setFont("DejaVuSans-Bold", 16)
    text_obj.setFillColor(text_color)
    max_width = (amount_box_x - left_margin - 30)
    line = ""
    for word in amount_words.split():
        if c.stringWidth(line + word + ' ', "DejaVuSans-Bold", 16) < max_width:
            line += word + ' '
        else:
            text_obj.textLine(line.strip())
            line = word + ' '
    text_obj.textLine(line.strip())
    c.drawText(text_obj)

    # --- Enhanced Payment Details Section ---
    y_pos -= 110
    
    # Section header with accent line
    c.setFont("DejaVuSans-Bold", 14)
    c.setFillColor(primary_color)
    c.drawString(left_margin, y_pos, "Payment Details")
    c.setStrokeColor(primary_color)
    c.setLineWidth(2)
    c.line(left_margin, y_pos - 5, left_margin + 120, y_pos - 5)

    # Payment info in styled boxes
    detail_y = y_pos - 35
    
    # Mode box
    mode_width = 150
    c.setFillColor(bg_gradient_start)
    c.roundRect(left_margin, detail_y - 5, mode_width, 25, 6, fill=1, stroke=0)
    c.setFont("DejaVuSans", 12)
    c.setFillColor(light_text)
    c.drawString(left_margin + 8, detail_y + 8, "Mode:")
    c.setFont("DejaVuSans-Bold", 12)
    c.setFillColor(text_color)
    c.drawString(left_margin + 45, detail_y + 8, mode)

    # Purpose box (right aligned)
    purpose_width = 180
    purpose_x = right_margin - purpose_width
    c.setFillColor(bg_gradient_start)
    c.roundRect(purpose_x, detail_y - 5, purpose_width, 25, 6, fill=1, stroke=0)
    c.setFont("DejaVuSans", 12)
    c.setFillColor(light_text)
    c.drawString(purpose_x + 8, detail_y + 8, "Purpose:")
    c.setFont("DejaVuSans-Bold", 12)
    c.setFillColor(text_color)
    c.drawString(purpose_x + 60, detail_y + 8, purpose)

    # Cheque details if provided
    if cheque_details:
        c.setFont("DejaVuSans", 11)
        c.setFillColor(light_text)
        c.drawString(left_margin, detail_y - 25, f"Details: {cheque_details}")

    # --- Enhanced Signature Section ---
    sig_y = 180
    sig_w = 160
    spacing = (w - 2 * left_margin - 3 * sig_w) / 2
    
    # Signature section header
    c.setFont("DejaVuSans-Bold", 12)
    c.setFillColor(primary_color)
    c.drawString(left_margin, sig_y + 40, "Authorized Signatures")
    c.setStrokeColor(primary_color)
    c.setLineWidth(1)
    c.line(left_margin, sig_y + 35, left_margin + 150, sig_y + 35)

    for i, role in enumerate(["PRESIDENT", "TREASURER", "ISSUED BY"]):
        x = left_margin + i * (sig_w + spacing)
        
        # Enhanced signature boxes
        c.setFillColor(bg_gradient_end)
        c.roundRect(x - 5, sig_y - 25, sig_w + 10, 50, 8, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor('#E2E8F0'))
        c.setLineWidth(1)
        c.roundRect(x - 5, sig_y - 25, sig_w + 10, 50, 8, fill=0, stroke=1)
        
        # Signature line
        c.setStrokeColor(light_text)
        c.setLineWidth(1)
        c.line(x + 10, sig_y, x + sig_w - 10, sig_y)
        
        if role == "ISSUED BY":
            c.setFont("DejaVuSans-Bold", 13)
            c.setFillColor(success_color)
            c.drawCentredString(x + sig_w / 2, sig_y + 10, issued_by.upper())
            c.setFont("DejaVuSans", 10)
            c.setFillColor(light_text)
            c.drawCentredString(x + sig_w / 2, sig_y - 15, role)
        else:
            c.setFont("DejaVuSans", 10)
            c.setFillColor(light_text)
            c.drawCentredString(x + sig_w / 2, sig_y - 15, role)

    # --- Enhanced Footer ---
    footer_y = 100
    
    # Decorative separator
    c.setStrokeColor(accent_color)
    c.setLineWidth(2)
    c.line(left_margin, footer_y, right_margin, footer_y)
    
    # Add small decorative elements
    circle_y = footer_y
    for i in range(5):
        x_pos = left_margin + (right_margin - left_margin) * i / 4
        c.setFillColor(accent_color)
        c.circle(x_pos, circle_y, 3, fill=1, stroke=0)

    # Footer text with better styling
    c.setFont("DejaVuSans", 10)
    c.setFillColor(light_text)
    c.drawCentredString(w / 2, footer_y - 25, "This is a computer-generated receipt and does not require a signature.")
    
    # Subtle branding
    c.setFont("DejaVuSans", 8)
    c.setFillColor(colors.HexColor('#A0AEC0'))
    c.drawCentredString(w / 2, footer_y - 40, "Generated with care by Nashik Bangiya Parishad")
    
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
