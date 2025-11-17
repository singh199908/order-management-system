from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
import os
import json
import sys
from io import BytesIO
from sqlalchemy import inspect, text
import logging

# Load environment variables from .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Allow insecure transport for OAuth on localhost (development only)
# This is required because oauthlib requires HTTPS by default
# Only enable for localhost, not for production (Render uses HTTPS)
if os.environ.get('FLASK_ENV') != 'production' and 'localhost' in os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', ''):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

try:
    import gspread
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
except ImportError:
    gspread = None
    service_account = None
    Flow = None
    Credentials = None
    Request = None

# Fix Windows console encoding for print statements
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Trust proxy headers on Render (so Flask knows requests are HTTPS)
# This is needed for OAuth to work correctly on Render
if os.environ.get('RENDER') or os.environ.get('FLASK_ENV') == 'production':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Add custom Jinja2 filter for JSON parsing
@app.template_filter('from_json')
def from_json_filter(value):
    return json.loads(value) if value else []

# WhatsApp/Twilio Configuration
# IMPORTANT: Set these as environment variables. Never commit credentials to Git!
app.config['TWILIO_ACCOUNT_SID'] = os.environ.get('TWILIO_ACCOUNT_SID', '')
app.config['TWILIO_AUTH_TOKEN'] = os.environ.get('TWILIO_AUTH_TOKEN', '')
app.config['TWILIO_WHATSAPP_FROM'] = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
app.config['ADMIN_WHATSAPP_NUMBER'] = os.environ.get('ADMIN_WHATSAPP_NUMBER', '')
app.config['TWILIO_CONTENT_SID'] = os.environ.get('TWILIO_CONTENT_SID', '')
app.config['GOOGLE_SERVICE_ACCOUNT_FILE'] = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', '')
app.config['GOOGLE_SERVICE_ACCOUNT_JSON'] = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
app.config['GOOGLE_DRIVE_FOLDER_ID'] = os.environ.get('GOOGLE_DRIVE_FOLDER_ID', '')
# OAuth Configuration
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
app.config['GOOGLE_OAUTH_REDIRECT_URI'] = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:5000/oauth2callback')


# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # Increased for scrypt hashes
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'ba'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_type_code = db.Column(db.String(100), nullable=False)
    parent_code = db.Column(db.String(100))
    item_lot_type = db.Column(db.String(200))
    quantity_available = db.Column(db.Integer, default=0)
    mrp = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_data = db.Column(db.Text, nullable=False)  # JSON string of order items
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, downloaded, confirmed, completed
    sheet_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Order', backref=db.backref('notifications', lazy=True))

class SavedCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cart_data = db.Column(db.Text, nullable=False)  # JSON string of cart items
    name = db.Column(db.String(100))  # Optional name for the saved cart
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('saved_carts', lazy=True))

class GoogleOAuthToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_data = db.Column(db.Text, nullable=False)  # JSON string of OAuth token
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_google_credentials():
    """Return Google credentials - OAuth tokens (preferred) or service account."""
    if not Credentials and not service_account:
        app.logger.warning('google-auth is not installed. Skipping Google Sheets backup.')
        return None
    
    cached_credentials = getattr(app, '_google_credentials', None)
    if cached_credentials:
        return cached_credentials
    
    # Try OAuth credentials first (preferred for personal accounts)
    if Credentials:
        try:
            oauth_token = GoogleOAuthToken.query.first()
            if oauth_token:
                token_dict = json.loads(oauth_token.token_data)
                credentials = Credentials.from_authorized_user_info(token_dict, GOOGLE_SCOPES)
                
                # Refresh token if expired
                if credentials.expired and credentials.refresh_token:
                    try:
                        credentials.refresh(Request())
                        # Save refreshed token
                        oauth_token.token_data = json.dumps({
                            'token': credentials.token,
                            'refresh_token': credentials.refresh_token,
                            'token_uri': credentials.token_uri,
                            'client_id': credentials.client_id,
                            'client_secret': credentials.client_secret,
                            'scopes': credentials.scopes
                        })
                        db.session.commit()
                        app.logger.info('OAuth token refreshed successfully.')
                    except Exception as refresh_error:
                        app.logger.error(f'Error refreshing OAuth token: {str(refresh_error)}')
                        return None
                
                app._google_credentials = credentials
                app.logger.info('Google OAuth credentials loaded successfully.')
                return credentials
        except Exception as e:
            app.logger.warning(f'Error loading OAuth credentials: {str(e)}')
    
    # Fall back to service account if OAuth not available
    if service_account:
        credentials_json = app.config.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        credentials_file = app.config.get('GOOGLE_SERVICE_ACCOUNT_FILE')
        
        try:
            if credentials_json:
                app.logger.info('Loading Google credentials from GOOGLE_SERVICE_ACCOUNT_JSON environment variable.')
                info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(info, scopes=GOOGLE_SCOPES)
            elif credentials_file and os.path.exists(credentials_file):
                app.logger.info(f'Loading Google credentials from file: {credentials_file}')
                credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=GOOGLE_SCOPES)
            else:
                app.logger.warning('No Google credentials configured. Use OAuth or set GOOGLE_SERVICE_ACCOUNT_FILE.')
                return None
            
            app._google_credentials = credentials
            app.logger.info('Google service account credentials loaded successfully.')
            return credentials
        except Exception as e:
            app.logger.error(f'Error loading Google credentials: {str(e)}', exc_info=True)
            return None
    
    return None


