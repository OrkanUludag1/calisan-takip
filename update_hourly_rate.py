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
        # Veritabanı dosyasının tam yolunu belirle
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'employee.db')
        
        # Veritabanına bağlan
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tüm çalışanları ve haftalık ücretlerini al
        cursor.execute('SELECT id, name, weekly_salary FROM employees')
        employees = cursor.fetchall()
        
        print("Haftalik ucretler saatlik ucretlere donusturuluyor...")
        print("Haftalik calisma saati: 50 saat")
        print("\nGuncellemeden Once:")
        print("ID | Isim | Haftalik Ucret")
        print("-" * 40)
        
        for emp_id, name, weekly_salary in employees:
            print(f"{emp_id} | {name} | {weekly_salary:.2f}")
        
        # Her çalışanın haftalık ücretini 50'ye bölerek saatlik ücrete dönüştür
        for emp_id, name, weekly_salary in employees:
            hourly_rate = weekly_salary / 50  # Haftalık ücreti 50 saate böl
            
            # Saatlik ücreti güncelle
            cursor.execute('''
            UPDATE employees
            SET weekly_salary = ?
            WHERE id = ?
            ''', (hourly_rate, emp_id))
        
        # Değişiklikleri kaydet
        conn.commit()
        
        # Güncellenmiş değerleri göster
        cursor.execute('SELECT id, name, weekly_salary FROM employees')
        updated_employees = cursor.fetchall()
        
        print("\nGuncellemeden Sonra (Saatlik Ucretler):")
        print("ID | Isim | Saatlik Ucret")
        print("-" * 40)
        
        for emp_id, name, hourly_rate in updated_employees:
            print(f"{emp_id} | {name} | {hourly_rate:.2f}")
        
        print("\nGuncelleme basariyla tamamlandi.")
        print("Artik 'weekly_salary' degeri saatlik ucreti temsil ediyor.")
        print("Haftalik ucret = Saatlik ucret x Toplam calisma saati")
        
    except Exception as e:
        print(f"Hata olustu: {e}")
        return 1
    finally:
        # Veritabanı bağlantısını kapat
        if 'conn' in locals():
            conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
