from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, UserRole, Permission, ROLE_PERMISSIONS, Employee, Supplier, Product, PurchaseOrder, PurchaseItem, Customer, SaleOrder, SaleItem, Collection, CashTransaction, FreezeDeposit, Transaction, CashBox, JournalEntry, JournalDetail, DailyCashSummary
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, UserRole, Permission, ROLE_PERMISSIONS, Employee, Supplier, Product, PurchaseOrder, PurchaseItem, Customer, SaleOrder, SaleItem, Collection, CashTransaction, FreezeDeposit, Transaction, CashBox, JournalEntry, JournalDetail, DailyCashSummary
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json

app = Flask(__name__)

# إعدادات التطبيق الأساسية
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد قاعدة البيانات (دعم SQLite محلياً و PostgreSQL على Render)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///thaljat_alsaleef.db')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

# تهيئة قاعدة البيانات
db.init_app(app)

# تهيئة نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def permission_required(permission):
    """ديكوراتور للتحقق من الصلاحيات"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== الصفحات الرئيسية ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password) and user.is_active:
            login_user(user)
            flash(f'مرحباً {user.full_name}', 'success')
            return redirect(url_for('dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.quantity < Product.min_quantity).count()
    total_suppliers = Supplier.query.count()
    total_customers = Customer.query.count()
    today_sales = db.session.query(db.func.sum(SaleOrder.total_amount)).filter(
        db.func.date(SaleOrder.sale_date) == datetime.now().date()
    ).scalar() or 0

    total_deposits = db.session.query(db.func.sum(FreezeDeposit.amount)).filter(
        FreezeDeposit.is_returned == False
    ).scalar() or 0

    recent_purchases = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).limit(5).all()
    recent_sales = SaleOrder.query.order_by(SaleOrder.sale_date.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_products=total_products,
                           low_stock=low_stock,
                           total_suppliers=total_suppliers,
                           total_customers=total_customers,
                           today_sales=today_sales,
                           total_deposits=total_deposits,
                           recent_purchases=recent_purchases,
                           recent_sales=recent_sales)


# ==================== إدارة المستخدمين ====================

@app.route('/users')
@login_required
@permission_required(Permission.MANAGE_USERS)
def users_list():
    users = User.query.all()
    return render_template('users/index.html', users=users)


@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        email = request.form.get('email')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('add_user'))

        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role,
            full_name=full_name,
            phone=phone,
            email=email
        )
        db.session.add(user)
        db.session.commit()
        flash('تم إضافة المستخدم بنجاح', 'success')
        return redirect(url_for('users_list'))

    roles = [(r.value, r.name) for r in UserRole]
    return render_template('users/add.html', roles=roles)


@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_USERS)
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.role = request.form.get('role')
        user.full_name = request.form.get('full_name')
        user.phone = request.form.get('phone')
        user.email = request.form.get('email')
        user.is_active = request.form.get('is_active') == 'on'

        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('تم تحديث بيانات المستخدم بنجاح', 'success')
        return redirect(url_for('users_list'))

    roles = [(r.value, r.name) for r in UserRole]
    return render_template('users/edit.html', user=user, roles=roles)


@app.route('/users/delete/<int:id>')
@login_required
@permission_required(Permission.MANAGE_USERS)
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('لا يمكن حذف حسابك الحالي', 'danger')
        return redirect(url_for('users_list'))

    db.session.delete(user)
    db.session.commit()
    flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('users_list'))


# ==================== إدارة الموظفين ====================

@app.route('/employees')
@login_required
@permission_required(Permission.MANAGE_EMPLOYEES)
def employees():
    employees_list = Employee.query.all()
    return render_template('employees/index.html', employees=employees_list)


@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_EMPLOYEES)
def add_employee():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        position = request.form.get('position')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        salary = float(request.form.get('salary', 0))
        hire_date_str = request.form.get('hire_date')
        hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d') if hire_date_str else datetime.now()

        employee = Employee(
            full_name=full_name,
            position=position,
            phone=phone,
            email=email,
            address=address,
            salary=salary,
            hire_date=hire_date
        )
        db.session.add(employee)
        db.session.flush()

        create_user = request.form.get('create_user') == 'on'
        if create_user:
            username = request.form.get('username')
            password = request.form.get('password')

            role_map = {
                'مسؤول الصندوق': UserRole.CASHIER.value,
                'أمين المخزن': UserRole.STORE_KEEPER.value,
                'المحصل': UserRole.COLLECTOR.value,
                'مسؤول المشتريات': UserRole.PURCHASE_MANAGER.value,
                'مسؤول المبيعات': UserRole.SALES_MANAGER.value,
                'مدير': UserRole.ADMIN.value
            }
            role = role_map.get(position, 'employee')

            user = User(
                username=username,
                password=generate_password_hash(password),
                role=role,
                full_name=full_name,
                phone=phone,
                email=email
            )
            db.session.add(user)
            db.session.flush()
            employee.user_id = user.id

        db.session.commit()
        flash('تم إضافة الموظف بنجاح', 'success')
        return redirect(url_for('employees'))

    positions = ['مسؤول الصندوق', 'أمين المخزن', 'المحصل', 'مسؤول المشتريات', 'مسؤول المبيعات', 'مدير']
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('employees/add.html', positions=positions, today=today)


@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_EMPLOYEES)
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        employee.full_name = request.form.get('full_name')
        employee.position = request.form.get('position')
        employee.phone = request.form.get('phone')
        employee.email = request.form.get('email')
        employee.address = request.form.get('address')
        employee.salary = float(request.form.get('salary', 0))
        employee.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash('تم تحديث بيانات الموظف بنجاح', 'success')
        return redirect(url_for('employees'))

    positions = ['مسؤول الصندوق', 'أمين المخزن', 'المحصل', 'مسؤول المشتريات', 'مسؤول المبيعات', 'مدير']
    return render_template('employees/edit.html', employee=employee, positions=positions)


@app.route('/employees/delete/<int:id>')
@login_required
@permission_required(Permission.MANAGE_EMPLOYEES)
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    if employee.user_id:
        user = User.query.get(employee.user_id)
        if user:
            db.session.delete(user)
    db.session.delete(employee)
    db.session.commit()
    flash('تم حذف الموظف بنجاح', 'success')
    return redirect(url_for('employees'))


# ==================== إدارة الموردين ====================

# تعديل صلاحيات الموردين - لمسؤول المشتريات فقط
@app.route('/suppliers')
@login_required
@permission_required(Permission.MANAGE_SUPPLIERS)
def suppliers():
    suppliers_list = Supplier.query.all()
    return render_template('suppliers/index.html', suppliers=suppliers_list)



@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_SUPPLIERS)
def add_supplier():
    if request.method == 'POST':
        supplier = Supplier(
            name=request.form.get('name'),
            contact_person=request.form.get('contact_person'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address')
        )
        db.session.add(supplier)
        db.session.commit()
        flash('تم إضافة المورد بنجاح', 'success')
        return redirect(url_for('suppliers'))
    return render_template('suppliers/add.html')


@app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        supplier.name = request.form.get('name')
        supplier.contact_person = request.form.get('contact_person')
        supplier.phone = request.form.get('phone')
        supplier.email = request.form.get('email')
        supplier.address = request.form.get('address')
        db.session.commit()
        flash('تم تحديث بيانات المورد بنجاح', 'success')
        return redirect(url_for('suppliers'))
    return render_template('suppliers/edit.html', supplier=supplier)


@app.route('/suppliers/delete/<int:id>')
@login_required
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash('تم حذف المورد بنجاح', 'success')
    return redirect(url_for('suppliers'))


# ==================== إدارة العملاء ====================

# تعديل صلاحيات العملاء - لمسؤول المبيعات والمحصل
@app.route('/customers')
@login_required
@permission_required(Permission.MANAGE_CUSTOMERS)
def customers():
    customers_list = Customer.query.all()
    return render_template('customers/index.html', customers=customers_list)


@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        customer = Customer(
            name=request.form.get('name'),
            type=request.form.get('type'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            credit_limit=float(request.form.get('credit_limit', 5000))
        )
        db.session.add(customer)
        db.session.commit()
        flash('تم إضافة العميل بنجاح', 'success')
        return redirect(url_for('customers'))
    return render_template('customers/add.html')


@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.type = request.form.get('type')
        customer.phone = request.form.get('phone')
        customer.address = request.form.get('address')
        customer.credit_limit = float(request.form.get('credit_limit', 5000))
        db.session.commit()
        flash('تم تحديث بيانات العميل بنجاح', 'success')
        return redirect(url_for('customers'))
    return render_template('customers/edit.html', customer=customer)


# ==================== إدارة المخزون (عرض فقط) ====================

@app.route('/inventory')
@login_required
@permission_required(Permission.VIEW_INVENTORY)
def inventory():
    products = Product.query.all()
    return render_template('inventory/index.html', products=products)


@app.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EDIT_PRODUCT)
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.unit = request.form.get('unit')
        product.selling_price = float(request.form.get('selling_price', 0))
        product.min_quantity = int(request.form.get('min_quantity', 10))
        product.location = request.form.get('location')
        product.is_frozen = request.form.get('is_frozen') == 'on'
        product.freeze_deposit = float(request.form.get('freeze_deposit', 0))
        db.session.commit()
        flash('تم تحديث بيانات المنتج بنجاح', 'success')
        return redirect(url_for('inventory'))
    return render_template('inventory/edit.html', product=product)


# ==================== إدارة المشتريات ====================

@app.route('/purchases')
@login_required
@permission_required(Permission.VIEW_PURCHASES)
def purchases():
    purchases_list = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).all()
    return render_template('purchases/index.html', purchases=purchases_list)


@app.route('/purchases/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADD_PURCHASE)
def add_purchase():
    suppliers = Supplier.query.all()
    existing_products = Product.query.all()

    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        payment_type = request.form.get('payment_type')
        total_amount = float(request.form.get('total_amount'))
        paid_amount = float(request.form.get('paid_amount', 0))

        purchase = PurchaseOrder(
            supplier_id=supplier_id,
            total_amount=total_amount,
            paid_amount=paid_amount,
            payment_type=payment_type,
            status='pending',
            cash_status='pending',  # ✅ تنتظر الموافقة المالية
            created_by=current_user.id
        )
        db.session.add(purchase)
        db.session.flush()

        # إضافة الأصناف
        items_data = json.loads(request.form.get('items_data', '[]'))
        for item in items_data:
            purchase_item = PurchaseItem(
                purchase_order_id=purchase.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['quantity'] * item['unit_price']
            )
            db.session.add(purchase_item)

            # ⚠️ لا يتم تحديث المخزون حتى موافقة الصندوق
            # product = Product.query.get(item['product_id'])
            # product.quantity += item['quantity']  # مؤجل

        # ✅ لا يتم تسجيل أي معاملة مالية

        db.session.commit()
        flash('تم تسجيل عملية الشراء بنجاح وتنتظر موافقة الصندوق', 'info')
        return redirect(url_for('purchases'))

    return render_template('purchases/add.html', suppliers=suppliers, products=existing_products)

# ==================== إدارة المبيعات ====================

@app.route('/sales')
@login_required
@permission_required(Permission.VIEW_SALES)
def sales():
    sales_list = SaleOrder.query.order_by(SaleOrder.sale_date.desc()).all()
    return render_template('sales/index.html', sales=sales_list)


@app.route('/sales/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADD_SALE)
def add_sale():
    customers = Customer.query.all()
    products = Product.query.filter(Product.quantity > 0).all()

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        payment_type = request.form.get('payment_type')
        total_amount = float(request.form.get('total_amount'))
        paid_amount = float(request.form.get('paid_amount', 0))

        sale = SaleOrder(
            customer_id=customer_id,
            total_amount=total_amount,
            paid_amount=paid_amount,
            payment_type=payment_type,
            status='pending',  # ✅ تنتظر موافقة الصندوق
            cash_status='pending',  # ✅ تنتظر الموافقة المالية
            created_by=current_user.id
        )
        db.session.add(sale)
        db.session.flush()

        # إضافة الأصناف (تحديث المخزون مؤقتاً أو لا؟ حسب الطلب)
        items_data = json.loads(request.form.get('items_data', '[]'))
        for item in items_data:
            sale_item = SaleItem(
                sale_order_id=sale.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['quantity'] * item['unit_price']
            )
            db.session.add(sale_item)

            # ⚠️ لا يتم تحديث المخزون حتى موافقة الصندوق
            # product = Product.query.get(item['product_id'])
            # product.quantity -= item['quantity']  # مؤجل

        # ✅ لا يتم تحديث مديونية العميل ولا الصندوق حتى الموافقة
        # ✅ لا يتم تسجيل أي معاملة مالية

        db.session.commit()
        flash('تم تسجيل عملية البيع بنجاح وتنتظر موافقة الصندوق', 'info')
        return redirect(url_for('sales'))

    return render_template('sales/add.html', customers=customers, products=products)


# ==================== إدارة التحصيل ====================

@app.route('/collections')
@login_required
@permission_required(Permission.VIEW_COLLECTIONS)
def collections():
    collections_list = Collection.query.order_by(Collection.collection_date.desc()).all()
    debt_customers = Customer.query.filter(Customer.balance > 0).all()
    collectors = User.query.filter(User.role == UserRole.COLLECTOR.value).all()

    # حساب تحصيلات اليوم
    today = datetime.now().date()
    today_collections = Collection.query.filter(
        db.func.date(Collection.collection_date) == today
    ).all()
    today_collections_total = sum(c.amount for c in today_collections)

    # حساب إجمالي التحصيلات
    total_collections = sum(c.amount for c in collections_list)

    # حساب إجمالي المديونيات
    total_debts = sum(c.balance for c in debt_customers)

    return render_template('collections/index.html',
                           collections=collections_list,
                           debt_customers=debt_customers,
                           collectors=collectors,
                           today_collections_total=today_collections_total,
                           total_collections=total_collections,
                           total_debts=total_debts)

@app.route('/collections/add', methods=['POST'])
@login_required
@permission_required(Permission.ADD_COLLECTION)
def add_collection():
    customer_id = request.form.get('customer_id')
    amount = float(request.form.get('amount'))
    collector_id = request.form.get('collector_id')
    notes = request.form.get('notes', '')

    collection = Collection(
        customer_id=customer_id,
        collector_id=collector_id,
        amount=amount,
        notes=notes,
        cash_status='pending'  # ✅ تنتظر موافقة الصندوق
    )
    db.session.add(collection)

    # ✅ لا يتم تحديث مديونية العميل حتى الموافقة
    # customer = Customer.query.get(customer_id)
    # customer.balance -= amount  # مؤجل

    # ✅ لا يتم تسجيل معاملة مالية

    db.session.commit()
    flash('تم تسجيل عملية التحصيل بنجاح وتنتظر موافقة الصندوق', 'info')
    return redirect(url_for('collections'))


# ==================== أمانات التجميد ====================

@app.route('/freeze-deposits')
@login_required
def freeze_deposits_list():
    deposits = FreezeDeposit.query.order_by(FreezeDeposit.deposit_date.desc()).all()
    return render_template('freeze_deposits/index.html', deposits=deposits)


@app.route('/freeze-deposits/add', methods=['GET', 'POST'])
@login_required
def add_freeze_deposit():
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        category = request.form.get('category')
        quantity = int(request.form.get('quantity'))
        freeze_deposit_amount = float(request.form.get('freeze_deposit_amount'))
        selling_price = float(request.form.get('selling_price', 0))
        customer_id = request.form.get('customer_id')
        notes = request.form.get('notes', '')

        existing_product = Product.query.filter_by(name=product_name).first()

        if existing_product:
            existing_product.quantity += quantity
            product = existing_product
            flash(f'تم إضافة {quantity} وحدة للمنتج {product_name} كأمانة تجميد', 'info')
        else:
            product = Product(
                name=product_name,
                category=category,
                unit='قطعة',
                purchase_price=0,
                selling_price=selling_price,
                quantity=quantity,
                min_quantity=10,
                location='ثلاجة التجميد',
                is_frozen=True,
                freeze_deposit=freeze_deposit_amount
            )
            db.session.add(product)
            db.session.flush()
            flash(f'تم إنشاء المنتج {product_name} مع أمانة تجميد', 'success')

        deposit = FreezeDeposit(
            product_id=product.id,
            customer_id=customer_id if customer_id else None,
            amount=freeze_deposit_amount * quantity,
            quantity=quantity,
            notes=notes,
            created_by=current_user.id
        )
        db.session.add(deposit)

        cash_transaction = CashTransaction(
            type='deposit',
            amount=freeze_deposit_amount * quantity,
            description=f'أمانة تجميد للمنتج {product_name} (كمية: {quantity})',
            reference_type='freeze_deposit',
            reference_id=deposit.id,
            user_id=current_user.id
        )
        db.session.add(cash_transaction)

        db.session.commit()
        return redirect(url_for('freeze_deposits_list'))

    customers = Customer.query.all()
    categories = ['water', 'soda']
    return render_template('freeze_deposits/add.html', customers=customers, categories=categories)


@app.route('/freeze-deposits/return/<int:id>', methods=['POST'])
@login_required
def return_freeze_deposit(id):
    deposit = FreezeDeposit.query.get_or_404(id)
    if deposit.is_returned:
        flash('هذه الأمانة تم إرجاعها بالفعل', 'warning')
        return redirect(url_for('freeze_deposits_list'))

    deposit.is_returned = True
    deposit.return_date = datetime.now()

    cash_transaction = CashTransaction(
        type='deposit_return',
        amount=deposit.amount,
        description=f'استرداد أمانة تجميد للمنتج {deposit.product.name}',
        reference_type='freeze_deposit_return',
        reference_id=deposit.id,
        user_id=current_user.id
    )
    db.session.add(cash_transaction)

    db.session.commit()
    flash(f'تم إرجاع أمانة التجميد بمبلغ {deposit.amount} د.ع', 'success')
    return redirect(url_for('freeze_deposits_list'))


# ==================== إدارة الصندوق ====================

@app.route('/cash')
@login_required
@permission_required(Permission.VIEW_CASH)
def cash_index():
    """الصفحة الرئيسية للصندوق"""
    cash_box = CashBox.query.first()
    if not cash_box:
        cash_box = CashBox(name='الصندوق الرئيسي', balance=0, initial_balance=0)
        db.session.add(cash_box)
        db.session.commit()

    today = datetime.now().date()
    today_summary = DailyCashSummary.query.filter(
        db.func.date(DailyCashSummary.summary_date) == today
    ).first()

    # إحصائيات اليوم
    today_cash_sales = db.session.query(db.func.sum(SaleOrder.paid_amount)).filter(
        db.func.date(SaleOrder.sale_date) == today,
        SaleOrder.payment_type == 'cash'
    ).scalar() or 0

    today_credit_sales = db.session.query(db.func.sum(SaleOrder.total_amount)).filter(
        db.func.date(SaleOrder.sale_date) == today,
        SaleOrder.payment_type == 'credit'
    ).scalar() or 0

    today_collections = db.session.query(db.func.sum(Collection.amount)).filter(
        db.func.date(Collection.collection_date) == today
    ).scalar() or 0

    today_purchases = db.session.query(db.func.sum(PurchaseOrder.paid_amount)).filter(
        db.func.date(PurchaseOrder.order_date) == today
    ).scalar() or 0

    today_deposits = db.session.query(db.func.sum(CashTransaction.amount)).filter(
        db.func.date(CashTransaction.transaction_date) == today,
        CashTransaction.type == 'deposit'
    ).scalar() or 0

    total_income = today_cash_sales + today_collections + today_deposits
    total_expense = today_purchases

    return render_template('cash/index.html',
                           cash_box=cash_box,
                           today_summary=today_summary,
                           today_cash_sales=today_cash_sales,
                           today_credit_sales=today_credit_sales,
                           today_collections=today_collections,
                           today_purchases=today_purchases,
                           today_deposits=today_deposits,
                           total_income=total_income,
                           total_expense=total_expense)


@app.route('/cash/journal')
@login_required
@permission_required(Permission.VIEW_JOURNAL)
def journal_entries():
    """قيد اليومية"""
    entries = JournalEntry.query.order_by(JournalEntry.entry_date.desc()).all()
    return render_template('cash/journal.html', entries=entries)


@app.route('/cash/journal/add', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADD_JOURNAL_ENTRY)
def add_journal_entry():
    """إضافة قيد يومية جديد"""
    if request.method == 'POST':
        reference_number = request.form.get('reference_number')
        description = request.form.get('description')

        # إنشاء رقم مرجعي تلقائي إذا لم يتم إدخاله
        if not reference_number:
            reference_number = f"ENT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        entry = JournalEntry(
            reference_number=reference_number,
            description=description,
            created_by=current_user.id
        )
        db.session.add(entry)
        db.session.flush()

        total_debit = 0
        total_credit = 0

        # إضافة تفاصيل القيد
        accounts = request.form.getlist('account_type[]')
        amounts = request.form.getlist('amount[]')
        types = request.form.getlist('dc_type[]')  # debit or credit
        notes_list = request.form.getlist('notes[]')

        for i in range(len(accounts)):
            if accounts[i] and amounts[i]:
                amount = float(amounts[i])
                detail = JournalDetail(
                    entry_id=entry.id,
                    account_type=accounts[i],
                    account_name=request.form.getlist('account_name[]')[i],
                    debit=amount if types[i] == 'debit' else 0,
                    credit=amount if types[i] == 'credit' else 0,
                    notes=notes_list[i] if i < len(notes_list) else ''
                )
                db.session.add(detail)

                if types[i] == 'debit':
                    total_debit += amount
                else:
                    total_credit += amount

        # التأكد من توازن القيد
        if total_debit != total_credit:
            flash('القيد غير متوازن! يجب أن يكون مجموع المدين = مجموع الدائن', 'danger')
            db.session.rollback()
            return redirect(url_for('add_journal_entry'))

        entry.total_debit = total_debit
        entry.total_credit = total_credit

        # تحديث رصيد الصندوق إذا كان القيد يتعلق بالنقدية
        cash_box = CashBox.query.first()
        if cash_box:
            for detail in entry.details:
                if detail.account_type == 'cash':
                    if detail.debit > 0:
                        cash_box.balance += detail.debit
                    elif detail.credit > 0:
                        cash_box.balance -= detail.credit
            cash_box.updated_at = datetime.now()

        db.session.commit()
        flash('تم إضافة قيد اليومية بنجاح', 'success')
        return redirect(url_for('journal_entries'))

    return render_template('cash/add_journal.html')


@app.route('/cash/journal/delete/<int:id>')
@login_required
@permission_required(Permission.MANAGE_CASH)
def delete_journal_entry(id):
    """حذف قيد يومية"""
    entry = JournalEntry.query.get_or_404(id)

    # إعادة رصيد الصندوق
    cash_box = CashBox.query.first()
    if cash_box:
        for detail in entry.details:
            if detail.account_type == 'cash':
                if detail.debit > 0:
                    cash_box.balance -= detail.debit
                elif detail.credit > 0:
                    cash_box.balance += detail.credit

    db.session.delete(entry)
    db.session.commit()
    flash('تم حذف قيد اليومية بنجاح', 'success')
    return redirect(url_for('journal_entries'))


@app.route('/cash/opening-balance', methods=['POST'])
@login_required
@permission_required(Permission.MANAGE_CASH)
def set_opening_balance():
    """تحديد الرصيد الافتتاحي للصندوق"""
    amount = float(request.form.get('opening_balance', 0))
    cash_box = CashBox.query.first()
    if cash_box:
        cash_box.initial_balance = amount
        cash_box.balance = amount
        cash_box.updated_at = datetime.now()
        db.session.commit()
        flash(f'تم تحديد الرصيد الافتتاحي للصندوق بمبلغ {amount} د.ع', 'success')
    return redirect(url_for('cash_index'))


@app.route('/cash/daily-closing', methods=['POST'])
@login_required
@permission_required(Permission.DAILY_CLOSING)
def daily_closing():
    """إغلاق يومي للصندوق"""
    today = datetime.now().date()

    # التحقق من عدم وجود إغلاق سابق لنفس اليوم
    existing = DailyCashSummary.query.filter(db.func.date(DailyCashSummary.summary_date) == today).first()
    if existing:
        flash('تم إغلاق الصندوق لهذا اليوم مسبقاً', 'warning')
        return redirect(url_for('cash_index'))

    cash_box = CashBox.query.first()

    # حساب إحصائيات اليوم
    today_cash_sales = db.session.query(db.func.sum(SaleOrder.paid_amount)).filter(
        db.func.date(SaleOrder.sale_date) == today,
        SaleOrder.payment_type == 'cash'
    ).scalar() or 0

    today_credit_sales = db.session.query(db.func.sum(SaleOrder.total_amount)).filter(
        db.func.date(SaleOrder.sale_date) == today,
        SaleOrder.payment_type == 'credit'
    ).scalar() or 0

    today_collections = db.session.query(db.func.sum(Collection.amount)).filter(
        db.func.date(Collection.collection_date) == today
    ).scalar() or 0

    today_purchases = db.session.query(db.func.sum(PurchaseOrder.paid_amount)).filter(
        db.func.date(PurchaseOrder.order_date) == today
    ).scalar() or 0

    today_deposits = db.session.query(db.func.sum(CashTransaction.amount)).filter(
        db.func.date(CashTransaction.transaction_date) == today,
        CashTransaction.type == 'deposit'
    ).scalar() or 0

    total_income = today_cash_sales + today_collections + today_deposits
    total_expense = today_purchases
    closing_balance = cash_box.balance if cash_box else 0

    summary = DailyCashSummary(
        summary_date=datetime.now(),
        opening_balance=cash_box.initial_balance if cash_box else 0,
        closing_balance=closing_balance,
        total_income=total_income,
        total_expense=total_expense,
        cash_sales=today_cash_sales,
        credit_sales=today_credit_sales,
        collections=today_collections,
        purchases=today_purchases,
        deposits=today_deposits,
        created_by=current_user.id
    )
    db.session.add(summary)
    db.session.commit()

    flash('تم إغلاق الصندوق اليومي بنجاح', 'success')
    return redirect(url_for('cash_index'))


@app.route('/cash/transactions')
@login_required
@permission_required(Permission.VIEW_CASH)
def cash_transactions():
    """سجل معاملات الصندوق"""
    transactions = CashTransaction.query.order_by(CashTransaction.transaction_date.desc()).all()
    return render_template('cash/transactions.html', transactions=transactions)


@app.route('/cash/approvals')
@login_required
@permission_required(Permission.MANAGE_CASH)
def cash_approvals():
    """عرض المعاملات التي تنتظر موافقة الصندوق"""

    # المشتريات المنتظرة
    pending_purchases = PurchaseOrder.query.filter_by(cash_status='pending').all()

    # المبيعات المنتظرة
    pending_sales = SaleOrder.query.filter_by(cash_status='pending').all()

    # التحصيلات المنتظرة
    pending_collections = Collection.query.filter_by(cash_status='pending').all()

    return render_template('cash/approvals.html',
                           pending_purchases=pending_purchases,
                           pending_sales=pending_sales,
                           pending_collections=pending_collections)


@app.route('/cash/approve/<string:type>/<int:id>', methods=['POST'])
@login_required
@permission_required(Permission.MANAGE_CASH)
def approve_transaction(type, id):
    """الموافقة على معاملة مالية"""

    action = request.form.get('action')  # approve or reject
    reason = request.form.get('reason', '')

    if type == 'purchase':
        transaction = PurchaseOrder.query.get_or_404(id)
    elif type == 'sale':
        transaction = SaleOrder.query.get_or_404(id)
    elif type == 'collection':
        transaction = Collection.query.get_or_404(id)
    else:
        flash('نوع المعاملة غير صحيح', 'danger')
        return redirect(url_for('cash_approvals'))

    if action == 'approve':
        # ✅ الموافقة على المعاملة
        transaction.cash_status = 'approved'
        transaction.cash_approved_by = current_user.id
        transaction.cash_approved_at = datetime.now()

        # ✅ تحديث الصندوق والمعاملات المالية
        if type == 'purchase':
            # تحديث المخزون
            for item in transaction.items:
                product = Product.query.get(item.product_id)
                product.quantity += item.quantity
                product.purchase_price = item.unit_price

            # تسجيل حركة صرف من الصندوق
            if transaction.paid_amount > 0:
                cash_transaction = CashTransaction(
                    type='expense',
                    amount=transaction.paid_amount,
                    description=f'شراء من مورد {transaction.supplier.name}',
                    reference_type='purchase',
                    reference_id=transaction.id,
                    user_id=current_user.id
                )
                db.session.add(cash_transaction)

                # تحديث رصيد الصندوق
                cash_box = CashBox.query.first()
                if cash_box:
                    cash_box.balance -= transaction.paid_amount
                    cash_box.updated_at = datetime.now()

            flash(f'تمت الموافقة على عملية الشراء رقم {transaction.id}', 'success')

        elif type == 'sale':
            # تحديث المخزون (خصم الكميات)
            for item in transaction.items:
                product = Product.query.get(item.product_id)
                product.quantity -= item.quantity

            # تحديث مديونية العميل
            if transaction.payment_type == 'credit':
                customer = Customer.query.get(transaction.customer_id)
                customer.balance += (transaction.total_amount - transaction.paid_amount)

            # تسجيل حركة إيداع في الصندوق
            if transaction.paid_amount > 0:
                cash_transaction = CashTransaction(
                    type='income',
                    amount=transaction.paid_amount,
                    description=f'مبيعات من عميل {transaction.customer.name}',
                    reference_type='sale',
                    reference_id=transaction.id,
                    user_id=current_user.id
                )
                db.session.add(cash_transaction)

                # تحديث رصيد الصندوق
                cash_box = CashBox.query.first()
                if cash_box:
                    cash_box.balance += transaction.paid_amount
                    cash_box.updated_at = datetime.now()

            flash(f'تمت الموافقة على عملية البيع رقم {transaction.id}', 'success')

        elif type == 'collection':
            # تحديث مديونية العميل
            customer = Customer.query.get(transaction.customer_id)
            customer.balance -= transaction.amount

            # تسجيل حركة إيداع في الصندوق
            cash_transaction = CashTransaction(
                type='income',
                amount=transaction.amount,
                description=f'تحصيل من عميل {customer.name}',
                reference_type='collection',
                reference_id=transaction.id,
                user_id=current_user.id
            )
            db.session.add(cash_transaction)

            # تحديث رصيد الصندوق
            cash_box = CashBox.query.first()
            if cash_box:
                cash_box.balance += transaction.amount
                cash_box.updated_at = datetime.now()

            flash(f'تمت الموافقة على عملية التحصيل رقم {transaction.id}', 'success')

        transaction.status = 'completed'

    else:  # reject
        transaction.cash_status = 'rejected'
        transaction.cash_rejection_reason = reason
        transaction.status = 'cancelled'
        flash(f'تم رفض المعاملة: {reason}', 'warning')

    db.session.commit()
    return redirect(url_for('cash_approvals'))

# ==================== تحديث صلاحيات Routes الموجودة ====================



# ==================== التقارير ====================

@app.route('/reports')
@login_required
@permission_required(Permission.VIEW_REPORTS)
def reports():
    return render_template('reports/index.html')


@app.route('/api/products/search')
@login_required
def search_products():
    query = request.args.get('q', '')
    products = Product.query.filter(Product.name.contains(query)).limit(10).all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.selling_price, 'quantity': p.quantity} for p in products])


@app.route('/api/reports/data')
@login_required
@permission_required(Permission.VIEW_REPORTS)
def reports_data():
    """API لجلب بيانات التقارير"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    report_type = request.args.get('type', 'all')

    # تحويل التواريخ
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.now().replace(day=1)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()

    # جلب بيانات المبيعات
    sales_query = SaleOrder.query.filter(
        db.func.date(SaleOrder.sale_date) >= start_date.date(),
        db.func.date(SaleOrder.sale_date) <= end_date.date()
    )
    sales = sales_query.all()

    sales_data = [{
        'date': s.sale_date.strftime('%Y-%m-%d'),
        'customer': s.customer.name,
        'total': s.total_amount,
        'paid': s.paid_amount,
        'remaining': s.total_amount - s.paid_amount,
        'type': s.payment_type
    } for s in sales]

    total_sales = sum(s.total_amount for s in sales)
    total_collected = sum(s.paid_amount for s in sales)

    # جلب بيانات المشتريات
    purchases_query = PurchaseOrder.query.filter(
        db.func.date(PurchaseOrder.order_date) >= start_date.date(),
        db.func.date(PurchaseOrder.order_date) <= end_date.date()
    )
    purchases = purchases_query.all()

    purchases_data = [{
        'date': p.order_date.strftime('%Y-%m-%d'),
        'supplier': p.supplier.name,
        'total': p.total_amount,
        'paid': p.paid_amount,
        'remaining': p.total_amount - p.paid_amount,
        'type': p.payment_type
    } for p in purchases]

    total_purchases = sum(p.total_amount for p in purchases)

    # جلب بيانات المديونيات
    debt_customers = Customer.query.filter(Customer.balance > 0).all()
    debts_data = [{
        'customer': c.name,
        'balance': c.balance,
        'limit': c.credit_limit,
        'percentage': (c.balance / c.credit_limit * 100) if c.credit_limit > 0 else 0,
        'last_collection': None
    } for c in debt_customers]

    total_debts = sum(c.balance for c in debt_customers)

    # جلب بيانات الصندوق
    cash_transactions = CashTransaction.query.filter(
        db.func.date(CashTransaction.transaction_date) >= start_date.date(),
        db.func.date(CashTransaction.transaction_date) <= end_date.date()
    ).all()

    cash_data = [{
        'date': t.transaction_date.strftime('%Y-%m-%d %H:%M'),
        'type': t.type,
        'amount': t.amount,
        'description': t.description,
        'user': t.user.full_name if t.user else '-'
    } for t in cash_transactions]

    total_expenses = sum(t.amount for t in cash_transactions if t.type == 'expense')
    total_collections = sum(t.amount for t in cash_transactions if t.type == 'income')

    # جلب بيانات المخزون
    products = Product.query.all()
    inventory_data = [{
        'name': p.name,
        'quantity': p.quantity,
        'unit': p.unit,
        'purchase_price': p.purchase_price,
        'selling_price': p.selling_price,
        'value': p.quantity * p.purchase_price,
        'min_quantity': p.min_quantity
    } for p in products]

    # جلب بيانات أمانات التجميد
    freeze_deposits = FreezeDeposit.query.filter(
        db.func.date(FreezeDeposit.deposit_date) >= start_date.date(),
        db.func.date(FreezeDeposit.deposit_date) <= end_date.date()
    ).all()

    freeze_data = [{
        'date': d.deposit_date.strftime('%Y-%m-%d'),
        'product': d.product.name,
        'quantity': d.quantity,
        'amount': d.amount,
        'is_returned': d.is_returned,
        'customer': d.customer.name if d.customer else '-'
    } for d in freeze_deposits]

    # البيانات الشهرية للرسوم البيانية
    months = ['يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر',
              'ديسمبر']
    monthly_sales = []
    monthly_purchases = []

    for i in range(1, 13):
        month_sales = SaleOrder.query.filter(
            db.extract('month', SaleOrder.sale_date) == i,
            db.extract('year', SaleOrder.sale_date) == datetime.now().year
        ).all()
        monthly_sales.append(sum(s.total_amount for s in month_sales))

        month_purchases = PurchaseOrder.query.filter(
            db.extract('month', PurchaseOrder.order_date) == i,
            db.extract('year', PurchaseOrder.order_date) == datetime.now().year
        ).all()
        monthly_purchases.append(sum(p.total_amount for p in month_purchases))

    return jsonify({
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'total_profit': total_sales - total_purchases,
        'total_debts': total_debts,
        'total_expenses': total_expenses,
        'total_collections': total_collections,
        'sales': sales_data,
        'purchases': purchases_data,
        'debts': debts_data,
        'cash_transactions': cash_data,
        'inventory': inventory_data,
        'freeze_deposits': freeze_data,
        'months': months[:6],
        'monthly_sales': monthly_sales[:6],
        'monthly_purchases': monthly_purchases[:6]
    })


