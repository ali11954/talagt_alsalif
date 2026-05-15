# accounting_utils.py
import sqlite3
from datetime import datetime

DB_PATH = r'D:\ghith\alsalif\instance\thaljat_alsaleef.db'


# ============================================================
# أدوات جلب معلومات الحسابات
# ============================================================

def get_account_info_by_code(account_code):
    """الحصول على معلومات الحساب كاملة (id, name, type) من كود الحساب"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, account_name, account_type FROM financial_accounts WHERE account_code = ?",
            (account_code,)
        )
        result = cur.fetchone()
        conn.close()
        return result if result else None
    except Exception as e:
        print(f"❌ خطأ في get_account_info_by_code: {e}")
        return None


def get_account_info_by_id(account_id):
    """الحصول على معلومات الحساب كاملة (id, name, type) من معرف الحساب"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, account_name, account_type FROM financial_accounts WHERE id = ?",
            (account_id,)
        )
        result = cur.fetchone()
        conn.close()
        return result if result else None
    except Exception as e:
        print(f"❌ خطأ في get_account_info_by_id: {e}")
        return None


def get_account_id_by_code(account_code):
    """الحصول على معرف الحساب من الكود"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id FROM financial_accounts WHERE account_code = ?", (account_code,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"❌ خطأ في get_account_id_by_code: {e}")
        return None


def get_account_balance(account_code):
    """الحصول على رصيد حساب معين"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT balance FROM financial_accounts WHERE account_code = ?", (account_code,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"❌ خطأ في get_account_balance: {e}")
        return 0


def get_all_accounts_balances():
    """الحصول على أرصدة جميع الحسابات"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT account_code, account_name, account_type, balance
            FROM financial_accounts
            WHERE is_active = 1
            ORDER BY account_code
        """)
        results = cur.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"❌ خطأ في get_all_accounts_balances: {e}")
        return []