def get_gspread_client():
    """Initialize and cache a gspread client."""
    if not gspread:
        app.logger.warning('gspread is not installed. Skipping Google Sheets backup.')
        return None
    
    cached_client = getattr(app, '_gspread_client', None)
    if cached_client:
        return cached_client
    
    credentials = get_google_credentials()
    if not credentials:
        app.logger.warning('Google credentials unavailable. Skipping Sheets backup.')
        return None
    
    try:
        client = gspread.authorize(credentials)
        app._gspread_client = client
        app.logger.info('gspread client created successfully.')
        return client
    except Exception as e:
        app.logger.error(f'Error creating gspread client: {str(e)}', exc_info=True)
        return None


def create_order_spreadsheet(order, ba_username=None):
    """Create a dedicated Google Sheet for the given order and return its URL."""
    client = get_gspread_client()
    if not client:
        return None
    
    app.logger.info(f'Preparing to create Google Sheet for order #{order.id}')
    
    # Use provided username or try to get from order.user relationship
    if not ba_username:
        try:
            ba_username = order.user.username if order.user else 'Unknown BA'
        except Exception:
            ba_username = 'Unknown BA'
    order_date = order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    sheet_title = f'Order #{order.id} - {ba_username} - {order.created_at.strftime("%Y-%m-%d") if order.created_at else datetime.utcnow().strftime("%Y-%m-%d")}'
    
    try:
        folder_id = app.config.get('GOOGLE_DRIVE_FOLDER_ID') or None
        # Also check environment variable directly in case config didn't load
        if not folder_id:
            folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID') or None
        
        spreadsheet = None
        
        # Try to create in folder if folder_id is provided
        if folder_id:
            app.logger.info(f'Using Google Drive folder ID: {folder_id}')
            try:
                spreadsheet = client.create(sheet_title, folder_id=folder_id)
                app.logger.info(f'Successfully created sheet in folder for order #{order.id}')
            except Exception as folder_error:
                error_str = str(folder_error)
                # Check if it's a quota error - don't fallback to root if quota is exceeded
                if 'quota' in error_str.lower() or 'storage' in error_str.lower():
                    app.logger.error(f'Google Drive storage quota exceeded. Cannot create sheet for order #{order.id}')
                    raise  # Re-raise quota errors - they'll be caught by outer handler
                # If folder not found (404) or permission denied (but not quota), fallback to root
                elif '404' in error_str or 'not found' in error_str.lower() or ('403' in error_str and 'quota' not in error_str.lower()):
                    app.logger.warning(f'Failed to create sheet in folder (ID: {folder_id}): {error_str}')
                    app.logger.info(f'Falling back to creating sheet in root for order #{order.id}')
                    try:
                        spreadsheet = client.create(sheet_title)
                    except Exception as root_error:
                        root_error_str = str(root_error)
                        # If root also fails with quota, don't try again
                        if 'quota' in root_error_str.lower() or 'storage' in root_error_str.lower():
                            app.logger.error(f'Google Drive storage quota exceeded in root as well for order #{order.id}')
                            raise
                        else:
                            raise
                else:
                    # Re-raise if it's a different error
                    raise
        else:
            app.logger.info('No Google Drive folder ID provided. Creating sheet in root.')
            spreadsheet = client.create(sheet_title)
        worksheet = spreadsheet.sheet1
        
        metadata_rows = [
            ['Order ID', order.id],
            ['BA Username', ba_username],
            ['Order Date', order_date],
            ['Status', order.status or 'pending'],
            ['']
        ]
        worksheet.update('A1', metadata_rows)
        
        header_row_index = len(metadata_rows) + 1
        headers = ['#', 'Lot Type Code', 'Item Type', 'Parent Code', 'Quantity Needed', 'MRP', 'Line Total (₹)']
        worksheet.update(f'A{header_row_index}', [headers])
        
        try:
            order_items = json.loads(order.order_data or '[]')
        except Exception:
            order_items = []
        
        if order_items:
            item_rows = []
            for idx, item in enumerate(order_items, start=1):
                item_rows.append([
                    idx,
                    item.get('lot_type_code') or '',
                    item.get('item_lot_type') or '',
                    item.get('parent_code') or '',
                    item.get('quantity') or 0,
                    item.get('mrp') or 0,
                    item.get('total') or 0
                ])
            worksheet.update(f'A{header_row_index + 1}', item_rows)
        
        summary_row_index = header_row_index + len(order_items) + 2
        worksheet.update(
            f'A{summary_row_index}',
            [['Total Amount (₹)', round(order.total_amount or 0, 2)]]
        )
        
        app.logger.info(f'Created Google Sheet for order #{order.id}: {spreadsheet.url}')
        return spreadsheet.url
    
    except Exception as e:
        error_msg = str(e)
        # Get more detailed error information
        error_details = {
            'error_type': type(e).__name__,
            'error_message': error_msg,
        }
        
        # Check for gspread APIError (quota, permissions, etc.)
        if gspread and hasattr(gspread, 'exceptions'):
            if isinstance(e, gspread.exceptions.APIError):
                # Get response details if available
                if hasattr(e, 'response'):
                    error_details['status_code'] = getattr(e.response, 'status_code', None)
                    try:
                        if hasattr(e.response, 'json'):
                            error_details['response_body'] = e.response.json()
                        elif hasattr(e.response, 'text'):
                            error_details['response_text'] = e.response.text
                    except Exception as resp_err:
                        error_details['response_error'] = str(resp_err)
                
                # Also check for error details in the exception itself
                if hasattr(e, 'args') and e.args:
                    error_details['exception_args'] = str(e.args)
                
                # Log full error details
                app.logger.error(f'Google Sheets APIError for order #{order.id}: {error_details}')
                
                if '403' in error_msg or 'quota' in error_msg.lower() or 'storage' in error_msg.lower():
                    # Service accounts don't have storage quotas - files must be in Shared Drive or use domain-wide delegation
                    quota_error = f'Google Drive storage quota error for order #{order.id}. Error: {error_msg}. '
                    quota_error += 'SOLUTION: Service accounts cannot own files. You need to either: '
                    quota_error += '1) Use a Google Workspace Shared Drive, or 2) Use domain-wide delegation to impersonate a user.'
                    app.logger.error(quota_error)
                    print(f"[ERROR] Google Drive storage quota error: {error_msg}")
                    print(f"[INFO] Service accounts don't have storage quotas. Files must be created in a Shared Drive or via domain-wide delegation.")
                    print(f"[INFO] Your personal storage has space, but the service account cannot create files in regular folders.")
                elif '403' in error_msg or 'permission' in error_msg.lower():
                    perm_error = 'Google Drive permission denied for order #{}: {}'.format(order.id, error_msg)
                    app.logger.error(perm_error)
                    print(f"[ERROR] Google Drive permission denied: {error_msg}")
                else:
                    api_error = 'Google Sheets API error for order #{}: {}'.format(order.id, error_msg)
                    app.logger.error(api_error)
                    print(f"[ERROR] Google Sheets API error: {error_msg}")
            else:
                app.logger.error(f'Error creating Google Sheet for order #{order.id}: {error_msg}', exc_info=True)
                print(f"[ERROR] Error creating Google Sheet: {error_msg}")
        else:
            # Fallback for when gspread exceptions aren't available
            if '403' in error_msg or 'quota' in error_msg.lower() or 'storage' in error_msg.lower():
                quota_error = 'Google Drive storage quota exceeded for order #{}. Please free up space in Google Drive or upgrade storage plan.'.format(order.id)
                app.logger.error(quota_error)
                print(f"[ERROR] Google Drive storage quota exceeded. Cannot create sheet for order #{order.id}")
            else:
                app.logger.error(f'Error creating Google Sheet for order #{order.id}: {error_msg}', exc_info=True)
                print(f"[ERROR] Error creating Google Sheet: {error_msg}")
        return None

