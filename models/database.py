import sqlite3
import os
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal

class EmployeeDB(QObject):
    """Çalışan veritabanı işlemleri için sınıf"""
    data_changed = pyqtSignal()
    
    def __init__(self, db_file="employee.db"):
        super().__init__()
        # Tam yolu kullanarak veritabanı dosyasına erişim
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(current_dir)
        self.db_file = os.path.join(project_dir, db_file)
        
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def create_tables(self):
        """Veritabanı tablolarını oluşturur"""
        cursor = self.conn.cursor()
        
        # Çalışan tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            weekly_salary REAL NOT NULL,
            daily_food REAL NOT NULL,
            daily_transport REAL NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Çalışma saatleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_hours (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            date TEXT NOT NULL,
            entry_time TEXT,
            lunch_start TEXT,
            lunch_end TEXT,
            exit_time TEXT,
            day_active INTEGER DEFAULT 1,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
        ''')
        
        # Payments tablosunda date sütunu varsa week_start_date olarak yeniden adlandır
        try:
            # Önce mevcut payments tablosunun yapısını kontrol et
            cursor.execute("PRAGMA table_info(payments)")
            columns = cursor.fetchall()
            
            has_date_column = False
            has_week_start_date_column = False
            
            for column in columns:
                if column[1] == 'date':
                    has_date_column = True
                if column[1] == 'week_start_date':
                    has_week_start_date_column = True
            
            # Eğer date sütunu varsa ve week_start_date sütunu yoksa
            if has_date_column and not has_week_start_date_column:
                # Geçici tablo oluştur
                cursor.execute('''
                CREATE TABLE payments_temp (
                    id INTEGER PRIMARY KEY,
                    employee_id INTEGER,
                    week_start_date TEXT NOT NULL,
                    payment_type TEXT,
                    amount REAL NOT NULL,
                    description TEXT,
                    is_permanent INTEGER DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
                )
                ''')
                
                # Verileri geçici tabloya kopyala
                cursor.execute('''
                INSERT INTO payments_temp (id, employee_id, week_start_date, payment_type, amount, description, is_permanent)
                SELECT id, employee_id, date, payment_type, amount, description, is_permanent FROM payments
                ''')
                
                # Eski tabloyu sil
                cursor.execute("DROP TABLE payments")
                
                # Geçici tabloyu yeniden adlandır
                cursor.execute("ALTER TABLE payments_temp RENAME TO payments")
                
                self.conn.commit()
            else:
                # Ödemeler tablosu
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY,
                    employee_id INTEGER,
                    week_start_date TEXT NOT NULL,
                    payment_type TEXT,
                    amount REAL NOT NULL,
                    description TEXT,
                    is_permanent INTEGER DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
                )
                ''')
        except Exception as e:
            # Ödemeler tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                employee_id INTEGER,
                week_start_date TEXT NOT NULL,
                payment_type TEXT,
                amount REAL NOT NULL,
                description TEXT,
                is_permanent INTEGER DEFAULT 0,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
            ''')
        
        # Haftalık özet tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_summaries (
            id INTEGER PRIMARY KEY,
            week_start_date TEXT NOT NULL UNIQUE,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Haftalık özet detayları tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_summary_details (
            id INTEGER PRIMARY KEY,
            summary_id INTEGER,
            employee_id INTEGER,
            name TEXT NOT NULL,
            total_hours REAL NOT NULL,
            weekly_salary REAL NOT NULL,
            food_allowance REAL NOT NULL,
            transport_allowance REAL NOT NULL,
            total_additions REAL NOT NULL,
            total_deductions REAL NOT NULL,
            total_weekly_salary REAL NOT NULL,
            FOREIGN KEY (summary_id) REFERENCES weekly_summaries (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_employee(self, name, weekly_salary, daily_food, daily_transport):
        """Yeni çalışan ekler"""
        cursor = self.conn.cursor()
        # İsmi büyük harfe çevir
        name = name.strip().upper()
        
        # Aynı isimde çalışan var mı kontrol et (aktif veya pasif)
        cursor.execute('''
        SELECT id, is_active FROM employees 
        WHERE name = ?
        ''', (name,))
        
        existing_employee = cursor.fetchone()
        if existing_employee:
            # Aynı isimde çalışan varsa False döndür
            return False
        
        # Haftalık ücreti saatlik ücrete çevir (50 saate böl)
        hourly_rate = weekly_salary / 50
        
        cursor.execute('''
        INSERT INTO employees (name, weekly_salary, daily_food, daily_transport, is_active)
        VALUES (?, ?, ?, ?, 1)
        ''', (name, hourly_rate, daily_food, daily_transport))
        
        self.conn.commit()
        last_id = cursor.lastrowid
        
        self.data_changed.emit()
        return last_id
    
    def update_employee(self, employee_id, name, weekly_salary, daily_food, daily_transport):
        """Çalışan bilgilerini günceller"""
        cursor = self.conn.cursor()
        
        # İsmi büyük harfe çevir
        name = name.strip().upper()
        
        # Haftalık ücreti saatlik ücrete çevir (50 saate böl)
        hourly_rate = weekly_salary / 50
        
        cursor.execute('''
        UPDATE employees 
        SET name = ?, weekly_salary = ?, daily_food = ?, daily_transport = ?
        WHERE id = ?
        ''', (name, hourly_rate, daily_food, daily_transport, employee_id))
        
        self.conn.commit()
        self.data_changed.emit()
        return True
    
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
            ORDER BY is_active DESC, weekly_salary DESC
        ''')
        employees = cursor.fetchall()
        return employees
    
    def get_employee(self, employee_id):
        """ID'ye göre çalışan bilgilerini getirir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, weekly_salary, daily_food, daily_transport, is_active FROM employees WHERE id = ?', (employee_id,))
        employee = cursor.fetchone()
        
        if employee:
            # Saatlik ücreti haftalık ücrete çevir (50 ile çarp)
            employee_list = list(employee)
            employee_list[2] = employee_list[2] * 50  # weekly_salary
            return tuple(employee_list)
        
        return None
    
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
        self.data_changed.emit()
    
    def save_work_hours(self, employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active=1, day_active=None):
        """Çalışma saatlerini kaydeder"""
        cursor = self.conn.cursor()
        
        # Önce bu tarih için kayıt var mı kontrol et
        cursor.execute('''
        SELECT id, day_active FROM work_hours 
        WHERE employee_id = ? AND date = ?
        ''', (employee_id, date))
        
        record = cursor.fetchone()
        
        # Eğer day_active parametresi None ise ve kayıt varsa, mevcut değeri koru
        if day_active is None and record:
            day_active = record[1]
        # Eğer day_active parametresi None ise ve kayıt yoksa, varsayılan olarak 1 (aktif) yap
        elif day_active is None:
            day_active = 1
        
        if record:
            # Kayıt varsa güncelle
            cursor.execute('''
            UPDATE work_hours
            SET entry_time = ?, lunch_start = ?, lunch_end = ?, exit_time = ?, is_active = ?, day_active = ?
            WHERE employee_id = ? AND date = ?
            ''', (entry_time, lunch_start, lunch_end, exit_time, is_active, day_active, employee_id, date))
        else:
            # Kayıt yoksa yeni ekle
            cursor.execute('''
            INSERT INTO work_hours (employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active, day_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active, day_active))
        
        self.conn.commit()
    
    def update_work_hours(self, employee_id, date, time_type, time_value):
        """Belirli bir zaman türünü günceller (giriş, çıkış, öğle başlangıç/bitiş)"""
        cursor = self.conn.cursor()
        
        # time_type değerini veritabanı sütun adına dönüştür
        db_column = time_type
        if time_type == "entry":
            db_column = "entry_time"
        elif time_type == "exit":
            db_column = "exit_time"
        
        # Önce bu tarih için kayıt var mı kontrol et
        cursor.execute('''
        SELECT id FROM work_hours 
        WHERE employee_id = ? AND date = ?
        ''', (employee_id, date))
        
        record = cursor.fetchone()
        
        if record:
            # Kayıt varsa güncelle
            cursor.execute(f'''
            UPDATE work_hours
            SET {db_column} = ?
            WHERE employee_id = ? AND date = ?
            ''', (time_value, employee_id, date))
        else:
            # Kayıt yoksa yeni ekle
            # Diğer varsayılan değerleri belirleyelim
            entry_time = lunch_start = lunch_end = exit_time = "00:00"
            
            # Güncellenen alanı ayarla
            if time_type == "entry":
                entry_time = time_value
            elif time_type == "lunch_start":
                lunch_start = time_value
            elif time_type == "lunch_end":
                lunch_end = time_value
            elif time_type == "exit":
                exit_time = time_value
                
            cursor.execute('''
            INSERT INTO work_hours (employee_id, date, entry_time, lunch_start, lunch_end, exit_time, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (employee_id, date, entry_time, lunch_start, lunch_end, exit_time))
        
        self.conn.commit()
    
    def get_work_hours(self, employee_id, date):
        """Belirli bir tarih için çalışma saatlerini getirir"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT entry_time, lunch_start, lunch_end, exit_time, is_active, day_active
        FROM work_hours
        WHERE employee_id = ? AND date = ?
        ''', (employee_id, date))
        
        record = cursor.fetchone()
        
        return record
    
    def get_week_work_hours(self, employee_id, week_start_date):
        """Haftalık çalışma saatlerini getirir
        
        Args:
            employee_id (int): Çalışan ID
            week_start_date (str): Hafta başlangıç tarihi (YYYY-MM-DD formatında)
            
        Returns:
            list: Haftalık çalışma saatleri listesi
        """
        cursor = self.conn.cursor()
        
        # String formatındaki tarihi datetime nesnesine çevir
        week_start = datetime.strptime(week_start_date, "%Y-%m-%d")
        
        # Haftanın son günü (6 gün sonrası - Pazartesiden Pazara)
        week_end = week_start + timedelta(days=6)
        
        # Tarih formatlarını string olarak al
        week_start_str = week_start.strftime("%Y-%m-%d")
        week_end_str = week_end.strftime("%Y-%m-%d")
        
        # Önce day_active sütununu kontrol et
        try:
            cursor.execute('SELECT day_active FROM work_hours LIMIT 1')
        except sqlite3.OperationalError:
            # Sütun yoksa ekle
            cursor.execute('ALTER TABLE work_hours ADD COLUMN day_active INTEGER DEFAULT 1')
            cursor.execute('UPDATE work_hours SET day_active = 1')
            self.conn.commit()
        
        cursor.execute('''
        SELECT id, date, entry_time, lunch_start, lunch_end, exit_time, is_active, day_active
        FROM work_hours
        WHERE employee_id = ? AND date BETWEEN ? AND ?
        ORDER BY date
        ''', (employee_id, week_start_str, week_end_str))
        
        rows = cursor.fetchall()
        records = []
        
        # Her satırı sözlüğe dönüştür
        for row in rows:
            record = {
                'id': row[0],
                'date': row[1],
                'entry_time': row[2],
                'lunch_start': row[3],
                'lunch_end': row[4],
                'exit_time': row[5],
                'is_active': row[6],
                'day_active': row[7] if row[7] is not None else 1
            }
            records.append(record)
        
        return records

    def update_day_active_status(self, work_hour_id, active_status):
        """Çalışma günü aktif/pasif durumunu günceller"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
        UPDATE work_hours
        SET day_active = ?
        WHERE id = ?
        ''', (1 if active_status else 0, work_hour_id))
        
        self.conn.commit()
        return cursor.rowcount > 0

    def toggle_employee_active(self, employee_id, active_status):
        """Çalışanın aktif/pasif durumunu değiştirir"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'UPDATE employees SET is_active = ? WHERE id = ?',
                (1 if active_status else 0, employee_id)
            )
            self.conn.commit()
            self.data_changed.emit()
            return True
        except Exception as e:
            return False

    def has_work_hours(self, employee_id, date):
        """Belirli bir tarih için çalışma saati kaydı var mı kontrol eder"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id FROM work_hours WHERE employee_id = ? AND date = ?',
            (employee_id, date)
        )
        return cursor.fetchone() is not None

    def add_work_hours(self, employee_id, date, entry_time, lunch_start, lunch_end, exit_time):
        """Yeni çalışma saati kaydı oluşturur"""
        cursor = self.conn.cursor()
        
        # Önce day_active sütununu kontrol et
        try:
            cursor.execute('SELECT day_active FROM work_hours LIMIT 1')
        except sqlite3.OperationalError:
            # Sütun yoksa ekle
            cursor.execute('ALTER TABLE work_hours ADD COLUMN day_active INTEGER DEFAULT 1')
            self.conn.commit()
            
        cursor.execute('''
        INSERT INTO work_hours (
            employee_id, date, entry_time, lunch_start, lunch_end, exit_time, day_active
        ) VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (employee_id, date, entry_time, lunch_start, lunch_end, exit_time))
        
        self.conn.commit()
        return cursor.lastrowid

    def update_all_employee_names_to_uppercase(self):
        """Tüm çalışanların isimlerini büyük harfe çevirir"""
        cursor = self.conn.cursor()
        
        # Önce tüm çalışanları al
        cursor.execute('SELECT id, name FROM employees')
        employees = cursor.fetchall()
        
        # Her çalışanın ismini büyük harfe çevir
        for employee_id, name in employees:
            uppercase_name = name.strip().upper()
            # Eğer isim zaten büyük harfse güncelleme yapma
            if name != uppercase_name:
                cursor.execute('UPDATE employees SET name = ? WHERE id = ?', 
                              (uppercase_name, employee_id))
        
        self.conn.commit()
        self.data_changed.emit()
        return len(employees)

    def get_active_employees(self):
        """Sadece aktif çalışanları getirir"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, name, weekly_salary, daily_food, daily_transport, is_active
        FROM employees
        WHERE is_active = 1
        ORDER BY name
        ''')
        
        return cursor.fetchall()

    def add_payment(self, employee_id, week_start_date, payment_type, amount, description="", is_permanent=0):
        """Ek ödeme, kesinti veya sabit ödeme ekler
        
        payment_type: 'bonus' (ek ödeme), 'deduction' (kesinti), 'permanent' (sabit ek ödeme)
        is_permanent: Sabit ödeme olup olmadığını belirtir (1: evet, 0: hayır)
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        INSERT INTO payments (employee_id, week_start_date, payment_type, amount, description, is_permanent)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_id, week_start_date, payment_type, amount, description, is_permanent))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_weekly_payments(self, employee_id, week_start_date):
        """Haftalık ek ödemeleri/kesintileri getirir
        
        Args:
            employee_id (int): Çalışan ID
            week_start_date (str): Hafta başlangıç tarihi (YYYY-MM-DD formatında)
            
        Returns:
            list: Ek ödemeler/kesintiler listesi
        """
        cursor = self.conn.cursor()
        
        # Belirli haftaya ait ek ödemeler/kesintiler
        cursor.execute('''
        SELECT id, payment_type, amount, description, is_permanent
        FROM payments
        WHERE employee_id = ? AND week_start_date = ?
        ''', (employee_id, week_start_date))
        
        week_payments = cursor.fetchall()
        
        # Sabit ek ödemeleri getir (tüm haftalara uygulanır)
        cursor.execute('''
        SELECT id, payment_type, amount, description, is_permanent
        FROM payments
        WHERE employee_id = ? AND is_permanent = 1
        ''', (employee_id,))
        
        permanent_payments = cursor.fetchall()
        
        # Tüm ödemeleri birleştir
        all_payments = list(week_payments)
        
        # Sabit ödemeleri ekle (bu hafta için zaten eklenmemişse)
        payment_ids = [p[0] for p in week_payments]
        for payment in permanent_payments:
            if payment[0] not in payment_ids:
                all_payments.append(payment)
        
        return all_payments

    def update_payment(self, payment_id, amount, description=None):
        """Ek ödeme, kesinti veya sabit ödeme günceller"""
        cursor = self.conn.cursor()
        
        # Açıklama güncellenmeyecekse sadece miktarı güncelle
        if description is None:
            cursor.execute('''
            UPDATE payments
            SET amount = ?
            WHERE id = ?
            ''', (amount, payment_id))
        else:
            cursor.execute('''
            UPDATE payments
            SET amount = ?, description = ?
            WHERE id = ?
            ''', (amount, description, payment_id))
        
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_payment(self, payment_id):
        """Ek ödeme, kesinti veya sabit ödemeyi siler"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
        DELETE FROM payments
        WHERE id = ?
        ''', (payment_id,))
        
        self.conn.commit()
        return cursor.rowcount > 0

    def get_payment(self, payment_id):
        """Belirli bir ödeme kaydını getirir"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id, employee_id, week_start_date, payment_type, amount, description, is_permanent
        FROM payments
        WHERE id = ?
        ''', (payment_id,))
        
        return cursor.fetchone()
    
    def save_weekly_summary(self, week_start_date, total_amount, employee_data):
        """Haftalık özeti veritabanına kaydeder
        
        Args:
            week_start_date (str): Hafta başlangıç tarihi (YYYY-MM-DD formatında)
            total_amount (float): Toplam ödenecek tutar
            employee_data (list): Çalışan verileri listesi
            
        Returns:
            int: Eklenen kaydın ID'si, hata durumunda None
        """
        try:
            cursor = self.conn.cursor()
            
            # Önce bu hafta için kayıt var mı kontrol et
            cursor.execute(
                "SELECT id FROM weekly_summaries WHERE week_start_date = ?", 
                (week_start_date,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Varsa güncelle
                summary_id = existing[0]
                cursor.execute(
                    "UPDATE weekly_summaries SET total_amount = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (total_amount, summary_id)
                )
                
                # Detayları sil
                cursor.execute("DELETE FROM weekly_summary_details WHERE summary_id = ?", (summary_id,))
            else:
                # Yoksa yeni kayıt ekle
                cursor.execute(
                    "INSERT INTO weekly_summaries (week_start_date, total_amount) VALUES (?, ?)",
                    (week_start_date, total_amount)
                )
                summary_id = cursor.lastrowid
            
            # Çalışan detaylarını ekle
            for employee in employee_data:
                cursor.execute('''
                INSERT INTO weekly_summary_details (
                    summary_id, employee_id, name, total_hours, weekly_salary,
                    food_allowance, transport_allowance, total_additions,
                    total_deductions, total_weekly_salary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    summary_id,
                    employee['id'],
                    employee['name'],
                    employee['total_hours'],
                    employee['weekly_salary'],
                    employee['food_allowance'],
                    employee['transport_allowance'],
                    employee['total_additions'],
                    employee['total_deductions'],
                    employee['total_weekly_salary']
                ))
            
            self.conn.commit()
            return summary_id
        
        except Exception as e:
            self.conn.rollback()
            return None
    
    def get_weekly_summary(self, week_start_date):
        """Belirli bir hafta için özet bilgilerini getirir
        
        Args:
            week_start_date (str): Hafta başlangıç tarihi (YYYY-MM-DD formatında)
            
        Returns:
            dict: Haftalık özet bilgileri ve detayları, bulunamazsa None
        """
        try:
            cursor = self.conn.cursor()
            
            # Haftalık özeti al
            cursor.execute(
                "SELECT id, total_amount FROM weekly_summaries WHERE week_start_date = ?", 
                (week_start_date,)
            )
            summary = cursor.fetchone()
            
            if not summary:
                return None
            
            summary_id, total_amount = summary
            
            # Detayları al
            cursor.execute('''
            SELECT employee_id, name, total_hours, weekly_salary, food_allowance,
                   transport_allowance, total_additions, total_deductions, total_weekly_salary
            FROM weekly_summary_details
            WHERE summary_id = ?
            ORDER BY total_weekly_salary DESC
            ''', (summary_id,))
            
            details = []
            for row in cursor.fetchall():
                details.append({
                    'id': row[0],
                    'name': row[1],
                    'total_hours': row[2],
                    'weekly_salary': row[3],
                    'food_allowance': row[4],
                    'transport_allowance': row[5],
                    'total_additions': row[6],
                    'total_deductions': row[7],
                    'total_weekly_salary': row[8]
                })
            
            return {
                'id': summary_id,
                'week_start_date': week_start_date,
                'total_amount': total_amount,
                'details': details
            }
        
        except Exception as e:
            return None
    
    def get_available_weekly_summaries(self):
        """Kaydedilmiş tüm haftalık özetleri getirir
        
        Returns:
            list: Haftalık özet listesi
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            SELECT id, week_start_date, total_amount, created_at
            FROM weekly_summaries
            ORDER BY week_start_date DESC
            ''')
            
            summaries = []
            for row in cursor.fetchall():
                summaries.append({
                    'id': row[0],
                    'week_start_date': row[1],
                    'total_amount': row[2],
                    'created_at': row[3]
                })
            
            return summaries
        
        except Exception as e:
            return []

    def get_employee_additions(self, employee_id, week_start_date, include_permanent_if_no_work=True):
        """
        Belirtilen çalışanın, verilen haftadaki toplam eklenti (bonus, prim, ek ödeme, sabit ek ödeme) tutarını getirir.
        Eğer include_permanent_if_no_work False ise ve o haftada hiç çalışmamışsa sabit ek ödeme eklenmez.
        week_start_date: datetime veya 'YYYY-MM-DD' string (hafta başı pazartesi)
        """
        import datetime
        if isinstance(week_start_date, datetime.date):
            week_start_str = week_start_date.strftime('%Y-%m-%d')
        else:
            week_start_str = str(week_start_date)

        # Haftanın son günü (pazar)
        week_end = (datetime.datetime.strptime(week_start_str, '%Y-%m-%d') + datetime.timedelta(days=6)).strftime('%Y-%m-%d')

        cursor = self.conn.cursor()
        # Haftaya özel ödemeleri al
        cursor.execute('''
            SELECT id, amount FROM payments
            WHERE employee_id = ?
            AND LOWER(payment_type) IN ("eklenti", "bonus", "prim", "ek ödeme", "ek odeme", "ikramiye", "permanent", "sabit ek ödeme", "sabit ek odeme")
            AND week_start_date >= ? AND week_start_date <= ?
        ''', (employee_id, week_start_str, week_end))
        week_rows = cursor.fetchall()
        week_ids = {row[0] for row in week_rows}
        week_sum = sum(row[1] for row in week_rows)

        # Sabit ek ödemeleri (is_permanent=1) al, sadece bu haftada olmayanları ekle
        cursor.execute('''
            SELECT id, amount FROM payments
            WHERE employee_id = ? AND is_permanent = 1
        ''', (employee_id,))
        perm_rows = cursor.fetchall()
        # Çalışma kontrolü
        if not include_permanent_if_no_work:
            # O haftada çalışma var mı kontrol et
            cursor.execute('''
                SELECT COUNT(*) FROM work_hours
                WHERE employee_id = ? AND date >= ? AND date <= ? AND (is_active = 1 OR day_active = 1)
            ''', (employee_id, week_start_str, week_end))
            work_count = cursor.fetchone()[0]
            if work_count == 0:
                perm_sum = 0
            else:
                perm_sum = sum(row[1] for row in perm_rows if row[0] not in week_ids)
        else:
            perm_sum = sum(row[1] for row in perm_rows if row[0] not in week_ids)
        return week_sum + perm_sum

    def get_available_weeks(self):
        """Tüm kaydedilmiş haftaların başlangıç tarihlerini (Pazartesi) döndürür"""
        cursor = self.conn.cursor()
        # Çalışma saatleri tablosundan benzersiz hafta başı tarihlerini çek
        cursor.execute('''
            SELECT DISTINCT date FROM work_hours
        ''')
        dates = [row[0] for row in cursor.fetchall()]
        # Her tarihi haftanın Pazartesi'sine yuvarla
        mondays = set()
        for d in dates:
            dt = datetime.strptime(d, '%Y-%m-%d')
            monday = dt - timedelta(days=dt.weekday())
            mondays.add(monday.strftime('%Y-%m-%d'))
        return sorted(mondays, reverse=True)

    def get_employees_with_entries_for_week(self, week_start_date):
        """
        Belirli bir haftada zaman/veri girişi olan tüm çalışanları (aktif/pasif fark etmeksizin) getirir.
        Args:
            week_start_date (str): Hafta başlangıç tarihi (YYYY-MM-DD formatında)
        Returns:
            list: Çalışan dict'leri
        """
        cursor = self.conn.cursor()
        from datetime import datetime, timedelta
        week_start = datetime.strptime(week_start_date, "%Y-%m-%d")
        week_end = week_start + timedelta(days=6)
        cursor.execute('''
            SELECT DISTINCT e.id, e.name, e.weekly_salary, e.daily_food, e.daily_transport, e.is_active
            FROM employees e
            INNER JOIN work_hours w ON e.id = w.employee_id
            WHERE w.date BETWEEN ? AND ?
        ''', (week_start_date, week_end.strftime("%Y-%m-%d")))
        results = cursor.fetchall()
        return [{'id': row[0], 'name': row[1], 'weekly_salary': row[2], 'daily_food': row[3], 'daily_transport': row[4], 'is_active': row[5]} for row in results]
