import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QTabWidget, QTimeEdit, 
                             QMessageBox, QComboBox, QCheckBox, QSizePolicy, QHBoxLayout, QFrame, QHeaderView,
                             QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTime, QDate, pyqtSignal, QObject, QTimer, QEventLoop
from PyQt5.QtGui import QFont, QColor
import sqlite3
from datetime import datetime, timedelta
import math

class EmployeeDB:
    def __init__(self):
        self.conn = sqlite3.connect('employee_tracking.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            weekly_salary REAL NOT NULL,
            daily_food REAL NOT NULL,
            daily_transport REAL NOT NULL
        )''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            entry_time TEXT,
            lunch_start TEXT,
            lunch_end TEXT,
            exit_time TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )''')
        self.conn.commit()
    
    def add_employee(self, name, weekly_salary, daily_food, daily_transport):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO employees (name, weekly_salary, daily_food, daily_transport) 
        VALUES (?, ?, ?, ?)
        ''', (name, weekly_salary, daily_food, daily_transport))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_employees(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, name, weekly_salary, daily_food, daily_transport 
        FROM employees
        ORDER BY weekly_salary DESC
        ''')
        return cursor.fetchall()
    
    def add_work_record(self, employee_id, date, entry_time, lunch_start, lunch_end, exit_time):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM work_records WHERE employee_id=? AND date=?', 
                     (employee_id, date))
        record = cursor.fetchone()
        
        if record:
            # Kayıt varsa güncelle
            cursor.execute('''
                UPDATE work_records 
                SET entry_time=?, lunch_start=?, lunch_end=?, exit_time=?
                WHERE employee_id=? AND date=?
            ''', (entry_time, lunch_start, lunch_end, exit_time, employee_id, date))
        else:
            # Kayıt yoksa ekle
            cursor.execute('''
                INSERT INTO work_records 
                (employee_id, date, entry_time, lunch_start, lunch_end, exit_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, date, entry_time, lunch_start, lunch_end, exit_time))
        
        self.conn.commit()
    
    def get_work_records(self, employee_id, start_date, end_date):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT wr.date, wr.entry_time, wr.lunch_start, wr.lunch_end, wr.exit_time 
        FROM work_records wr
        INNER JOIN employees e ON e.id = wr.employee_id
        WHERE wr.employee_id = ? AND wr.date BETWEEN ? AND ?
        ORDER BY wr.date
        ''', (employee_id, start_date, end_date))
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()

class EmployeeForm(QWidget):
    data_updated = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_edit_id = None  # Düzenlenen çalışanın ID'si
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Form alanları
        form_layout = QVBoxLayout()
        
        # Sabit genişlik değeri
        input_width = 200
        
        name_layout = QHBoxLayout()
        name_label = QLabel("İsim:")
        name_label.setFixedWidth(100)  # Etiket genişliği
        self.name_input = QLineEdit()
        self.name_input.setFixedWidth(input_width)  # Giriş alanı genişliği
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        name_layout.addStretch()  # Sağa doğru boşluk ekle
        form_layout.addLayout(name_layout)
        
        salary_layout = QHBoxLayout()
        salary_label = QLabel("Haftalık Ücret:")
        salary_label.setFixedWidth(100)  # Etiket genişliği
        self.salary_input = QLineEdit()
        self.salary_input.setFixedWidth(input_width)  # Giriş alanı genişliği
        salary_layout.addWidget(salary_label)
        salary_layout.addWidget(self.salary_input)
        salary_layout.addStretch()  # Sağa doğru boşluk ekle
        form_layout.addLayout(salary_layout)
        
        food_layout = QHBoxLayout()
        food_label = QLabel("Günlük Yemek:")
        food_label.setFixedWidth(100)  # Etiket genişliği
        self.food_input = QLineEdit()
        self.food_input.setFixedWidth(input_width)  # Giriş alanı genişliği
        food_layout.addWidget(food_label)
        food_layout.addWidget(self.food_input)
        food_layout.addStretch()  # Sağa doğru boşluk ekle
        form_layout.addLayout(food_layout)
        
        transport_layout = QHBoxLayout()
        transport_label = QLabel("Günlük Yol:")
        transport_label.setFixedWidth(100)  # Etiket genişliği
        self.transport_input = QLineEdit()
        self.transport_input.setFixedWidth(input_width)  # Giriş alanı genişliği
        transport_layout.addWidget(transport_label)
        transport_layout.addWidget(self.transport_input)
        transport_layout.addStretch()  # Sağa doğru boşluk ekle
        form_layout.addLayout(transport_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Ekle")
        self.add_button.clicked.connect(self.add_employee)
        button_layout.addWidget(self.add_button)
        
        self.update_button = QPushButton("Güncelle")
        self.update_button.clicked.connect(self.update_employee)
        self.update_button.setVisible(False)  # Başlangıçta gizli
        button_layout.addWidget(self.update_button)
        
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.clicked.connect(self.cancel_edit)
        self.cancel_button.setVisible(False)  # Başlangıçta gizli
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()  # Sağa doğru boşluk ekle
        form_layout.addLayout(button_layout)
        layout.addLayout(form_layout)
        
        # Çalışan listesi
        self.employee_list = QTableWidget()
        self.employee_list.setColumnCount(4)
        self.employee_list.setHorizontalHeaderLabels(["İsim", "Haftalık Ücret", "Günlük Yemek", "Günlük Yol"])
        self.employee_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_list.setSelectionMode(QTableWidget.SingleSelection)
        self.employee_list.itemDoubleClicked.connect(self.edit_employee)
        self.employee_list.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        layout.addWidget(self.employee_list)
        
        self.setLayout(layout)
        self.load_employees()
    
    def format_currency(self, amount):
        """
        Para birimini formatlar:
        - Ondalık kısım olmayacak
        - Birler basamağı 5'e yuvarlanacak
        - Binlik ayırıcı kullanılacak
        """
        # Birler basamağını 5'e yuvarla
        rounded = round(amount / 5) * 5
        # Binlik ayırıcı ekle
        return "{:,.0f}".format(rounded).replace(",", ".")
    
    def add_employee(self):
        try:
            name = self.name_input.text().strip()
            weekly_salary = float(self.salary_input.text().replace(".", "").replace(",", "."))
            daily_food = float(self.food_input.text().replace(".", "").replace(",", "."))
            daily_transport = float(self.transport_input.text().replace(".", "").replace(",", "."))
            
            if not name:
                QMessageBox.warning(self, "Uyarı", "İsim alanı boş olamaz!")
                return
            
            if self.current_edit_id is None:  # Yeni çalışan ekleme
                self.db.add_employee(name, weekly_salary, daily_food, daily_transport)
            else:  # Mevcut çalışanı güncelleme
                cursor = self.db.conn.cursor()
                cursor.execute('''
                UPDATE employees 
                SET name=?, weekly_salary=?, daily_food=?, daily_transport=?
                WHERE id=?
                ''', (name, weekly_salary, daily_food, daily_transport, self.current_edit_id))
                self.db.conn.commit()
            
            self.clear_form()
            self.load_employees()
            self.data_updated.emit()
            
        except ValueError:
            QMessageBox.warning(self, "Uyarı", "Lütfen ücret alanlarına geçerli sayısal değerler girin!")
    
    def update_employee(self):
        self.add_employee()  # Aynı fonksiyonu kullan ama current_edit_id ile güncelleme yap
    
    def edit_employee(self, item):
        row = item.row()
        employee_id = int(self.employee_list.item(row, 0).data(Qt.UserRole))
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT name, weekly_salary, daily_food, daily_transport FROM employees WHERE id=?', (employee_id,))
        employee = cursor.fetchone()
        
        if employee:
            self.current_edit_id = employee_id
            self.name_input.setText(employee[0])
            self.salary_input.setText(self.format_currency(employee[1]))
            self.food_input.setText(self.format_currency(employee[2]))
            self.transport_input.setText(self.format_currency(employee[3]))
            
            self.add_button.setVisible(False)
            self.update_button.setVisible(True)
            self.cancel_button.setVisible(True)
    
    def cancel_edit(self):
        self.clear_form()
    
    def clear_form(self):
        self.current_edit_id = None
        self.name_input.clear()
        self.salary_input.clear()
        self.food_input.clear()
        self.transport_input.clear()
        
        self.add_button.setVisible(True)
        self.update_button.setVisible(False)
        self.cancel_button.setVisible(False)
    
    def load_employees(self):
        self.employee_list.setRowCount(0)
        employees = self.db.get_employees()
        
        for row, (emp_id, name, weekly_salary, daily_food, daily_transport) in enumerate(employees):
            self.employee_list.insertRow(row)
            
            name_item = QTableWidgetItem(name.upper())
            name_item.setData(Qt.UserRole, emp_id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Düzenlemeyi devre dışı bırak
            
            items = [
                name_item,
                QTableWidgetItem(self.format_currency(weekly_salary) + " TL"),
                QTableWidgetItem(self.format_currency(daily_food) + " TL"),
                QTableWidgetItem(self.format_currency(daily_transport) + " TL")
            ]
            
            # Tüm öğeleri ekle
            for col, item in enumerate(items):
                self.employee_list.setItem(row, col, item)
        
        self.employee_list.resizeColumnsToContents()

class TimeTrackingForm(QWidget):
    data_updated = pyqtSignal()
    
    def __init__(self, db, employee_id=None, employee_name=None):
        super().__init__()
        self.db = db
        self.current_employee_id = employee_id
        self.current_employee_name = employee_name
        self.changes_pending = False
        self.current_totals = {}
        
        # Otomatik kaydetme zamanlayıcısı
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(2000)  # 2 saniyede bir kaydet
        
        self.initUI()
        self.load_week_days()  # Haftayı yükle
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Sol: Tablo, Sağ: Özetler
        main_layout = QHBoxLayout()
        
        # Sol Bölüm: Tablo ve Başlık
        left_layout = QVBoxLayout()
        
        # Başlık
        if self.current_employee_name:
            title_label = QLabel(f"<h2>{self.current_employee_name.upper()}</h2>")
            title_label.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(title_label)
        
        # Tarih aralığı container'ı
        self.date_range_label = QLabel()
        self.date_range_label.setAlignment(Qt.AlignCenter)
        self.date_range_label.setStyleSheet("""
            font-weight: bold;
            padding: 5px;
            background-color: #f5f5f5;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            margin-bottom: 5px;
        """)
        left_layout.addWidget(self.date_range_label)
        
        # Tablo
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(5)
        self.days_table.setRowCount(7)
        self.days_table.setHorizontalHeaderLabels([
            "Gün", "Giriş", "Öğle Başlangıç",
            "Öğle Bitiş", "Çıkış"
        ])
        self.days_table.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        left_layout.addWidget(self.days_table)
        
        # Sağ taraf (toplam bilgileri)
        right_widget = QWidget()
        right_widget.setFixedWidth(250)  # Sabit genişlik
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(right_widget)
        
        # Toplam bilgileri için grup kutusu
        totals_group = QWidget()
        totals_group.setFixedWidth(230)  # İç grup kutusu genişliği
        totals_layout = QVBoxLayout()
        totals_layout.setSpacing(10)  # Öğeler arası boşluk
        
        # Container'lar için sabit yükseklik
        container_height = 80
        
        # Toplam çalışma
        total_hours_container = QWidget()
        total_hours_container.setFixedHeight(container_height)
        total_hours_layout = QVBoxLayout(total_hours_container)
        total_hours_layout.setContentsMargins(0, 0, 0, 0)
        total_hours_layout.setSpacing(0)
        total_hours_title = QLabel("Toplam Çalışma")
        self.total_hours_label = QLabel("0 saat")
        total_hours_layout.addWidget(total_hours_title)
        total_hours_layout.addWidget(self.total_hours_label)
        
        # Çalışma ücreti
        salary_container = QWidget()
        salary_container.setFixedHeight(container_height)
        salary_layout = QVBoxLayout(salary_container)
        salary_layout.setContentsMargins(0, 0, 0, 0)
        salary_layout.setSpacing(0)
        salary_title = QLabel("Çalışma Ücreti")
        self.weekly_salary_label = QLabel("0 TL")
        salary_layout.addWidget(salary_title)
        salary_layout.addWidget(self.weekly_salary_label)
        
        # Yol parası
        transport_container = QWidget()
        transport_container.setFixedHeight(container_height)
        transport_layout = QVBoxLayout(transport_container)
        transport_layout.setContentsMargins(0, 0, 0, 0)
        transport_layout.setSpacing(0)
        transport_title = QLabel("Yol Parası")
        self.transport_total_label = QLabel("0 TL")
        transport_layout.addWidget(transport_title)
        transport_layout.addWidget(self.transport_total_label)
        
        # Yemek parası
        food_container = QWidget()
        food_container.setFixedHeight(container_height)
        food_layout = QVBoxLayout(food_container)
        food_layout.setContentsMargins(0, 0, 0, 0)
        food_layout.setSpacing(0)
        food_title = QLabel("Yemek Parası")
        self.food_total_label = QLabel("0 TL")
        food_layout.addWidget(food_title)
        food_layout.addWidget(self.food_total_label)
        
        # Toplam tutar
        total_container = QWidget()
        total_container.setFixedHeight(container_height)
        total_layout = QVBoxLayout(total_container)
        total_layout.setContentsMargins(0, 0, 0, 0)
        total_layout.setSpacing(0)
        total_title = QLabel("Toplam")
        self.total_amount_label = QLabel("0 TL")
        total_layout.addWidget(total_title)
        total_layout.addWidget(self.total_amount_label)
        
        # Stil tanımlamaları
        title_style = """
            QLabel {
                color: #666;
                font-weight: bold;
                padding: 5px;
                padding-bottom: 2px;
                margin: 2px;
                margin-bottom: 0;
                border: 1px solid #ccc;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background-color: #f8f9fa;
            }
        """
        
        value_style = """
            QLabel {
                color: #000;
                font-size: 14px;
                padding: 5px;
                padding-top: 2px;
                margin: 2px;
                margin-top: 0;
                border: 1px solid #ccc;
                border-top: none;
                border-radius: 0 0 4px 4px;
                background-color: #fff;
            }
        """
        
        # Stilleri uygula
        for title in [total_hours_title, salary_title, transport_title, food_title, total_title]:
            title.setStyleSheet(title_style)
            title.setAlignment(Qt.AlignCenter)
        
        for value in [self.total_hours_label, self.weekly_salary_label, 
                     self.transport_total_label, self.food_total_label, 
                     self.total_amount_label]:
            value.setStyleSheet(value_style)
            value.setAlignment(Qt.AlignCenter)
        
        # Containerları layout'a ekle
        totals_layout.addWidget(total_hours_container)
        totals_layout.addWidget(salary_container)
        totals_layout.addWidget(transport_container)
        totals_layout.addWidget(food_container)
        totals_layout.addWidget(total_container)
        
        # Toplam grup kutusunu tamamla
        totals_group.setLayout(totals_layout)
        
        # Ana layout'a sol ve sağ tarafı ekle
        main_layout.addLayout(left_layout, 2)  # 2 birim genişlik
        right_layout.addWidget(totals_group)  # 1 birim genişlik
        
        # Durum etiketi
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                margin-top: 5px;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.status_label)
        
        # Ana layout'u widget'a ekle
        self.setLayout(main_layout)
        
        # Değişiklik bayrağı
        self.changes_pending = False
        
        self.days_table.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        self.days_table.setShowGrid(True)
        self.days_table.setAlternatingRowColors(True)
        self.days_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                selection-background-color: #e0e0ff;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
    
    def load_week_days(self):
        """Haftalık günleri yükler"""
        if not self.current_employee_id:
            return
            
        # Tarihleri ayarla
        current_date = QDate.currentDate()
        start_of_week = current_date.addDays(-current_date.dayOfWeek() + 1)
        end_of_week = start_of_week.addDays(6)
        
        # Tarih aralığını göster
        self.date_range_label.setText(
            f"Tarih Aralığı: {start_of_week.toString('dd.MM.yyyy')} - {end_of_week.toString('dd.MM.yyyy')}"
        )
        
        # Varsayılan saatler
        default_times = [
            QTime(8, 15),    # Giriş: 08:15
            QTime(13, 15),   # Öğle başlangıç: 13:15
            QTime(13, 45),   # Öğle bitiş: 13:45
            QTime(18, 45)    # Çıkış: 18:45
        ]
        
        # Türkçe gün isimleri
        turkce_gunler = [
            "Pazartesi", "Salı", "Çarşamba", 
            "Perşembe", "Cuma", "Cumartesi", "Pazar"
        ]
        
        # Tablo başlıklarını ayarla
        self.days_table.setHorizontalHeaderLabels([
            "Gün", "Giriş", "Öğle Başlangıç",
            "Öğle Bitiş", "Çıkış"
        ])
        
        # Sütun genişliklerini ayarla
        self.days_table.setColumnCount(5)
        header = self.days_table.horizontalHeader()
        
        # Tarih sütunu sabit genişlikte
        self.days_table.setColumnWidth(0, 180)
        
        # Diğer sütunlar eşit genişlikte
        for col in range(1, 5):
            self.days_table.setColumnWidth(col, 110)
        
        # Sütun modlarını ayarla
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Tarih sütunu sabit
        for col in range(1, 5):
            header.setSectionResizeMode(col, QHeaderView.Fixed)  # Saat sütunları sabit
        
        # Günleri tabloya ekle
        for row in range(7):
            current_day = start_of_week.addDays(row)
            is_weekend = current_day.dayOfWeek() in [6, 7]  # 6=Cumartesi, 7=Pazar
            
            # Gün hücresi - Sadece gün adını göster
            gun_adi = turkce_gunler[row]
            day_item = QTableWidgetItem(gun_adi)
            day_item.setData(Qt.UserRole, current_day)  # Tam tarihi UserRole'da sakla
            day_item.setFlags(day_item.flags() & ~Qt.ItemIsEditable)
            day_item.setTextAlignment(Qt.AlignCenter)
            self.days_table.setItem(row, 0, day_item)
            
            # Saat hücreleri
            for col, default_time in enumerate(default_times, start=1):
                time_edit = QTimeEdit()
                time_edit.setDisplayFormat("HH:mm")
                time_edit.setTime(default_time)
                time_edit.timeChanged.connect(lambda time, r=row: self.on_time_changed(r))
                time_edit.setAlignment(Qt.AlignCenter)
                time_edit.setStyleSheet("padding: 2px;")
                self.days_table.setCellWidget(row, col, time_edit)
            
            # Hafta sonu günlerini gri yap
            if is_weekend:
                for col in range(5):
                    item = self.days_table.item(row, col)
                    if item:
                        item.setBackground(QColor("#f0f0f0"))
                    widget = self.days_table.cellWidget(row, col)
                    if widget:
                        widget.setStyleSheet("background-color: #f0f0f0; padding: 2px;")
        
        # Satır yüksekliğini ayarla
        for row in range(7):
            self.days_table.setRowHeight(row, 30)
            
        # Veritabanından kayıtlı günleri yükle
        self.load_saved_records()
    
    def load_saved_records(self):
        """Veritabanından kayıtlı günleri yükler"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT date, entry_time, lunch_start, lunch_end, exit_time 
            FROM work_records 
            WHERE employee_id = ?
        ''', (self.current_employee_id,))
        
        records = cursor.fetchall()
        for record in records:
            date = QDate.fromString(record[0], "yyyy-MM-dd")
            
            # Tarihi bul ve saatleri ayarla
            for row in range(7):
                date_item = self.days_table.item(row, 0)
                if date_item and date_item.data(Qt.UserRole).toString("yyyy-MM-dd") == date.toString("yyyy-MM-dd"):
                    # Saatleri ayarla
                    for col, time_str in enumerate(record[1:], start=1):
                        time_widget = self.days_table.cellWidget(row, col)
                        if time_widget:
                            time = QTime.fromString(time_str, "HH:mm")
                            time_widget.setTime(time)
                    break
    
    def on_time_changed(self, row):
        """Saat değiştiğinde çağrılır"""
        self.changes_pending = True  # Değişiklik bayrağını işaretle
        self.calculate_total_hours()  # Sadece toplamları güncelle
    
    def save_day_data(self, row):
        """Günlük veriyi kaydeder"""
        if not self.current_employee_id:
            return
            
        # Tarih bilgisini al
        date_item = self.days_table.item(row, 0)
        if not date_item:
            return
            
        date = date_item.data(Qt.UserRole).toString("yyyy-MM-dd")
        
        # Saat verilerini al
        entry_time = self.days_table.cellWidget(row, 1).time().toString("HH:mm")
        lunch_start = self.days_table.cellWidget(row, 2).time().toString("HH:mm")
        lunch_end = self.days_table.cellWidget(row, 3).time().toString("HH:mm")
        exit_time = self.days_table.cellWidget(row, 4).time().toString("HH:mm")
        
        # Veritabanına kaydet
        self.db.add_work_record(
            self.current_employee_id,
            date,
            entry_time,
            lunch_start,
            lunch_end,
            exit_time
        )
    
    def calculate_total_hours(self):
        """Toplam çalışma saatlerini hesaplar"""
        total_minutes = 0
        
        for row in range(7):
            # Günlük çalışma süresini hesapla
            entry_widget = self.days_table.cellWidget(row, 1)
            lunch_start_widget = self.days_table.cellWidget(row, 2)
            lunch_end_widget = self.days_table.cellWidget(row, 3)
            exit_widget = self.days_table.cellWidget(row, 4)
            
            if entry_widget and lunch_start_widget and lunch_end_widget and exit_widget:
                # Sabah mesaisi
                morning_minutes = entry_widget.time().secsTo(lunch_start_widget.time()) / 60
                # Öğleden sonra mesaisi
                afternoon_minutes = lunch_end_widget.time().secsTo(exit_widget.time()) / 60
                
                total_minutes += morning_minutes + afternoon_minutes
        
        # Haftalık toplam süreyi güncelle
        total_hours = total_minutes / 60
        self.total_hours_label.setText(f"{total_hours:.1f}")
    
    def auto_save_all(self):
        """Değişiklikleri otomatik kaydeder"""
        if not self.changes_pending:  # Değişiklik yoksa kaydetme
            return
            
        if self.current_employee_id:
            for row in range(7):
                # Günlük veriyi kaydet
                self.save_day_data(row)
            
            self.changes_pending = False  # Değişiklik bayrağını sıfırla

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = EmployeeDB()
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)
        self.is_updating = False  # Güncelleme durumunu takip etmek için
        self.init_ui()
        
    def init_ui(self):
        # Çalışanlar sekmesi
        self.employee_form = EmployeeForm(self.db)
        self.employee_form.data_updated.connect(self.update_all_tabs)
        self.central_widget.addTab(self.employee_form, "Çalışanlar")
        
        # Aktif çalışanlar için çalışma saati sekmeleri
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, name 
            FROM employees 
            ORDER BY weekly_salary DESC
        ''')
        employees = cursor.fetchall()
        
        for employee_id, name in employees:
            time_form = TimeTrackingForm(self.db, employee_id, name)
            time_form.data_updated.connect(self.update_all_tabs)
            self.central_widget.addTab(time_form, name.upper())
        
        # Pencere ayarları
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle('Çalışan Takip')
        self.show()
    
    def update_all_tabs(self):
        if self.is_updating:  # Zaten güncelleme yapılıyorsa çık
            return
            
        self.is_updating = True  # Güncelleme başlıyor
        
        try:
            # Aktif çalışanları al
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT id, name 
                FROM employees 
                ORDER BY weekly_salary DESC
            ''')
            active_employees = {emp_id: name for emp_id, name in cursor.fetchall()}
            
            # Mevcut sekmeleri kontrol et
            index = 0
            while index < self.central_widget.count():
                widget = self.central_widget.widget(index)
                if isinstance(widget, TimeTrackingForm):
                    if widget.current_employee_id not in active_employees:
                        # Çalışan artık aktif değilse sekmeyi kaldır
                        self.central_widget.removeTab(index)
                        continue
                    else:
                        # Aktif çalışanın sekmesini güncelle
                        widget.load_week_days()
                        # Çalışanı işlenmiş olarak işaretle
                        active_employees.pop(widget.current_employee_id)
                index += 1
            
            # Yeni aktif çalışanlar için sekme ekle
            for emp_id, name in active_employees.items():
                time_form = TimeTrackingForm(self.db, emp_id, name)
                time_form.data_updated.connect(self.update_all_tabs)
                self.central_widget.addTab(time_form, name.upper())
        finally:
            self.is_updating = False  # Güncelleme bitti
    
    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())