# Create tables
with app.app_context():
    db.create_all()

    # Ensure legacy databases have the sheet_url column
    try:
        inspector = inspect(db.engine)
        order_columns = [col['name'] for col in inspector.get_columns('order')]
        if 'sheet_url' not in order_columns:
            with db.engine.connect() as connection:
                connection.execute(text('ALTER TABLE "order" ADD COLUMN sheet_url VARCHAR(500)'))
    except Exception as e:
        app.logger.warning(f'Could not verify/add sheet_url column: {str(e)}')
    
    # Ensure password_hash column is large enough for scrypt hashes (PostgreSQL migration)
    # This runs BEFORE creating admin user to avoid errors
    try:
        inspector = inspect(db.engine)
        # Check if user table exists
        if 'user' in inspector.get_table_names():
            user_columns = {col['name']: col for col in inspector.get_columns('user')}
            if 'password_hash' in user_columns:
                password_hash_col = user_columns['password_hash']
                col_type_str = str(password_hash_col['type'])
                # Check if column is too small - try to alter it regardless
                # PostgreSQL VARCHAR(120) or CHARACTER VARYING(120) needs updating
                if '120' in col_type_str or len(col_type_str) < 20:
                    app.logger.info(f'Updating password_hash column from {col_type_str} to VARCHAR(200)')
                    with db.engine.connect() as connection:
                        # Use USING clause to handle type conversion
                        connection.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(200) USING password_hash::VARCHAR(200)'))
                        connection.commit()
                        app.logger.info('Successfully updated password_hash column size to 200')
    except Exception as e:
        # If column doesn't exist or is already correct, that's fine
        app.logger.info(f'Password hash column check: {str(e)} (this is OK if column is already correct or doesn\'t exist yet)')
    
    # Create/update default admin user
    admin = User.query.filter_by(username='rtc').first()
    if admin:
        # Update existing admin password
        admin.password_hash = generate_password_hash('rtc1336')
        admin.role = 'admin'
    else:
        # Create new admin user
        admin = User(
            username='rtc',
            password_hash=generate_password_hash('rtc1336'),
            role='admin'
        )
        db.session.add(admin)
    
    db.session.commit()

