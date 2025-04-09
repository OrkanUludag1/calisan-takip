import sqlite3
import os

# Veritabanı dosyasının tam yolunu belirle
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'employee.db')
print(f"Veritabanı dosyası: {db_path}")

# Veritabanına bağlan
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Önce mevcut çalışanları al
cursor.execute('SELECT id, name FROM employees')
employees = cursor.fetchall()

print("Mevcut çalışanlar:")
for emp_id, name in employees:
    print(f"ID: {emp_id}, İsim: {name}")

# Her çalışanın ismini büyük harfe çevir ve güncelle
for emp_id, name in employees:
    upper_name = name.upper()
    cursor.execute('UPDATE employees SET name = ? WHERE id = ?', (upper_name, emp_id))
    print(f"Güncellendi: {name} -> {upper_name}")

# Değişiklikleri kaydet
conn.commit()

# Güncellenmiş çalışanları kontrol et
cursor.execute('SELECT id, name FROM employees')
updated_employees = cursor.fetchall()

print("\nGüncellenmiş çalışanlar:")
for emp_id, name in updated_employees:
    print(f"ID: {emp_id}, İsim: {name}")

# Bağlantıyı kapat
conn.close()

print("\nTüm çalışan isimleri büyük harfe çevrildi!")
