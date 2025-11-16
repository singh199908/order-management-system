# Order Management System

A web-based order management system for Business Associates (BAs) to place orders with real-time stock updates.

## Features

- **BA Order Placement**: BAs can view available products and place orders
- **Real-time Stock Updates**: Quantities automatically update when orders are placed
- **Excel Stock Import**: Admin can upload Excel files to update product inventory
- **Order Notifications**: Admin receives notifications when new orders are placed
- **Admin Dashboard**: Complete admin panel to manage orders, products, and BAs
- **User Isolation**: Each BA can only see their own orders

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Navigate to the project folder:
```bash
cd order_management_system
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Default Login Credentials

- **Admin**: 
  - Username: `admin`
  - Password: `admin123`

## Excel File Format

When uploading stock, your Excel file should have the following columns:
- **Lot Type Code** (required)
- **Parent Code** (optional)
- **Item Lot Type: Lot Type** (optional)
- **Quantity Available** (required)
- **MRP** (optional)

## Usage

### For Business Associates (BAs):
1. Login with your BA credentials
2. View available products with current stock
3. Select quantities for products you want to order
4. Review your order summary
5. Submit the order

### For Admin:
1. Login with admin credentials
2. **Notifications Tab**: View new order notifications
3. **Orders Tab**: View all orders from all BAs
4. **Products Tab**: View current inventory
5. **Update Stock Tab**: Upload Excel file to update product quantities
6. **Create BA Tab**: Create new BA user accounts

## Database

The application uses SQLite database (`orders.db`) which is automatically created on first run.

## Security Notes

- Change the `SECRET_KEY` in `app.py` before deploying to production
- Change the default admin password after first login
- Use strong passwords for all user accounts

## File Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── login.html
│   ├── order.html
│   └── admin_dashboard.html
└── uploads/             # Temporary folder for Excel uploads (auto-created)
```

## Notes

- Stock quantities are automatically deducted when orders are placed
- Each BA can only view their own orders (not other BAs' orders)
- Admin has full access to view all orders and manage the system
- Notifications are created automatically when new orders are placed

