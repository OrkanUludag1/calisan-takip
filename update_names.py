import os
import sqlite3

def main():
    # Veritabanı dosyasının tam yolunu belirle
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'employee.db')
    
    # Veritabanına bağlan
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tüm çalışanları al
    cursor.execute('SELECT id, name FROM employees')
    employees = cursor.fetchall()
    
    # Her çalışanın ismini büyük harfe çevir
    for emp_id, name in employees:
        upper_name = name.upper()
        
        # İsmi güncelle
        cursor.execute('UPDATE employees SET name = ? WHERE id = ?', (upper_name, emp_id))
    
    # Değişiklikleri kaydet
    conn.commit()
    
    # Veritabanı bağlantısını kapat
    conn.close()
    
    return True

if __name__ == "__main__":
    main()