# WhatsApp notification function
def send_whatsapp_notification(order_id, ba_username, total_amount, item_count, to_number=None):
    """Send WhatsApp notification using Twilio Content Template API"""
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        account_sid = app.config['TWILIO_ACCOUNT_SID']
        auth_token = app.config['TWILIO_AUTH_TOKEN']
        from_number = app.config['TWILIO_WHATSAPP_FROM']
        content_sid = app.config['TWILIO_CONTENT_SID']
        
        # Use admin number if no specific number provided
        if not to_number:
            to_number = app.config['ADMIN_WHATSAPP_NUMBER']
        
        # Validate Account SID format (should start with "AC")
        if account_sid and not account_sid.startswith('AC'):
            error_msg = f'[ERROR] Invalid Twilio Account SID format. Account SID should start with "AC". Current value starts with: {account_sid[:2] if len(account_sid) >= 2 else "empty"}'
            app.logger.error(error_msg)
            print(error_msg)
            return False
        
        # Check if WhatsApp is configured
        if not account_sid or not auth_token or not to_number:
            missing = []
            if not account_sid: missing.append('TWILIO_ACCOUNT_SID')
            if not auth_token: missing.append('TWILIO_AUTH_TOKEN')
            if not to_number: missing.append('ADMIN_WHATSAPP_NUMBER')
            error_msg = f'WhatsApp not configured. Missing: {", ".join(missing)}'
            app.logger.warning(error_msg)
            print(f"[WARNING] {error_msg}")  # Also print to console
            return False
        
        # Log credential info for debugging (masked)
        masked_sid = f"{account_sid[:4]}...{account_sid[-4:]}" if len(account_sid) > 8 else "***"
        app.logger.debug(f"Using Twilio Account SID: {masked_sid}")
        
        # Format number if needed (ensure it starts with whatsapp:)
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Send a simple text message instead of using the appointment template
        # Message: "YOU HAVE A NEW ORDER FROM (STORE NAME)"
        message_body = f"YOU HAVE A NEW ORDER FROM {ba_username}"
        
        # Twilio API endpoint
        url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
        
        # Prepare data - using Body instead of ContentSid for simple text message
        data = {
            'To': to_number,
            'From': from_number,
            'Body': message_body
        }
        
        # Send request with basic auth
        response = requests.post(
            url,
            data=data,
            auth=HTTPBasicAuth(account_sid, auth_token)
        )
        
        if response.status_code == 201:
            result = response.json()
            success_msg = f'[SUCCESS] WhatsApp notification sent successfully! Message SID: {result.get("sid", "unknown")}'
            app.logger.info(success_msg)
            print(success_msg)  # Also print to console
            return True
        else:
            error_data = response.json() if response.text else {}
            error_code = error_data.get('code', 'unknown')
            error_message = error_data.get('message', response.text)
            
            # Provide specific error messages
            if response.status_code == 401:
                if error_code == 20003:
                    error_msg = f'[ERROR] Twilio Authentication Error: Invalid Account SID or Auth Token. Please check your TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in environment variables or admin settings.'
                else:
                    error_msg = f'[ERROR] Twilio Authentication Error ({error_code}): {error_message}'
            else:
                error_msg = f'[ERROR] Twilio API error: {response.status_code} - {error_message}'
            
            app.logger.error(error_msg)
            print(error_msg)  # Also print to console
            return False
    
    except Exception as e:
        error_msg = f'[ERROR] Error sending WhatsApp notification: {str(e)}'
        app.logger.error(error_msg, exc_info=True)
        try:
            print(error_msg)  # Also print to console
        except UnicodeEncodeError:
            print(f"[ERROR] Error sending WhatsApp notification: {repr(e)}")
        try:
            import traceback
            traceback.print_exc()
        except UnicodeEncodeError:
            pass
        return False

