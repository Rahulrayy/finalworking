import firebase_admin
from firebase_admin import credentials, db
import os
import json

# --- Firebase Configuration ---
DATABASE_URL = 'https://receipt-generator-95b80-default-rtdb.asia-southeast1.firebasedatabase.app/'

def initialize_firebase():
    """Initializes the Firebase Admin SDK using environment variable."""
    try:
        firebase_json = os.environ.get("FIREBASE_KEY_JSON")
        if not firebase_json:
            print("❌ FIREBASE_KEY_JSON environment variable not found.")
            return False

        firebase_dict = json.loads(firebase_json)

        # Initialize Firebase only once
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': DATABASE_URL
            })

        print("✅ Firebase connection initialized successfully.")
        return True

    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False

def fetch_receipt_data():
    """Fetches all receipt data from Firebase Realtime Database."""
    try:
        ref = db.reference('receipts')
        data = ref.get()

        if not data:
            print("ℹ️ No receipt data found in the database.")
            return

        print("\n--- 🧾 Fetched Receipt Data ---")

        if isinstance(data, dict):
            for receipt_id, details in data.items():
                if not details: continue
                print(f"\n🧾 Receipt ID: {receipt_id}")
                for key, value in details.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        elif isinstance(data, list):
            for i, details in enumerate(data):
                if not details: continue
                receipt_id = details.get('receipt_no', f"Entry {i}")
                print(f"\n🧾 Receipt ID: {receipt_id}")
                for key, value in details.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\n✅ All receipt data printed.")
    except Exception as e:
        print(f"❌ Error fetching receipt data: {e}")

if __name__ == "__main__":
    print("📡 Connecting to Firebase...")
    if initialize_firebase():
        fetch_receipt_data()
