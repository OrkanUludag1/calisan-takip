import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QTabWidget, QTimeEdit, 
                             QMessageBox, QComboBox, QCheckBox, QSizePolicy, QHBoxLayout, QFrame, QHeaderView,
                             QGraphicsOpacityEffect, QGroupBox, QFormLayout)
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
        self.current_id = None  # Düzenlenen çalışanın ID'si
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("<h1>Çalışan Yönetimi</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("margin-bottom: 15px; color: #2c3e50;")
        main_layout.addWidget(title_label)
        
        # Form alanları - Grup kutusu içinde 
        form_group = QGroupBox("Çalışan Bilgileri")
        form_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #f9f9f9;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #fcfcfc;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #f0f8ff;
            }
        """)
        
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Çalışan Adı")
        self.name_edit.setMinimumHeight(30)
        form_layout.addRow("<b>İsim:</b>", self.name_edit)
        
        self.weekly_salary_edit = QLineEdit()
        self.weekly_salary_edit.setPlaceholderText("Haftalık Ücret")
        self.weekly_salary_edit.setMinimumHeight(30)
        form_layout.addRow("<b>Haftalık Ücret:</b>", self.weekly_salary_edit)
        
        self.daily_food_edit = QLineEdit()
        self.daily_food_edit.setPlaceholderText("Günlük Yemek Ücreti")
        self.daily_food_edit.setMinimumHeight(30)
        form_layout.addRow("<b>Günlük Yemek:</b>", self.daily_food_edit)
        
        self.daily_transport_edit = QLineEdit()
        self.daily_transport_edit.setPlaceholderText("Günlük Yol Ücreti")
        self.daily_transport_edit.setMinimumHeight(30)
        form_layout.addRow("<b>Günlük Yol:</b>", self.daily_transport_edit)
        
        main_layout.addWidget(form_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 15, 0, 15)
        
        self.add_btn = QPushButton("Ekle")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.add_employee)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.add_btn)
        
        self.update_btn = QPushButton("Güncelle")
        self.update_btn.setMinimumHeight(40)
        self.update_btn.clicked.connect(self.update_employee)
        self.update_btn.setEnabled(False)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        button_layout.addWidget(self.update_btn)
        
        self.clear_btn = QPushButton("Temizle")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        button_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(button_layout)
        
        # Çalışan listesi - Grup kutusu içinde
        list_group = QGroupBox("Çalışan Listesi")
        list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #f9f9f9;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                alternate-row-color: #f9f9f9;
                gridline-color: #dcdcdc;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #dcdcdc;
                border-bottom-width: 2px;
                border-bottom-color: #bdc3c7;
                font-weight: bold;
            }
        """)
        
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(10, 20, 10, 10)
        
        self.employee_list = QTableWidget()
        self.employee_list.setColumnCount(4)
        self.employee_list.setHorizontalHeaderLabels(["İsim", "Haftalık Ücret", "Günlük Yemek", "Günlük Yol"])
        self.employee_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_list.setSelectionMode(QTableWidget.SingleSelection)
        self.employee_list.itemDoubleClicked.connect(self.edit_employee)
        self.employee_list.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        self.employee_list.setAlternatingRowColors(True)
        self.employee_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # İsim sütunu esnek
        
        list_layout.addWidget(self.employee_list)
        
        main_layout.addWidget(list_group)
        
        self.setLayout(main_layout)
        
        # Veriyi yükle
        self.load_employees()
    
    def add_employee(self):
        try:
            name = self.name_edit.text().strip()
            weekly_salary = float(self.weekly_salary_edit.text().replace(".", "").replace(",", "."))
            daily_food = float(self.daily_food_edit.text().replace(".", "").replace(",", "."))
            daily_transport = float(self.daily_transport_edit.text().replace(".", "").replace(",", "."))
            
            if not name:
                QMessageBox.warning(self, "Uyarı", "İsim alanı boş olamaz!")
                return
            
            if self.current_id is None:  # Yeni çalışan ekleme
                self.db.add_employee(name, weekly_salary, daily_food, daily_transport)
            else:  # Mevcut çalışanı güncelleme
                cursor = self.db.conn.cursor()
                cursor.execute('''
                UPDATE employees 
                SET name=?, weekly_salary=?, daily_food=?, daily_transport=?
                WHERE id=?
                ''', (name, weekly_salary, daily_food, daily_transport, self.current_id))
                self.db.conn.commit()
            
            self.clear_form()
            self.load_employees()
            self.data_updated.emit()
            
        except ValueError:
            QMessageBox.warning(self, "Uyarı", "Lütfen ücret alanlarına geçerli sayısal değerler girin!")
    
    def update_employee(self):
        self.add_employee()  # Aynı fonksiyonu kullan ama current_id ile güncelleme yap
    
    def edit_employee(self, item):
        row = item.row()
        employee_id = int(self.employee_list.item(row, 0).data(Qt.UserRole))
        
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT name, weekly_salary, daily_food, daily_transport FROM employees WHERE id=?', (employee_id,))
        employee = cursor.fetchone()
        
        if employee:
            self.current_id = employee_id
            self.name_edit.setText(employee[0])
            self.weekly_salary_edit.setText(str(employee[1]))
            self.daily_food_edit.setText(str(employee[2]))
            self.daily_transport_edit.setText(str(employee[3]))
            
            self.add_btn.setVisible(False)
            self.update_btn.setVisible(True)
            self.clear_btn.setVisible(True)
    
    def clear_form(self):
        self.current_id = None
        self.name_edit.clear()
        self.weekly_salary_edit.clear()
        self.daily_food_edit.clear()
        self.daily_transport_edit.clear()
        
        self.add_btn.setVisible(True)
        self.update_btn.setVisible(False)
        self.clear_btn.setVisible(False)
    
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
                QTableWidgetItem(str(weekly_salary)),
                QTableWidgetItem(str(daily_food)),
                QTableWidgetItem(str(daily_transport))
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
            title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
            left_layout.addWidget(title_label)
        
        # Tarih aralığı container'ı
        self.date_range_label = QLabel()
        self.date_range_label.setAlignment(Qt.AlignCenter)
        self.date_range_label.setStyleSheet("""
            font-weight: bold;
            padding: 8px;
            background-color: #f5f5f5;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            margin-bottom: 10px;
            color: #34495e;
        """)
        left_layout.addWidget(self.date_range_label)
        
        # Tablo Grup Kutusu
        time_table_group = QGroupBox("Zaman Çizelgesi")
        time_table_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #f9f9f9;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                alternate-row-color: #f9f9f9;
                gridline-color: #dcdcdc;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #dcdcdc;
                border-bottom-width: 2px;
                border-bottom-color: #bdc3c7;
                font-weight: bold;
            }
            QTimeEdit {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QTimeEdit:focus {
                border: 1px solid #3498db;
                background-color: #f0f8ff;
            }
        """)
        
        time_table_layout = QVBoxLayout(time_table_group)
        
        # Tablo
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(5)
        self.days_table.setRowCount(7)
        self.days_table.setHorizontalHeaderLabels([
            "Gün", "Giriş", "Öğle Başlangıç",
            "Öğle Bitiş", "Çıkış"
        ])
        self.days_table.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        self.days_table.setAlternatingRowColors(True)
        
        time_table_layout.addWidget(self.days_table)
        left_layout.addWidget(time_table_group)
        
        # Sağ taraf (toplam bilgileri)
        right_layout = QVBoxLayout()
        
        # Özet Grup Kutusu
        summary_group = QGroupBox("Haftalık Özet")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 25px;
                padding-top: 15px;
                min-width: 250px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #f9f9f9;
            }
            QLabel {
                padding: 5px;
            }
        """)
        
        summary_layout = QVBoxLayout(summary_group)
        
        # Toplam saat ve ücretler
        self.total_hours_label = QLabel("Toplam Saat: 0")
        self.total_hours_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        summary_layout.addWidget(self.total_hours_label)
        
        self.total_amount_label = QLabel("Haftalık Ücret: 0 TL")
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        summary_layout.addWidget(self.total_amount_label)
        
        self.food_total_label = QLabel("Yemek Toplam: 0 TL")
        self.food_total_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        summary_layout.addWidget(self.food_total_label)
        
        self.transport_total_label = QLabel("Yol Toplam: 0 TL")
        self.transport_total_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        summary_layout.addWidget(self.transport_total_label)
        
        self.gross_total_label = QLabel("Brüt Toplam: 0 TL")
        self.gross_total_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #27ae60;")
        summary_layout.addWidget(self.gross_total_label)
        
        # Çalışma durumu ayarları
        active_layout = QVBoxLayout()
        
        active_label = QLabel("Çalışma Durumu:")
        active_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        active_layout.addWidget(active_label)
        
        # Gün durumu checkboxları
        day_status_layout = QVBoxLayout()
        day_status_layout.setSpacing(8)
        
        self.day_status_checkboxes = []
        
        for i in range(7):
            day_checkbox = QCheckBox(f"Gün {i+1}")
            day_checkbox.setStyleSheet("""
                QCheckBox {
                    padding: 5px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #bdc3c7;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #2ecc71;
                    border: 2px solid #27ae60;
                }
            """)
            day_checkbox.setChecked(True)
            day_checkbox.stateChanged.connect(lambda state, idx=i: self.on_day_status_changed(idx, state))
            day_status_layout.addWidget(day_checkbox)
            self.day_status_checkboxes.append(day_checkbox)
        
        active_layout.addLayout(day_status_layout)
        summary_layout.addLayout(active_layout)
        
        # Durum mesajı
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            padding: 5px;
            color: #27ae60;
            font-style: italic;
            min-height: 20px;
        """)
        summary_layout.addWidget(self.status_label)
        
        right_layout.addWidget(summary_group)
        right_layout.addStretch()
        
        # Ana layouta ekle
        main_layout.addLayout(left_layout, 7)  # Sol taraf daha geniş
        main_layout.addLayout(right_layout, 3)  # Sağ taraf daha dar
        
        # Ana layout'u widget'a ekle
        layout.addLayout(main_layout)
        self.setLayout(layout)
        
        # Değişiklik bayrağı
        self.changes_pending = False
    
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
        
        self.db = EmployeeDB("employee_tracking.db")
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Çalışan Takip Sistemi")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget {
                background-color: white;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d6d9dc;
            }
        """)
        
        # Ana widget ve tab widget
        self.central_widget = QTabWidget()
        self.central_widget.setTabPosition(QTabWidget.North)
        self.central_widget.setMovable(True)
        self.setCentralWidget(self.central_widget)
        
        # Çalışan ekleme sekmesi
        self.employee_form = EmployeeForm(self.db)
        self.employee_form.data_updated.connect(self.update_all_tabs)
        self.central_widget.addTab(self.employee_form, "ÇALIŞANLAR")
        
        # Mevcut çalışanlar için sekmeleri yükle
        self.load_employee_tabs()
        
        self.show()
    
    def load_employee_tabs(self):
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
    
    def update_all_tabs(self):
        if self.central_widget.count() < 2:  # Çalışan sekmesi yoksa çık
            return
            
        # Aktif çalışanları al
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT id, name 
            FROM employees 
            ORDER BY weekly_salary DESC
        ''')
        active_employees = {emp_id: name for emp_id, name in cursor.fetchall()}
        
        # Mevcut sekmeleri kontrol et
        index = 1
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
    
    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())