# File upload functions removed - files are not sent via WhatsApp
# Users can download Excel files from the admin dashboard instead

# Routes
@app.route('/health')
@app.route('/ping')
def health_check():
    """Health check endpoint for keepalive services"""
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('order_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('order_page'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/order')
def order_page():
    if 'user_id' not in session or session.get('role') == 'admin':
        return redirect(url_for('login'))
    
    products = Product.query.all()
    return render_template('order.html', products=products)

@app.route('/my_orders')
def my_orders():
    if 'user_id' not in session or session.get('role') != 'ba':
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/api/save_cart', methods=['POST'])
def save_cart():
    if 'user_id' not in session or session.get('role') != 'ba':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        cart_data = data.get('cart', {})
        cart_name = data.get('name', '')
        
        if not cart_data:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Check if user has an existing saved cart
        existing_cart = SavedCart.query.filter_by(user_id=session['user_id']).first()
        
        if existing_cart:
            # Update existing cart
            existing_cart.cart_data = json.dumps(cart_data)
            existing_cart.name = cart_name if cart_name else existing_cart.name
            existing_cart.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Cart updated successfully', 'cart_id': existing_cart.id})
        else:
            # Create new saved cart
            saved_cart = SavedCart(
                user_id=session['user_id'],
                cart_data=json.dumps(cart_data),
                name=cart_name
            )
            db.session.add(saved_cart)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Cart saved successfully', 'cart_id': saved_cart.id})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error saving cart: {str(e)}', exc_info=True)
        return jsonify({'error': f'Error saving cart: {str(e)}'}), 500

@app.route('/api/load_cart', methods=['GET'])
def load_cart():
    if 'user_id' not in session or session.get('role') != 'ba':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        saved_cart = SavedCart.query.filter_by(user_id=session['user_id']).first()
        
        if not saved_cart:
            return jsonify({'success': False, 'cart': {}})
        
        cart_data = json.loads(saved_cart.cart_data)
        return jsonify({
            'success': True,
            'cart': cart_data,
            'name': saved_cart.name,
            'updated_at': saved_cart.updated_at.isoformat()
        })
    
    except Exception as e:
        app.logger.error(f'Error loading cart: {str(e)}', exc_info=True)
        return jsonify({'error': f'Error loading cart: {str(e)}'}), 500

@app.route('/api/clear_saved_cart', methods=['POST'])
def clear_saved_cart():
    if 'user_id' not in session or session.get('role') != 'ba':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        saved_cart = SavedCart.query.filter_by(user_id=session['user_id']).first()
        
        if saved_cart:
            db.session.delete(saved_cart)
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Saved cart cleared'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error clearing cart: {str(e)}', exc_info=True)
        return jsonify({'error': f'Error clearing cart: {str(e)}'}), 500

@app.route('/api/products')
def get_products():
    """API endpoint to get all products with current quantities"""
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'lot_type_code': p.lot_type_code,
        'parent_code': p.parent_code,
        'item_lot_type': p.item_lot_type,
        'quantity_available': p.quantity_available,
        'mrp': p.mrp
    } for p in products])

