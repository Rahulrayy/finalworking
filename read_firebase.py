import firebase_admin
from firebase_admin import credentials, db
import os

# --- IMPORTANT: PLEASE EDIT THESE VALUES ---
# 1. Replace with the absolute path to your Firebase service account JSON file.
# Example: 'C:\Users\YourUser\path\to\your-service-account-key.json'
SERVICE_ACCOUNT_KEY_PATH = "firebase_key.json"

# 2. Replace with your Firebase Realtime Database URL.
# Example: 'https://your-project-id-default-rtdb.firebaseio.com/'
DATABASE_URL = 'https://receipt-generator-95b80-default-rtdb.asia-southeast1.firebasedatabase.app/'
# ------------------------------------------

def initialize_firebase():
    """Initializes the Firebase Admin SDK."""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            print(f"Error: Service account key file not found at: {SERVICE_ACCOUNT_KEY_PATH}")
            print("Please update the SERVICE_ACCOUNT_KEY_PATH variable in this script.")
            return False

        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)

        # Check if the app is already initialized to prevent errors on re-runs
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': DATABASE_URL
            })
        print("Firebase connection initialized successfully.")
        return True
    except Exception as e:
        print(f"An error occurred during Firebase initialization: {e}")
        print("Please check your service account key path and database URL.")
        return False

def fetch_receipt_data():
    """Fetches all receipt data from the database."""
    try:
        ref = db.reference('receipts')
        data = ref.get()

        if not data:
            print("No receipt data found in the database.")
            return

        print("\n--- Fetched Receipt Data ---")

        if isinstance(data, dict):
            for receipt_id, details in data.items():
                if not details: continue
                print(f"\nReceipt ID: {receipt_id}")
                for key, value in details.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        elif isinstance(data, list):
            for i, details in enumerate(data):
                if not details: continue
                receipt_id = details.get('receipt_no', f"Entry {i}")
                print(f"\nReceipt ID: {receipt_id}")
                for key, value in details.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\n---------------------------")

    except Exception as e:
        print(f"An error occurred while fetching data: {e}")

if __name__ == "__main__":
    print("Attempting to connect to Firebase and read data...")
    if initialize_firebase():
        fetch_receipt_data()