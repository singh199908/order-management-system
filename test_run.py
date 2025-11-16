import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importing app...")
    from app import app
    print("App imported successfully!")
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")