@app.route('/api/place_order', methods=['POST'])
def place_order():
    try:
        if 'user_id' not in session or session.get('role') == 'admin':
            return jsonify({'error': 'Unauthorized'}), 401
        
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        order_items = data.get('items', [])
        
        if not order_items:
            return jsonify({'error': 'No items in order'}), 400
        
        # Validate quantities and calculate total
        total_amount = 0
        order_data = []
        
        for item in order_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            if quantity <= 0:
                continue
            
            if not product_id:
                return jsonify({'error': 'Invalid product ID'}), 400
            
            product = db.session.get(Product, product_id)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 400
            
            if quantity > product.quantity_available:
                return jsonify({'error': f'Insufficient stock for {product.lot_type_code}. Available: {product.quantity_available}'}), 400
            
            item_total = quantity * (product.mrp or 0)
            total_amount += item_total
            
            order_data.append({
                'product_id': product_id,
                'lot_type_code': product.lot_type_code,
                'parent_code': product.parent_code,
                'item_lot_type': product.item_lot_type,
                'quantity': quantity,
                'mrp': product.mrp,
                'total': item_total
            })
            
            # Update product quantity
            product.quantity_available -= quantity
        
        if not order_data:
            return jsonify({'error': 'No valid items in order'}), 400
        
        # Create order
        order = Order(
            user_id=session['user_id'],
            order_data=json.dumps(order_data),
            total_amount=total_amount,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Get order.id before commit
        
        # Create notification for admin
        notification = Notification(
            order_id=order.id,
            message=f"New order #{order.id} received from {session['username']} - Total: ₹{total_amount:.2f}"
        )
        db.session.add(notification)

        # Create dedicated Google Sheet for this order (if configured)
        sheet_url = None
        if app.config.get('GOOGLE_SERVICE_ACCOUNT_JSON') or app.config.get('GOOGLE_SERVICE_ACCOUNT_FILE'):
            try:
                sheet_url = create_order_spreadsheet(order, ba_username=session.get('username', 'Unknown BA'))
                if sheet_url:
                    order.sheet_url = sheet_url
            except Exception as sheet_error:
                app.logger.error(f'Error creating Google Sheet (order will still be saved): {str(sheet_error)}', exc_info=True)
                # Continue even if sheet creation fails - order should still be saved
        
        db.session.commit()
        
        # Send WhatsApp notification
        send_whatsapp_notification(
            order_id=order.id,
            ba_username=session['username'],
            total_amount=total_amount,
            item_count=len(order_data)
        )
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Order placed successfully!'
        })
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error placing order: {str(e)}', exc_info=True)
        return jsonify({'error': f'Error placing order: {str(e)}'}), 500

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    notifications = Notification.query.filter_by(read=False).order_by(Notification.created_at.desc()).all()
    products = Product.query.all()
    
    return render_template('admin_dashboard.html', orders=orders, notifications=notifications, products=products)

@app.route('/admin/upload_stock', methods=['POST'])
def upload_stock():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Read Excel file
            df = pd.read_excel(filepath)
            
            # Expected columns: Lot Type Code, Parent Code, Item Lot Type: Lot Type, Quantity Available, MRP
            # Handle different possible column names
            column_mapping = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if 'lot type code' in col_lower or 'lot_type_code' in col_lower:
                    column_mapping['lot_type_code'] = col
                elif 'parent code' in col_lower or 'parent_code' in col_lower:
                    column_mapping['parent_code'] = col
                elif 'item lot type' in col_lower or 'item_lot_type' in col_lower:
                    column_mapping['item_lot_type'] = col
                elif 'quantity' in col_lower and 'available' in col_lower:
                    column_mapping['quantity_available'] = col
                elif 'mrp' in col_lower:
                    column_mapping['mrp'] = col
            
            if 'lot_type_code' not in column_mapping:
                return jsonify({'error': 'Lot Type Code column not found'}), 400
            
            updated_count = 0
            created_count = 0
            
            for _, row in df.iterrows():
                lot_type_code = str(row[column_mapping['lot_type_code']]).strip()
                
                if pd.isna(lot_type_code) or lot_type_code == '':
                    continue
                
                parent_code = str(row[column_mapping.get('parent_code', '')]).strip() if 'parent_code' in column_mapping else None
                item_lot_type = str(row[column_mapping.get('item_lot_type', '')]).strip() if 'item_lot_type' in column_mapping else None
                
                quantity = 0
                if 'quantity_available' in column_mapping:
                    try:
                        quantity = int(float(row[column_mapping['quantity_available']]))
                    except:
                        quantity = 0
                
                mrp = None
                if 'mrp' in column_mapping:
                    try:
                        mrp = float(row[column_mapping['mrp']])
                    except:
                        mrp = None
                
                # Check if product exists
                product = Product.query.filter_by(lot_type_code=lot_type_code).first()
                
                if product:
                    # Update existing product
                    if 'parent_code' in column_mapping:
                        product.parent_code = parent_code if parent_code and parent_code != 'nan' else product.parent_code
                    if 'item_lot_type' in column_mapping:
                        product.item_lot_type = item_lot_type if item_lot_type and item_lot_type != 'nan' else product.item_lot_type
                    product.quantity_available = quantity
                    if 'mrp' in column_mapping and mrp is not None:
                        product.mrp = mrp
                    product.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new product
                    product = Product(
                        lot_type_code=lot_type_code,
                        parent_code=parent_code if parent_code and parent_code != 'nan' else None,
                        item_lot_type=item_lot_type if item_lot_type and item_lot_type != 'nan' else None,
                        quantity_available=quantity,
                        mrp=mrp
                    )
                    db.session.add(product)
                    created_count += 1
            
            db.session.commit()
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'message': f'Stock updated successfully! Created: {created_count}, Updated: {updated_count}'
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format. Please upload Excel file (.xlsx or .xls)'}), 400

