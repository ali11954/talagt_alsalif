# accounting_utils.py
import sqlite3
from datetime import datetime
import traceback

from models import db, JournalEntry, JournalDetail, AccountTransaction, FinancialAccount

DB_PATH = r'D:\ghith\alsalif\instance\thaljat_alsaleef.db'


# ============================================================
# أدوات جلب معلومات الحسابات
# ============================================================

def get_financial_account_by_code(account_code):
    """إرجاع كائن FinancialAccount من كود الحساب"""
    return FinancialAccount.query.filter_by(account_code=account_code).first()

def get_financial_account_by_id(account_id):
    """إرجاع كائن FinancialAccount من المعرف"""
    return db.session.get(FinancialAccount, account_id)

# دوال التوافق القديمة (يمكن الاحتفاظ بها للاستخدام القديم)
def get_account_info_by_code(account_code):
    """إرجاع (id, account_name, account_type) فقط (بدون balance)"""
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
    """إرجاع (id, account_name, account_type) من معرف الحساب"""
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

def get_account_code_by_id(account_id):
    """إرجاع كود الحساب من المعرف"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT account_code FROM financial_accounts WHERE id = ?",
            (account_id,)
        )
        result = cur.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"❌ خطأ في get_account_code_by_id: {e}")
        return None

def get_account_id_by_code(account_code):
    """إرجاع معرف الحساب من الكود"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM financial_accounts WHERE account_code = ?",
            (account_code,)
        )
        result = cur.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"❌ خطأ في get_account_id_by_code: {e}")
        return None

