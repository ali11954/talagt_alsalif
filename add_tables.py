import psycopg2
from datetime import datetime, timedelta
import random

DATABASE_URL = "postgresql://postgres.augjutrkulpmonywppju:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"


def redistribute_purchases():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("✅ تم الاتصال بقاعدة البيانات")
        print("=" * 60)

        # حذف المشتريات القديمة
        cur.execute("DELETE FROM purchase_items")
        cur.execute("DELETE FROM purchase_orders")
        print("✅ تم حذف المشتريات القديمة")

        # الحصول على معرفات المستخدمين
        cur.execute("SELECT id FROM users LIMIT 1")
        user_id = cur.fetchone()[0]

        # ==================== تعريف المنتجات مع مورديها ====================
        print("\n📝 جاري إنشاء أوامر شراء لكل مورد...")

        # بيانات المنتجات مع الموردين المناسبين
        products_with_suppliers = [
            # شركة شملان للمياه - منتجات شملان
            ('شركة شملان للمياه', [
                ('مياه شملان 750 مل', 100, 150, 1000),
                ('مياه شملان 1.5 لتر', 150, 220, 600),
            ]),

            # شركة اليمن للمياه - منتجات اليمن
            ('شركة اليمن للمياه', [
                ('مياه اليمن 750 مل', 90, 130, 800),
            ]),

            # شركة بركت للمياه - منتجات بركت
            ('شركة بركت للمياه', [
                ('مياه بركت 750 مل', 95, 140, 700),
            ]),

            # مصنع ثلج الصليف - مياه الصليف
            ('مصنع ثلج الصليف', [
                ('مياه الصليف 750 مل', 100, 150, 500),
            ]),

            # شركة كوكاكولا اليمن - منتجات كوكاكولا
            ('شركة كوكاكولا اليمن', [
                ('كوكاكولا 330 مل', 180, 250, 800),
                ('كوكاكولا 1 لتر', 350, 500, 500),
                ('كوكاكولا 1.5 لتر', 450, 650, 400),
                ('سبرايت 330 مل', 170, 240, 550),
                ('فانتا 330 مل', 170, 240, 450),
            ]),

            # شركة بيبسي كولا - منتجات بيبسي
            ('شركة بيبسي كولا', [
                ('بيبسي 330 مل', 170, 240, 700),
                ('بيبسي 1 لتر', 340, 480, 450),
                ('سفن أب 330 مل', 170, 240, 600),
                ('ميرندا 330 مل', 170, 240, 500),
            ]),

            # شركة المرطبات اليمنية - يمني كولا
            ('شركة المرطبات اليمنية', [
                ('يمني كولا 330 مل', 150, 210, 600),
                ('ريد بول 250 مل', 400, 600, 200),
            ]),
        ]

        purchase_ids = []
        total_all = 0

        for supplier_name, products in products_with_suppliers:
            # الحصول على معرف المورد
            cur.execute("SELECT id FROM suppliers WHERE name = %s", (supplier_name,))
            supplier_row = cur.fetchone()

            if not supplier_row:
                print(f"   ⚠️ المورد غير موجود: {supplier_name}")
                continue

            supplier_id = supplier_row[0]

            # حساب المبلغ الإجمالي لهذا المورد
            total_amount = sum(qty * price for _, price, _, qty in products)
            total_all += total_amount

            # إنشاء أمر شراء للمورد
            order_date = datetime.now() - timedelta(days=random.randint(1, 20))

            cur.execute("""
                INSERT INTO purchase_orders 
                (supplier_id, order_date, total_amount, paid_amount, payment_type, status, notes, created_by, cash_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (supplier_id, order_date, total_amount, total_amount, 'cash', 'completed',
                  f'أمر شراء من {supplier_name}', user_id, 'approved'))

            purchase_id = cur.fetchone()[0]
            purchase_ids.append(purchase_id)

            print(f"\n   🏭 {supplier_name}:")
            print(f"      🆔 أمر شراء رقم {purchase_id}")
            print(f"      💰 الإجمالي: {total_amount:,.2f} ريال")

            # إضافة منتجات هذا المورد
            for product_name, purchase_price, selling_price, quantity in products:
                # تحديث سعر المنتج
                cur.execute("""
                    UPDATE products 
                    SET purchase_price = %s, selling_price = %s
                    WHERE name = %s
                """, (purchase_price, selling_price, product_name))

                # الحصول على معرف المنتج
                cur.execute("SELECT id FROM products WHERE name = %s", (product_name,))
                product_row = cur.fetchone()

                if product_row:
                    product_id = product_row[0]
                    total_price = quantity * purchase_price

                    cur.execute("""
                        INSERT INTO purchase_items 
                        (purchase_order_id, product_id, quantity, unit_price, total_price)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (purchase_id, product_id, quantity, purchase_price, total_price))

                    print(f"      ✅ {product_name}: {quantity} قطعة × {purchase_price} = {total_price:,.2f} ريال")

        conn.commit()

        print("\n" + "=" * 60)
        print("🎉 تم إعادة توزيع المشتريات على الموردين!")
        print(f"📊 إجمالي أوامر الشراء: {len(purchase_ids)}")
        print(f"💰 إجمالي قيمة المخزون: {total_all:,.2f} ريال")
        print("=" * 60)

        # عرض ملخص أوامر الشراء
        print("\n📋 قائمة أوامر الشراء:")
        cur.execute("""
            SELECT po.id, s.name, po.total_amount, po.order_date
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            ORDER BY po.order_date DESC
        """)

        for po_id, supplier_name, amount, order_date in cur.fetchall():
            print(f"   🧾 رقم {po_id}: {supplier_name} - {amount:,.2f} ريال - {order_date.strftime('%Y-%m-%d')}")

        cur.close()
        conn.close()

        print("\n✅ تم الانتهاء! افتح صفحة المشتريات الآن وسترى جميع أوامر الشراء")

    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    redistribute_purchases()