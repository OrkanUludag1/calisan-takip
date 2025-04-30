import os
import sqlite3

def main():
    # Veritabanı dosyasının tam yolunu belirle
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'employee.db')
    
    # Veritabanına bağlan
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tüm çalışanları al
    cursor.execute('SELECT id, name, is_active FROM employees')
    employees = cursor.fetchall()
    
    # Veritabanı bağlantısını kapat
    conn.close()
    
    return employees

if __name__ == "__main__":
    main()
