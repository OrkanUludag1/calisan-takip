# Gerekli modüllerin import edilmesi
try:
    # Normal import yöntemi (ana uygulamadan çağrıldığında)
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QTableWidget, QTableWidgetItem, QHeaderView, 
        QTimeEdit, QCheckBox, QComboBox, QDateEdit,
        QPushButton, QGraphicsOpacityEffect, QAbstractSpinBox,
        QFrame, QSizePolicy, QDateEdit, QMenu, QAction, QGridLayout, QApplication
    )
    from PyQt5.QtCore import Qt, QDate, QTime, QTimer, pyqtSignal, QPoint
    from PyQt5.QtGui import QColor, QBrush, QPainter, QPen
    from datetime import datetime, timedelta

    from models.database import EmployeeDB
    from utils.helpers import format_currency, calculate_working_hours
except ModuleNotFoundError:
    # Dosya doğrudan çalıştırıldığında
    import sys
    import os
    
    # Ana dizini Python yoluna ekle
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QTableWidget, QTableWidgetItem, QHeaderView, 
        QTimeEdit, QCheckBox, QComboBox, QDateEdit,
        QPushButton, QGraphicsOpacityEffect, QAbstractSpinBox,
        QFrame, QSizePolicy, QDateEdit, QMenu, QAction, QGridLayout, QApplication
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
        self.is_inactive = False  # Pasif mi?
        
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
        
    def setInactive(self, inactive):
        """Pasif görünümünü ayarla"""
        self.is_inactive = inactive
        self.update()
    
    def paintEvent(self, event):
        """Özel çizim olayı"""
        super().paintEvent(event)
        
        # Eğer pasif ise, arkaplanı siyah yap ve yazıyı beyaz yap (gün isimleriyle aynı)
        if self.is_inactive:
            painter = QPainter(self)
            
            # Arkaplan için siyah dikdörtgen çiz
            painter.setBrush(QBrush(QColor("#000000")))  # Siyah arkaplan
            painter.setPen(Qt.NoPen)  # Kenar çizgisi yok
            painter.drawRect(self.rect())
            
            # Metni beyaz yap (gün isimleriyle aynı)
            painter.setPen(QPen(QColor("#ffffff")))  # Beyaz yazı
            
            # Metnin içeriğini al ve yeniden çiz
            text = self.time().toString("HH:mm")  # Saat formatını kullan
            font = self.font()
            rect = self.rect()
            
            # Metni ortala
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, text)
    
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
    
    def wheelEvent(self, event):
        # Fare tekerleği olayını yok say (saat değişimini önlemek için)
        event.ignore()
    
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
        self.day_active_status = []
        
        # Otomatik kaydetme için zamanlayıcı
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(10000)  # 10 saniyede bir otomatik kaydet
        
        # Mevcut haftanın başlangıç tarihi
        days_to_monday = self.current_date.dayOfWeek() - 1
        week_start = self.current_date.addDays(-days_to_monday)
        self.current_week_start = week_start.toString("yyyy-MM-dd")
        
        # UI'ı başlat
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Başlık
        header_layout = QHBoxLayout()
        
        # Çalışan adı etiketi
        self.employee_name_label = QLabel("")
        self.employee_name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
        """)
        
        # Başlık düzeni
        header_layout.addWidget(self.employee_name_label)
        header_layout.addStretch()
        
        # İçerik düzeni (tablo ve özet yan yana)
        content_layout = QHBoxLayout()
        
        # Tablo
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(5)  # Durum sütunu kaldırıldı
        self.days_table.setHorizontalHeaderLabels(["Gün", "Giriş", "Öğle Başlangıç", "Öğle Bitiş", "Çıkış"])
        
        # Satır yüksekliğini ayarla
        self.days_table.verticalHeader().setDefaultSectionSize(40)  # 40 piksel yükseklik
        
        # Gün durumu sütunu için özel delegasyon
        self.days_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Gün
        self.days_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Giriş
        self.days_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Öğle Başlangıç
        self.days_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Öğle Bitiş
        self.days_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Çıkış
        
        # Tablo özelliklerini ayarla
        self.days_table.verticalHeader().setVisible(False)
        self.days_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.days_table.setContextMenuPolicy(Qt.CustomContextMenu)  # Sağ tık menüsü için
        self.days_table.customContextMenuRequested.connect(self.show_context_menu)  # Sağ tık olayını bağla
        
        self.days_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #ddd;
                border: none;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        # Özet Alanı
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(15)
        
        # Çalışan adı için etiket (özet bölümünde tekrar)
        self.summary_employee_name = QLabel("")
        self.summary_employee_name.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #333;
            padding: 10px;
            text-align: center;
        """)
        self.summary_employee_name.setAlignment(Qt.AlignCenter)
        
        # Özet bilgileri için düzen
        summary_grid = QVBoxLayout()
        summary_grid.setSpacing(15)
        
        # Çalışma saati
        hours_layout = QVBoxLayout()
        hours_title = QLabel("Toplam Çalışma Saatleri")
        hours_title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
        """)
        hours_title.setAlignment(Qt.AlignCenter)
        
        self.total_hours_value = QLabel("0 saat")
        self.total_hours_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2a5885;
        """)
        self.total_hours_value.setAlignment(Qt.AlignCenter)
        
        hours_layout.addWidget(hours_title)
        hours_layout.addWidget(self.total_hours_value)
        
        # Haftalık ücret
        salary_layout = QVBoxLayout()
        salary_title = QLabel("Haftalık Ücret")
        salary_title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
        """)
        salary_title.setAlignment(Qt.AlignCenter)
        
        self.weekly_salary_value = QLabel("0 ₺")
        self.weekly_salary_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2a5885;
        """)
        self.weekly_salary_value.setAlignment(Qt.AlignCenter)
        
        salary_layout.addWidget(salary_title)
        salary_layout.addWidget(self.weekly_salary_value)
        
        # Yol ve yemek toplamı
        allowances_layout = QVBoxLayout()
        allowances_title = QLabel("Yol ve Yemek")
        allowances_title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
        """)
        allowances_title.setAlignment(Qt.AlignCenter)
        
        self.allowances_value = QLabel("0 ₺")
        self.allowances_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2a5885;
        """)
        self.allowances_value.setAlignment(Qt.AlignCenter)
        
        allowances_layout.addWidget(allowances_title)
        allowances_layout.addWidget(self.allowances_value)
        
        # Ek Ödemeler bölümü
        additions_layout = QVBoxLayout()
        additions_title = QLabel("Ek Ödemeler")
        additions_title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
        """)
        additions_title.setAlignment(Qt.AlignCenter)
        
        self.additions_value = QLabel("0 ₺")
        self.additions_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2a5885;
        """)
        self.additions_value.setAlignment(Qt.AlignCenter)
        
        additions_layout.addWidget(additions_title)
        additions_layout.addWidget(self.additions_value)
        
        # Kesintiler bölümü
        deductions_layout = QVBoxLayout()
        deductions_title = QLabel("Kesintiler")
        deductions_title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
        """)
        deductions_title.setAlignment(Qt.AlignCenter)
        
        self.deductions_value = QLabel("0 ₺")
        self.deductions_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2a5885;
        """)
        self.deductions_value.setAlignment(Qt.AlignCenter)
        
        deductions_layout.addWidget(deductions_title)
        deductions_layout.addWidget(self.deductions_value)
        
        # Özet grid'e ekle
        summary_grid.addLayout(hours_layout)
        summary_grid.addLayout(salary_layout)
        summary_grid.addLayout(allowances_layout)
        summary_grid.addLayout(additions_layout)
        summary_grid.addLayout(deductions_layout)
        
        # Toplam Haftalık Ücret bölümü
        total_weekly_layout = QVBoxLayout()
        total_weekly_title = QLabel("Toplam Haftalık Ücret")
        total_weekly_title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #333;
        """)
        total_weekly_title.setAlignment(Qt.AlignCenter)
        
        self.total_weekly_value = QLabel("0 ₺")
        self.total_weekly_value.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2a5885;
        """)
        self.total_weekly_value.setAlignment(Qt.AlignCenter)
        
        total_weekly_layout.addWidget(total_weekly_title)
        total_weekly_layout.addWidget(self.total_weekly_value)
        
        # Ayırıcı çizgi ekle
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ddd; min-height: 1px;")
        
        # Toplam haftalık ücret bölümünü ekle
        summary_grid.addWidget(line)
        summary_grid.addLayout(total_weekly_layout)
        
        # Grid için bir widget oluştur
        summary_widget = QWidget()
        summary_widget.setLayout(summary_grid)
        
        # Özet düzenine ekle
        summary_layout.addWidget(self.summary_employee_name)
        summary_layout.addWidget(summary_widget)
        summary_layout.addStretch()
        
        # İçerik düzenine ekle
        content_layout.addWidget(self.days_table, 7)
        
        # Özet alanını içerik düzenine widget olarak ekle
        summary_container = QWidget()
        summary_container.setLayout(summary_layout)
        content_layout.addWidget(summary_container, 3)
        
        # Ana düzene ekle
        main_layout.addLayout(header_layout)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        self.load_week_days()
    
    def format_currency(self, value):
        """Para birimini formatlar"""
        return format_currency(value)
    
    def load_week_days(self):
        """Haftanın günlerini yükle"""
        if not self.current_employee_id:
            return
        
        # Önce tabloyu temizle
        self.days_table.setRowCount(0)
        self.days_table.setRowCount(7)
        
        # Günlerin aktif durumunu takip etmek için liste oluştur
        self.day_active_status = [False] * 7
        
        # Haftanın başlangıç tarihini hesapla (Pazartesi)
        week_start = self.current_date
        if week_start.dayOfWeek() != 1:  # 1 = Pazartesi
            days_to_monday = week_start.dayOfWeek() - 1
            week_start = week_start.addDays(-days_to_monday)
        
        # current_week_start değerini ayarla (DB sorgularında kullanılacak)
        self.current_week_start = week_start.toString("yyyy-MM-dd")
        
        # Haftanın her günü için
        for i in range(7):
            current_date = week_start.addDays(i)
            day_name = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][i]
            
            # Sadece gün ismi
            day_item = QTableWidgetItem(f"{day_name}")
            day_item.setTextAlignment(Qt.AlignCenter)
            # Tarih nesnesini UserRole olarak ata (arama için gerekli)
            day_item.setData(Qt.UserRole, current_date)
            self.days_table.setItem(i, 0, day_item)
            
            # Veritabanından bu gün için kaydedilmiş veriyi al
            record = self.db.get_work_hours(self.current_employee_id, current_date.toString("yyyy-MM-dd"))
            
            # Eğer kayıt varsa ve aktifse
            is_active = record and record['day_active'] == 1 if record else False
            self.day_active_status[i] = is_active
            
            # Gün aktif değilse satırı siyah göster
            if not is_active:
                day_item.setBackground(QBrush(QColor("#000000")))  # Siyah arkaplan
                day_item.setForeground(QBrush(QColor("#ffffff")))  # Beyaz yazı
            
            # Zaman editörleri
            times = {
                1: QTime(9, 0) if not record else QTime.fromString(record['entry_time'], "HH:mm"),   # Giriş
                2: QTime(13, 0) if not record else QTime.fromString(record['lunch_start'], "HH:mm"),  # Öğle Başlangıç
                3: QTime(14, 0) if not record else QTime.fromString(record['lunch_end'], "HH:mm"),  # Öğle Bitiş
                4: QTime(18, 0) if not record else QTime.fromString(record['exit_time'], "HH:mm")   # Çıkış
            }
            
            # Her saat için CustomTimeEdit oluştur
            for col, default_time in times.items():
                time_edit = CustomTimeEdit()
                time_edit.setTime(default_time)
                time_edit.setReadOnly(not is_active)
                time_edit.setInactive(not is_active)
                time_edit.setEnabled(is_active)
                time_edit.timeChanged.connect(lambda time, row=i: self.on_time_changed(row))
                
                self.days_table.setCellWidget(i, col, time_edit)
        
        # Toplam saatleri hesapla
        self.calculate_total_hours()
    
    def show_context_menu(self, pos):
        """Sağ tık menüsünü gösterir"""
        # Tıklanan öğenin indeksini al
        index = self.days_table.indexAt(pos)
        
        if index.isValid() and index.column() == 0:  # Sadece gün sütununda sağ tıklandığında
            row = index.row()
            
            # Bağlam menüsü oluştur
            menu = QMenu(self)
            
            # Günün aktif/pasif durumuna göre farklı eylemler göster
            if self.day_active_status[row]:
                action = menu.addAction("Pasif Yap")
                action.triggered.connect(lambda: self.toggle_day_status(row, False))
            else:
                action = menu.addAction("Aktif Yap")
                action.triggered.connect(lambda: self.toggle_day_status(row, True))
            
            # Menüyü göster
            menu.exec_(self.days_table.viewport().mapToGlobal(pos))
            
    def toggle_day_status(self, row, active_status):
        """Günün aktif/pasif durumunu değiştir"""
        # Günün durumunu güncelle
        self.day_active_status[row] = active_status
        
        # Görsel güncelleme
        day_item = self.days_table.item(row, 0)
        
        if active_status:
            # Aktif yaparken normal görünüme getir
            day_item.setBackground(QBrush())  # Varsayılan arkaplan
            day_item.setForeground(QBrush())  # Varsayılan yazı rengi
        else:
            # Pasif yaparken siyah arkaplan ve beyaz yazı yap
            day_item.setBackground(QBrush(QColor("#000000")))  # Siyah arkaplan
            day_item.setForeground(QBrush(QColor("#ffffff")))  # Beyaz yazı
        
        # Zaman editörlerini güncelle
        for col in range(1, 5):  # Giriş, öğle başlangıç, öğle bitiş, çıkış
            time_edit = self.days_table.cellWidget(row, col)
            time_edit.setReadOnly(not active_status)
            time_edit.setInactive(not active_status)
            time_edit.setEnabled(active_status)
        
        # Değişiklikleri kaydet
        self.auto_save_row(row)
        
        # Toplam saatleri güncelle
        self.calculate_total_hours()
    
    def on_time_changed(self, row):
        """Zaman değiştiğinde çağrılır"""
        self.auto_save_row(row)
        self.calculate_total_hours()
    
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
        is_active = self.day_active_status[row]
        
        # Zaman bilgilerini al
        entry_time = self.days_table.cellWidget(row, 1).time().toString("HH:mm")
        lunch_start = self.days_table.cellWidget(row, 2).time().toString("HH:mm")
        lunch_end = self.days_table.cellWidget(row, 3).time().toString("HH:mm")
        exit_time = self.days_table.cellWidget(row, 4).time().toString("HH:mm")
        
        # Veritabanına kaydet - day_active parametresini de ekle
        self.db.save_work_hours(
            self.current_employee_id, date_str, 
            entry_time, lunch_start, lunch_end, exit_time, 
            1 if is_active else 0,  # is_active parametresi
            1 if is_active else 0   # day_active parametresi
        )
    
    def auto_save_all(self):
        """Tüm satırları otomatik kaydeder"""
        if not self.current_employee_id:
            return
        
        for row in range(7):
            self.auto_save_row(row)
    
    def calculate_total_hours(self):
        """Toplam çalışma saatlerini hesaplar"""
        if not self.current_employee_id:
            return
        
        # day_active_status henüz oluşturulmamış olabilir
        if not hasattr(self, 'day_active_status') or not self.day_active_status:
            return
        
        total_hours = 0
        active_days = 0
        
        # Her gün için çalışma saatlerini hesapla
        for row in range(min(7, len(self.day_active_status))):
            # Gün aktif mi kontrol et
            is_active = self.day_active_status[row]
            if not is_active:
                continue
            
            # Aktif gün sayısını artır
            active_days += 1
            
            # Zaman bilgilerini al
            entry_widget = self.days_table.cellWidget(row, 1)
            lunch_start_widget = self.days_table.cellWidget(row, 2)
            lunch_end_widget = self.days_table.cellWidget(row, 3)
            exit_widget = self.days_table.cellWidget(row, 4)
            
            # Eğer herhangi bir widget eksikse, bu günü atla
            if not entry_widget or not lunch_start_widget or not lunch_end_widget or not exit_widget:
                continue
            
            # Zaman değerlerini al
            entry_time = entry_widget.time()
            lunch_start = lunch_start_widget.time()
            lunch_end = lunch_end_widget.time()
            exit_time = exit_widget.time()
            
            # Sabah çalışma saatleri (saniye cinsinden)
            morning_seconds = entry_time.secsTo(lunch_start)
            
            # Öğleden sonra çalışma saatleri (saniye cinsinden)
            afternoon_seconds = lunch_end.secsTo(exit_time)
            
            # Toplam çalışma saatleri (saat cinsinden)
            day_hours = (morning_seconds + afternoon_seconds) / 3600.0
            
            # Negatif değerleri düzelt (zaman çakışmaları veya hatalı giriş)
            if day_hours < 0:
                day_hours = 0
            
            # Toplam saatlere ekle
            total_hours += day_hours
        
        # Çalışan bilgilerini al
        employee_info = self.db.get_employee(self.current_employee_id)
        if not employee_info:
            return
        
        # Saatlik ücreti al (varsayılan 0)
        hourly_rate = employee_info['weekly_salary'] if employee_info else 0
        
        # Haftalık ücret hesapla
        weekly_salary = total_hours * hourly_rate
        
        # Yol ve yemek ödemeleri (aktif gün sayısına göre)
        food_allowance = active_days * employee_info['daily_food']  # Günlük yemek ücreti
        transport_allowance = active_days * employee_info['daily_transport']  # Günlük yol ücreti
        total_allowances = food_allowance + transport_allowance
        
        # Ek ödemeler ve kesintileri al
        week_start_date = self.current_week_start
        payments = self.db.get_weekly_payments(self.current_employee_id, week_start_date)
        
        # Ek ödemeler ve kesintileri hesapla
        total_additions = 0
        total_deductions = 0
        
        for payment_id, payment_type, amount, description, is_permanent in payments:
            # Ödeme tipini küçük harfe çevir (büyük/küçük harf duyarlılığını ortadan kaldırmak için)
            payment_type_lower = payment_type.lower() if payment_type else ""
            
            # Eklenti olarak kabul edilen tipler
            if payment_type_lower in ["eklenti", "bonus", "prim", "ek ödeme", "ek odeme", "ikramiye"]:
                total_additions += amount
            # Kesinti olarak kabul edilen tipler
            elif payment_type_lower in ["kesinti", "ceza", "borç", "borc", "avans", "deduction"]:
                total_deductions += amount
        
        # Toplam ek ödeme/kesinti
        net_payments = total_additions - total_deductions
        
        # Etiketleri güncelle
        self.total_hours_value.setText(f"{total_hours:.1f} saat")
        self.weekly_salary_value.setText(f"{self.format_currency(weekly_salary)}")
        self.allowances_value.setText(f"{self.format_currency(total_allowances)}")
        self.additions_value.setText(f"{self.format_currency(total_additions)}")
        self.deductions_value.setText(f"{self.format_currency(total_deductions)}")
        
        # Toplam haftalık ücreti hesapla (ek ödemeler eklenir, kesintiler düşülür)
        total_weekly_salary = weekly_salary + total_allowances + total_additions - total_deductions
        self.total_weekly_value.setText(f"{self.format_currency(total_weekly_salary)}")
    
    def set_employee(self, employee_id, employee_name):
        """Çalışan bilgisini ayarlar ve günleri yükler"""
        if not employee_id:
            return
        
        self.current_employee_id = employee_id
        self.employee_name_label.setText(f"{employee_name}")
        self.summary_employee_name.setText(f"{employee_name}")
        
        # Günleri yükle
        self.load_week_days()
        self.load_saved_records()
    
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
    
    def load_prev_week(self):
        """Önceki haftayı yükler"""
        self.current_date = self.current_date.addDays(-7)
        self.load_week_days()
    
    def load_next_week(self):
        """Sonraki haftayı yükler"""
        self.current_date = self.current_date.addDays(7)
        self.load_week_days()
    
    def on_date_changed(self, date):
        """Tarih değiştiğinde çağrılır"""
        self.current_date = date
        self.load_week_days()
    
# Bu blok sadece bu dosya doğrudan çalıştırıldığında çalışır
if __name__ == "__main__":
    import sys
    import os
    
    # Ana dizini Python yoluna ekle
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from PyQt5.QtWidgets import QApplication
    from models.database import EmployeeDB
    
    app = QApplication(sys.argv)
    db = EmployeeDB('employee.db')
    window = TimeTrackingForm(db)
    window.show()
    sys.exit(app.exec_())