def get_account_balance(account_code):
    """إرجاع رصيد حساب معين"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT balance FROM financial_accounts WHERE account_code = ?",
            (account_code,)
        )
        result = cur.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"❌ خطأ في get_account_balance: {e}")
        return 0

def get_all_accounts_balances():
    """إرجاع أرصدة جميع الحسابات"""
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
    """إرجاع account_id الخاص بالعميل إن وجد"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM customers WHERE id = ?", (customer_id,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    except Exception as e:
        print(f"❌ خطأ في get_customer_account_id: {e}")
        return None

def get_supplier_account_id(supplier_id):
    """إرجاع account_id الخاص بالمورد إن وجد"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM suppliers WHERE id = ?", (supplier_id,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result and result[0] else None
    except Exception as e:
        print(f"❌ خطأ في get_supplier_account_id: {e}")
        return None

def get_customer_posting_account_code(customer_id):
    """كود الحساب المستخدم في قيود العميل، مع الرجوع للحساب العام 1004"""
    account_id = get_customer_account_id(customer_id)
    if account_id:
        code = get_account_code_by_id(account_id)
        if code:
            return code
    return '1004'

def get_supplier_posting_account_code(supplier_id):
    """كود الحساب المستخدم في قيود المورد، مع الرجوع للحساب العام 2001"""
    account_id = get_supplier_account_id(supplier_id)
    if account_id:
        code = get_account_code_by_id(account_id)
        if code:
            return code
    return '2001'


# ============================================================
# دالة مركزية لتحديث الرصيد حسب نوع الحساب
# ============================================================

def update_balance(account, transaction_type, amount):
    """
    تحديث رصيد الحساب وفقاً لنوع الحساب (asset, liability, equity, revenue, expense)
    """
    if not account:
        return

    current = float(account.balance or 0)
    amt = float(amount or 0)
    acc_type = account.account_type

    if acc_type in ['asset', 'expense']:
        if transaction_type == 'debit':
            account.balance = current + amt
        else:
            account.balance = current - amt
    elif acc_type in ['liability', 'equity', 'revenue']:
        if transaction_type == 'credit':
            account.balance = current + amt
        else:
            account.balance = current - amt
    else:
        if transaction_type == 'debit':
            account.balance = current + amt
        else:
            account.balance = current - amt


# ============================================================
# إنشاء القيود اليومية باستخدام SQLAlchemy
# ============================================================

def create_journal_entry(reference_number, description, debit_account, credit_account, amount, user_id):
    """
    debit_account, credit_account: كائنات FinancialAccount
    """
    now = datetime.utcnow()
    try:
        entry = JournalEntry(
            entry_date=now,
            reference_number=reference_number,
            description=description,
            total_debit=amount,
            total_credit=amount,
            is_posted=True,
            created_by=user_id,
            created_at=now
        )
        db.session.add(entry)
        db.session.flush()

        db.session.add(JournalDetail(
            entry_id=entry.id,
            account_type=debit_account.account_type,
            account_id=debit_account.id,
            account_name=debit_account.account_name,
            debit=amount,
            credit=0,
            notes=''
        ))

        db.session.add(JournalDetail(
            entry_id=entry.id,
            account_type=credit_account.account_type,
            account_id=credit_account.id,
            account_name=credit_account.account_name,
            debit=0,
            credit=amount,
            notes=''
        ))

        db.session.add(AccountTransaction(
            account_id=debit_account.id,
            transaction_type='debit',
            amount=amount,
            reference_type='journal',
            reference_id=entry.id,
            transaction_date=now,
            description=f"(مدين) {description}",
            created_by=user_id,
            created_at=now
        ))

        db.session.add(AccountTransaction(
            account_id=credit_account.id,
            transaction_type='credit',
            amount=amount,
            reference_type='journal',
            reference_id=entry.id,
            transaction_date=now,
            description=f"(دائن) {description}",
            created_by=user_id,
            created_at=now
        ))

        if debit_account:
            update_balance(debit_account, 'debit', amount)
        if credit_account:
            update_balance(credit_account, 'credit', amount)

        db.session.commit()
        print(f"✅ تم إنشاء قيد {reference_number}: {description} - {amount:,.2f} ريال")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في create_journal_entry: {e}")
        traceback.print_exc()
        return False


def create_account_transaction(account_id, transaction_type, amount, reference_type, reference_id, description, user_id, update_balance_flag=True):
    """إنشاء حركة حسابية في account_transactions وتحديث رصيد financial_accounts اختياريًا"""
    now = datetime.utcnow()

    try:
        db.session.add(AccountTransaction(
            account_id=account_id,
            transaction_type=transaction_type,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            transaction_date=now,
            description=description,
            created_by=user_id,
            created_at=now
        ))

        if update_balance_flag:
            account = db.session.get(FinancialAccount, account_id)
            if account:
                update_balance(account, transaction_type, amount)

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في create_account_transaction: {e}")
        traceback.print_exc()
        return False


def create_double_entry(account_debit_code, account_credit_code, amount, reference_type, reference_id, description, user_id):
    debit_account = get_financial_account_by_code(account_debit_code)
    credit_account = get_financial_account_by_code(account_credit_code)
    if not debit_account or not credit_account:
        print(f"❌ خطأ: الحسابات غير موجودة - مدين: {account_debit_code}, دائن: {account_credit_code}")
        return False
    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return create_journal_entry(ref_num, description, debit_account, credit_account, amount, user_id)


# ============================================================
# دوال خاصة بالعملاء والموردين
# ============================================================

def create_customer_double_entry(customer_id, account_credit_code, amount, reference_type, reference_id, description, user_id):
    customer_code = get_customer_posting_account_code(customer_id)
    debit_account = get_financial_account_by_code(customer_code)
    credit_account = get_financial_account_by_code(account_credit_code)
    if not debit_account or not credit_account:
        print(f"❌ خطأ: حساب العميل ({customer_code}) أو حساب الدائن ({account_credit_code}) غير موجود")
        return False
    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return create_journal_entry(ref_num, description, debit_account, credit_account, amount, user_id)


def create_supplier_double_entry(supplier_id, account_debit_code, amount, reference_type, reference_id, description, user_id):
    supplier_code = get_supplier_posting_account_code(supplier_id)
    debit_account = get_financial_account_by_code(account_debit_code)
    credit_account = get_financial_account_by_code(supplier_code)
    if not debit_account or not credit_account:
        print(f"❌ خطأ: حساب المدين ({account_debit_code}) أو حساب المورد ({supplier_code}) غير موجود")
        return False
    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return create_journal_entry(ref_num, description, debit_account, credit_account, amount, user_id)


def create_supplier_payment_entry(supplier_id, amount, reference_type, reference_id, description, user_id):
    supplier_code = get_supplier_posting_account_code(supplier_id)
    debit_account = get_financial_account_by_code(supplier_code)
    credit_account = get_financial_account_by_code('1001')
    if not debit_account or not credit_account:
        print("❌ خطأ: حساب المورد أو الصندوق غير موجود")
        return False
    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return create_journal_entry(ref_num, description, debit_account, credit_account, amount, user_id)


def create_customer_collection_entry(customer_id, amount, reference_type, reference_id, description, user_id):
    customer_code = get_customer_posting_account_code(customer_id)
    debit_account = get_financial_account_by_code('1001')
    credit_account = get_financial_account_by_code(customer_code)
    if not debit_account or not credit_account:
        print("❌ خطأ: حساب الصندوق أو حساب العميل غير موجود")
        return False
    ref_num = f"{reference_type.upper()}-{reference_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return create_journal_entry(ref_num, description, debit_account, credit_account, amount, user_id)


# ============================================================
# دوال مساعدة للتحقق والصيانة
# ============================================================

def get_journal_entries_count():
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
    debit, credit = get_journal_total()
    return (debit or 0) == (credit or 0)