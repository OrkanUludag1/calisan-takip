import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QTabWidget, QTimeEdit, 
                             QMessageBox, QComboBox, QCheckBox, QSizePolicy, QHBoxLayout, QFrame, QHeaderView,
                             QStyledItemDelegate, QGroupBox)
from PyQt5.QtCore import Qt, QTime, QDate, pyqtSignal, QObject, QTimer, QEventLoop
from PyQt5.QtGui import QFont, QColor
from PyQt5.Qt import QGraphicsOpacityEffect
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
            daily_transport REAL NOT NULL,
            is_active INTEGER DEFAULT 1
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
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )''')
        self.conn.commit()
    
    def add_employee(self, name, weekly_salary, daily_food, daily_transport, is_active=1):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO employees (name, weekly_salary, daily_food, daily_transport, is_active) 
        VALUES (?, ?, ?, ?, ?)
        ''', (name, weekly_salary, daily_food, daily_transport, is_active))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_employees(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, name, weekly_salary, daily_food, daily_transport, is_active 
        FROM employees
        ''')
        return cursor.fetchall()
    
    def update_employee_status(self, employee_id, is_active):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE employees SET is_active = ? WHERE id = ?', (1 if is_active else 0, employee_id))
        self.conn.commit()
    
    def add_work_record(self, employee_id, date, entry_time, lunch_start, lunch_end, exit_time):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM work_records WHERE employee_id=? AND date=?', 
                     (employee_id, date))
        record = cursor.fetchone()
        
        if record:
            cursor.execute('''
            UPDATE work_records 
            SET entry_time=?, lunch_start=?, lunch_end=?, exit_time=?
            WHERE id=?
            ''', (entry_time, lunch_start, lunch_end, exit_time, record[0]))
        else:
            cursor.execute('''
            INSERT INTO work_records (employee_id, date, entry_time, lunch_start, lunch_end, exit_time)
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
        AND (e.is_active = 1 OR EXISTS (
            SELECT 1 FROM work_records wr2 
            WHERE wr2.employee_id = wr.employee_id 
            AND wr2.date = wr.date
            AND (wr2.entry_time IS NOT NULL OR wr2.lunch_start IS NOT NULL 
                OR wr2.lunch_end IS NOT NULL OR wr2.exit_time IS NOT NULL)
        ))
        ORDER BY wr.date
        ''', (employee_id, start_date, end_date))
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()

class TimeEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QTimeEdit(parent)
        editor.setDisplayFormat("HH:mm")
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value:
            time = QTime.fromString(value, "HH:mm")
            editor.setTime(time)
            
    def setModelData(self, editor, model, index):
        model.setData(index, editor.time().toString("HH:mm"))

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
        self.employee_list.setColumnCount(5)
        self.employee_list.setHorizontalHeaderLabels(["İsim", "Haftalık Ücret", "Günlük Yemek", "Günlük Yol", "Durum"])
        self.employee_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_list.setSelectionMode(QTableWidget.SingleSelection)
        self.employee_list.itemDoubleClicked.connect(self.edit_employee)
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
        
        for row, (emp_id, name, weekly_salary, daily_food, daily_transport, is_active) in enumerate(employees):
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
            
            # Tüm öğeleri ekle ve pasif durumdaysa flulaştır
            for col, item in enumerate(items):
                if col > 0:  # İlk öğe (name_item) zaten ayarlandı
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Düzenlemeyi devre dışı bırak
                self.employee_list.setItem(row, col, item)
                if not is_active:
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                    item.setForeground(Qt.gray)
            
            status_checkbox = QCheckBox()
            status_checkbox.setChecked(bool(is_active))
            status_checkbox.stateChanged.connect(lambda state, id=emp_id: self.update_employee_status(id, state))
            
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.addWidget(status_checkbox)
            status_layout.setAlignment(Qt.AlignCenter)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_widget.setLayout(status_layout)
            
            self.employee_list.setCellWidget(row, 4, status_widget)
        
        self.employee_list.resizeColumnsToContents()

    def update_employee_status(self, employee_id, state):
        cursor = self.db.conn.cursor()
        cursor.execute('UPDATE employees SET is_active=? WHERE id=?', (1 if state else 0, employee_id))
        self.db.conn.commit()
        self.load_employees()
        self.data_updated.emit()

class TimeTrackingForm(QWidget):
    data_updated = pyqtSignal()
    
    def __init__(self, db, employee_id=None):
        super().__init__()
        self.db = db
        self.current_employee_id = employee_id
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(60000)  # Her 1 dakikada bir otomatik kaydet
        
        # Mevcut haftanın başlangıç tarihi
        self.current_date = QDate.currentDate()
        self.current_date = self.current_date.addDays(-self.current_date.dayOfWeek() + 1)
        
        self.current_totals = {
            'total_hours': 0,
            'work_salary': 0,
            'transport_total': 0,
            'food_total': 0,
            'total_amount': 0
        }
        
        self.init_ui()
        self.load_week_days()
    
    def init_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        
        # Tablo
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(7)
        self.days_table.setRowCount(7)
        self.days_table.setHorizontalHeaderLabels([
            "Durum",
            "Tarih",
            "Giriş",
            "Öğle Başlangıç",
            "Öğle Bitiş",
            "Çıkış",
            "Toplam"
        ])
        
        # TimeEdit delegasyonu
        delegate = TimeEditDelegate()
        self.days_table.setItemDelegateForColumn(2, delegate)
        self.days_table.setItemDelegateForColumn(3, delegate)
        self.days_table.setItemDelegateForColumn(4, delegate)
        self.days_table.setItemDelegateForColumn(5, delegate)
        
        left_layout.addWidget(self.days_table)
        
        # Sağ taraf (toplam bilgileri)
        right_widget = QWidget()
        right_widget.setFixedWidth(250)  # Sabit genişlik
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(right_widget)
        
        # Toplam bilgileri için grup kutusu
        totals_group = QGroupBox("Haftalık Özet")
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
        
        # Otomatik kaydetme için zamanlayıcı
        self.save_timer = QTimer()
        self.save_timer.setInterval(1000)  # 1 saniye
        self.save_timer.timeout.connect(self.save_week_data)
        self.save_timer.start()
    
    def load_week_days(self):
        if not self.current_employee_id:
            return
            
        start_of_week = self.current_date
        
        # Varsayılan saatler - Tüm günler için aynı
        default_times = {
            'entry': QTime(8, 15),      # 08:15
            'lunch_start': QTime(13, 15), # 13:15
            'lunch_end': QTime(13, 45),   # 13:45
            'exit': QTime(18, 45)       # 18:45
        }
        
        for i in range(7):
            current_date = start_of_week.addDays(i)
            date_str = current_date.toString("yyyy-MM-dd")
            is_weekend = current_date.dayOfWeek() in [6, 7]  # 6=Cumartesi, 7=Pazar
            
            # Aktif/Pasif checkbox
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.setAlignment(Qt.AlignCenter)
            
            checkbox = QCheckBox()
            checkbox.setChecked(not is_weekend)  # Hafta içi günler varsayılan olarak aktif
            checkbox.stateChanged.connect(lambda state, row=i: self.on_day_status_changed(row, state))
            status_layout.addWidget(checkbox)
            
            self.days_table.setCellWidget(i, 0, status_widget)
            
            # Tarih sütunu
            date_item = QTableWidgetItem(current_date.toString("dd.MM.yyyy ddd"))
            date_item.setData(Qt.UserRole, date_str)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.days_table.setItem(i, 1, date_item)
            
            # Giriş saati
            entry_edit = QTimeEdit()
            entry_edit.setDisplayFormat("HH:mm")
            entry_edit.setTime(default_times['entry'])
            entry_edit.timeChanged.connect(lambda time, row=i: self.on_time_changed(row))
            self.days_table.setCellWidget(i, 2, entry_edit)
            
            # Öğle başlangıç
            lunch_start = QTimeEdit()
            lunch_start.setDisplayFormat("HH:mm")
            lunch_start.setTime(default_times['lunch_start'])
            lunch_start.timeChanged.connect(lambda time, row=i: self.on_time_changed(row))
            self.days_table.setCellWidget(i, 3, lunch_start)
            
            # Öğle bitiş
            lunch_end = QTimeEdit()
            lunch_end.setDisplayFormat("HH:mm")
            lunch_end.setTime(default_times['lunch_end'])
            lunch_end.timeChanged.connect(lambda time, row=i: self.on_time_changed(row))
            self.days_table.setCellWidget(i, 4, lunch_end)
            
            # Çıkış saati
            exit_edit = QTimeEdit()
            exit_edit.setDisplayFormat("HH:mm")
            exit_edit.setTime(default_times['exit'])
            exit_edit.timeChanged.connect(lambda time, row=i: self.on_time_changed(row))
            self.days_table.setCellWidget(i, 5, exit_edit)
            
            # Toplam sütunu
            total_item = QTableWidgetItem("10:00")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            total_item.setTextAlignment(Qt.AlignCenter)
            self.days_table.setItem(i, 6, total_item)
            
            # Hafta sonu ise satırı devre dışı bırak
            if is_weekend:
                for col in range(2, 7):
                    widget = self.days_table.cellWidget(i, col)
                    if isinstance(widget, QTimeEdit):
                        widget.setEnabled(False)
                        widget.setStyleSheet("background-color: #f0f0f0;")
                    elif isinstance(widget, QTableWidgetItem):
                        widget.setBackground(QColor("#f0f0f0"))
                date_item.setBackground(QColor("#f0f0f0"))
                checkbox.setEnabled(False)  # Hafta sonu günleri için checkbox'ı devre dışı bırak
            
            # İlk yüklemede aktif/pasif durumuna göre alanları ayarla
            self.on_day_status_changed(i, Qt.Checked if checkbox.isChecked() else Qt.Unchecked)
            
        self.calculate_total_hours()
        
    def on_time_changed(self, row):
        """Saat değiştiğinde çağrılır"""
        self.save_day_data(row)
        self.calculate_total_hours()

    def auto_save_all(self):
        for row in range(7):
            self.save_day_data(row)
        self.update_status("Otomatik kayıt yapıldı")
    
    def update_status(self, message):
        self.status_label.setText(message)
        QTimer.singleShot(3000, lambda: self.status_label.clear())
    
    def save_day_data(self, row):
        if not self.current_employee_id:
            return
            
        date_item = self.days_table.item(row, 1)
        if not date_item:
            return
            
        date = date_item.data(Qt.UserRole)
        
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
        
        self.data_updated.emit()
    
    def calculate_total_hours(self):
        if not self.current_employee_id:
            return
            
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT weekly_salary, daily_food, daily_transport 
            FROM employees 
            WHERE id = ?
        ''', (self.current_employee_id,))
        employee_data = cursor.fetchone()
        
        if not employee_data:
            return
            
        weekly_salary, daily_food, daily_transport = employee_data
        
        total_hours = 0
        work_days = 0
        
        for row in range(7):
            # Önce günün aktif olup olmadığını kontrol et
            status_widget = self.days_table.cellWidget(row, 0)
            if not status_widget or not status_widget.findChild(QCheckBox).isChecked():
                continue
                
            entry_widget = self.days_table.cellWidget(row, 2)
            lunch_start_widget = self.days_table.cellWidget(row, 3)
            lunch_end_widget = self.days_table.cellWidget(row, 4)
            exit_widget = self.days_table.cellWidget(row, 5)
            
            if not all([entry_widget, lunch_start_widget, lunch_end_widget, exit_widget]):
                continue
            
            # Saat hesaplamaları
            entry_time = entry_widget.time()
            lunch_start = lunch_start_widget.time()
            lunch_end = lunch_end_widget.time()
            exit_time = exit_widget.time()
            
            # Öğle molası öncesi çalışma süresi
            morning_seconds = entry_time.secsTo(lunch_start)
            # Öğle molası sonrası çalışma süresi
            afternoon_seconds = lunch_end.secsTo(exit_time)
            
            # Toplam çalışma süresi (saat)
            day_hours = (morning_seconds + afternoon_seconds) / 3600
            total_hours += day_hours
            work_days += 1
            
            # Günlük toplam süreyi güncelle
            total_item = self.days_table.item(row, 6)
            if total_item:
                hours = int(day_hours)
                minutes = int((day_hours - hours) * 60)
                total_item.setText(f"{hours:02d}:{minutes:02d}")
        
        # Haftalık toplam hesaplamaları
        self.current_totals = {
            'total_hours': round(total_hours, 2),
            'work_salary': weekly_salary if work_days > 0 else 0,
            'transport_total': daily_transport * work_days,
            'food_total': daily_food * work_days,
            'total_amount': (weekly_salary if work_days > 0 else 0) + (daily_transport + daily_food) * work_days
        }
        
        # Etiketleri güncelle
        self.total_hours_label.setText(f"{self.current_totals['total_hours']} saat")
        self.weekly_salary_label.setText(f"{self.format_currency(self.current_totals['work_salary'])} TL")
        self.transport_total_label.setText(f"{self.format_currency(self.current_totals['transport_total'])} TL")
        self.food_total_label.setText(f"{self.format_currency(self.current_totals['food_total'])} TL")
        self.total_amount_label.setText(f"{self.format_currency(self.current_totals['total_amount'])} TL")
        
        self.data_updated.emit()
    
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
    
    def on_day_status_changed(self, row, state):
        """Gün durumu değiştiğinde çağrılır"""
        is_active = state == Qt.Checked
        
        # Saat widgetlarını aktif/pasif yap
        for col in range(2, 6):  # Giriş, öğle başlangıç/bitiş, çıkış
            time_widget = self.days_table.cellWidget(row, col)
            if time_widget:
                time_widget.setEnabled(is_active)
        
        # Toplam süreyi güncelle
        total_item = self.days_table.item(row, 6)
        if total_item:
            if not is_active:
                total_item.setText("--:--")
                # Veritabanından günü sil
                if self.current_employee_id:
                    cursor = self.db.conn.cursor()
                    cursor.execute('''
                        DELETE FROM work_records 
                        WHERE employee_id = ? AND date = ?
                    ''', (self.current_employee_id, self.days_table.item(row, 1).data(Qt.UserRole)))
                    self.db.conn.commit()
            else:
                # Varsayılan değerleri ayarla
                entry_widget = self.days_table.cellWidget(row, 2)
                lunch_start_widget = self.days_table.cellWidget(row, 3)
                lunch_end_widget = self.days_table.cellWidget(row, 4)
                exit_widget = self.days_table.cellWidget(row, 5)
                
                if entry_widget and lunch_start_widget and lunch_end_widget and exit_widget:
                    entry_widget.setTime(QTime(8, 0))
                    lunch_start_widget.setTime(QTime(12, 0))
                    lunch_end_widget.setTime(QTime(13, 0))
                    exit_widget.setTime(QTime(18, 0))
                    
                    # Veritabanına varsayılan değerleri kaydet
                    if self.current_employee_id:
                        self.save_day_data(row)
        
        # Değişiklikten sonra toplamları güncelle
        self.calculate_total_hours()

    def save_week_data(self):
        """Tüm haftanın verilerini kaydeder"""
        try:
            for row in range(7):
                # Günün aktif olup olmadığını kontrol et
                status_widget = self.days_table.cellWidget(row, 0)
                if not status_widget or not status_widget.findChild(QCheckBox).isChecked():
                    continue
                
                # Günlük veriyi kaydet
                self.save_day_data(row)
            
        except Exception as e:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("❌ Hata: " + str(e))

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
        cursor.execute('SELECT id, name FROM employees WHERE is_active = 1 ORDER BY name')
        employees = cursor.fetchall()
        
        for employee_id, name in employees:
            time_form = TimeTrackingForm(self.db, employee_id)
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
            cursor.execute('SELECT id, name FROM employees WHERE is_active = 1 ORDER BY name')
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
                time_form = TimeTrackingForm(self.db, emp_id)
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