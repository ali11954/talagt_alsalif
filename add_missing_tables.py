# -*- coding: utf-8 -*-
import sqlite3
import os

# التأكد من وجود ملف قاعدة البيانات
if not os.path.exists('thaljat_alsaleef.db'):
    print("❌ ملف قاعدة البيانات غير موجود!")
    print("يرجى تشغيل python app.py أولاً لإنشاء قاعدة البيانات")
    exit(1)

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('thaljat_alsaleef.db')
cursor = conn.cursor()

# إنشاء جدول المعاملات النقدية
cursor.execute('''
CREATE TABLE IF NOT EXISTS cash_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(20),
    amount FLOAT NOT NULL,
    description VARCHAR(200),
    reference_type VARCHAR(50),
    reference_id INTEGER,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
)
''')

# إنشاء جدول صناديق النقدية
cursor.execute('''
CREATE TABLE IF NOT EXISTS cash_boxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL DEFAULT 'الصندوق الرئيسي',
    balance FLOAT DEFAULT 0,
    initial_balance FLOAT DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# إنشاء جدول قيود اليومية
cursor.execute('''
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    reference_number VARCHAR(50) UNIQUE,
    description VARCHAR(200) NOT NULL,
    total_debit FLOAT DEFAULT 0,
    total_credit FLOAT DEFAULT 0,
    is_posted BOOLEAN DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# إنشاء جدول تفاصيل القيد
cursor.execute('''
CREATE TABLE IF NOT EXISTS journal_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL REFERENCES journal_entries(id),
    account_type VARCHAR(50) NOT NULL,
    account_id INTEGER,
    account_name VARCHAR(100),
    debit FLOAT DEFAULT 0,
    credit FLOAT DEFAULT 0,
    notes VARCHAR(200)
)
''')

# إنشاء جدول الملخص اليومي
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_cash_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    opening_balance FLOAT DEFAULT 0,
    closing_balance FLOAT DEFAULT 0,
    total_income FLOAT DEFAULT 0,
    total_expense FLOAT DEFAULT 0,
    cash_sales FLOAT DEFAULT 0,
    credit_sales FLOAT DEFAULT 0,
    collections FLOAT DEFAULT 0,
    purchases FLOAT DEFAULT 0,
    deposits FLOAT DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# إضافة الصندوق الرئيسي إذا لم يكن موجوداً
cursor.execute('''
INSERT OR IGNORE INTO cash_boxes (name, balance, initial_balance, is_active)
VALUES ('الصندوق الرئيسي', 0, 0, 1)
''')

# إنشاء فهارس لتحسين الأداء
cursor.execute('CREATE INDEX IF NOT EXISTS idx_cash_transactions_date ON cash_transactions(transaction_date)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_details_entry ON journal_details(entry_id)')

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("=" * 50)
print("✅ تم إنشاء الجداول المفقودة بنجاح!")
print("-" * 50)
print("الجداول التي تم إنشاؤها:")
print("1. cash_transactions")
print("2. cash_boxes")
print("3. journal_entries")
print("4. journal_details")
print("5. daily_cash_summaries")
print("=" * 50)