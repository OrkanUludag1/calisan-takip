import sqlite3
import os
from datetime import datetime, timedelta

class EmployeeDB:
    """Çalışan veritabanı işlemleri için sınıf"""
    
    def __init__(self, db_file="employee.db"):
        """Veritabanı bağlantısını başlatır"""
        self.db_file = db_file
        self.create_tables()
    
    def create_tables(self):
        """Gerekli tabloları oluşturur"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Çalışanlar tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            weekly_salary REAL,
            daily_food REAL,
            daily_transport REAL
        )
        ''')
        
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
        
        conn.commit()
        conn.close()
    
    def add_employee(self, name, weekly_salary, daily_food, daily_transport):
        """Yeni çalışan ekler"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO employees (name, weekly_salary, daily_food, daily_transport)
        VALUES (?, ?, ?, ?)
        ''', (name, weekly_salary, daily_food, daily_transport))
        
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        
        return last_id
    
    def update_employee(self, employee_id, name, weekly_salary, daily_food, daily_transport):
        """Çalışan bilgilerini günceller"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE employees
        SET name = ?, weekly_salary = ?, daily_food = ?, daily_transport = ?
        WHERE id = ?
        ''', (name, weekly_salary, daily_food, daily_transport, employee_id))
        
        conn.commit()
        conn.close()
    
    def get_employees(self):
        """Tüm çalışanları getirir"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM employees ORDER BY name')
        employees = cursor.fetchall()
        
        conn.close()
        return employees
    
    def get_employee(self, employee_id):
        """ID'ye göre çalışan bilgilerini getirir"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
        employee = cursor.fetchone()
        
        conn.close()
        return employee
    
    def save_work_hours(self, employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active=1):
        """Çalışma saatlerini kaydeder"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
    
    def get_work_hours(self, employee_id, date):
        """Belirli bir tarih için çalışma saatlerini getirir"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT entry_time, lunch_start, lunch_end, exit_time, is_active
        FROM work_hours
        WHERE employee_id = ? AND date = ?
        ''', (employee_id, date))
        
        record = cursor.fetchone()
        conn.close()
        
        return record
    
    def get_week_work_hours(self, employee_id, week_start_date):
        """Bir haftalık çalışma saatlerini getirir"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
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
        conn.close()
        
        return records