@app.route('/api/customer/<int:id>/details')
@login_required
def customer_details(id):
    """جلب تفاصيل العميل للمودال"""
    customer = Customer.query.get_or_404(id)

    # جلب عمليات الشراء للعميل
    sales = SaleOrder.query.filter_by(customer_id=id).order_by(SaleOrder.sale_date.desc()).limit(10).all()
    collections = Collection.query.filter_by(customer_id=id).order_by(Collection.collection_date.desc()).limit(10).all()

    transactions = []
    for sale in sales:
        transactions.append({
            'date': sale.sale_date.strftime('%Y-%m-%d'),
            'type': 'sale',
            'amount': sale.total_amount,
            'description': f'فاتورة رقم {sale.id}'
        })

    for coll in collections:
        transactions.append({
            'date': coll.collection_date.strftime('%Y-%m-%d'),
            'type': 'collection',
            'amount': coll.amount,
            'description': coll.notes or 'تحصيل نقدي'
        })

    # ترتيب المعاملات حسب التاريخ
    transactions.sort(key=lambda x: x['date'], reverse=True)

    total_purchases = sum(s.total_amount for s in sales)
    total_payments = sum(c.amount for c in collections)

    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'phone': customer.phone,
        'address': customer.address,
        'credit_limit': customer.credit_limit,
        'balance': customer.balance,
        'total_purchases': total_purchases,
        'total_payments': total_payments,
        'last_purchase': sales[0].sale_date.strftime('%Y-%m-%d') if sales else None,
        'last_collection': collections[0].collection_date.strftime('%Y-%m-%d') if collections else None,
        'transactions': transactions[:20]
    })


