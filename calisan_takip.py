import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QTabWidget, QTimeEdit, 
                             QMessageBox, QComboBox, QCheckBox, QSizePolicy, QHBoxLayout, QFrame, QHeaderView,
                             QGraphicsOpacityEffect, QGridLayout)
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
        
        # Otomatik kaydetme zamanlayıcısı
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(2000)  # 2 saniyede bir kaydet
        
        # Mevcut haftanın başlangıç tarihi
        self.current_date = QDate.currentDate()
        self.current_date = self.current_date.addDays(-self.current_date.dayOfWeek() + 1)
        
        # Durum kontrol kutuları
        self.day_status_checkboxes = []
        
        # Toplamları tutacak değişkenler
        self.current_totals = {
            'total_hours': 0,
            'work_salary': 0,
            'transport_total': 0,
            'food_total': 0,
            'total_amount': 0
        }
        
        self.initUI()
        self.load_week_days()  # Haftayı yükle
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Sol: Tablo, Sağ: Özetler
        main_layout = QHBoxLayout()
        
        # Tarih aralığını göster
        self.date_range_group = QFrame()
        self.date_range_group.setFrameShape(QFrame.StyledPanel)
        self.date_range_group.setStyleSheet("background-color: #f8f9fa; border-radius: 5px;")
        date_range_layout = QHBoxLayout(self.date_range_group)
        
        # Current date'i Pazartesi olarak ayarla (haftanın başlangıcı)
        self.current_date = QDate.currentDate()
        self.current_date = self.current_date.addDays(-self.current_date.dayOfWeek() + 1)
        
        start_date = self.current_date
        end_date = self.current_date.addDays(6)
        
        date_label = QLabel(f"<b>Tarih Aralığı:</b> {start_date.toString('dd.MM.yyyy')} - {end_date.toString('dd.MM.yyyy')}")
        date_range_layout.addWidget(date_label)
        layout.addWidget(self.date_range_group)
        
        # Tablo
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(6)  # Gün, Durum, Giriş, Öğle Başlangıç, Öğle Bitiş, Çıkış
        self.days_table.setRowCount(7)
        self.days_table.setHorizontalHeaderLabels([
            "Gün", "Durum", "Giriş", "Öğle Başlangıç",
            "Öğle Bitiş", "Çıkış"
        ])
        self.days_table.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        
        # Tablo için kutu
        table_group = QFrame()
        table_group.setFrameShape(QFrame.StyledPanel)
        table_group.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 5px;
            padding: 5px;
        """)
        table_layout = QVBoxLayout(table_group)
        table_layout.addWidget(QLabel("<b>Zaman Çizelgesi</b>"))
        table_layout.addWidget(self.days_table)
        
        # Özet bölümü
        summary_group = QFrame()
        summary_group.setFrameShape(QFrame.StyledPanel)
        summary_group.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 5px;
            padding: 10px;
        """)
        summary_layout = QVBoxLayout(summary_group)
        
        # Çalışma saati
        hours_layout = QVBoxLayout()
        hours_layout.setContentsMargins(0, 0, 0, 0)
        hours_layout.setSpacing(0)
        hours_title = QLabel("Çalışma Saati")
        self.total_hours_label = QLabel("0.0")
        hours_layout.addWidget(hours_title)
        hours_layout.addWidget(self.total_hours_label)
        
        # Haftalık ücret
        salary_layout = QVBoxLayout()
        salary_layout.setContentsMargins(0, 0, 0, 0)
        salary_layout.setSpacing(0)
        salary_title = QLabel("Haftalık Ücret")
        self.weekly_salary_label = QLabel("0 TL")
        salary_layout.addWidget(salary_title)
        salary_layout.addWidget(self.weekly_salary_label)
        
        # Yol ücreti toplamı
        transport_layout = QVBoxLayout()
        transport_layout.setContentsMargins(0, 0, 0, 0)
        transport_layout.setSpacing(0)
        transport_title = QLabel("Yol Ücreti")
        self.transport_total_label = QLabel("0 TL")
        transport_layout.addWidget(transport_title)
        transport_layout.addWidget(self.transport_total_label)
        
        # Yemek ücreti toplamı
        food_layout = QVBoxLayout()
        food_layout.setContentsMargins(0, 0, 0, 0)
        food_layout.setSpacing(0)
        food_title = QLabel("Yemek Ücreti")
        self.food_total_label = QLabel("0 TL")
        food_layout.addWidget(food_title)
        food_layout.addWidget(self.food_total_label)
        
        # Toplam tutar
        total_layout = QVBoxLayout()
        total_layout.setContentsMargins(0, 0, 0, 0)
        total_layout.setSpacing(0)
        total_title = QLabel("Toplam")
        self.gross_total_label = QLabel("0 TL")
        total_layout.addWidget(total_title)
        total_layout.addWidget(self.gross_total_label)
        
        # Stil tanımlamaları
        title_style = """
            color: #495057;
            font-weight: bold;
            padding: 5px;
            background-color: #e9ecef;
            border-radius: 3px 3px 0 0;
            margin-bottom: 2px;
        """
        
        value_style = """
            color: #212529;
            font-size: 16px;
            padding: 5px;
            background-color: #f8f9fa;
            border-radius: 0 0 3px 3px;
            margin-bottom: 10px;
        """
        
        # Stilleri uygula
        for title in [hours_title, salary_title, transport_title, food_title, total_title]:
            title.setStyleSheet(title_style)
            title.setAlignment(Qt.AlignCenter)
        
        for value in [self.total_hours_label, self.weekly_salary_label, 
                     self.transport_total_label, self.food_total_label, 
                     self.gross_total_label]:
            value.setStyleSheet(value_style)
            value.setAlignment(Qt.AlignCenter)
        
        # Durum mesajı
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            color: #28a745;
            font-style: italic;
            padding: 5px;
        """)
        
        # Özetleri ekle
        grid_layout = QGridLayout()
        grid_layout.addLayout(hours_layout, 0, 0)
        grid_layout.addLayout(salary_layout, 0, 1)
        grid_layout.addLayout(transport_layout, 1, 0)
        grid_layout.addLayout(food_layout, 1, 1)
        grid_layout.addLayout(total_layout, 2, 0, 1, 2)  # 2 sütunu da kapla
        
        summary_layout.addLayout(grid_layout)
        summary_layout.addWidget(self.status_label)
        
        # Ana düzeni oluştur
        main_layout.addWidget(table_group, 7)  # 70% genişlik
        main_layout.addWidget(summary_group, 3)  # 30% genişlik
        
        layout.addLayout(main_layout)
        self.setLayout(layout)
    
    def load_week_days(self):
        """Haftalık günleri yükler"""
        self.days_table.clearContents()
        
        # Varsayılan saatler
        default_entry = QTime(8, 0)  # 08:00
        default_lunch_start = QTime(12, 0)  # 12:00
        default_lunch_end = QTime(13, 0)  # 13:00
        default_exit = QTime(17, 0)  # 17:00
        
        # Tablonun başlangıç gününü belirle (Pazartesi)
        current_week_start = self.current_date
        
        # Tablo başlıklarını ayarla
        self.days_table.setHorizontalHeaderLabels([
            "Gün", "Durum", "Giriş", "Öğle Başlangıç",
            "Öğle Bitiş", "Çıkış"
        ])
        
        # Tablo başlıklarını daha okunaklı hale getir
        header = self.days_table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #4a86e8;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                font-size: 12px;
            }
        """)
        
        # Sütun genişliklerini ayarla
        self.days_table.setColumnCount(6)
        
        # Tarih sütunu sabit genişlikte
        self.days_table.setColumnWidth(0, 120)
        self.days_table.setColumnWidth(1, 60)
        
        # Diğer sütunlar eşit genişlikte
        for col in range(2, 6):
            self.days_table.setColumnWidth(col, 110)
        
        # Sütun modlarını ayarla
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Tarih sütunu sabit
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Durum sütunu sabit
        for col in range(2, 6):
            header.setSectionResizeMode(col, QHeaderView.Fixed)  # Saat sütunları sabit
        
        # Günleri tabloya ekle
        for row in range(7):
            current_day = current_week_start.addDays(row)
            day_name = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][row]
            is_weekend = current_day.dayOfWeek() in [6, 7]  # 6=Cumartesi, 7=Pazar
            
            # Gün hücresi - Sadece gün adını göster (tarih olmadan)
            day_item = QTableWidgetItem(day_name)
            day_item.setData(Qt.UserRole, current_day)  # Tarih verisini sakla
            day_item.setFlags(day_item.flags() & ~Qt.ItemIsEditable)  # Düzenlenemez yap
            day_item.setTextAlignment(Qt.AlignCenter)
            self.days_table.setItem(row, 0, day_item)
            
            # Durum hücresi
            status_checkbox = QCheckBox()
            status_checkbox.setChecked(True)
            status_checkbox.stateChanged.connect(lambda state, r=row: self.on_day_status_changed(r))
            self.days_table.setCellWidget(row, 1, status_checkbox)
            self.day_status_checkboxes.append(status_checkbox)
            
            # Saat hücreleri
            for col, default_time in enumerate([default_entry, default_lunch_start, default_lunch_end, default_exit], start=2):
                time_edit = QTimeEdit()
                time_edit.setDisplayFormat("HH:mm")
                time_edit.setTime(default_time)
                time_edit.timeChanged.connect(lambda time, r=row: self.on_time_changed(r))
                time_edit.setStyleSheet("QTimeEdit { padding: 4px; }")
                self.days_table.setCellWidget(row, col, time_edit)
            
            # Hafta sonu günlerini gri yap
            if is_weekend:
                for col in range(6):
                    item = self.days_table.item(row, col)
                    if item:
                        item.setBackground(QColor("#f0f0f0"))
                    widget = self.days_table.cellWidget(row, col)
                    if widget:
                        effect = QGraphicsOpacityEffect(widget)
                        effect.setOpacity(0.7)
                        widget.setGraphicsEffect(effect)
        
        # Kaydedilmiş kayıtları yükle
        if self.current_employee_id:
            self.load_saved_records()
            self.calculate_total_hours()  # Toplamları güncelle
    
    def on_day_status_changed(self, row):
        """Durum değiştiğinde çağrılır"""
        self.changes_pending = True  # Değişiklik bayrağını işaretle
        self.calculate_total_hours()  # Sadece toplamları güncelle
    
    def calculate_total_hours(self):
        """Toplam çalışma saatlerini hesaplar"""
        if not self.current_employee_id:
            return
            
        # Çalışanın haftalık ücretini al
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT weekly_salary, daily_food, daily_transport 
            FROM employees 
            WHERE id=?
        ''', (self.current_employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            return
            
        weekly_salary, daily_food, daily_transport = employee
        
        # Toplam çalışma süresini ve aktif gün sayısını hesapla
        total_minutes = 0
        active_days = 0
        
        for row in range(7):
            # Geçerli günü al
            date_item = self.days_table.item(row, 0)
            if not date_item:
                continue
                
            current_day = date_item.data(Qt.UserRole)
            is_weekend = current_day.dayOfWeek() in [6, 7]  # 6=Cumartesi, 7=Pazar
            
            # Zamanları al
            entry_widget = self.days_table.cellWidget(row, 2)
            lunch_start_widget = self.days_table.cellWidget(row, 3)
            lunch_end_widget = self.days_table.cellWidget(row, 4)
            exit_widget = self.days_table.cellWidget(row, 5)
            
            if entry_widget and lunch_start_widget and lunch_end_widget and exit_widget:
                # Checkbox kontrolü
                is_active = True
                if row < len(self.day_status_checkboxes):
                    is_active = self.day_status_checkboxes[row].isChecked()
                
                if is_active:
                    # Aktif gün sayısını artır
                    active_days += 1
                    
                    # Sabah vardiyası süresi (dakika)
                    morning_minutes = entry_widget.time().secsTo(lunch_start_widget.time()) / 60
                    
                    # Öğleden sonra vardiyası süresi (dakika)
                    afternoon_minutes = lunch_end_widget.time().secsTo(exit_widget.time()) / 60
                    
                    # Günlük toplamı ekle
                    total_minutes += morning_minutes + afternoon_minutes
        
        # Toplam süreyi saat cinsine çevir
        total_hours = total_minutes / 60
        
        # Toplam değerleri hesapla
        work_salary = weekly_salary
        food_total = daily_food * active_days
        transport_total = daily_transport * active_days
        total_amount = work_salary + food_total + transport_total
        
        # Değerleri görüntüle
        self.total_hours_label.setText(f"{total_hours:.1f}")
        self.weekly_salary_label.setText(self.format_currency(work_salary))
        self.food_total_label.setText(self.format_currency(food_total))
        self.transport_total_label.setText(self.format_currency(transport_total))
        self.gross_total_label.setText(self.format_currency(total_amount))
        
        # Toplamları kaydet
        self.current_totals = {
            'total_hours': total_hours,
            'work_salary': work_salary,
            'transport_total': transport_total,
            'food_total': food_total,
            'total_amount': total_amount
        }
    
    def auto_save_all(self):
        """Değişiklikleri otomatik kaydeder"""
        if not hasattr(self, 'changes_pending') or not self.changes_pending:
            return
            
        if self.current_employee_id:
            for row in range(7):
                self.save_day_data(row)
            
            self.changes_pending = False
            self.status_label.setText("Değişiklikler kaydedildi")
            
            # 3 saniye sonra durum mesajını temizle
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))
    
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
        entry_time = self.days_table.cellWidget(row, 2).time().toString("HH:mm")
        lunch_start = self.days_table.cellWidget(row, 3).time().toString("HH:mm")
        lunch_end = self.days_table.cellWidget(row, 4).time().toString("HH:mm")
        exit_time = self.days_table.cellWidget(row, 5).time().toString("HH:mm")
        
        # Veritabanına kaydet
        self.db.add_work_record(
            self.current_employee_id,
            date,
            entry_time,
            lunch_start,
            lunch_end,
            exit_time
        )
        
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
                    for col, time_str in enumerate(record[1:], start=2):
                        time_widget = self.days_table.cellWidget(row, col)
                        if time_widget:
                            time = QTime.fromString(time_str, "HH:mm")
                            time_widget.setTime(time)
                    break
    
    def on_time_changed(self, row):
        """Saat değiştiğinde çağrılır"""
        self.changes_pending = True  # Değişiklik bayrağını işaretle
        self.calculate_total_hours()  # Sadece toplamları güncelle
    
    def format_currency(self, value):
        """Para birimini istenilen formata çevirir:
        - Birler basamağı 5'e yuvarlanır
        - Binlik ayırıcı eklenir (örn: 1.000)
        - Ondalık kısmı olmaz
        - TL ibaresi eklenir
        """
        # Birler basamağını 5'e yuvarla
        rounded_value = round(value / 5) * 5
        
        # Binlik ayırıcı ekle
        formatted = f"{rounded_value:,.0f}".replace(",", ".")
        
        # TL ibaresi ekle
        return f"{formatted} TL"

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