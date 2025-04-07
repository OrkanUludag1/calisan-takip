import sqlite3
import os
from datetime import datetime, timedelta

class EmployeeDB:
    """Çalışan veritabanı işlemleri için sınıf"""
    
    def __init__(self, db_file="employee.db"):
        """Veritabanı bağlantısını başlatır"""
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.create_tables()
    
    def create_tables(self):
        """Gerekli tabloları oluşturur"""
        cursor = self.conn.cursor()
        
        # Çalışanlar tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            weekly_salary REAL,
            daily_food REAL,
            daily_transport REAL,
            is_active INTEGER DEFAULT 1
        )
        ''')

        # Mevcut kayıtlara is_active sütunu ekle
        try:
            cursor.execute('SELECT is_active FROM employees LIMIT 1')
        except sqlite3.OperationalError:
            cursor.execute('ALTER TABLE employees ADD COLUMN is_active INTEGER DEFAULT 1')
            cursor.execute('UPDATE employees SET is_active = 1')
            self.conn.commit()
        
        # Çalışma saatleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date TEXT,
            entry_time TEXT,
            lunch_start TEXT,
            lunch_end TEXT,
            exit_time TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_employee(self, name, weekly_salary, daily_food, daily_transport):
        """Yeni çalışan ekler"""
        cursor = self.conn.cursor()
        
        # İsmin ilk harfini büyük yap
        name = name.strip().title()
        
        # Aynı isimde aktif çalışan var mı kontrol et
        cursor.execute('''
        SELECT id FROM employees 
        WHERE name = ? AND is_active = 1
        ''', (name,))
        
        existing_employee = cursor.fetchone()
        if existing_employee:
            # Aynı isimde aktif çalışan varsa False döndür
            return False
        
        cursor.execute('''
        INSERT INTO employees (name, weekly_salary, daily_food, daily_transport, is_active)
        VALUES (?, ?, ?, ?, 1)
        ''', (name, weekly_salary, daily_food, daily_transport))
        
        self.conn.commit()
        last_id = cursor.lastrowid
        
        return last_id
    
    def update_employee(self, employee_id, name, weekly_salary, daily_food, daily_transport):
        """Çalışan bilgilerini günceller"""
        cursor = self.conn.cursor()
        
        # İsmin ilk harfini büyük yap
        name = name.strip().title()
        
        cursor.execute('''
        UPDATE employees
        SET name = ?, weekly_salary = ?, daily_food = ?, daily_transport = ?
        WHERE id = ?
        ''', (name, weekly_salary, daily_food, daily_transport, employee_id))
        
        self.conn.commit()
    
    def update_employee_status(self, employee_id, is_active):
        """Çalışanın aktif/pasif durumunu günceller"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
        UPDATE employees
        SET is_active = ?
        WHERE id = ?
        ''', (is_active, employee_id))
        
        self.conn.commit()
    
    def get_employees(self):
        """Tüm çalışanları getirir"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, name, weekly_salary, daily_food, daily_transport, is_active 
            FROM employees 
            ORDER BY is_active DESC, weekly_salary DESC, name
        ''')
        return cursor.fetchall()
    
    def get_employee(self, employee_id):
        """ID'ye göre çalışan bilgilerini getirir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
        employee = cursor.fetchone()
        
        return employee
    
    def delete_employee(self, employee_id):
        """Çalışanı veritabanından siler"""
        cursor = self.conn.cursor()
        
        # Önce çalışanın çalışma saatlerini sil
        cursor.execute('''
        DELETE FROM work_hours
        WHERE employee_id = ?
        ''', (employee_id,))
        
        # Sonra çalışanı sil
        cursor.execute('''
        DELETE FROM employees
        WHERE id = ?
        ''', (employee_id,))
        
        self.conn.commit()
    
    def save_work_hours(self, employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active=1):
        """Çalışma saatlerini kaydeder"""
        cursor = self.conn.cursor()
        
        # Önce bu tarih için kayıt var mı kontrol et
        cursor.execute('''
        SELECT id FROM work_hours 
        WHERE employee_id = ? AND date = ?
        ''', (employee_id, date))
        
        record = cursor.fetchone()
        
        if record:
            # Kayıt varsa güncelle
            cursor.execute('''
            UPDATE work_hours
            SET entry_time = ?, lunch_start = ?, lunch_end = ?, exit_time = ?, is_active = ?
            WHERE employee_id = ? AND date = ?
            ''', (entry_time, lunch_start, lunch_end, exit_time, is_active, employee_id, date))
        else:
            # Kayıt yoksa yeni ekle
            cursor.execute('''
            INSERT INTO work_hours (employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active))
        
        self.conn.commit()
    
    def get_work_hours(self, employee_id, date):
        """Belirli bir tarih için çalışma saatlerini getirir"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT entry_time, lunch_start, lunch_end, exit_time, is_active
        FROM work_hours
        WHERE employee_id = ? AND date = ?
        ''', (employee_id, date))
        
        record = cursor.fetchone()
        
        return record
    
    def get_week_work_hours(self, employee_id, week_start_date):
        """Bir haftalık çalışma saatlerini getirir"""
        cursor = self.conn.cursor()
        
        # Haftanın başlangıç ve bitiş tarihlerini hesapla
        week_start = datetime.strptime(week_start_date, "%Y-%m-%d")
        week_end = week_start + timedelta(days=6)
        
        cursor.execute('''
        SELECT date, entry_time, lunch_start, lunch_end, exit_time, is_active
        FROM work_hours
        WHERE employee_id = ? AND date BETWEEN ? AND ?
        ORDER BY date
        ''', (employee_id, week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")))
        
        records = cursor.fetchall()
        
        return records
