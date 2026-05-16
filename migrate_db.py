#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تنظيف قاعدة البيانات الإنتاجية (Supabase PostgreSQL)
- حذف جميع البيانات مع الاحتفاظ بالحسابات المالية فقط
- حذف العملاء، الموردين، المنتجات
- حذف المشتريات، المبيعات، التحصيلات، سداد الموردين
- حذف القيود اليومية وحركات الحسابات المالية
- حذف حركات الصندوق
- إعادة تعيين أرصدة العملاء والموردين إلى صفر
- إعادة تعيين رصيد الصندوق إلى صفر
"""

import os
import sys
from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

# ============================================================
# رابط قاعدة البيانات (Supabase)
# ============================================================
DATABASE_URL = "postgresql://postgres.augjutrkulpmonywppju:ali1993mubark@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

# تهيئة تطبيق Flask صغير
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, FinancialAccount

db.init_app(app)

# ============================================================
# قائمة الجداول بالترتيب الصحيح للحذف (من الأبناء إلى الآباء)
# ============================================================
TABLES_IN_ORDER = [
    # أبناء الجداول الرئيسية (يجب حذفها أولاً)
    'purchase_items',  # تفاصيل المشتريات (يحتوي على foreign key إلى purchase_orders, products)
    'sale_items',  # تفاصيل المبيعات (يحتوي على foreign key إلى sale_orders, products)
    'journal_details',  # تفاصيل القيود (يحتوي على foreign key إلى journal_entries)
    'account_transactions',  # حركات الحسابات المالية
    'cash_transactions',  # حركات الصندوق
    'collections',  # التحصيلات (يحتوي على foreign key إلى customers, sale_orders)
    'supplier_payments',  # سداد الموردين (يحتوي على foreign key إلى suppliers, purchase_orders)
    'daily_cash_summaries',  # إغلاقات يومية
    'freeze_deposits',  # أمانات التجميد
    'transactions',  # المعاملات

    # الجداول الرئيسية
    'purchase_orders',  # المشتريات (يحتوي على foreign key إلى suppliers, users)
    'sale_orders',  # المبيعات (يحتوي على foreign key إلى customers, users)
    'journal_entries',  # القيود اليومية (يحتوي على foreign key إلى users)

    # الجداول الأساسية
    'products',  # المنتجات
    'suppliers',  # الموردين
    'customers',  # العملاء
    'employees',  # الموظفين
    'users',  # المستخدمين

    # الصندوق
    'cash_boxes',  # صناديق
]


# ============================================================
# الدوال المساعدة
# ============================================================

def disable_triggers():
    """تعطيل فحص القيود مؤقتاً (لـ PostgreSQL)"""
    with app.app_context():
        try:
            db.session.execute(text("SET session_replication_role = replica;"))
            db.session.commit()
            print("✅ تم تعطيل فحص القيود مؤقتاً.")
        except Exception as e:
            print(f"⚠️ لم نتمكن من تعطيل القيود: {e}")


def enable_triggers():
    """إعادة تفعيل فحص القيود"""
    with app.app_context():
        try:
            db.session.execute(text("SET session_replication_role = DEFAULT;"))
            db.session.commit()
            print("✅ تم إعادة تفعيل فحص القيود.")
        except Exception as e:
            print(f"⚠️ لم نتمكن من إعادة تفعيل القيود: {e}")


def truncate_table(table_name):
    """حذف جميع السجلات من جدول معين (باستخدام TRUNCATE)"""
    with app.app_context():
        try:
            db.session.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
            db.session.commit()
            return True
        except Exception as e:
            print(f"   ❌ فشل TRUNCATE {table_name}: {e}")
            return False


def delete_from_table(table_name):
    """حذف جميع السجلات من جدول معين (باستخدام DELETE)"""
    with app.app_context():
        try:
            deleted = db.session.execute(text(f"DELETE FROM {table_name}"))
            db.session.commit()
            return deleted.rowcount
        except Exception as e:
            print(f"   ❌ فشل DELETE {table_name}: {e}")
            return 0


def table_exists(table_name):
    """التحقق من وجود جدول"""
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        return table_name in inspector.get_table_names()


def count_records(table_name):
    """حساب عدد السجلات في جدول"""
    with app.app_context():
        try:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
        except Exception:
            return 0


def reset_sequences():
    """إعادة تعيين العدادات التلقائية (PostgreSQL)"""
    with app.app_context():
        try:
            # طريقة مبسطة لإعادة تعيين العدادات
            tables = ['suppliers', 'customers', 'products', 'purchase_orders',
                      'sale_orders', 'collections', 'supplier_payments',
                      'journal_entries', 'users']
            for table in tables:
                try:
                    db.session.execute(text(f"SELECT setval('{table}_id_seq', 1, false)"))
                except Exception:
                    pass
            db.session.commit()
            print("✅ تم إعادة تعيين العدادات التلقائية.")
        except Exception as e:
            print(f"⚠️ لم يتم إعادة تعيين العدادات: {e}")


def keep_only_admin_user():
    """الاحتفاظ بمستخدم admin فقط وحذف باقي المستخدمين"""
    with app.app_context():
        from models import User
        from werkzeug.security import generate_password_hash

        try:
            # حذف جميع المستخدمين
            db.session.execute(text("DELETE FROM users"))

            # إضافة مستخدم admin جديد
            db.session.execute(text("""
                INSERT INTO users (username, password, role, full_name, phone, email, is_active, created_at)
                VALUES ('admin', :password, 'admin', 'مدير النظام', '123456789', 'admin@thaljat.com', true, NOW())
            """), {'password': generate_password_hash('admin123')})

            db.session.commit()
            print("✅ تم الاحتفاظ بمستخدم admin فقط (كلمة المرور: admin123).")
        except Exception as e:
            print(f"⚠️ فشل تنظيف المستخدمين: {e}")


def keep_only_one_cash_box():
    """الاحتفاظ بصندوق واحد فقط وتصفير رصيده"""
    with app.app_context():
        from models import CashBox
        try:
            # حذف جميع الصناديق
            db.session.execute(text("DELETE FROM cash_boxes"))

            # إنشاء صندوق جديد
            db.session.execute(text("""
                INSERT INTO cash_boxes (name, balance, initial_balance, is_active, created_at, updated_at)
                VALUES ('الصندوق الرئيسي', 0, 0, true, NOW(), NOW())
            """))
            db.session.commit()
            print("✅ تم إنشاء صندوق رئيسي جديد برصيد صفر.")
        except Exception as e:
            print(f"⚠️ فشل تنظيف الصناديق: {e}")


def reset_accounts_balance():
    """إعادة تعيين أرصدة الحسابات المالية إلى صفر"""
    with app.app_context():
        try:
            db.session.execute(text("UPDATE financial_accounts SET balance = 0"))
            db.session.commit()
            print("✅ تم إعادة تعيين أرصدة الحسابات المالية إلى صفر.")
        except Exception as e:
            print(f"⚠️ فشل إعادة تعيين الأرصدة: {e}")


def verify_financial_accounts():
    """التحقق من وجود الحسابات المالية الأساسية"""
    with app.app_context():
        try:
            count = db.session.execute(text("SELECT COUNT(*) FROM financial_accounts")).scalar()
            print(f"📌 عدد الحسابات المالية الموجودة: {count}")

            if count == 0:
                print("⚠️ لا توجد حسابات مالية! يجب تشغيل migrate_db.py أولاً.")
                return False
            return True
        except Exception as e:
            print(f"❌ فشل التحقق من الحسابات المالية: {e}")
            return False


def run_cleanup():
    """تنفيذ عملية التنظيف"""
    print("=" * 70)
    print("🧹 تنظيف قاعدة البيانات الإنتاجية (Supabase PostgreSQL)")
    print("=" * 70)
    print("⚠️  سيتم حذف جميع البيانات التالية:")
    print("   - العملاء والموردين والمنتجات")
    print("   - المشتريات والمبيعات")
    print("   - التحصيلات وسداد الموردين")
    print("   - القيود اليومية وحركات الحسابات")
    print("   - حركات الصندوق")
    print("=" * 70)
    print("✅ سيتم الاحتفاظ بـ:")
    print("   - الحسابات المالية (أصول، خصوم، إيرادات، مصروفات)")
    print("   - مستخدم admin واحد (admin / admin123)")
    print("   - صندوق رئيسي واحد برصيد صفر")
    print("=" * 70)

    confirm = input("\n❗ هل أنت متأكد من رغبتك في حذف جميع البيانات؟ (اكتب 'نعم' للتأكيد): ").strip()
    if confirm != 'نعم':
        print("❌ تم إلغاء العملية.")
        return

    print("\n🔄 جاري التنظيف...")
    print()

    try:
        # اختبار الاتصال بقاعدة البيانات
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            print("✅ الاتصال بقاعدة البيانات ناجح.")
        print()

        # التحقق من وجود الحسابات المالية
        if not verify_financial_accounts():
            print("\n⚠️ يرجى تشغيل migrate_db.py أولاً لإضافة الحسابات المالية.")
            return

        # تعطيل فحص القيود مؤقتاً
        print("📋 0. تعطيل فحص القيود مؤقتاً...")
        disable_triggers()
        print()

        # 1. حذف البيانات من الجداول بالترتيب الصحيح
        print("📋 1. حذف البيانات من الجداول...")
        deleted_total = 0
        for table in TABLES_IN_ORDER:
            if table_exists(table):
                count = count_records(table)
                if count > 0:
                    # استخدام TRUNCATE للأطفال و DELETE للآباء
                    if table in ['purchase_items', 'sale_items', 'journal_details', 'account_transactions',
                                 'cash_transactions']:
                        if truncate_table(table):
                            deleted_total += count
                            print(f"   ✅ جدول {table}: تم حذف {count} سجل (TRUNCATE)")
                    else:
                        deleted = delete_from_table(table)
                        deleted_total += deleted
                        if deleted > 0:
                            print(f"   ✅ جدول {table}: تم حذف {deleted} سجل")
                        else:
                            print(f"   ⚠️ جدول {table}: لا توجد بيانات أو فشل الحذف")
                else:
                    print(f"   ⚠️ جدول {table}: لا توجد بيانات")

        print(f"\n   ✅ إجمالي السجلات المحذوفة: {deleted_total}")

        # 2. إعادة تفعيل فحص القيود
        print("\n📋 2. إعادة تفعيل فحص القيود...")
        enable_triggers()

        # 3. إنشاء مستخدم admin جديد
        print("\n📋 3. إعداد المستخدمين...")
        keep_only_admin_user()

        # 4. إنشاء صندوق جديد
        print("\n📋 4. إعداد الصندوق...")
        keep_only_one_cash_box()

        # 5. إعادة تعيين أرصدة الحسابات المالية
        print("\n📋 5. إعادة تعيين الأرصدة...")
        reset_accounts_balance()

        # 6. إعادة تعيين العدادات
        print("\n📋 6. إعادة تعيين العدادات...")
        reset_sequences()

        print("\n" + "=" * 70)
        print("🎉 اكتمل تنظيف قاعدة البيانات بنجاح!")
        print("=" * 70)
        print("\n📌 ما تبقى في قاعدة البيانات:")
        print("   - الحسابات المالية (12 حساباً أساسياً)")
        print("   - مستخدم admin واحد (admin / admin123)")
        print("   - صندوق رئيسي واحد برصيد صفر")
        print("\n📌 يمكنك الآن البدء من جديد بإضافة:")
        print("   - موردين جدد (سيتم إنشاء حسابات فرعية لهم تلقائياً)")
        print("   - عملاء جدد")
        print("   - منتجات جديدة")
        print("   - عمليات شراء ومبيعات")

    except Exception as e:
        print(f"\n❌ خطأ أثناء تنظيف قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ============================================================
# تشغيل الملف
# ============================================================
if __name__ == "__main__":
    run_cleanup()