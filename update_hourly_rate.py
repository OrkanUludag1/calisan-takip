#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys

def main():
    """
    Haftalik ucretleri saatlik ucretlere donusturur.
    Haftalik ucret degerlerini 50'ye bolerek saatlik ucret olarak gunceller.
    """
    try:
        # Veritabanı bağlantısı
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'employee.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tüm çalışanları al
        cursor.execute('SELECT id, name, weekly_salary FROM employees')
        employees = cursor.fetchall()
        
        # Haftalık çalışma saati
        weekly_hours = 50
        
        # Her çalışan için saatlik ücreti hesapla ve güncelle
        for emp in employees:
            emp_id = emp[0]
            name = emp[1]
            weekly_salary = emp[2]
            
            # Saatlik ücret = Haftalık ücret / Haftalık çalışma saati
            hourly_rate = weekly_salary / weekly_hours
            
            # Veritabanını güncelle
            cursor.execute('''
            UPDATE employees
            SET weekly_salary = ?
            WHERE id = ?
            ''', (hourly_rate, emp_id))
        
        # Değişiklikleri kaydet
        conn.commit()
        
        return True
    except Exception as e:
        return False
    finally:
        # Veritabanı bağlantısını kapat
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
