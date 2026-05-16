#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إضافة الحسابات المالية الأساسية إلى قاعدة بيانات فارغة.
يعمل هذا السكريبت على إنشاء الجداول (إذا لم تكن موجودة) ثم إدراج الحسابات المطلوبة.
"""

import os
from flask import Flask
from models import db, FinancialAccount

# تهيئة تطبيق Flask صغير
app = Flask(__name__)
# استخدم نفس مسار قاعدة البيانات الموجود في app.py
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'thaljat_alsaleef.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# التأكد من وجود مجلد instance
instance_dir = os.path.join(basedir, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)
    print(f"✅ تم إنشاء مجلد {instance_dir}")

db.init_app(app)

# قائمة الحسابات المالية الأساسية
ACCOUNTS = [
    # الأصول (Assets)
    {'code': '1001', 'name': 'الصندوق', 'type': 'asset', 'balance': 0},
    {'code': '1002', 'name': 'البنك', 'type': 'asset', 'balance': 0},
    {'code': '1003', 'name': 'المخزون', 'type': 'asset', 'balance': 0},
    {'code': '1004', 'name': 'مديونية العملاء (حساب عام)', 'type': 'asset', 'balance': 0},
    {'code': '1005', 'name': 'أصول ثابتة', 'type': 'asset', 'balance': 0},

    # الخصوم (Liabilities)
    {'code': '2001', 'name': 'مديونية الموردين (حساب عام)', 'type': 'liability', 'balance': 0},
    {'code': '2002', 'name': 'قروض وسلف', 'type': 'liability', 'balance': 0},

    # حقوق الملكية (Equity)
    {'code': '3001', 'name': 'رأس المال', 'type': 'equity', 'balance': 0},
    {'code': '3002', 'name': 'أرباح محتجزة', 'type': 'equity', 'balance': 0},

    # الإيرادات (Revenue)
    {'code': '4001', 'name': 'إيرادات المبيعات', 'type': 'revenue', 'balance': 0},

    # المصروفات (Expenses)
    {'code': '5001', 'name': 'تكلفة البضاعة المباعة', 'type': 'expense', 'balance': 0},
    {'code': '5002', 'name': 'مصاريف تشغيلية', 'type': 'expense', 'balance': 0},
]


def seed_accounts():
    with app.app_context():
        # إنشاء الجداول إذا لم تكن موجودة (لأول مرة)
        db.create_all()
        print("✅ تم التأكد من وجود جميع الجداول.")

        # إضافة الحسابات إذا لم تكن موجودة مسبقاً
        for acc in ACCOUNTS:
            existing = FinancialAccount.query.filter_by(account_code=acc['code']).first()
            if not existing:
                new_account = FinancialAccount(
                    account_code=acc['code'],
                    account_name=acc['name'],
                    account_type=acc['type'],
                    balance=acc['balance'],
                    is_active=True
                )
                db.session.add(new_account)
                print(f"➕ إضافة حساب: {acc['code']} - {acc['name']}")
            else:
                print(f"⚠️ الحساب {acc['code']} موجود مسبقاً، تم تخطيه.")

        db.session.commit()
        print("\n🎉 اكتملت إضافة الحسابات المالية الأساسية.")
        print("📌 يمكنك الآن إضافة العملاء والموردين وربطهم بحسابات فرعية من واجهة التطبيق.")
        print("📌 لتشغيل التطبيق الرئيسي، قم بتنفيذ: python app.py")


if __name__ == "__main__":
    print("=" * 60)
    print("🌱 إضافة الحسابات المالية الأساسية")
    print("=" * 60)
    seed_accounts()