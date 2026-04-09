from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum

db = SQLAlchemy()


class UserRole(Enum):
    ADMIN = 'admin'
    CASHIER = 'cashier'
    STORE_KEEPER = 'store_keeper'
    COLLECTOR = 'collector'
    PURCHASE_MANAGER = 'purchase_manager'
    SALES_MANAGER = 'sales_manager'


class Permission:
    VIEW_INVENTORY = 'view_inventory'
    EDIT_PRODUCT = 'edit_product'
    VIEW_PURCHASES = 'view_purchases'
    ADD_PURCHASE = 'add_purchase'
    MANAGE_SUPPLIERS = 'manage_suppliers'
    VIEW_SALES = 'view_sales'
    ADD_SALE = 'add_sale'
    MANAGE_CUSTOMERS = 'manage_customers'
    VIEW_CASH = 'view_cash'
    MANAGE_CASH = 'manage_cash'
    VIEW_JOURNAL = 'view_journal'
    ADD_JOURNAL_ENTRY = 'add_journal_entry'
    DAILY_CLOSING = 'daily_closing'
    VIEW_COLLECTIONS = 'view_collections'
    ADD_COLLECTION = 'add_collection'
    VIEW_REPORTS = 'view_reports'
    MANAGE_USERS = 'manage_users'
    MANAGE_EMPLOYEES = 'manage_employees'


ROLE_PERMISSIONS = {
    UserRole.ADMIN.value: [getattr(Permission, attr) for attr in dir(Permission) if not attr.startswith('_')],
    UserRole.CASHIER.value: [
        Permission.VIEW_CASH, Permission.MANAGE_CASH,
        Permission.VIEW_JOURNAL, Permission.ADD_JOURNAL_ENTRY,
        Permission.DAILY_CLOSING, Permission.VIEW_REPORTS
    ],
    UserRole.STORE_KEEPER.value: [
        Permission.VIEW_INVENTORY, Permission.EDIT_PRODUCT,
        Permission.VIEW_REPORTS
    ],
    UserRole.COLLECTOR.value: [
        Permission.VIEW_COLLECTIONS, Permission.ADD_COLLECTION,
        Permission.MANAGE_CUSTOMERS, Permission.VIEW_REPORTS
    ],
    UserRole.PURCHASE_MANAGER.value: [
        Permission.MANAGE_SUPPLIERS, Permission.VIEW_PURCHASES,
        Permission.ADD_PURCHASE, Permission.VIEW_INVENTORY,
        Permission.VIEW_REPORTS
    ],
    UserRole.SALES_MANAGER.value: [
        Permission.MANAGE_CUSTOMERS, Permission.VIEW_SALES,
        Permission.ADD_SALE, Permission.VIEW_INVENTORY,
        Permission.VIEW_REPORTS
    ]
}


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def has_permission(self, permission):
        if self.role == UserRole.ADMIN.value:
            return True
        permissions = ROLE_PERMISSIONS.get(self.role, [])
        return permission in permissions

    def get_permissions(self):
        return ROLE_PERMISSIONS.get(self.role, [])


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    salary = db.Column(db.Float, default=0.0)
    hire_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='employee_info', foreign_keys=[user_id])


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    balance = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), default='قطعة')
    purchase_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=10)
    location = db.Column(db.String(50))
    is_frozen = db.Column(db.Boolean, default=False)
    freeze_deposit = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    payment_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # حقول الموافقة المالية
    cash_status = db.Column(db.String(20), default='pending')
    cash_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cash_approved_at = db.Column(db.DateTime, nullable=True)
    cash_rejection_reason = db.Column(db.String(200), nullable=True)

    supplier = db.relationship('Supplier', backref='purchase_orders')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_purchases')
    cash_approver = db.relationship('User', foreign_keys=[cash_approved_by], backref='approved_purchases')


class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    purchase_order = db.relationship('PurchaseOrder', backref='items')
    product = db.relationship('Product')


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    balance = db.Column(db.Float, default=0.0)
    credit_limit = db.Column(db.Float, default=5000.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SaleOrder(db.Model):
    __tablename__ = 'sale_orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    payment_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')
    delivery_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # حقول الموافقة المالية
    cash_status = db.Column(db.String(20), default='pending')
    cash_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cash_approved_at = db.Column(db.DateTime, nullable=True)
    cash_rejection_reason = db.Column(db.String(200), nullable=True)

    customer = db.relationship('Customer', backref='sale_orders')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_sales')
    cash_approver = db.relationship('User', foreign_keys=[cash_approved_by], backref='approved_sales')


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_order_id = db.Column(db.Integer, db.ForeignKey('sale_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    sale_order = db.relationship('SaleOrder', backref='items')
    product = db.relationship('Product')


class Collection(db.Model):
    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    collector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    collection_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    # حقول الموافقة المالية
    cash_status = db.Column(db.String(20), default='pending')
    cash_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cash_approved_at = db.Column(db.DateTime, nullable=True)
    cash_rejection_reason = db.Column(db.String(200), nullable=True)

    customer = db.relationship('Customer', backref='collections')
    collector = db.relationship('User', foreign_keys=[collector_id], backref='collections_made')
    cash_approver = db.relationship('User', foreign_keys=[cash_approved_by], backref='approved_collections')


class CashTransaction(db.Model):
    __tablename__ = 'cash_transactions'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='cash_transactions')


class CashBox(db.Model):
    __tablename__ = 'cash_boxes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='الصندوق الرئيسي')
    balance = db.Column(db.Float, default=0.0)
    initial_balance = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    reference_number = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(200), nullable=False)
    total_debit = db.Column(db.Float, default=0.0)
    total_credit = db.Column(db.Float, default=0.0)
    is_posted = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by], backref='journal_entries')
    details = db.relationship('JournalDetail', backref='entry', cascade='all, delete-orphan')


class JournalDetail(db.Model):
    __tablename__ = 'journal_details'

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    account_id = db.Column(db.Integer)
    account_name = db.Column(db.String(100))
    debit = db.Column(db.Float, default=0.0)
    credit = db.Column(db.Float, default=0.0)
    notes = db.Column(db.String(200))


class DailyCashSummary(db.Model):
    __tablename__ = 'daily_cash_summaries'

    id = db.Column(db.Integer, primary_key=True)
    summary_date = db.Column(db.DateTime, default=datetime.utcnow)
    opening_balance = db.Column(db.Float, default=0.0)
    closing_balance = db.Column(db.Float, default=0.0)
    total_income = db.Column(db.Float, default=0.0)
    total_expense = db.Column(db.Float, default=0.0)
    cash_sales = db.Column(db.Float, default=0.0)
    credit_sales = db.Column(db.Float, default=0.0)
    collections = db.Column(db.Float, default=0.0)
    purchases = db.Column(db.Float, default=0.0)
    deposits = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by], backref='cash_summaries')


class FreezeDeposit(db.Model):
    __tablename__ = 'freeze_deposits'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    is_returned = db.Column(db.Boolean, default=False)
    deposit_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    product = db.relationship('Product', backref='freeze_deposits')
    customer = db.relationship('Customer', backref='freeze_deposits')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_deposits')


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    reference_id = db.Column(db.Integer)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=[user_id], backref='transactions_list')