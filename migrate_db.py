import sqlite3
from datetime import datetime

# مسار قاعدة البيانات المحلية
DB_PATH = r'D:\ghith\alsalif\instance\thaljat_alsaleef.db'


def update_customer_balance():
    """تحديث رصيد العميل بناءً على الفاتورة رقم 1"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        print("=" * 60)
        print("💰 تحديث رصيد العميل - مطعم الرشيد")
        print("=" * 60)

        # 1. جلب معلومات الفاتورة
        print("\n📋 1. جلب معلومات الفاتورة...")
        cur.execute("""
            SELECT id, customer_id, total_amount, paid_amount, payment_type, status
            FROM sale_orders 
            WHERE id = 1
        """)
        sale = cur.fetchone()

        if sale:
            print(f"   ✅ الفاتورة رقم 1:")
            print(f"      - المبلغ الإجمالي: {sale['total_amount']:,.2f} ريال")
            print(f"      - المدفوع: {sale['paid_amount']:,.2f} ريال")
            print(f"      - المتبقي: {sale['total_amount'] - sale['paid_amount']:,.2f} ريال")

            remaining = sale['total_amount'] - sale['paid_amount']
            customer_id = sale['customer_id']

            # 2. تحديث رصيد العميل مباشرة
            print(f"\n💰 2. تحديث رصيد العميل...")
            cur.execute("""
                UPDATE customers 
                SET balance = ?,
                    credit_limit = 50000
                WHERE id = ?
            """, (remaining, customer_id))

            print(f"   ✅ تم تحديث رصيد العميل إلى {remaining:,.2f} ريال")

            # 3. التحقق من التحديث
            cur.execute("""
                SELECT id, name, balance, phone, credit_limit 
                FROM customers 
                WHERE id = ?
            """, (customer_id,))
            customer = cur.fetchone()

            print(f"\n📊 3. بيانات العميل بعد التحديث:")
            print(f"   👤 اسم العميل: {customer['name']}")
            print(f"   💰 المديونية: {customer['balance']:,.2f} ريال")
            print(f"   📞 الهاتف: {customer['phone']}")
            print(f"   💳 الحد الائتماني: {customer['credit_limit']:,.2f} ريال")

            # 4. التأكد من أن الفاتورة مكتملة
            print(f"\n✅ 4. التأكد من حالة الفاتورة...")
            cur.execute("""
                UPDATE sale_orders 
                SET status = 'completed',
                    cash_status = 'approved'
                WHERE id = 1
            """)
            print(f"   ✅ الفاتورة مكتملة ومعتمدة")

            conn.commit()

            print("\n" + "=" * 60)
            print("🎉 تم تحديث رصيد العميل بنجاح!")
            print("⚠️ الآن أعد تشغيل التطبيق المحلي وافتح صفحة التحصيل")
            print("=" * 60)

        else:
            print("   ❌ الفاتورة رقم 1 غير موجودة!")

        conn.close()

    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()


def show_all_debtors():
    """عرض جميع العملاء المدينين"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        print("\n" + "=" * 60)
        print("📋 قائمة العملاء المدينين بعد التحديث")
        print("=" * 60)

        cur.execute("""
            SELECT id, name, balance, phone, credit_limit
            FROM customers 
            WHERE balance > 0
            ORDER BY balance DESC
        """)

        debtors = cur.fetchall()

        if debtors:
            for debtor in debtors:
                print(f"\n   🏪 {debtor['name']}")
                print(f"      💰 المديونية: {debtor['balance']:,.2f} ريال")
                print(f"      📞 الهاتف: {debtor['phone'] or '-'}")
        else:
            print("\n   ⚠️ لا يوجد عملاء مدينين")

        conn.close()

    except Exception as e:
        print(f"❌ خطأ: {e}")


if __name__ == "__main__":
    # تحديث الرصيد
    update_customer_balance()

    # عرض النتيجة
    show_all_debtors()