@app.route('/admin/orders')
def admin_orders():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([{
        'id': order.id,
        'username': order.user.username,
        'order_data': json.loads(order.order_data),
        'total_amount': order.total_amount,
        'status': order.status,
        'sheet_url': order.sheet_url,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for order in orders])

@app.route('/admin/notifications')
def admin_notifications():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': n.id,
        'order_id': n.order_id,
        'message': n.message,
        'read': n.read,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for n in notifications])

@app.route('/admin/mark_notification_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    notification = Notification.query.get_or_404(notification_id)
    notification.read = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/create_ba', methods=['POST'])
def create_ba():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role='ba'
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'BA user created successfully'})

@app.route('/admin/download_order/<int:order_id>', methods=['GET'])
def download_order(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get the specific order
        order = Order.query.get_or_404(order_id)
        order_items = json.loads(order.order_data)
        ba_username = order.user.username
        
        # Prepare data for Excel
        excel_data = []
        
        for item in order_items:
            excel_data.append({
                'Lot Type Code': item.get('lot_type_code', ''),
                'Parent Code': item.get('parent_code', ''),
                'Item Lot Type: Lot Type': item.get('item_lot_type', ''),
                'MRP': item.get('mrp', 0),
                'BA Store Name': ba_username,
                'Quantity Needed': item.get('quantity', 0)
            })
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Order')
        
        output.seek(0)
        
        # Update order status to 'downloaded'
        order.status = 'downloaded'
        db.session.commit()
        
        # Generate filename with order ID and timestamp
        filename = f'order_{order_id}_{ba_username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error generating order Excel: {str(e)}', exc_info=True)
        return jsonify({'error': f'Error generating Excel file: {str(e)}'}), 500

