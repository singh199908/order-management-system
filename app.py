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

try:
    import gspread
    from google.oauth2 import service_account
except ImportError:
    gspread = None
    service_account = None

# Fix Windows console encoding for print statements
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

app = Flask(__name__)
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


# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
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

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_google_credentials():
    """Return cached Google service account credentials if configured."""
    if not service_account:
        app.logger.warning('google-auth is not installed. Skipping Google Sheets backup.')
        return None
    
    cached_credentials = getattr(app, '_google_credentials', None)
    if cached_credentials:
        return cached_credentials
    
    credentials_json = app.config.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    credentials_file = app.config.get('GOOGLE_SERVICE_ACCOUNT_FILE')
    
    try:
        if credentials_json:
            info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=GOOGLE_SCOPES)
        elif credentials_file and os.path.exists(credentials_file):
            credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=GOOGLE_SCOPES)
        else:
            app.logger.warning('Google service account not configured. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON to enable backups.')
            return None
        
        app._google_credentials = credentials
        return credentials
    except Exception as e:
        app.logger.error(f'Error loading Google credentials: {str(e)}', exc_info=True)
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
        return None
    
    try:
        client = gspread.authorize(credentials)
        app._gspread_client = client
        return client
    except Exception as e:
        app.logger.error(f'Error creating gspread client: {str(e)}', exc_info=True)
        return None


def create_order_spreadsheet(order):
    """Create a dedicated Google Sheet for the given order and return its URL."""
    client = get_gspread_client()
    if not client:
        return None
    
    ba_username = order.user.username if order.user else 'Unknown BA'
    order_date = order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    sheet_title = f'Order #{order.id} - {ba_username} - {order.created_at.strftime("%Y-%m-%d") if order.created_at else datetime.utcnow().strftime("%Y-%m-%d")}'
    
    try:
        folder_id = app.config.get('GOOGLE_DRIVE_FOLDER_ID') or None
        spreadsheet = client.create(sheet_title, folder_id=folder_id)
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
        app.logger.error(f'Error creating Google Sheet for order #{order.id}: {str(e)}', exc_info=True)
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
            sheet_url = create_order_spreadsheet(order)
            if sheet_url:
                order.sheet_url = sheet_url
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Render sets PORT automatically, use it
    app.run(debug=False, host='0.0.0.0', port=port)


