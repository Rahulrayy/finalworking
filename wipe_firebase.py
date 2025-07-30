import firebase_admin
from firebase_admin import credentials, db
import os
import json

# Firebase DB URL
DATABASE_URL = 'https://receipt-generator-95b80-default-rtdb.asia-southeast1.firebasedatabase.app/'
NODE_TO_WIPE = 'receipts'

def initialize_firebase():
    """Initializes the Firebase Admin SDK using env variable."""
    try:
        firebase_json = os.environ.get("FIREBASE_KEY_JSON")
        if not firebase_json:
            print("Error: FIREBASE_KEY_JSON environment variable not set.")
            return False

        firebase_dict = json.loads(firebase_json)
        cred = credentials.Certificate(firebase_dict)

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
