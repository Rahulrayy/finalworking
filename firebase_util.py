import firebase_admin
from firebase_admin import credentials, db
import os
import json  # 🔧 You missed this import

# Initialize Firebase
if not firebase_admin._apps:
    firebase_json = os.environ.get("FIREBASE_KEY_JSON")
    if firebase_json:
        firebase_dict = json.loads(firebase_json)
        cred = credentials.Certificate(firebase_dict)
    else:
        raise FileNotFoundError("FIREBASE_KEY_JSON environment variable not set")

    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://receipt-generator-95b80-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

def get_next_receipt_number():
    ref = db.reference("receipt_counter")
    current = ref.get()
    if current is None:
        current = 1
    else:
        current += 1
    ref.set(current)
    return current

def save_receipt_entry(receipt_no, name, amount, mode, cheque_details, purpose, issued_by, date_str, time_str):
    ref = db.reference(f"receipts/{receipt_no}")
    ref.set({
        "name": name,
        "amount": amount,
        "mode": mode,
        "cheque_details": cheque_details,
        "purpose": purpose,
        "issued_by": issued_by,
        "date": date_str,
        "time": time_str
    })