def get_customer_account_id(customer_id):
    """الحصول على معرف حساب العميل من جدول العملاء"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM customers WHERE id = ?", (customer_id,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result and result[0] else get_account_id_by_code('1004')
    except Exception as e:
        print(f"❌ خطأ في get_customer_account_id: {e}")
        return get_account_id_by_code('1004')


def get_supplier_account_id(supplier_id):
    """الحصول على معرف حساب المورد من جدول الموردين"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM suppliers WHERE id = ?", (supplier_id,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result and result[0] else get_account_id_by_code('2001')
    except Exception as e:
        print(f"❌ خطأ في get_supplier_account_id: {e}")
        return get_account_id_by_code('2001')


# ============================================================
# إنشاء القيود اليومية
# ============================================================

def create_journal_entry(reference_number, description, debit_account_info, credit_account_info, amount, user_id):
    """
    إنشاء قيد يومية كامل مع تفاصيله في journal_entries و journal_details

    Args:
        reference_number: رقم الإذن (مثل PUR-001, SAL-001)
        description: وصف القيد
        debit_account_info: (account_id, account_name, account_type) للحساب المدين
        credit_account_info: (account_id, account_name, account_type) للحساب الدائن
        amount: المبلغ
        user_id: معرف المستخدم المنشئ
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        debit_id, debit_name, debit_type = debit_account_info
        credit_id, credit_name, credit_type = credit_account_info

        now = datetime.now()

        # إنشاء القيد الرئيسي
        cur.execute("""
            INSERT INTO journal_entries
            (entry_date, reference_number, description, total_debit, total_credit, is_posted, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """, (now, reference_number, description, amount, amount, user_id, now))

        entry_id = cur.lastrowid

        # إضافة تفصيلة المدين
        cur.execute("""
            INSERT INTO journal_details
            (entry_id, account_type, account_id, account_name, debit, credit, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, debit_type, debit_id, debit_name, amount, 0, ''))

        # إضافة تفصيلة الدائن
        cur.execute("""
            INSERT INTO journal_details
            (entry_id, account_type, account_id, account_name, debit, credit, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, credit_type, credit_id, credit_name, 0, amount, ''))

        # تحديث أرصدة الحسابات المالية
        cur.execute("UPDATE financial_accounts SET balance = balance + ? WHERE id = ?", (amount, debit_id))
        cur.execute("UPDATE financial_accounts SET balance = balance - ? WHERE id = ?", (amount, credit_id))

        conn.commit()
        conn.close()

        print(f"✅ تم إنشاء قيد {reference_number}: {description} - {amount:,.2f} ريال")
        return True

    except Exception as e:
        print(f"❌ خطأ في create_journal_entry: {e}")
        return False

def create_account_transaction(account_id, transaction_type, amount, reference_type, reference_id, description, user_id, update_balance=True):
    """إنشاء حركة حسابية في account_transactions وتحديث رصيد financial_accounts اختياريًا"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now = datetime.now()

        cur.execute("""
            INSERT INTO account_transactions
            (account_id, transaction_type, amount, reference_type, reference_id, transaction_date, description, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (account_id, transaction_type, amount, reference_type, reference_id, now, description, user_id, now))

        if update_balance:
            if transaction_type == 'debit':
                cur.execute("UPDATE financial_accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
            else:
                cur.execute("UPDATE financial_accounts SET balance = balance - ? WHERE id = ?", (amount, account_id))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ خطأ في create_account_transaction: {e}")
        return False

def create_double_entry(account_debit_code, account_credit_code, amount, reference_type, reference_id, description, user_id):
    """
    إنشاء قيد مزدوج كامل (مدين/دائن)
    - يسجل في journal_entries و journal_details
    - يسجل في account_transactions
    - يحدث أرصدة financial_accounts مرة واحدة فقط
    """
    debit_info = get_account_info_by_code(account_debit_code)
    credit_info = get_account_info_by_code(account_credit_code)

    if not debit_info or not credit_info:
        print(f"❌ خطأ: الحسابات غير موجودة - مدين: {account_debit_code}, دائن: {account_credit_code}")
        return False

    debit_id, debit_name, debit_type = debit_info
    credit_id, credit_name, credit_type = credit_info

    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # ============================================================
    # 1) تسجيل القيد في journal_entries و journal_details
    # ============================================================
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now = datetime.now()

        cur.execute("""
            INSERT INTO journal_entries
            (entry_date, reference_number, description, total_debit, total_credit, is_posted, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """, (now, ref_num, description, amount, amount, user_id, now))

        entry_id = cur.lastrowid

        cur.execute("""
            INSERT INTO journal_details
            (entry_id, account_type, account_id, account_name, debit, credit, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, debit_type, debit_id, debit_name, amount, 0, ''))

        cur.execute("""
            INSERT INTO journal_details
            (entry_id, account_type, account_id, account_name, debit, credit, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, credit_type, credit_id, credit_name, 0, amount, ''))

        conn.commit()
        conn.close()

        print(f"✅ تم إنشاء قيد {ref_num}: {description}")

    except Exception as e:
        print(f"❌ خطأ في إنشاء القيد: {e}")
        return False

    # ============================================================
    # 2) تسجيل الحركات في account_transactions
    #    بدون تحديث الرصيد هنا حتى لا يتكرر التحديث
    # ============================================================
    ok1 = create_account_transaction(
        debit_id, 'debit', amount, reference_type, reference_id,
        f"(مدين) {description}", user_id,
        update_balance=False
    )
    ok2 = create_account_transaction(
        credit_id, 'credit', amount, reference_type, reference_id,
        f"(دائن) {description}", user_id,
        update_balance=False
    )

    # ============================================================
    # 3) تحديث الرصيد مرة واحدة فقط
    # ============================================================
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "UPDATE financial_accounts SET balance = balance + ? WHERE id = ?",
            (amount, debit_id)
        )
        cur.execute(
            "UPDATE financial_accounts SET balance = balance - ? WHERE id = ?",
            (amount, credit_id)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"❌ خطأ في تحديث الأرصدة: {e}")
        return False

    return ok1 and ok2
# ============================================================
# دوال خاصة بالعملاء
# ============================================================

def create_customer_double_entry(customer_id, account_credit_code, amount, reference_type, reference_id, description, user_id):
    """إنشاء قيد مع حساب العميل (مدين) وحساب عام (دائن)"""
    customer_account_id = get_customer_account_id(customer_id)
    customer_info = get_account_info_by_id(customer_account_id)

    if not customer_info:
        customer_info = get_account_info_by_code('1004')

    credit_info = get_account_info_by_code(account_credit_code)

    if not customer_info or not credit_info:
        print(f"❌ خطأ: حسابات غير موجودة - عميل: {customer_id}, حساب دائن: {account_credit_code}")
        return False

    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    description_full = f"{description} (حساب عميل)"

    return create_journal_entry(ref_num, description_full, customer_info, credit_info, amount, user_id)


# ============================================================
# دوال خاصة بالموردين
# ============================================================

def create_supplier_double_entry(supplier_id, account_debit_code, amount, reference_type, reference_id, description, user_id):
    """إنشاء قيد مع حساب المورد (دائن) وحساب عام (مدين)"""
    supplier_account_id = get_supplier_account_id(supplier_id)
    supplier_info = get_account_info_by_id(supplier_account_id)

    if not supplier_info:
        supplier_info = get_account_info_by_code('2001')

    debit_info = get_account_info_by_code(account_debit_code)

    if not supplier_info or not debit_info:
        print(f"❌ خطأ: حسابات غير موجودة - مورد: {supplier_id}, حساب مدين: {account_debit_code}")
        return False

    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    description_full = f"{description} (حساب مورد)"

    return create_journal_entry(ref_num, description_full, debit_info, supplier_info, amount, user_id)


# ============================================================
# دوال مساعدة للتحقق والصيانة
# ============================================================

def get_journal_entries_count():
    """الحصول على عدد القيود المسجلة"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM journal_entries")
        result = cur.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"❌ خطأ في get_journal_entries_count: {e}")
        return 0


def get_journal_total():
    """الحصول على إجمالي المدين والدائن في القيود"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT SUM(total_debit), SUM(total_credit) FROM journal_entries")
        result = cur.fetchone()
        conn.close()
        return result if result else (0, 0)
    except Exception as e:
        print(f"❌ خطأ في get_journal_total: {e}")
        return (0, 0)


def is_balanced():
    """التحقق من توازن القيود"""
    debit, credit = get_journal_total()
    debit = debit or 0
    credit = credit or 0
    return debit == credit