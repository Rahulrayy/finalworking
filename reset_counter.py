import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIPT_COUNTER_FILE = os.path.join(BASE_DIR, "receipt_counter.txt")

START_NUMBER = 1001  # Set to 1001 if you want the first receipt to be 1001

def reset_receipt_counter():
    """Resets the receipt counter file to the specified start number."""
    try:
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(RECEIPT_COUNTER_FILE, "w") as f:
            f.write(str(START_NUMBER))
        print(f"✅ Successfully reset the receipt counter to {START_NUMBER}.")
        print(f"ℹ️ The next receipt number generated will be {START_NUMBER}.")
    except Exception as e:
        print(f"❌ Error writing to the file: {e}")

if __name__ == "__main__":
    print(f"⚠️ This will reset the receipt counter file: {RECEIPT_COUNTER_FILE}")
    reset_receipt_counter()
