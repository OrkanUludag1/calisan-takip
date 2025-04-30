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
    from PyQt5.QtCore import Qt, QDate, QTime, QTimer, pyqtSignal, QPoint, QEvent
    from PyQt5.QtGui import QColor, QBrush, QPainter, QPen, QFont
    from datetime import datetime, timedelta
    import os
    import sys
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
    from PyQt5.QtCore import Qt, QDate, QTime, QTimer, pyqtSignal, QPoint, QEvent
    from PyQt5.QtGui import QColor, QBrush, QPainter, QPen, QFont
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
        
        # Stil ayarları
        self.setStyleSheet("""
            QTimeEdit {
                border: none;
                padding: 6px;
                font-size: 14px;
                background-color: transparent;
            }
            QTimeEdit::up-button, QTimeEdit::down-button {
                border: none;
                width: 0px;
                height: 0px;
            }
        """)
    
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
        # Sadece sayı tuşlarına izin ver ve iki hane girilmeden değişiklik olmasın
        if event.key() >= Qt.Key_0 and event.key() <= Qt.Key_9:
            digit = event.key() - Qt.Key_0
            current_time = self.time()
            hour = current_time.hour()
            minute = current_time.minute()
            section = self.currentSection()
            self.current_section = section
            if section == QTimeEdit.HourSection:
                if self.first_digit == -1:
                    # Sadece iki hane girilmeden değişmesin
                    if digit > 2:
                        # 24 saat formatı, tek hane girilirse başına 0 ekle
                        hour = digit
                        self.first_digit = -1
                        self.setSelectedSection(QTimeEdit.MinuteSection)
                    else:
                        self.first_digit = digit
                        return  # İkinci hane bekleniyor, değişiklik yok
                else:
                    if self.first_digit == 2 and digit > 3:
                        digit = 3
                    hour = self.first_digit * 10 + digit
                    self.first_digit = -1
                    self.setSelectedSection(QTimeEdit.MinuteSection)
            elif section == QTimeEdit.MinuteSection:
                if self.first_digit == -1:
                    if digit > 5:
                        minute = digit
                        self.first_digit = -1
                        self.setSelectedSection(QTimeEdit.HourSection)
                    else:
                        self.first_digit = digit
                        return  # İkinci hane bekleniyor, değişiklik yok
                else:
                    minute = self.first_digit * 10 + digit
                    self.first_digit = -1
                    self.setSelectedSection(QTimeEdit.HourSection)
            new_time = QTime(hour, minute)
            self.setTime(new_time)
            return
        elif event.key() == Qt.Key_Backspace:
            self.first_digit = -1
            super().keyPressEvent(event)
        elif event.key() == Qt.Key_Tab:
            self.first_digit = -1
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

