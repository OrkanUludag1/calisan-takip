from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QTimeEdit, QCheckBox, QComboBox, QDateEdit,
    QPushButton, QGraphicsOpacityEffect, QAbstractSpinBox
)
from PyQt5.QtCore import Qt, QDate, QTime, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QColor, QBrush, QPainter, QPen
from datetime import datetime, timedelta

from models.database import EmployeeDB
from utils.helpers import format_currency, calculate_working_hours

# Özel TimeEdit sınıfı
class CustomTimeEdit(QTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("HH:mm")
        self.setReadOnly(False)
        self.setKeyboardTracking(True)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        
        # İki basamaklı giriş için değişkenler
        self.first_digit = -1  # İlk basılan rakam
        self.current_section = None  # Şu anki seçili bölüm
        self.is_strikeout = False  # Üstü çizili mi?
        
        # Stil ayarları
        self.setStyleSheet("""
            CustomTimeEdit { 
                padding: 6px; 
                qproperty-alignment: AlignCenter;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                color: #333;
            }
            CustomTimeEdit:focus { 
                border: 1px solid #4a86e8;
                background-color: #e8f0fe;
            }
        """)
    
    def setStrikeOut(self, strikeout):
        """Üstü çizili görünümünü ayarla"""
        self.is_strikeout = strikeout
        self.update()
    
    def paintEvent(self, event):
        """Özel çizim olayı"""
        super().paintEvent(event)
        
        # Eğer üstü çizili ise, metin üzerine çizgi çiz
        if self.is_strikeout:
            painter = QPainter(self)
            painter.setPen(QPen(QColor("#FF6B6B"), 1, Qt.SolidLine))
            
            # Metnin ortasından geçen bir çizgi çiz
            rect = self.rect()
            y = rect.height() // 2  # Tam sayı bölme kullan
            # x1, y1, x2, y2 şeklinde kullan
            painter.drawLine(QPoint(5, y), QPoint(rect.width() - 5, y))
        
    def mousePressEvent(self, event):
        # Tıklama pozisyonunu al
        pos = event.pos()
        rect = self.rect()
        
        # Saat ve dakika bölgelerini belirle (yaklaşık olarak)
        hour_region = rect.width() / 2
        
        # Tıklama pozisyonuna göre saat veya dakika seçimi yap
        if pos.x() < hour_region:
            # Saat kısmına tıklandı
            self.setSelectedSection(QTimeEdit.HourSection)
            self.current_section = QTimeEdit.HourSection
        else:
            # Dakika kısmına tıklandı
            self.setSelectedSection(QTimeEdit.MinuteSection)
            self.current_section = QTimeEdit.MinuteSection
        
        # Yeni bir tıklama yapıldığında ilk rakamı sıfırla
        self.first_digit = -1
        
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        # Sayı tuşlarına basıldığında
        if event.key() >= Qt.Key_0 and event.key() <= Qt.Key_9:
            # Basılan tuşun değerini al (0-9)
            digit = event.key() - Qt.Key_0
            
            # Mevcut saati al
            current_time = self.time()
            hour = current_time.hour()
            minute = current_time.minute()
            
            # Mevcut seçili bölümü al
            section = self.currentSection()
            self.current_section = section
            
            # Seçili bölüme göre değeri güncelle
            if section == QTimeEdit.HourSection:
                # Saat bölümü seçili
                if self.first_digit == -1:
                    # İlk rakam giriliyor
                    self.first_digit = digit
                    # 24 saat formatında ilk rakam en fazla 2 olabilir
                    if digit > 2:
                        # Eğer 2'den büyükse, doğrudan tek basamaklı saat olarak ayarla
                        hour = digit
                        self.first_digit = -1  # İlk rakamı sıfırla
                        self.setSelectedSection(QTimeEdit.MinuteSection)  # Dakika bölümüne geç
                    else:
                        # İlk rakamı saatin onlar basamağı olarak ayarla
                        hour = digit * 10 + (hour % 10)
                else:
                    # İkinci rakam giriliyor
                    # İlk rakam 2 ise, ikinci rakam en fazla 3 olabilir (23 saat)
                    if self.first_digit == 2 and digit > 3:
                        digit = 3
                    
                    # İki basamaklı saati ayarla
                    hour = self.first_digit * 10 + digit
                    self.first_digit = -1  # İlk rakamı sıfırla
                    self.setSelectedSection(QTimeEdit.MinuteSection)  # Dakika bölümüne geç
            
            elif section == QTimeEdit.MinuteSection:
                # Dakika bölümü seçili
                if self.first_digit == -1:
                    # İlk rakam giriliyor
                    self.first_digit = digit
                    # Dakikanın ilk rakamı en fazla 5 olabilir
                    if digit > 5:
                        # Eğer 5'ten büyükse, doğrudan tek basamaklı dakika olarak ayarla
                        minute = digit
                        self.first_digit = -1  # İlk rakamı sıfırla
                        self.setSelectedSection(QTimeEdit.HourSection)  # Saat bölümüne geç
                    else:
                        # İlk rakamı dakikanın onlar basamağı olarak ayarla
                        minute = digit * 10 + (minute % 10)
                else:
                    # İkinci rakam giriliyor
                    # İki basamaklı dakikayı ayarla
                    minute = self.first_digit * 10 + digit
                    self.first_digit = -1  # İlk rakamı sıfırla
                    self.setSelectedSection(QTimeEdit.HourSection)  # Saat bölümüne geç
            
            # Yeni zamanı ayarla
            new_time = QTime(hour, minute)
            self.setTime(new_time)
            
            return
        elif event.key() == Qt.Key_Backspace:
            # Backspace tuşuna basıldığında ilk rakamı sıfırla
            self.first_digit = -1
            super().keyPressEvent(event)
        elif event.key() == Qt.Key_Tab:
            # Tab tuşuna basıldığında ilk rakamı sıfırla ve diğer bölüme geç
            self.first_digit = -1
            super().keyPressEvent(event)
        else:
            # Diğer tuşlar için varsayılan davranışı kullan
            super().keyPressEvent(event)

class TimeTrackingForm(QWidget):
    """Zaman takibi formu"""
    
    def __init__(self, db, employee_id=None):
        super().__init__()
        self.db = db
        self.current_employee_id = employee_id
        self.current_date = QDate.currentDate()
        self.day_status_checkboxes = []
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(10000)  # 10 saniyede bir otomatik kaydet
        
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Ana içerik için yatay düzen (tablo ve özet yan yana)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)  # Tablo ve özet arasındaki boşluğu artır
        
        # Tablo için dikey düzen
        table_layout = QVBoxLayout()
        
        # Zaman çizelgesi tablosu
        self.days_table = QTableWidget()
        self.days_table.setRowCount(7)  # Haftanın 7 günü
        self.days_table.setColumnCount(6)  # Gün, Durum, Giriş, Öğle Başlangıç, Öğle Bitiş, Çıkış
        
        # Satır numaralarını gizle
        self.days_table.verticalHeader().setVisible(False)
        
        # Tabloyu tam sığdır ve kaydırma çubuklarını kaldır
        self.days_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.days_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Tablonun boyutunu sabitle
        self.days_table.setFixedSize(800, 350)
        
        table_layout.addWidget(self.days_table)
        content_layout.addLayout(table_layout, 7)  # Tabloya daha fazla alan ver
        
        # Haftalık özet
        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(20, 15, 10, 10)
        summary_layout.setSpacing(15)
        
        # Özet bölümünü içeren widget
        summary_widget = QWidget()
        summary_widget.setLayout(summary_layout)
        summary_widget.setFixedWidth(250)  # Sabit genişlik
        summary_widget.setFixedHeight(650)  # Sabit yükseklik - 650 piksel
        summary_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        
        # Çalışan ismi başlığı
        self.employee_name_label = QLabel()
        self.employee_name_label.setAlignment(Qt.AlignCenter)
        self.employee_name_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 18px;
                font-weight: bold;
                margin: 12px 0;
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        summary_layout.addWidget(self.employee_name_label)
        
        # Başlık ve değer etiketleri için stil tanımları
        title_style = """
            QLabel {
                color: #495057;
                font-size: 16px;
                margin-top: 10px;
                text-align: center;
            }
        """
        
        value_style = """
            QLabel {
                color: #212529;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 15px;
                text-align: center;
            }
        """
        
        # Toplam çalışma saatleri
        hours_title = QLabel("Toplam Çalışma Saati:")
        hours_title.setStyleSheet(title_style)
        hours_title.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(hours_title)
        
        self.total_hours_label = QLabel("0.0 saat")
        self.total_hours_label.setStyleSheet(value_style)
        self.total_hours_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.total_hours_label)
        
        # Haftalık ücret
        salary_title = QLabel("Haftalık Ücret:")
        salary_title.setStyleSheet(title_style)
        salary_title.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(salary_title)
        
        self.weekly_salary_label = QLabel("0 TL")
        self.weekly_salary_label.setStyleSheet(value_style)
        self.weekly_salary_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.weekly_salary_label)
        
        # Yemek ücreti
        food_title = QLabel("Yemek Ücreti:")
        food_title.setStyleSheet(title_style)
        food_title.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(food_title)
        
        self.food_allowance_label = QLabel("0 TL")
        self.food_allowance_label.setStyleSheet(value_style)
        self.food_allowance_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.food_allowance_label)
        
        # Yol ücreti
        transport_title = QLabel("Yol Ücreti:")
        transport_title.setStyleSheet(title_style)
        transport_title.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(transport_title)
        
        self.transport_allowance_label = QLabel("0 TL")
        self.transport_allowance_label.setStyleSheet(value_style)
        self.transport_allowance_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.transport_allowance_label)
        
        # Toplam ödeme
        total_title = QLabel("Toplam Ödeme:")
        total_title.setStyleSheet(title_style)
        total_title.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(total_title)
        
        self.total_payment_label = QLabel("0 TL")
        self.total_payment_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-size: 20px;
                font-weight: bold;
                margin-top: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
        """)
        self.total_payment_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.total_payment_label)
        
        # Boşluk ekle
        summary_layout.addStretch()
        
        content_layout.addWidget(summary_widget)
        
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        
        # Günleri yükle
        self.load_saved_records()
    
    def format_currency(self, value):
        """Para birimini formatlar"""
        return format_currency(value)
    
    def load_week_days(self):
        """Haftalık günleri yükler"""
        self.days_table.clearContents()
        
        # Varsayılan saatler
        default_entry = QTime(8, 15)  # 08:15
        default_lunch_start = QTime(13, 15)  # 13:15
        default_lunch_end = QTime(13, 45)  # 13:45
        default_exit = QTime(18, 45)  # 18:45
        
        # Tablonun başlangıç gününü belirle (Pazartesi)
        current_week_start = self.current_date
        
        # Tablo başlıklarını ayarla
        self.days_table.setHorizontalHeaderLabels([
            "Gün", "Durum", "Giriş", "Öğle Baş.",
            "Öğle Bit.", "Çıkış"
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
        
        # Satır numaralarını gizle
        self.days_table.verticalHeader().setVisible(False)
        
        # Sütun genişliklerini ayarla
        self.days_table.setColumnCount(6)
        
        # Tablonun toplam genişliğini al
        total_width = self.days_table.viewport().width()
        
        # Sütun genişliklerini orantılı olarak ayarla
        self.days_table.setColumnWidth(0, int(total_width * 0.20))  # Gün
        self.days_table.setColumnWidth(1, int(total_width * 0.10))  # Durum
        self.days_table.setColumnWidth(2, int(total_width * 0.15))  # Giriş
        self.days_table.setColumnWidth(3, int(total_width * 0.18))  # Öğle Başlangıç
        self.days_table.setColumnWidth(4, int(total_width * 0.17))  # Öğle Bitiş
        self.days_table.setColumnWidth(5, int(total_width * 0.15))  # Çıkış
        
        # Sütun modlarını ayarla
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Gün sütunu esnek
        header.setSectionResizeMode(1, QHeaderView.Fixed)    # Durum sütunu sabit
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Giriş sütunu esnek
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Öğle Başlangıç sütunu eslek
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Öğle Bitiş sütunu esnek
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Çıkış sütunu esnek
        
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
            
            # Veritabanında kayıtlı çalışma saatlerini kontrol et
            date_str = current_day.toString("yyyy-MM-dd")
            saved_record = None
            
            if self.current_employee_id:
                saved_record = self.db.get_work_hours(self.current_employee_id, date_str)
            
            # Durum hücresi - Hafta sonu günleri her zaman pasif olarak ayarla
            status_checkbox = QCheckBox()
            
            if saved_record:
                # Kaydedilmiş kayıt varsa, day_active değerini kullan
                is_active = saved_record[5] == 1 if len(saved_record) > 5 else (not is_weekend)
            else:
                # Kaydedilmiş kayıt yoksa, hafta sonu günleri pasif olarak ayarla
                is_active = not is_weekend
            
            status_checkbox.setChecked(is_active)
            status_checkbox.stateChanged.connect(lambda state, r=row: self.on_day_status_changed(r))
            self.days_table.setCellWidget(row, 1, status_checkbox)
            self.day_status_checkboxes.append(status_checkbox)
            
            # Saat hücreleri
            for col, default_time in enumerate([default_entry, default_lunch_start, default_lunch_end, default_exit], start=2):
                time_edit = CustomTimeEdit()  # Özel TimeEdit sınıfını kullan
                
                # Kaydedilmiş saat varsa kullan
                if saved_record and col - 2 < len(saved_record):
                    saved_time_str = saved_record[col - 2]
                    if saved_time_str:
                        hours, minutes = map(int, saved_time_str.split(':'))
                        time_edit.setTime(QTime(hours, minutes))
                else:
                    time_edit.setTime(default_time)
                    
                time_edit.timeChanged.connect(lambda time, r=row: self.on_time_changed(r))
                self.days_table.setCellWidget(row, col, time_edit)
            
            # Pasif günleri görsel olarak işaretle
            if not is_active:
                # Gün hücresini pasif yap
                font = day_item.font()
                font.setItalic(True)
                font.setStrikeOut(True)  # Üstü çizili göster
                day_item.setFont(font)
                day_item.setForeground(QBrush(QColor("#FF6B6B")))  # Kırmızımsı renk
                
                # Saat hücrelerini pasif yap
                for col in range(2, 6):
                    time_edit = self.days_table.cellWidget(row, col)
                    if time_edit:
                        # Pasif stil uygula
                        time_edit.setStyleSheet("""
                            CustomTimeEdit { 
                                padding: 6px; 
                                qproperty-alignment: AlignCenter;
                                background-color: #f8f8f8;
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                font-size: 13px;
                                font-weight: bold;
                                color: #FF6B6B;
                            }
                            CustomTimeEdit:focus { 
                                border: 1px solid #4a86e8;
                                background-color: #e8f0fe;
                            }
                        """)
                        # Üstü çizili göster
                        time_edit.setStrikeOut(True)
        
        # Kaydedilmiş kayıtları yükle
        if self.current_employee_id:
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
                        if record['date'] == current_date_str:
                            # Kayıt bulundu, değerleri ayarla
                            entry_time = QTime.fromString(record['entry_time'], "HH:mm")
                            lunch_start = QTime.fromString(record['lunch_start'], "HH:mm")
                            lunch_end = QTime.fromString(record['lunch_end'], "HH:mm")
                            exit_time = QTime.fromString(record['exit_time'], "HH:mm")
                            is_active = bool(record['day_active'])
                            
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
                # Hata mesajını sadece gerçek bir hata varsa göster
                if str(e) != "0":
                    print(f"Kayıtları yüklerken hata: {e}")
        
        # Toplamları güncelle
        self.calculate_total_hours()
    
    def on_time_changed(self, row):
        """Zaman değiştiğinde çağrılır"""
        self.calculate_total_hours()
        self.auto_save_row(row)
    
    def on_day_status_changed(self, row):
        """Gün durumu değiştiğinde çağrılır"""
        is_active = self.day_status_checkboxes[row].isChecked()
        
        # Günün tüm hücrelerini güncelle
        day_item = self.days_table.item(row, 0)
        
        # Saat hücrelerini al
        time_widgets = []
        for col in range(2, 6):  # Giriş, Öğle Başlangıç, Öğle Bitiş, Çıkış
            time_widgets.append(self.days_table.cellWidget(row, col))
        
        if day_item:
            # Pasif günleri daha belirgin şekilde göster
            if not is_active:
                # Gün hücresini pasif yap
                font = day_item.font()
                font.setItalic(True)
                font.setStrikeOut(True)  # Üstü çizili göster
                day_item.setFont(font)
                day_item.setForeground(QBrush(QColor("#FF6B6B")))  # Kırmızımsı renk
                
                # Saat hücrelerini pasif yap
                for time_edit in time_widgets:
                    if time_edit:
                        # Pasif stil uygula
                        time_edit.setStyleSheet("""
                            CustomTimeEdit { 
                                padding: 6px; 
                                qproperty-alignment: AlignCenter;
                                background-color: #f8f8f8;
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                font-size: 13px;
                                font-weight: bold;
                                color: #FF6B6B;
                            }
                            CustomTimeEdit:focus { 
                                border: 1px solid #4a86e8;
                                background-color: #e8f0fe;
                            }
                        """)
                        # Üstü çizili göster
                        time_edit.setStrikeOut(True)
            else:
                # Gün hücresini aktif yap
                font = day_item.font()
                font.setItalic(False)
                font.setStrikeOut(False)
                day_item.setFont(font)
                day_item.setForeground(QBrush(QColor("#333")))  # Normal renk
                
                # Saat hücrelerini aktif yap
                for time_edit in time_widgets:
                    if time_edit:
                        # Normal stil uygula - üstü çizili olmadan
                        time_edit.setStyleSheet("""
                            CustomTimeEdit { 
                                padding: 6px; 
                                qproperty-alignment: AlignCenter;
                                background-color: #f8f8f8;
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                font-size: 13px;
                                font-weight: bold;
                                color: #333;
                            }
                            CustomTimeEdit:focus { 
                                border: 1px solid #4a86e8;
                                background-color: #e8f0fe;
                            }
                        """)
                        # Üstü çizili kaldır
                        time_edit.setStrikeOut(False)
        
        # Değişikliği kaydet
        self.on_time_changed(row)
    
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
        
        # Veritabanına kaydet - day_active parametresini de ekle
        self.db.save_work_hours(
            self.current_employee_id, date_str, 
            entry_time, lunch_start, lunch_end, exit_time, 
            1 if is_active else 0,
            1 if is_active else 0  # day_active parametresi
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
        
        # get_employee 6 değer döndürüyor, son değer is_active olduğu için onu yok sayıyoruz
        _, _, weekly_salary, daily_food, daily_transport, _ = employee
        
        # Toplam ödemeleri hesapla
        food_allowance = daily_food * active_days
        transport_allowance = daily_transport * active_days
        total_payment = weekly_salary + food_allowance + transport_allowance
        
        # Etiketleri güncelle
        self.total_hours_label.setText(f"{total_hours:.1f} saat")
        self.weekly_salary_label.setText(f"{self.format_currency(weekly_salary)}")
        self.food_allowance_label.setText(f"{self.format_currency(food_allowance)}")
        self.transport_allowance_label.setText(f"{self.format_currency(transport_allowance)}")
        self.total_payment_label.setText(f"{self.format_currency(total_payment)}")
    
    def load_saved_records(self):
        """Kaydedilmiş kayıtları yükler"""
        if not self.current_employee_id:
            return
            
        # Mevcut haftanın başlangıcını bul (Pazartesi)
        today = QDate.currentDate()
        days_to_monday = today.dayOfWeek() - 1  # Pazartesi = 1, Pazar = 7
        week_start = today.addDays(-days_to_monday)
        self.current_date = week_start
        
        # Günleri yükle
        self.load_week_days()
        
        # Toplam saatleri hesapla
        self.calculate_total_hours()
    
    def set_employee_data(self, employee_id, employee_name):
        """Çalışan verilerini ayarlar"""
        self.current_employee_id = employee_id
        
        # Çalışan adını başlığa ekle
        self.employee_name_label.setText(employee_name)
        
        # Kayıtları yükle
        self.load_saved_records()
