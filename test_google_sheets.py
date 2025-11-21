"""Test script to diagnose Google Sheets connectivity issues"""
import os
import json
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import gspread
    from google.oauth2 import service_account
    print("[OK] gspread and google-auth are installed")
except ImportError as e:
    print(f"[ERROR] Missing required packages: {e}")
    print("Run: pip install gspread google-auth")
    sys.exit(1)

# Check for credentials file
credentials_file = 'service_account.json'
if os.path.exists(credentials_file):
    print(f"[OK] Found credentials file: {credentials_file}")
else:
    print(f"[ERROR] Credentials file not found: {credentials_file}")
    sys.exit(1)

# Try to load credentials
try:
    print("\nAttempting to load credentials...")
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
    )
    print("[OK] Credentials loaded successfully")
    print(f"  Service account email: {credentials.service_account_email}")
except Exception as e:
    print(f"[ERROR] Error loading credentials: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to create gspread client
try:
    print("\nAttempting to create gspread client...")
    client = gspread.authorize(credentials)
    print("[OK] gspread client created successfully")
except Exception as e:
    print(f"[ERROR] Error creating gspread client: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to create a test spreadsheet
try:
    print("\nAttempting to create a test spreadsheet...")
    test_title = f"Test Sheet - {os.path.basename(os.getcwd())}"
    spreadsheet = client.create(test_title)
    print(f"[OK] Test spreadsheet created successfully!")
    print(f"  URL: {spreadsheet.url}")
    print(f"  ID: {spreadsheet.id}")
    
    # Try to update it
    worksheet = spreadsheet.sheet1
    worksheet.update('A1', [['Test', 'Data'], ['1', '2']])
    print("[OK] Successfully updated test spreadsheet")
    
    # Clean up - delete the test sheet
    print("\nCleaning up test spreadsheet...")
    client.del_spreadsheet(spreadsheet.id)
    print("[OK] Test spreadsheet deleted")
    
except Exception as e:
    print(f"[ERROR] Error creating/updating spreadsheet: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("[OK] All Google Sheets tests passed!")
print("="*50)