# Zaman takibi formu
class TimeTrackingForm(QWidget):
    """Zaman takibi formu"""
    
    # Zaman değiştiğinde yayınlanacak sinyal
    time_changed_signal = pyqtSignal()
    data_changed = pyqtSignal()
    
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

        # Pencere aktif/pasif kontrolü için event filter ekle
        self.installEventFilter(self)

        # Mevcut haftanın başlangıç tarihi
        days_to_monday = self.current_date.dayOfWeek() - 1
        week_start = self.current_date.addDays(-days_to_monday)
        self.current_week_start = week_start.toString("yyyy-MM-dd")

        # UI'ı başlat
        self.initUI()
        
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
        
        # Haftanın başlangıç tarihi hesapla (Pazartesi)
        week_start = self.current_date
        if week_start.dayOfWeek() != 1:  # 1 = Pazartesi
            days_to_monday = week_start.dayOfWeek() - 1
            week_start = week_start.addDays(-days_to_monday)
        
        # current_week_start değerini ayarla (DB sorgularında kullanılacak)
        self.current_week_start = week_start.toString("yyyy-MM-dd")
        
        # Eğer haftada hiç kayıt yoksa, aktif çalışanlar için varsayılan saatlerle otomatik kayıt oluştur
        week_start_str = self.current_date.toString("yyyy-MM-dd") if hasattr(self.current_date, 'toString') else str(self.current_date)
        records = []
        for i in range(7):
            current_date = week_start.addDays(i)
            # Sadece Pazartesi(0)~Cuma(4) günleri için kayıt oluştur
            if i < 5 and self.current_employee_id:
                record = self.db.get_work_hours(self.current_employee_id, current_date.toString("yyyy-MM-dd"))
                if not record:
                    # Varsayılan saatlerle otomatik kayıt oluştur
                    self.db.add_work_hours(
                        self.current_employee_id,
                        current_date.toString("yyyy-MM-dd"),
                        "08:15", "13:15", "13:45", "18:45"
                    )
        # Sonrasında tabloyu güncelle
        
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
                # Pasif gün: sadece italik ve flu, bold olmasın
                font = day_item.font()
                font.setBold(False)
                font.setItalic(True)
                day_item.setFont(font)
                day_item.setForeground(QBrush(QColor("#666666")))  # Gri yazı
            else:
                # Aktif gün: sadece bold, italik olmasın
                font_day = day_item.font()
                font_day.setBold(True)
                font_day.setItalic(False)
                day_item.setFont(font_day)
            
            # Saat alanlarını ayarla
            entry_time_val = record['entry_time'] if record and record['entry_time'] else "08:15"
            lunch_start_val = record['lunch_start'] if record and record['lunch_start'] else "13:15"
            lunch_end_val = record['lunch_end'] if record and record['lunch_end'] else "13:45"
            exit_time_val = record['exit_time'] if record and record['exit_time'] else "18:45"
            
            for col in range(1, 5):
                time_edit = CustomTimeEdit()
                time_edit.setDisplayFormat("HH:mm")
                # Veritabanından gelen saatleri kullan
                if col == 1:
                    h, m = map(int, entry_time_val.split(":"))
                    time_edit.setTime(QTime(h, m))
                elif col == 2:
                    h, m = map(int, lunch_start_val.split(":"))
                    time_edit.setTime(QTime(h, m))
                elif col == 3:
                    h, m = map(int, lunch_end_val.split(":"))
                    time_edit.setTime(QTime(h, m))
                elif col == 4:
                    h, m = map(int, exit_time_val.split(":"))
                    time_edit.setTime(QTime(h, m))
                time_edit.setReadOnly(not is_active)
                time_edit.setEnabled(is_active)
                time_edit.timeChanged.connect(lambda time, row=i: self.on_time_changed(row))
                # QTimeEdit'in görünümünü özelleştir
                time_edit.setStyleSheet("""
                    QTimeEdit {
                        border: none;
                        padding: 6px;
                        font-size: 14px;
                        background-color: transparent;
                    }
                    QTimeEdit::up-button, QTimeEdit::down-button {
                        border: none;
                        width: 0px;
                        height: 0px;
                    }
                """)
                # Metni ortala
                time_edit.setAlignment(Qt.AlignCenter)
                # Eğer pasifse, sayıyı gizle
                if not is_active:
                    time_edit.setStyleSheet(time_edit.styleSheet() + """
                        QTimeEdit {
                            color: transparent;
                        }
                    """)
                self.days_table.setCellWidget(i, col, time_edit)
        
        # Toplam saatleri hesapla
        self.calculate_total_hours()
    
    def initUI(self):
        # Tabloyu önce oluştur
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(8)
        self.days_table.setHorizontalHeaderLabels([
            "Gün", "Giriş", "Ö. Başlangıç", "Ö. Bitiş", "Çıkış", "Normal Ç.", "Fazla Ç.", "Yemek"
        ])
        self.days_table.verticalHeader().setDefaultSectionSize(34)
        self.days_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.days_table.setFixedWidth(850)
        self.days_table.verticalHeader().setVisible(False)
        self.days_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.days_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.days_table.customContextMenuRequested.connect(self.show_context_menu)
        self.days_table.setStyleSheet("""
            QTableWidget { 
                background: white; 
                font-size: 14px; 
                border: none; 
            } 
            QTableWidget::item { 
                font-size: 14px; 
                height: 34px; 
            } 
            QTableWidget::item:selected { 
                background: #e0edfa; 
                color: #2a5885; 
            }
        """)
        self.days_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section { 
                background-color: #2a5885; 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
                padding: 6px 0; 
                border: none; 
            }
        """)
        self.days_table.setAlternatingRowColors(True)
        self.days_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.days_table.setSelectionMode(QTableWidget.SingleSelection)

        # --- ORTA: Tabloyu ortalamak için ---
        week_select_layout = QHBoxLayout()
        week_select_layout.setSpacing(8)
        week_select_layout.setContentsMargins(0, 0, 0, 0)
        center_vlayout = QVBoxLayout()
        center_vlayout.addWidget(self.days_table, alignment=Qt.AlignHCenter)
        center_widget = QWidget()
        center_widget.setLayout(center_vlayout)
        center_widget.setMinimumWidth(900)
        # İçerik düzeni (tablo ve merkez)
        content_layout = QVBoxLayout()
        content_layout.addWidget(center_widget)

        # Özet paneli (summary_container ve içeriği)
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(0)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        # ÇALIŞAN ADI LABEL'I SADECE BİR KEZ OLUŞTURULUYOR
        if hasattr(self, 'employee_name_label_summary') and self.employee_name_label_summary is not None:
            label = self.employee_name_label_summary
        else:
            self.employee_name_label_summary = QLabel("")
            label = self.employee_name_label_summary
        label.setStyleSheet("font-size: 16px; color: #183153; font-weight: bold; font-family: Arial, Helvetica, sans-serif; padding: 8px 0px;")
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(32)
        employee_name_frame = QFrame()
        employee_name_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: 2px solid #d0d8e8;
                border-radius: 18px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        employee_name_layout = QVBoxLayout()
        employee_name_layout.setContentsMargins(16, 8, 16, 8)
        employee_name_layout.addWidget(label)
        employee_name_frame.setLayout(employee_name_layout)
        employee_name_frame.setMinimumHeight(48)
        summary_layout.addWidget(employee_name_frame, alignment=Qt.AlignTop)
        summary_layout.addSpacing(18)
        summary_rows = [
            ("Normal Çalışma Saati Toplamı", "hours", "00:00"),
            ("Fazla Çalışma Saati Toplamı", "overtime_hours", "00:00"),
            ("Normal Çalışma Ücreti", "normal_salary", "0,00 TL"),
            ("Fazla Çalışma Ücreti", "overtime_salary", "0,00 TL"),
            ("Yemek", "food", "0,00 TL"),
            ("Yol", "transport", "0,00 TL"),
            ("Eklenti", "addition", "0,00 TL"),
            ("Kesinti", "deduction", "0,00 TL"),
        ]
        self.summary_labels = {}
        for idx, (label, key, default_value) in enumerate(summary_rows):
            row_widget = QWidget()
            row_widget.setMinimumHeight(48)
            row_widget.setMaximumHeight(60)
            row_layout = QVBoxLayout()
            row_layout.setSpacing(0)
            row_layout.setContentsMargins(4, 0, 4, 0)
            title_lbl = QLabel(label)
            title_lbl.setStyleSheet("font-size: 13px; color: #222; font-weight: normal; font-family: Arial, Helvetica, sans-serif;")
            title_lbl.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            value_lbl = QLabel(default_value)
            value_lbl.setStyleSheet("font-size: 17px; color: #111; font-weight: bold; font-family: Arial, Helvetica, sans-serif; margin-top: 10px;")
            value_lbl.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            row_layout.addWidget(title_lbl)
            row_layout.addWidget(value_lbl)
            row_widget.setLayout(row_layout)
            summary_layout.addWidget(row_widget)
            if idx < len(summary_rows) - 1:
                summary_layout.addSpacing(10)
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Plain)
                line.setStyleSheet("color: #e0e0e0; background: #e0e0e0; height: 1px;")
                line.setFixedHeight(1)
                summary_layout.addWidget(line)
                summary_layout.addSpacing(10)
            self.summary_labels[key] = {'title': title_lbl, 'value': value_lbl}
        summary_widget = QWidget()
        summary_widget.setLayout(summary_layout)
        net_frame = QFrame()
        net_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: 2px solid #d0d8e8;
                border-radius: 18px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        net_layout = QVBoxLayout()
        net_layout.setContentsMargins(16, 10, 16, 10)
        net_title = QLabel("Toplam Ödenecek")
        net_title.setStyleSheet("font-size: 16px; color: #111; font-weight: bold; letter-spacing: 1px; font-family: Arial, Helvetica, sans-serif;")
        net_title.setAlignment(Qt.AlignCenter)
        net_layout.addWidget(net_title, alignment=Qt.AlignCenter)
        net_value = QLabel("0,00 TL")
        net_value.setStyleSheet("font-size: 26px; color: #111; font-weight: bold; letter-spacing: 1px; font-family: Arial, Helvetica, sans-serif;")
        net_value.setAlignment(Qt.AlignCenter)
        net_layout.addWidget(net_value, alignment=Qt.AlignCenter)
        net_frame.setLayout(net_layout)
        self.summary_labels['net'] = {'title': net_title, 'value': net_value}
        summary_container_layout = QVBoxLayout()
        summary_container_layout.addStretch(1)
        summary_container_layout.addWidget(summary_widget, alignment=Qt.AlignHCenter)
        summary_container_layout.addWidget(net_frame, alignment=Qt.AlignHCenter)
        summary_container_layout.addStretch(1)
        summary_container_layout.setContentsMargins(0, 0, 0, 0)
        summary_container = QWidget()
        summary_container.setLayout(summary_container_layout)
        summary_container.show()

        # Ana layout'u oluşturup doğrudan self'e bağla
        ana_layout = QHBoxLayout(self)
        ana_layout.addLayout(content_layout, stretch=3)
        ana_layout.addWidget(summary_container, stretch=1)

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
            font = day_item.font()
            font.setItalic(False)
            day_item.setFont(font)
            day_item.setForeground(QBrush())  # Varsayılan yazı rengi
            
            # Eğer gün Cumartesi veya Pazar ise saatleri otomatik olarak ayarla
            date_item = self.days_table.item(row, 0)
            current_day = None
            if date_item:
                current_day = date_item.data(Qt.UserRole)
            if current_day:
                try:
                    weekday = current_day.dayOfWeek() - 1  # Pazartesi=0, Cumartesi=5, Pazar=6
                except Exception:
                    weekday = None
                if weekday in [5, 6]:
                    # Saatleri otomatik olarak ayarla
                    saatler = [(8,15), (13,15), (13,45), (18,45)]
                    for col, (h, m) in enumerate(saatler, start=1):
                        time_edit = self.days_table.cellWidget(row, col)
                        if time_edit:
                            time_edit.setTime(QTime(h, m))
            # Saatleri göster
            for col in range(1, 5):
                time_edit = self.days_table.cellWidget(row, col)
                if time_edit:
                    time_edit.setStyleSheet(time_edit.styleSheet().replace("color: transparent;", ""))
            # Aktif günler için gün ismini bold yap
            font_day = day_item.font()
            font_day.setBold(True)
            day_item.setFont(font_day)
        else:
            # Pasif yaparken italik ve gri renk
            font = day_item.font()
            font.setBold(False)
            font.setItalic(True)
            day_item.setFont(font)
            day_item.setForeground(QBrush(QColor("#666666")))  # Gri renk
            
            # Saatleri gizle
            for col in range(1, 5):
                time_edit = self.days_table.cellWidget(row, col)
                if time_edit:
                    time_edit.setStyleSheet(time_edit.styleSheet() + """
                        QTimeEdit {
                            color: transparent;
                        }
                    """)
        
        # Normal Ç. ve Fazla Ç. hücrelerini de aktif/pasif durumuna göre güncelle
        for col in [5, 6]:
            item = self.days_table.item(row, col)
            if item:
                if active_status:
                    # Aktif: varsa bold yap, boşsa dokunma
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                else:
                    # Pasif: tamamen boş bırak
                    self.days_table.setItem(row, col, QTableWidgetItem(""))
        
        # Zaman editörlerini güncelle
        for col in range(1, 5):  # Giriş, Öğle Başlangıç, Öğle Bitiş, Çıkış
            time_edit = self.days_table.cellWidget(row, col)
            time_edit.setReadOnly(not active_status)
            time_edit.setEnabled(active_status)
        
        # Değişiklikleri kaydet
        self.auto_save_row(row)
        
        # Toplam saatleri güncelle
        self.calculate_total_hours()
        self.data_changed.emit()
    
    def on_time_changed(self, row):
        """Zaman değiştiğinde çağrılır"""
        self.auto_save_row(row)
        self.calculate_total_hours()
        
        # Sinyali yayınla - haftalık sekmenin güncellenmesi için
        self.time_changed_signal.emit()
        self.data_changed.emit()
    
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
        entry_widget = self.days_table.cellWidget(row, 1)
        lunch_start_widget = self.days_table.cellWidget(row, 2)
        lunch_end_widget = self.days_table.cellWidget(row, 3)
        exit_widget = self.days_table.cellWidget(row, 4)
        entry_time = entry_widget.time().toString("HH:mm") if entry_widget else "00:00"
        lunch_start = lunch_start_widget.time().toString("HH:mm") if lunch_start_widget else "00:00"
        lunch_end = lunch_end_widget.time().toString("HH:mm") if lunch_end_widget else "00:00"
        exit_time = exit_widget.time().toString("HH:mm") if exit_widget else "00:00"
        
        # Veritabanına kaydet - day_active parametresini de ekle
        self.db.save_work_hours(
            self.current_employee_id, date_str, 
            entry_time, lunch_start, lunch_end, exit_time, 
            1 if is_active else 0,  # is_active parametresi
            1 if is_active else 0   # day_active parametresi
        )

        # --- Sabit ek ödeme kontrolü ve ekleme ---
        # Haftada en az bir aktif gün varsa ve o haftaya ait sabit ek ödeme yoksa otomatik ekle
        week_start_date = self.current_week_start if hasattr(self, 'current_week_start') else None
        if week_start_date:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT 1 FROM payments WHERE employee_id = ? AND week_start_date = ? AND is_permanent = 1
            ''', (self.current_employee_id, week_start_date))
            sabit_odeme_var = cursor.fetchone() is not None
            if not sabit_odeme_var:
                self.db.add_payment(
                    self.current_employee_id,
                    week_start_date,
                    "bonus",  # veya "permanent"
                    0.0,
                    "Otomatik Sabit Ek Ödeme",
                    1
                )
        self.data_changed.emit()
    
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
        food_days = 0  # 5 saat üstü gün sayısı
        
        # Her gün için çalışma saatlerini hesapla
        daily_overtime_list = []
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
            date_item = self.days_table.item(row, 0)
            current_day = None
            if date_item:
                current_day = date_item.data(Qt.UserRole)

            # Eğer herhangi bir widget eksikse, bu günü atla
            if not entry_widget or not lunch_start_widget or not lunch_end_widget or not exit_widget:
                continue

            # Zaman değerlerini al
            entry_time = entry_widget.time()
            lunch_start = lunch_start_widget.time()
            lunch_end = lunch_end_widget.time()
            exit_time = exit_widget.time()

            # Sabah çalışma saatleri (saat cinsinden)
            morning_hours = 0
            if entry_time.hour() <= lunch_start.hour():  # Normal durum
                morning_seconds = (lunch_start.hour() * 3600 + lunch_start.minute() * 60) - (entry_time.hour() * 3600 + entry_time.minute() * 60)
                morning_hours = morning_seconds / 3600.0 if morning_seconds > 0 else 0

            # Öğleden sonra çalışma saatleri (saat cinsinden)
            afternoon_hours = 0
            if lunch_end.hour() <= exit_time.hour():  # Normal durum
                overtime_start_minutes_actual = 18 * 60 + 45
                day_end_minutes = exit_time.hour() * 60 + exit_time.minute()
                # Normal çalışma bitişi: 18:45 veya çıkış saati hangisi erkense
                normal_end_minutes = min(day_end_minutes, overtime_start_minutes_actual)
                afternoon_seconds = (normal_end_minutes * 60) - (lunch_end.hour() * 3600 + lunch_end.minute() * 60)
                afternoon_hours = afternoon_seconds / 3600.0 if afternoon_seconds > 0 else 0

            # Toplam çalışma saatleri (saat cinsinden)
            day_hours = morning_hours + afternoon_hours

            # Negatif değerleri düzelt (zaman çakışmaları veya hatalı giriş)
            if day_hours < 0:
                day_hours = 0

            # 5 saatten fazla çalışıldıysa yemek hakkı kazandır
            daily_food_count = 0
            if day_hours > 5:
                daily_food_count += 1

            # Eğer çıkış saati 20:00'dan sonra ise, bir yemek hakkı daha ekle
            if (exit_time.hour() > 20) or (exit_time.hour() == 20 and exit_time.minute() > 0):
                daily_food_count += 1

            # Günlük yemek parası, ilgili günün satırına yazılsın
            if is_active:
                daily_food_amount = daily_food_count * 10  # employee_info[3]
                food_item = QTableWidgetItem(self.format_currency(daily_food_amount))
                food_item.setTextAlignment(Qt.AlignCenter)
                self.days_table.setItem(row, 7, food_item)

            # Haftalık toplam için de sayacı artır
            food_days += daily_food_count

            # Gün bilgisi ve hafta içi/sonu kontrolü
            weekday = None
            if current_day:
                try:
                    weekday = current_day.dayOfWeek() - 1  # Pazartesi=0, Cumartesi=5, Pazar=6
                except Exception:
                    weekday = None

            # Fazla mesai ve normal saat hesaplamaları
            overtime_hours = 0
            normal_hours = 0
            if weekday in [5, 6]:
                # Cumartesi/Pazar: tümü fazla mesai
                overtime_hours = day_hours
                normal_hours = 0
            else:
                # Hafta içi
                overtime_start_minutes_actual = 18 * 60 + 45
                day_start_minutes = entry_time.hour() * 60 + entry_time.minute()
                day_end_minutes = exit_time.hour() * 60 + exit_time.minute()
                # Normal çalışma bitişi: 18:45 veya çıkış saati hangisi erkense
                normal_end_minutes = min(day_end_minutes, overtime_start_minutes_actual)
                # Sabah çalışma: Giriş -> Öğle Başlangıç
                morning_seconds = (lunch_start.hour() * 3600 + lunch_start.minute() * 60) - (entry_time.hour() * 3600 + entry_time.minute() * 60)
                morning_hours = morning_seconds / 3600.0 if morning_seconds > 0 else 0
                # Akşam çalışma: Öğle Bitiş -> Normal Çalışma Bitişi
                afternoon_seconds = (normal_end_minutes * 60) - (lunch_end.hour() * 3600 + lunch_end.minute() * 60)
                afternoon_hours = afternoon_seconds / 3600.0 if afternoon_seconds > 0 else 0
                normal_hours = morning_hours + afternoon_hours
                # Fazla mesai: 18:45 sonrası
                if day_end_minutes > overtime_start_minutes_actual:
                    overtime_minutes = day_end_minutes - overtime_start_minutes_actual
                    overtime_hours = overtime_minutes / 60.0
                else:
                    overtime_hours = 0

            # Negatif değerleri sıfırla
            if normal_hours < 0:
                normal_hours = 0
            if overtime_hours < 0:
                overtime_hours = 0

            # Günlük saatleri tabloya yaz
            normal_int = int(normal_hours)
            normal_min = int(round((normal_hours - normal_int) * 60))
            if normal_min == 60:
                normal_int += 1
                normal_min = 0
            if not is_active or (normal_int == 0 and normal_min == 0):
                normal_item = QTableWidgetItem("")
            else:
                normal_item = QTableWidgetItem(f"{normal_int}:{normal_min:02d}")
                font = normal_item.font()
                font.setBold(True)
                normal_item.setFont(font)
            normal_item.setTextAlignment(Qt.AlignCenter)
            self.days_table.setItem(row, 5, normal_item)

            overtime_int = int(overtime_hours)
            overtime_min = int(round((overtime_hours - overtime_int) * 60))
            if overtime_min == 60:
                overtime_int += 1
                overtime_min = 0
            if not is_active or (overtime_int == 0 and overtime_min == 0):
                overtime_item = QTableWidgetItem("")
            else:
                overtime_item = QTableWidgetItem(f"{overtime_int}:{overtime_min:02d}")
                font_ot = overtime_item.font()
                font_ot.setBold(True)
                overtime_item.setFont(font_ot)
            overtime_item.setTextAlignment(Qt.AlignCenter)
            self.days_table.setItem(row, 6, overtime_item)

            # Toplamlar için biriktir
            total_hours += normal_hours
            if 'total_overtime_hours' not in locals():
                total_overtime_hours = 0
            total_overtime_hours += overtime_hours

            # Günlük fazla mesai saatini tabloya yaz
            # overtime_val = overtime_hours
            # overtime_int = int(overtime_val)
            # overtime_min = int((overtime_val - overtime_int) * 60)
            # overtime_item = QTableWidgetItem(f"{overtime_int}:{overtime_min:02d}")
            # overtime_item.setTextAlignment(Qt.AlignCenter)
            # self.days_table.setItem(row, 6, overtime_item)

            # Normal saatleri tabloya yaz
            # normal_val = normal_hours
            # normal_int = int(normal_val)
            # normal_min = int((normal_val - normal_int) * 60)
            # normal_item = QTableWidgetItem(f"{normal_int}:{normal_min:02d}")
            # normal_item.setTextAlignment(Qt.AlignCenter)
            # self.days_table.setItem(row, 5, normal_item)

        # Toplam saati saat ve dakika olarak ayır
        total_hours_int = int(total_hours)
        total_minutes = int(round((total_hours - total_hours_int) * 60))
        if total_minutes == 60:
            total_hours_int += 1
            total_minutes = 0
        self.summary_labels['hours']['value'].setText(f"{total_hours_int}:{total_minutes:02d}")

        overtime_total = total_overtime_hours if 'total_overtime_hours' in locals() else 0
        overtime_hours_int = int(overtime_total)
        overtime_minutes = int(round((overtime_total - overtime_hours_int) * 60))
        if overtime_minutes == 60:
            overtime_hours_int += 1
            overtime_minutes = 0
        self.summary_labels['overtime_hours']['value'].setText(f"{overtime_hours_int}:{overtime_minutes:02d}")

        # Çalışan bilgilerini al
        employee_info = self.db.get_employee(self.current_employee_id)
        if not employee_info:
            return

        weekly_salary = employee_info[2] if employee_info else 0  # Haftalık ücret
        hourly_rate = weekly_salary / 50  # Saatlik ücret
        overtime_rate = hourly_rate * 1.5  # Fazla mesai ücreti

        # Haftalık ücret hesapla (normal çalışma saati x saatlik ücret)
        earned_salary = total_hours * hourly_rate
        # Fazla mesai ücreti ekle
        if 'total_overtime_hours' in locals():
            earned_salary += total_overtime_hours * overtime_rate

        # Yol ve yemek ödemeleri (günlük 5 saatten fazla olan günler için yemek)
        food_allowance = food_days * employee_info[3]  # daily_food
        transport_allowance = active_days * employee_info[4]  # daily_transport
        total_allowances = food_allowance + transport_allowance

        # Eklenti değeri, kesintiyi girdiğimiz yerdeki eklenti değerinden gelsin
        week_start_str = self.current_date.toString('yyyy-MM-dd') if hasattr(self.current_date, 'toString') else str(self.current_date)
        # Haftada hiç çalışma yoksa sabit ek ödeme eklenmesin
        calisma_var = (total_hours > 0 or (hasattr(self, 'day_active_status') and any(self.day_active_status)))
        total_additions = self.db.get_employee_additions(self.current_employee_id, week_start_str, include_permanent_if_no_work=calisma_var) if self.current_employee_id else 0

        # Etiketleri güncelle - toplam saati saat:dakika formatında göster
        # self.summary_labels['hours']['value'].setText(f"{total_hours_int}:{total_minutes:02d}")
        # overtime_hours_int = int(total_overtime_hours) if 'total_overtime_hours' in locals() else 0
        # overtime_minutes = int(((total_overtime_hours if 'total_overtime_hours' in locals() else 0) - overtime_hours_int) * 60)
        # self.summary_labels['overtime_hours']['value'].setText(f"{overtime_hours_int}:{overtime_minutes:02d}")

        normal_salary = total_hours * hourly_rate
        overtime_salary = (total_overtime_hours if 'total_overtime_hours' in locals() else 0) * overtime_rate
        self.summary_labels['normal_salary']['value'].setText(self.format_currency(normal_salary))
        self.summary_labels['overtime_salary']['value'].setText(self.format_currency(overtime_salary))

        self.summary_labels['food']['value'].setText(self.format_currency(food_allowance))
        self.summary_labels['transport']['value'].setText(self.format_currency(transport_allowance))
        self.summary_labels['addition']['value'].setText(self.format_currency(total_additions))
        self.summary_labels['deduction']['value'].setText("0,00 TL")

        # Net ödenek hesapla (ücret + ödenekler)
        total_weekly_salary = normal_salary + overtime_salary + total_allowances + total_additions
        self.summary_labels['net']['value'].setText(self.format_currency(total_weekly_salary))
    
    def set_employee(self, employee_id, employee_name):
        """Çalışan bilgisini ayarlar ve günleri yükler"""
        self.current_employee_id = employee_id
        
        # Günleri yükle
        self.load_week_days()
        self.load_saved_records()
        
        # Çalışan adını özet panelinin üstüne yaz
        self.employee_name_label_summary.setText(employee_name)
        
        # Görünürlüğü zorla
        self.employee_name_label_summary.show()
        parent_frame = self.employee_name_label_summary.parent()
        if parent_frame:
            parent_frame.show()
        if parent_frame and parent_frame.parent():
            parent_frame.parent().show()
    
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
    
    def set_week(self, week_str):
        """Haftayı dışarıdan ayarla ve tabloyu güncelle"""
        from PyQt5.QtCore import QDate
        self.current_date = QDate.fromString(week_str, "yyyy-MM-dd")
        self.load_week_days()
    
    def clear_form(self):
        """Formu temizle"""
        self.days_table.setRowCount(0)
        self.day_active_status = []
        for key in self.summary_labels:
            self.summary_labels[key]['value'].setText("0,00 TL")

    def disconnect_all_signals(self):
        for row in range(self.days_table.rowCount()):
            for col in range(1, 5):  # Giriş, Öğle Başlangıç, Öğle Bitiş, Çıkış
                time_edit = self.days_table.cellWidget(row, col)
                if time_edit:
                    try:
                        time_edit.timeChanged.disconnect()
                    except Exception:
                        pass

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.WindowActivate:
            # Pencere aktif oldu, timer'ı başlat
            if not self.auto_save_timer.isActive():
                self.auto_save_timer.start(10000)
        elif event.type() == QEvent.WindowDeactivate:
            # Pencere pasif oldu, timer'ı durdur
            if self.auto_save_timer.isActive():
                self.auto_save_timer.stop()
        return super().eventFilter(obj, event)

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
    sys.exit(app.exec_())
