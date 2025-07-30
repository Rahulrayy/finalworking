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

# The node in your database to wipe. 
# For example, 'receipts'. To wipe the entire database, set this to '/'
NODE_TO_WIPE = 'receipts'

def initialize_firebase():
    """Initializes the Firebase Admin SDK."""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            print(f"Error: Service account key file not found at: {SERVICE_ACCOUNT_KEY_PATH}")
            print("Please update the SERVICE_ACCOUNT_KEY_PATH variable in this script.")
            return False

        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': DATABASE_URL
            })
        print("Firebase connection initialized successfully.")
        return True
    except Exception as e:
        print(f"An error occurred during Firebase initialization: {e}")
        return False

def wipe_database_node():
    """Deletes all data from the specified node in the database."""
    try:
        print("\n--- DANGER ZONE ---")
        print(f"You are about to permanently delete all data from the '{NODE_TO_WIPE}' node.")
        print("This action is irreversible.")
        
        confirmation = input("To confirm, please type 'DELETE': ")
        
        if confirmation == "DELETE":
            print(f"\nDeleting data from '{NODE_TO_WIPE}'...")
            ref = db.reference(NODE_TO_WIPE)
            ref.delete()
            print("Data has been successfully deleted.")
        else:
            print("\nDeletion cancelled. No changes were made.")
            
    except Exception as e:
        print(f"An error occurred while trying to delete data: {e}")

if __name__ == "__main__":
    print("Attempting to connect to Firebase...")
    if initialize_firebase():
        wipe_database_node()
