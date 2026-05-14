import psycopg2
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random

# رابط قاعدة البيانات
DATABASE_URL = "postgresql://postgres.augjutrkulpmonywppju:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"


def add_demo_data():
    try:
        # الاتصال بقاعدة البيانات
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("✅ تم الاتصال بقاعدة البيانات")
        print("=" * 60)

        # ==================== 1. إنشاء المستخدمين بجميع الأدوار ====================
        print("\n📝 جاري إنشاء المستخدمين...")

        users_data = [
            # المشرفون
            ('admin', 'admin123', 'admin', 'مدير النظام', '0500000000', 'admin@thaljat.com'),
            ('admin2', 'admin123', 'admin', 'نائب المدير', '0500000001', 'admin2@thaljat.com'),

            # مسؤولو الصندوق
            ('cashier1', 'cash123', 'cashier', 'أحمد محمود', '0511111111', 'ahmed@thaljat.com'),
            ('cashier2', 'cash123', 'cashier', 'سارة خالد', '0511111112', 'sara@thaljat.com'),

            # أمناء المخزن
            ('store1', 'store123', 'store_keeper', 'خالد عبدالله', '0522222222', 'khaled@thaljat.com'),
            ('store2', 'store123', 'store_keeper', 'نورة محمد', '0522222223', 'noura@thaljat.com'),

            # المحصلون
            ('collector1', 'collect123', 'collector', 'علي حسن', '0533333333', 'ali@thaljat.com'),
            ('collector2', 'collect123', 'collector', 'فاطمة علي', '0533333334', 'fatima@thaljat.com'),

            # مسؤولو المشتريات
            ('purchase1', 'purchase123', 'purchase_manager', 'محمد ابراهيم', '0544444444', 'mohammed@thaljat.com'),
            ('purchase2', 'purchase123', 'purchase_manager', 'هدى سعيد', '0544444445', 'huda@thaljat.com'),

            # مسؤولو المبيعات
            ('sales1', 'sales123', 'sales_manager', 'عمر خالد', '0555555555', 'omar@thaljat.com'),
            ('sales2', 'sales123', 'sales_manager', 'ليلى احمد', '0555555556', 'layla@thaljat.com'),
        ]

        for username, password, role, full_name, phone, email in users_data:
            # تجنب تكرار المستخدمين
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if not cur.fetchone():
                hashed_password = generate_password_hash(password)
                cur.execute("""
                    INSERT INTO users (username, password, role, full_name, phone, email, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, true, %s)
                    RETURNING id
                """, (username, hashed_password, role, full_name, phone, email, datetime.now()))
                user_id = cur.fetchone()[0]
                print(f"   ✅ تم إنشاء المستخدم: {username} ({role}) - كلمة المرور: {password}")

                # إنشاء موظف مرتبط بكل مستخدم
                cur.execute("""
                    INSERT INTO employees (full_name, position, phone, email, salary, hire_date, is_active, user_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, true, %s, %s)
                """, (full_name, get_position_name(role), phone, email, random.uniform(3000, 8000), datetime.now(),
                      user_id, datetime.now()))
                print(f"   ✅ تم إنشاء الموظف: {full_name}")

        # ==================== 2. إنشاء الموردين ====================
        print("\n📝 جاري إنشاء الموردين...")

        suppliers_data = [
            ('شركة العطارة الحديثة', 'أحمد العطار', '0555123456', 'contact@attara.com', 'الرياض - شارع العطارين', 0),
            ('مؤسسة الغذاء الصحي', 'سعد المطيري', '0555234567', 'info@healthyfood.com', 'جدة - حي الروضة', 0),
            ('شركة المشروبات الوطنية', 'عبدالله القحطاني', '0555345678', 'sales@nationaldrinks.com',
             'الدمام - المنطقة الصناعية', 0),
            ('مصنع حلواني للألبان', 'محمد حلواني', '0555456789', 'm.halwani@dairy.com', 'مكة المكرمة - النزهة', 1500),
            ('الشرق للتجارة', 'خالد الشمري', '0555567890', 'khalid@alsharq.com', 'المدينة المنورة - العالية', 800),
            ('مؤسسة الفاخرة للمواد الغذائية', 'ناصر الفهد', '0555678901', 'nasser@fakhera.com', 'الرياض - الملز', 0),
            ('شركة الربيع للمياه', 'سلطان الربيع', '0555789012', 'sultan@rabee.com', 'الرياض - السلي', 2000),
            ('مصنع المراعي', 'عبدالعزيز المراعي', '0555890123', 'aziz@marai.com', 'الخرج - الصناعية', 1000),
        ]

        for name, contact, phone, email, address, balance in suppliers_data:
            cur.execute("SELECT id FROM suppliers WHERE name = %s", (name,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO suppliers (name, contact_person, phone, email, address, balance, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, true, %s)
                """, (name, contact, phone, email, address, balance, datetime.now()))
                print(f"   ✅ تم إنشاء المورد: {name}")

        # ==================== 3. إنشاء العملاء ====================
        print("\n📝 جاري إنشاء العملاء...")

        customers_data = [
            ('مؤسسة الأغر للتجارة', 'شركة', '0501234567', 'الرياض - حي المروج', 0, 10000),
            ('سوبر ماركت الأمانة', 'سوبر ماركت', '0501234568', 'جدة - حي الصفا', 2500, 8000),
            ('بقالة الهدى', 'بقالة', '0501234569', 'مكة المكرمة - الشوقية', 500, 5000),
            ('هايبر ماركت العثيم', 'هايبر ماركت', '0501234570', 'الدمام - الفيصلية', 3000, 15000),
            ('مؤسسة التاج الذهبي', 'شركة', '0501234571', 'المدينة المنورة - قباء', 0, 7500),
            ('كارفور السعودية', 'هايبر ماركت', '0501234572', 'الرياض - غرناطة', 4500, 20000),
            ('دانوب', 'سوبر ماركت', '0501234573', 'جدة - التحلية', 1200, 10000),
            ('لولو هايبر ماركت', 'هايبر ماركت', '0501234574', 'الرياض - العليا', 800, 12000),
            ('بقالة الأمين', 'بقالة', '0501234575', 'الخبر - البندرية', 200, 3000),
            ('مؤسسة اليمامة', 'شركة', '0501234576', 'الرياض - اليمامة', 0, 5000),
        ]

        for name, cust_type, phone, address, balance, credit_limit in customers_data:
            cur.execute("SELECT id FROM customers WHERE name = %s", (name,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO customers (name, type, phone, address, balance, credit_limit, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, cust_type, phone, address, balance, credit_limit, datetime.now()))
                print(f"   ✅ تم إنشاء العميل: {name}")

        # ==================== 4. إنشاء المنتجات ====================
        print("\n📝 جاري إنشاء المنتجات...")

        products_data = [
            # مياه
            ('ماء قوارير 1.5 لتر', 'مياه', 'قارورة', 2.5, 3.5, 500, 50, 'المستودع أ', False, 0),
            ('ماء قوارير 5 لتر', 'مياه', 'قارورة', 5.0, 7.0, 200, 30, 'المستودع أ', False, 0),
            ('ماء قوارير 330 مل', 'مياه', 'قارورة', 1.0, 1.5, 1000, 100, 'المستودع أ', False, 0),

            # مشروبات غازية
            ('كوكاكولا 1.5 لتر', 'مشروبات غازية', 'قارورة', 4.5, 6.5, 300, 40, 'المستودع ب', False, 0),
            ('بيبسي 1.5 لتر', 'مشروبات غازية', 'قارورة', 4.5, 6.5, 280, 40, 'المستودع ب', False, 0),
            ('سفن أب 1.5 لتر', 'مشروبات غازية', 'قارورة', 4.5, 6.5, 250, 40, 'المستودع ب', False, 0),
            ('كوكاكولا علب 330 مل', 'مشروبات غازية', 'علبة', 2.0, 3.0, 800, 80, 'المستودع ب', False, 0),
            ('بيبسي علب 330 مل', 'مشروبات غازية', 'علبة', 2.0, 3.0, 750, 80, 'المستودع ب', False, 0),

            # أجبان وألبان
            ('جبنة بيضاء 500 جم', 'أجبان', 'قطعة', 12.0, 18.0, 150, 20, 'الثلاجة 1', True, 5.0),
            ('جبنة شيدر 250 جم', 'أجبان', 'قطعة', 10.0, 15.0, 120, 20, 'الثلاجة 1', True, 4.0),
            ('زبادي 200 جم', 'ألبان', 'علبة', 3.0, 4.5, 300, 40, 'الثلاجة 2', True, 1.0),
            ('حليب 1 لتر', 'ألبان', 'علبة', 5.0, 7.5, 200, 30, 'الثلاجة 2', True, 2.0),
            ('حليب بودرة 2.5 كجم', 'ألبان', 'علبة', 45.0, 65.0, 50, 10, 'المستودع ج', False, 0),

            # زيوت ومواد غذائية
            ('زيت نباتي 1.5 لتر', 'زيوت', 'قارورة', 12.0, 18.0, 200, 30, 'المستودع ج', False, 0),
            ('زيت زيتون 1 لتر', 'زيوت', 'قارورة', 25.0, 38.0, 80, 15, 'المستودع ج', False, 0),
            ('سكر 5 كجم', 'مواد غذائية', 'كيس', 15.0, 22.0, 100, 20, 'المستودع د', False, 0),
            ('أرز بسمتي 10 كجم', 'مواد غذائية', 'كيس', 45.0, 65.0, 60, 10, 'المستودع د', False, 0),
            ('طحين 5 كجم', 'مواد غذائية', 'كيس', 12.0, 18.0, 120, 20, 'المستودع د', False, 0),

            # مأكولات مجمدة
            ('خضروات مشكلة مجمدة 1 كجم', 'مجمدة', 'كيس', 8.0, 12.0, 150, 25, 'الفريزر 1', True, 3.0),
            ('دجاج مجمد 1 كجم', 'مجمدة', 'كيس', 15.0, 22.0, 100, 20, 'الفريزر 1', True, 5.0),
            ('بطاطس مقلية مجمدة 2.5 كجم', 'مجمدة', 'كيس', 18.0, 28.0, 80, 15, 'الفريزر 2', True, 6.0),
            ('سمبوسة 500 جم', 'مجمدة', 'علبة', 10.0, 15.0, 120, 20, 'الفريزر 2', True, 3.0),
            ('لحم مفروم 1 كجم', 'مجمدة', 'كيس', 25.0, 38.0, 60, 10, 'الفريزر 3', True, 8.0),
        ]

        product_ids = []
        for name, category, unit, purchase_price, selling_price, quantity, min_qty, location, is_frozen, freeze_deposit in products_data:
            cur.execute("SELECT id FROM products WHERE name = %s", (name,))
            existing = cur.fetchone()
            if not existing:
                cur.execute("""
                    INSERT INTO products (name, category, unit, purchase_price, selling_price, quantity, min_quantity, location, is_frozen, freeze_deposit, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, category, unit, purchase_price, selling_price, quantity, min_qty, location, is_frozen,
                      freeze_deposit, datetime.now()))
                product_id = cur.fetchone()[0]
                product_ids.append(product_id)
                print(f"   ✅ تم إنشاء المنتج: {name} ({quantity} قطعة)")

        # ==================== 5. إنشاء أوامر شراء تجريبية ====================
        print("\n📝 جاري إنشاء أوامر شراء تجريبية...")

        # الحصول على معرفات الموردين والمنتجات
        cur.execute("SELECT id FROM suppliers")
        supplier_ids = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT id FROM users WHERE role = 'purchase_manager'")
        purchase_user_ids = [row[0] for row in cur.fetchall()]

        for i in range(10):  # إنشاء 10 أوامر شراء تجريبية
            supplier_id = random.choice(supplier_ids) if supplier_ids else 1
            created_by = random.choice(purchase_user_ids) if purchase_user_ids else 1

            total_amount = random.uniform(500, 5000)
            paid_amount = random.uniform(0, total_amount)

            cur.execute("""
                INSERT INTO purchase_orders (supplier_id, order_date, total_amount, paid_amount, payment_type, status, notes, created_by, cash_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (supplier_id, datetime.now() - timedelta(days=random.randint(0, 30)),
                  total_amount, paid_amount, random.choice(['cash', 'credit']),
                  random.choice(['pending', 'completed']), 'طلب شراء تجريبي', created_by, 'approved'))
            purchase_id = cur.fetchone()[0]

            # إضافة عناصر للطلب
            num_items = random.randint(1, 5)
            selected_products = random.sample(product_ids, min(num_items, len(product_ids)))
            for product_id in selected_products:
                quantity = random.randint(10, 100)
                cur.execute("SELECT purchase_price FROM products WHERE id = %s", (product_id,))
                unit_price = cur.fetchone()[0]
                total_price = quantity * unit_price

                cur.execute("""
                    INSERT INTO purchase_items (purchase_order_id, product_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (purchase_id, product_id, quantity, unit_price, total_price))

        print(f"   ✅ تم إنشاء 10 أوامر شراء تجريبية")

        # ==================== 6. إنشاء أوامر بيع تجريبية ====================
        print("\n📝 جاري إنشاء أوامر بيع تجريبية...")

        cur.execute("SELECT id FROM customers")
        customer_ids = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT id FROM users WHERE role = 'sales_manager'")
        sales_user_ids = [row[0] for row in cur.fetchall()]

        for i in range(15):  # إنشاء 15 أمر بيع تجريبي
            customer_id = random.choice(customer_ids) if customer_ids else 1
            created_by = random.choice(sales_user_ids) if sales_user_ids else 1

            total_amount = random.uniform(100, 3000)
            paid_amount = random.uniform(0, total_amount)

            cur.execute("""
                INSERT INTO sale_orders (customer_id, sale_date, total_amount, paid_amount, payment_type, status, notes, created_by, cash_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (customer_id, datetime.now() - timedelta(days=random.randint(0, 30)),
                  total_amount, paid_amount, random.choice(['cash', 'credit']),
                  random.choice(['pending', 'completed']), 'طلب بيع تجريبي', created_by, 'approved'))
            sale_id = cur.fetchone()[0]

            # إضافة عناصر للطلب
            num_items = random.randint(1, 4)
            selected_products = random.sample(product_ids, min(num_items, len(product_ids)))
            for product_id in selected_products:
                quantity = random.randint(1, 20)
                cur.execute("SELECT selling_price FROM products WHERE id = %s", (product_id,))
                unit_price = cur.fetchone()[0]
                total_price = quantity * unit_price

                cur.execute("""
                    INSERT INTO sale_items (sale_order_id, product_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sale_id, product_id, quantity, unit_price, total_price))

        print(f"   ✅ تم إنشاء 15 أمر بيع تجريبي")

        # ==================== 7. إنشاء معاملات نقدية ====================
        print("\n📝 جاري إنشاء المعاملات النقدية...")

        # إنشاء صندوق نقدي رئيسي
        cur.execute("SELECT id FROM cash_boxes")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO cash_boxes (name, balance, initial_balance, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('الصندوق الرئيسي', 10000.0, 10000.0, True, datetime.now(), datetime.now()))
            print("   ✅ تم إنشاء الصندوق الرئيسي")

        # تأكيد جميع العمليات
        conn.commit()

        print("\n" + "=" * 60)
        print("🎉 تم إضافة جميع البيانات التجريبية بنجاح!")
        print("=" * 60)

        # عرض ملخص البيانات
        cur.execute("SELECT COUNT(*) FROM users")
        users_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM employees")
        employees_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM products")
        products_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM customers")
        customers_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM purchase_orders")
        purchases_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sale_orders")
        sales_count = cur.fetchone()[0]

        print(f"\n📊 ملخص البيانات:")
        print(f"   👥 المستخدمين: {users_count}")
        print(f"   👔 الموظفين: {employees_count}")
        print(f"   🏭 الموردين: {suppliers_count}")
        print(f"   📦 المنتجات: {products_count}")
        print(f"   👤 العملاء: {customers_count}")
        print(f"   🛒 أوامر الشراء: {purchases_count}")
        print(f"   🛍️ أوامر البيع: {sales_count}")

        print("\n" + "=" * 60)
        print("🔑 بيانات الدخول للمستخدمين:")
        print("-" * 40)
        for username, password, role, full_name, _, _ in users_data:
            print(f"   {username} / {password}  [{role}] - {full_name}")
        print("=" * 60)

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def get_position_name(role):
    """تحويل دور المستخدم إلى مسمى وظيفي"""
    positions = {
        'admin': 'مدير',
        'cashier': 'مسؤول صندوق',
        'store_keeper': 'أمين مخزن',
        'collector': 'محصل',
        'purchase_manager': 'مسؤول مشتريات',
        'sales_manager': 'مسؤول مبيعات'
    }
    return positions.get(role, 'موظف')


if __name__ == "__main__":
    add_demo_data()