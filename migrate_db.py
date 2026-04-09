import sqlite3


def migrate_database():
    conn = sqlite3.connect('thaljat_alsaleef.db')
    cursor = conn.cursor()

    # قائمة الجداول والأعمدة المطلوب إضافتها
    migrations = [
        ('purchase_orders', [
            ('cash_status', 'VARCHAR(20)', "DEFAULT 'pending'"),
            ('cash_approved_by', 'INTEGER', 'REFERENCES users(id)'),
            ('cash_approved_at', 'DATETIME', ''),
            ('cash_rejection_reason', 'VARCHAR(200)', '')
        ]),
        ('sale_orders', [
            ('cash_status', 'VARCHAR(20)', "DEFAULT 'pending'"),
            ('cash_approved_by', 'INTEGER', 'REFERENCES users(id)'),
            ('cash_approved_at', 'DATETIME', ''),
            ('cash_rejection_reason', 'VARCHAR(200)', '')
        ]),
        ('collections', [
            ('cash_status', 'VARCHAR(20)', "DEFAULT 'pending'"),
            ('cash_approved_by', 'INTEGER', 'REFERENCES users(id)'),
            ('cash_approved_at', 'DATETIME', ''),
            ('cash_rejection_reason', 'VARCHAR(200)', '')
        ])
    ]

    for table, columns in migrations:
        for col_name, col_type, col_constraint in columns:
            try:
                sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} {col_constraint}"
                cursor.execute(sql)
                print(f'✅ تم إضافة عمود {col_name} إلى جدول {table}')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f'⚠️ عمود {col_name} موجود بالفعل في جدول {table}')
                else:
                    print(f'❌ خطأ في إضافة {col_name} إلى {table}: {e}')

    conn.commit()
    conn.close()
    print('\n' + '=' * 50)
    print('✅ عملية الترحيل اكتملت بنجاح!')
    print('=' * 50)


if __name__ == '__main__':
    migrate_database()