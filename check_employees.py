import sqlite3
import os

# Veritabanı dosyasının tam yolunu belirle
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'employee.db')
print(f"Veritabanı dosyası: {db_path}")

# Veritabanına bağlan
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tüm çalışanları sorgula
cursor.execute('SELECT id, name, is_active FROM employees')
employees = cursor.fetchall()

print("Tüm çalışanlar:")
for emp_id, name, is_active in employees:
    status = "Aktif" if is_active else "Pasif"
    print(f"ID: {emp_id}, İsim: {name}, Durum: {status}")

# Bağlantıyı kapat
conn.close()
