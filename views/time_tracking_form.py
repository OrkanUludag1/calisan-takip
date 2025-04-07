from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QTimeEdit, QCheckBox, QComboBox, QDateEdit,
    QPushButton, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QDate, QTime, QTimer
from PyQt5.QtGui import QColor
from datetime import datetime, timedelta

from models.database import EmployeeDB
from utils.helpers import format_currency, calculate_working_hours

class TimeTrackingForm(QWidget):
    """Zaman takibi formu"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_employee_id = None
        self.current_date = QDate.currentDate()
        self.current_date = self.current_date.addDays(-(self.current_date.dayOfWeek() - 1))  # Haftanın başlangıcı (Pazartesi)
        self.day_status_checkboxes = []
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(10000)  # 10 saniyede bir otomatik kaydet
        
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Çalışan seçimi
        employee_layout = QHBoxLayout()
        
        self.employee_combo = QComboBox()
        self.employee_combo.setMinimumHeight(35)
        self.employee_combo.currentIndexChanged.connect(self.on_employee_changed)
        self.employee_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 10px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        employee_layout.addWidget(self.employee_combo)
        
        main_layout.addLayout(employee_layout)
        
        # Tarih aralığı
        date_layout = QHBoxLayout()
        date_layout.setAlignment(Qt.AlignCenter)
        
        self.prev_week_btn = QPushButton("◀")
        self.prev_week_btn.clicked.connect(self.prev_week)
        self.prev_week_btn.setFixedWidth(40)
        self.prev_week_btn.setStyleSheet("""
            QPushButton {
                background-color: #495057;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #343a40;
            }
        """)
        date_layout.addWidget(self.prev_week_btn)
        
        self.date_range_label = QLabel()
        self.date_range_label.setAlignment(Qt.AlignCenter)
        self.date_range_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        date_layout.addWidget(self.date_range_label)
        
        self.next_week_btn = QPushButton("▶")
        self.next_week_btn.clicked.connect(self.next_week)
        self.next_week_btn.setFixedWidth(40)
        self.next_week_btn.setStyleSheet("""
            QPushButton {
                background-color: #495057;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #343a40;
            }
        """)
        date_layout.addWidget(self.next_week_btn)
        
        main_layout.addLayout(date_layout)
        
        # Ana içerik için yatay düzen (tablo ve özet yan yana)
        content_layout = QHBoxLayout()
        
        # Tablo için dikey düzen
        table_layout = QVBoxLayout()
        
        # Zaman çizelgesi tablosu
        self.days_table = QTableWidget()
        self.days_table.setRowCount(7)  # Haftanın 7 günü
        self.days_table.setColumnCount(6)  # Gün, Durum, Giriş, Öğle Başlangıç, Öğle Bitiş, Çıkış
        
        table_layout.addWidget(self.days_table)
        content_layout.addLayout(table_layout, 7)  # Tabloya daha fazla alan ver
        
        # Haftalık özet
        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(20, 15, 10, 10)
        summary_layout.setSpacing(15)
        
        # Özet başlığı
        summary_title = QLabel("Haftalık Özet")
        summary_title.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        summary_layout.addWidget(summary_title)
        
        # Toplam çalışma saatleri
        self.total_hours_label = QLabel("Toplam Çalışma Saati: 0.0 saat")
        self.total_hours_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 14px;
            }
        """)
        summary_layout.addWidget(self.total_hours_label)
        
        # Haftalık ücret
        self.weekly_salary_label = QLabel("Haftalık Ücret: 0 TL")
        self.weekly_salary_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 14px;
            }
        """)
        summary_layout.addWidget(self.weekly_salary_label)
        
        # Yemek ücreti
        self.food_allowance_label = QLabel("Yemek Ücreti: 0 TL")
        self.food_allowance_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 14px;
            }
        """)
        summary_layout.addWidget(self.food_allowance_label)
        
        # Yol ücreti
        self.transport_allowance_label = QLabel("Yol Ücreti: 0 TL")
        self.transport_allowance_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 14px;
            }
        """)
        summary_layout.addWidget(self.transport_allowance_label)
        
        # Toplam ücret
        self.total_payment_label = QLabel("Toplam Ödeme: 0 TL")
        self.total_payment_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        summary_layout.addWidget(self.total_payment_label)
        
        # Boşluk ekle
        summary_layout.addStretch()
        
        content_layout.addLayout(summary_layout, 3)  # Özete daha az alan ver
        
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        
        # Çalışanları ve günleri yükle
        self.load_employees()
        self.load_week_days()
        self.update_date_range_label()
    
    def format_currency(self, value):
        """Para birimini formatlar"""
        return format_currency(value)
    
    def load_employees(self):
        """Çalışanları combobox'a yükler"""
        self.employee_combo.clear()
        
        employees = self.db.get_employees()
        
        for employee_id, name, _, _, _ in employees:
            self.employee_combo.addItem(name, employee_id)
    
    def on_employee_changed(self, index):
        """Çalışan değiştiğinde çağrılır"""
        if index >= 0:
            self.current_employee_id = self.employee_combo.itemData(index)
            self.load_saved_records()
            # Only calculate total hours if day_status_checkboxes is properly initialized
            if self.day_status_checkboxes and len(self.day_status_checkboxes) == 7:
                self.calculate_total_hours()
    
    def update_date_range_label(self):
        """Tarih aralığı etiketini günceller"""
        week_start = self.current_date
        week_end = week_start.addDays(6)
        
        start_str = week_start.toString("dd.MM.yyyy")
        end_str = week_end.toString("dd.MM.yyyy")
        
        self.date_range_label.setText(f"{start_str} - {end_str}")
    
    def prev_week(self):
        """Önceki haftaya geçer"""
        self.current_date = self.current_date.addDays(-7)
        self.update_date_range_label()
        self.load_week_days()
        if self.current_employee_id:
            self.load_saved_records()
            self.calculate_total_hours()
    
    def next_week(self):
        """Sonraki haftaya geçer"""
        self.current_date = self.current_date.addDays(7)
        self.update_date_range_label()
        self.load_week_days()
        if self.current_employee_id:
            self.load_saved_records()
            self.calculate_total_hours()
    
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
        
        # Tablo başlıklarını daha okunaklı hale getir ve ortala
        header = self.days_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)  # Başlıkları ortala
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
        self.day_status_checkboxes = []  # Temizle
        
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
                time_edit.setStyleSheet("""
                    QTimeEdit { 
                        padding: 4px; 
                        qproperty-alignment: AlignCenter;
                    }
                """)
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
    
    def load_saved_records(self):
        """Kaydedilmiş çalışma saatlerini yükler"""
        if not self.current_employee_id:
            return
        
        try:
            # Haftanın başlangıç tarihini al
            week_start = self.current_date.toString("yyyy-MM-dd")
            
            # Veritabanından kayıtları al
            records = self.db.get_week_work_hours(self.current_employee_id, week_start)
            
            # Kayıtları tabloya yükle
            for row in range(7):
                current_day = self.current_date.addDays(row)
                current_date_str = current_day.toString("yyyy-MM-dd")
                
                # Bu tarih için kayıt var mı kontrol et
                record_found = False
                for record in records:
                    if record[0] == current_date_str:
                        # Kayıt bulundu, değerleri ayarla
                        entry_time = QTime.fromString(record[1], "HH:mm")
                        lunch_start = QTime.fromString(record[2], "HH:mm")
                        lunch_end = QTime.fromString(record[3], "HH:mm")
                        exit_time = QTime.fromString(record[4], "HH:mm")
                        is_active = bool(record[5])
                        
                        # Zaman değerlerini ayarla - None kontrolü ekle
                        entry_widget = self.days_table.cellWidget(row, 2)
                        lunch_start_widget = self.days_table.cellWidget(row, 3)
                        lunch_end_widget = self.days_table.cellWidget(row, 4)
                        exit_widget = self.days_table.cellWidget(row, 5)
                        
                        if entry_widget:
                            entry_widget.setTime(entry_time)
                        if lunch_start_widget:
                            lunch_start_widget.setTime(lunch_start)
                        if lunch_end_widget:
                            lunch_end_widget.setTime(lunch_end)
                        if exit_widget:
                            exit_widget.setTime(exit_time)
                        
                        # Durum checkbox'ını ayarla
                        if row < len(self.day_status_checkboxes):
                            self.day_status_checkboxes[row].setChecked(is_active)
                        
                        record_found = True
                        break
            
            # Kayıt bulunamadıysa, varsayılan değerleri kullan
            if not record_found and row < len(self.day_status_checkboxes):
                # Durum checkbox'ını aktif yap
                self.day_status_checkboxes[row].setChecked(True)
        except Exception as e:
            print(f"Kayıtları yüklerken hata: {e}")
    
    def on_time_changed(self, row):
        """Zaman değiştiğinde çağrılır"""
        self.calculate_total_hours()
        self.auto_save_row(row)
    
    def on_day_status_changed(self, row):
        """Gün durumu değiştiğinde çağrılır"""
        is_active = self.day_status_checkboxes[row].isChecked()
        
        # Zaman alanlarını etkinleştir/devre dışı bırak
        for col in range(2, 6):
            time_edit = self.days_table.cellWidget(row, col)
            if time_edit:
                time_edit.setEnabled(is_active)
                
                # Görsel efekt uygula
                effect = QGraphicsOpacityEffect(time_edit)
                effect.setOpacity(1.0 if is_active else 0.5)
                time_edit.setGraphicsEffect(effect)
        
        self.calculate_total_hours()
        self.auto_save_row(row)
    
    def auto_save_row(self, row):
        """Belirli bir satırı otomatik kaydeder"""
        if not self.current_employee_id:
            return
        
        # Tarih bilgisini al
        date_item = self.days_table.item(row, 0)
        if not date_item:
            return
        
        current_day = date_item.data(Qt.UserRole)
        date_str = current_day.toString("yyyy-MM-dd")
        
        # Durum bilgisini al
        is_active = self.day_status_checkboxes[row].isChecked()
        
        # Zaman bilgilerini al
        entry_time = self.days_table.cellWidget(row, 2).time().toString("HH:mm")
        lunch_start = self.days_table.cellWidget(row, 3).time().toString("HH:mm")
        lunch_end = self.days_table.cellWidget(row, 4).time().toString("HH:mm")
        exit_time = self.days_table.cellWidget(row, 5).time().toString("HH:mm")
        
        # Veritabanına kaydet
        self.db.save_work_hours(
            self.current_employee_id, date_str, 
            entry_time, lunch_start, lunch_end, exit_time, 
            1 if is_active else 0
        )
    
    def auto_save_all(self):
        """Tüm satırları otomatik kaydeder"""
        if not self.current_employee_id:
            return
        
        for row in range(7):
            self.auto_save_row(row)
    
    def calculate_total_hours(self):
        """Toplam çalışma saatlerini ve ödemeleri hesaplar"""
        if not self.current_employee_id or not self.day_status_checkboxes:
            return
        
        total_hours = 0
        active_days = 0
        
        # Her gün için çalışma saatlerini hesapla
        for row in range(min(7, len(self.day_status_checkboxes))):
            # Gün aktif mi kontrol et
            is_active = self.day_status_checkboxes[row].isChecked()
            if not is_active:
                continue
            
            # Zaman değerlerini al
            entry_time = self.days_table.cellWidget(row, 2).time()
            lunch_start = self.days_table.cellWidget(row, 3).time()
            lunch_end = self.days_table.cellWidget(row, 4).time()
            exit_time = self.days_table.cellWidget(row, 5).time()
            
            # Günlük çalışma saatlerini hesapla
            day_hours = calculate_working_hours(entry_time, lunch_start, lunch_end, exit_time)
            total_hours += day_hours
            
            if day_hours > 0:
                active_days += 1
        
        # Çalışan bilgilerini al
        employee = self.db.get_employee(self.current_employee_id)
        if not employee:
            return
        
        _, _, weekly_salary, daily_food, daily_transport = employee
        
        # Toplam ödemeleri hesapla
        food_allowance = daily_food * active_days
        transport_allowance = daily_transport * active_days
        total_payment = weekly_salary + food_allowance + transport_allowance
        
        # Etiketleri güncelle
        self.total_hours_label.setText(f"Toplam Çalışma Saati: {total_hours:.1f} saat")
        self.weekly_salary_label.setText(f"Haftalık Ücret: {self.format_currency(weekly_salary)}")
        self.food_allowance_label.setText(f"Yemek Ücreti: {self.format_currency(food_allowance)}")
        self.transport_allowance_label.setText(f"Yol Ücreti: {self.format_currency(transport_allowance)}")
        self.total_payment_label.setText(f"Toplam Ödeme: {self.format_currency(total_payment)}")
