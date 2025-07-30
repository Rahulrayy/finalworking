import os

# --- Configuration ---
# This path must match the one in your main app.py file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIPT_COUNTER_FILE = os.path.join(BASE_DIR, "receipt_counter.txt")

START_NUMBER = 1000

def reset_receipt_counter():
    """Resets the receipt counter file to the specified start number."""
    try:
        # Open the file in write mode ('w'), which creates or overwrites the file
        with open(RECEIPT_COUNTER_FILE, "w") as f:
            f.write(str(START_NUMBER))
        print(f"Successfully reset the receipt counter to {START_NUMBER}.")
        print(f"The next receipt number generated will be {START_NUMBER}.")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")

if __name__ == "__main__":
    print(f"This script will reset the receipt counter in the file: {RECEIPT_COUNTER_FILE}")
    reset_receipt_counter()