@app.route('/reports/sales')
@login_required
@permission_required(Permission.VIEW_REPORTS)
def sales_report():
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-01'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    payment_type = request.args.get('payment_type', 'all')

    query = SaleOrder.query.filter(
        db.func.date(SaleOrder.sale_date) >= start_date,
        db.func.date(SaleOrder.sale_date) <= end_date
    )

    if payment_type != 'all':
        query = query.filter(SaleOrder.payment_type == payment_type)

    sales_data = query.order_by(SaleOrder.sale_date.desc()).all()

    total_sales = sum(s.total_amount for s in sales_data)
    total_collected = sum(s.paid_amount for s in sales_data)
    total_credit = total_sales - total_collected

    # بيانات الرسم البياني اليومي
    daily_data = db.session.query(
        db.func.date(SaleOrder.sale_date).label('date'),
        db.func.sum(SaleOrder.total_amount).label('total')
    ).filter(
        db.func.date(SaleOrder.sale_date) >= start_date,
        db.func.date(SaleOrder.sale_date) <= end_date
    ).group_by(db.func.date(SaleOrder.sale_date)).all()

    daily_sales = [{'date': d.date.strftime('%Y-%m-%d'), 'total': float(d.total)} for d in daily_data]

    return render_template('reports/sales.html',
                           sales=sales_data,
                           total_sales=total_sales,
                           total_collected=total_collected,
                           total_credit=total_credit,
                           start_date=start_date,
                           end_date=end_date,
                           payment_type=payment_type,
                           daily_sales=daily_sales)


