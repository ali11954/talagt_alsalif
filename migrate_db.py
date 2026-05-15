import sqlite3

DB_PATH = r'D:\ghith\alsalif\instance\thaljat_alsaleef.db'


def fix_wrong_reference():
    """تصحيح المرجع الخاطئ للقيد"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        print("=" * 80)
        print("🔧 تصحيح المرجع الخاطئ للقيد")
        print("=" * 80)

        # البحث عن القيد
        cur.execute("""
            SELECT id, reference_number, description, total_debit
            FROM journal_entries
            WHERE reference_number = 'PAY-20260514-003'
        """)

        entry = cur.fetchone()

        if entry:
            entry_id, old_ref, description, amount = entry
            print(f"\n📋 القيد الحالي:")
            print(f"   ID: {entry_id}")
            print(f"   رقم الإذن: {old_ref}")
            print(f"   البيان: {description}")
            print(f"   المبلغ: {amount:,.2f} ريال")

            # تغيير رقم الإذن إلى COL بدلاً من PAY
            new_ref = old_ref.replace('PAY', 'COL')

            cur.execute("""
                UPDATE journal_entries 
                SET reference_number = ?
                WHERE id = ?
            """, (new_ref, entry_id))

            print(f"\n✅ تم تغيير رقم الإذن إلى: {new_ref}")

            conn.commit()
        else:
            print("\n   ⚠️ لم يتم العثور على القيد")

        # عرض الإحصائيات بعد التصحيح
        print("\n📊 الإحصائيات بعد التصحيح:")

        cur.execute("SELECT COUNT(*), SUM(total_debit) FROM journal_entries WHERE reference_number LIKE 'PAY-%'")
        pay_count, pay_total = cur.fetchone()
        pay_total = pay_total or 0

        cur.execute("SELECT COUNT(*), SUM(total_debit) FROM journal_entries WHERE reference_number LIKE 'COL-%'")
        col_count, col_total = cur.fetchone()
        col_total = col_total or 0

        print(f"\n   💰 قيود PAY (مدفوعات موردين): {pay_count} قيد - {pay_total:,.2f} ريال")
        print(f"   💰 قيود COL (تحصيلات): {col_count} قيد - {col_total:,.2f} ريال")

        conn.close()

        print("\n" + "=" * 80)
        print("🎉 تم تصحيح المرجع بنجاح!")

    except Exception as e:
        print(f"❌ خطأ: {e}")


if __name__ == "__main__":
    fix_wrong_reference()