@app.route('/admin/delete_order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        order = Order.query.get_or_404(order_id)
        
        # Also delete associated notifications
        Notification.query.filter_by(order_id=order_id).delete()
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Order deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting order: {str(e)}', exc_info=True)
        return jsonify({'error': f'Error deleting order: {str(e)}'}), 500

@app.route('/admin/whatsapp/test', methods=['POST'])
def test_whatsapp():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    import requests
    from requests.auth import HTTPBasicAuth
    
    data = request.json
    account_sid = data.get('account_sid', '')
    auth_token = data.get('auth_token', '')
    from_number = data.get('from_number', '')
    to_number = data.get('to_number', '')
    content_sid = data.get('content_sid', '')
    
    try:
        if not account_sid or not auth_token or not from_number or not to_number or not content_sid:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Format numbers
        if not from_number.startswith('whatsapp:'):
            from_number = f'whatsapp:{from_number}'
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Send a simple text message for testing
        message_body = "YOU HAVE A NEW ORDER FROM TEST STORE"
        
        # Twilio API endpoint
        url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
        
        # Prepare data - using Body instead of ContentSid for simple text message
        post_data = {
            'To': to_number,
            'From': from_number,
            'Body': message_body
        }
        
        # Send request with basic auth
        response = requests.post(
            url,
            data=post_data,
            auth=HTTPBasicAuth(account_sid, auth_token)
        )
        
        if response.status_code == 201:
            result = response.json()
            return jsonify({'success': True, 'message': f'Test message sent! Message SID: {result.get("sid", "unknown")}'})
        else:
            return jsonify({'error': f'Twilio API error: {response.status_code} - {response.text}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Error sending test message: {str(e)}'}), 500

@app.route('/admin/whatsapp/settings', methods=['POST'])
def save_whatsapp_settings():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    
    # Update app config (for current session only)
    # Note: In production, store these in environment variables or a secure config file
    if data.get('account_sid'):
        app.config['TWILIO_ACCOUNT_SID'] = data.get('account_sid')
    if data.get('auth_token'):
        app.config['TWILIO_AUTH_TOKEN'] = data.get('auth_token')
    if data.get('from_number'):
        app.config['TWILIO_WHATSAPP_FROM'] = data.get('from_number')
    if data.get('to_number'):
        app.config['ADMIN_WHATSAPP_NUMBER'] = data.get('to_number')
    if data.get('content_sid'):
        app.config['TWILIO_CONTENT_SID'] = data.get('content_sid')
    
    # Test the configuration immediately
    test_result = send_whatsapp_notification(
        order_id=999,
        ba_username="TEST",
        total_amount=0.00,
        item_count=0
    )
    
    if test_result:
        return jsonify({
            'success': True,
            'message': 'Settings saved and test message sent successfully! Check your WhatsApp.'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Settings saved but test message failed. Check the console/terminal for error details.'
        })

@app.route('/admin/google/authorize', methods=['GET'])
def google_authorize():
    """Start OAuth flow for Google Drive/Sheets access."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if not Flow:
        flash('OAuth libraries not installed. Install google-auth-oauthlib.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    client_id = app.config.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_OAUTH_CLIENT_SECRET')
    redirect_uri = app.config.get('GOOGLE_OAUTH_REDIRECT_URI')
    
    # Also check environment variable directly
    if not redirect_uri:
        redirect_uri = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', '')
    
    # Log the redirect URI being used for debugging
    app.logger.info(f'OAuth redirect URI being used: {redirect_uri}')
    
    if not client_id or not client_secret:
        flash('Google OAuth not configured. Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if not redirect_uri:
        flash('GOOGLE_OAUTH_REDIRECT_URI not configured. Set it in environment variables.', 'error')
        app.logger.error('GOOGLE_OAUTH_REDIRECT_URI is not set!')
        return redirect(url_for('admin_dashboard'))
    
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=GOOGLE_SCOPES
        )
        flow.redirect_uri = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        session['oauth_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        app.logger.error(f'Error starting OAuth flow: {str(e)}', exc_info=True)
        flash(f'Error starting authorization: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback and save tokens."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    if not Flow:
        flash('OAuth libraries not installed.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    state = session.get('oauth_state')
    if not state or state != request.args.get('state'):
        flash('Invalid OAuth state. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    client_id = app.config.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_OAUTH_CLIENT_SECRET')
    redirect_uri = app.config.get('GOOGLE_OAUTH_REDIRECT_URI')
    
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=GOOGLE_SCOPES,
            state=state
        )
        flow.redirect_uri = redirect_uri
        
        # Construct authorization response URL - ensure it uses HTTPS on Render
        # request.url might be HTTP if Flask doesn't know about the proxy
        if request.is_secure or os.environ.get('RENDER') or os.environ.get('FLASK_ENV') == 'production':
            # Use HTTPS for the callback URL
            scheme = 'https'
        else:
            scheme = request.scheme
        
        authorization_response = f"{scheme}://{request.host}{request.full_path}"
        app.logger.info(f'OAuth callback URL: {authorization_response}')
        flow.fetch_token(authorization_response=authorization_response)
        
        credentials = flow.credentials
        
        # Save token to database
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Delete old token if exists
        GoogleOAuthToken.query.delete()
        db.session.commit()
        
        # Save new token
        oauth_token = GoogleOAuthToken(token_data=json.dumps(token_data))
        db.session.add(oauth_token)
        db.session.commit()
        
        # Clear cached credentials
        if hasattr(app, '_google_credentials'):
            delattr(app, '_google_credentials')
        if hasattr(app, '_gspread_client'):
            delattr(app, '_gspread_client')
        
        session.pop('oauth_state', None)
        flash('Google OAuth authorization successful! You can now create Google Sheets.', 'success')
        app.logger.info('Google OAuth token saved successfully.')
    except Exception as e:
        app.logger.error(f'Error in OAuth callback: {str(e)}', exc_info=True)
        flash(f'Authorization failed: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/google/status', methods=['GET'])
def google_oauth_status():
    """Check OAuth authorization status."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    oauth_token = GoogleOAuthToken.query.first()
    has_oauth = oauth_token is not None
    
    has_service_account = bool(
        app.config.get('GOOGLE_SERVICE_ACCOUNT_FILE') or 
        app.config.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    )
    
    has_oauth_config = bool(
        app.config.get('GOOGLE_OAUTH_CLIENT_ID') and 
        app.config.get('GOOGLE_OAUTH_CLIENT_SECRET')
    )
    
    return jsonify({
        'oauth_authorized': has_oauth,
        'service_account_configured': has_service_account,
        'oauth_configured': has_oauth_config,
        'using_oauth': has_oauth  # OAuth takes precedence
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Render sets PORT automatically, use it
    # Enable debug mode locally for better error messages
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)