@app.route('/api/product/<int:id>/details')
@login_required
def product_details(id):
    """جلب تفاصيل المنتج"""
    product = Product.query.get_or_404(id)

    return jsonify({
        'id': product.id,
        'name': product.name,
        'category': product.category,
        'quantity': product.quantity,
        'min_quantity': product.min_quantity,
        'purchase_price': product.purchase_price,
        'selling_price': product.selling_price,
        'location': product.location,
        'is_frozen': product.is_frozen,
        'freeze_deposit': product.freeze_deposit,
        'created_at': product.created_at.strftime('%Y-%m-%d') if product.created_at else None
    })


# ==================== تشغيل التطبيق ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role=UserRole.ADMIN.value,
                full_name='مدير النظام',
                phone='123456789',
                email='admin@thaljat.com'
            )
            db.session.add(admin)
            db.session.flush()

            admin_employee = Employee(
                full_name='مدير النظام',
                position='مدير',
                phone='123456789',
                email='admin@thaljat.com',
                salary=5000,
                user_id=admin.id
            )
            db.session.add(admin_employee)

            db.session.commit()
            print("=" * 50)
            print("تم إنشاء المستخدم admin بنجاح")
            print("اسم المستخدم: admin")
            print("كلمة المرور: admin123")
            print("=" * 50)

    app.run(debug=True)
