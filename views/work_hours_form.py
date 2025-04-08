from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QComboBox, QPushButton, QMessageBox,
    QSpinBox, QMenu
)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont

from datetime import datetime, timedelta
import calendar

from models.database import EmployeeDB
from utils.helpers import calculate_working_hours

class WorkHoursForm(QWidget):
    """Çalışma saatleri formu"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Veritabanı bağlantısı
        self.db = EmployeeDB()
        
        # Çalışan ID'si
        self.current_employee_id = None
        
        # Hafta başlangıç tarihi
        self.current_week_start = QDate.currentDate()
        self.current_week_start = self.current_week_start.addDays(-(self.current_week_start.dayOfWeek() - 1))
        
        # Hafta tarihleri
        self.week_dates = []
        
        # Varsayılan saatler
        self.default_entry_time = QTime(8, 15)
        self.default_lunch_start = QTime(13, 15)
        self.default_lunch_end = QTime(13, 45)
        self.default_exit_time = QTime(18, 45)
        
        # UI başlat
        self.initUI()
        
        # Çalışanları yükle
        self.load_employees()
        
        # Hafta tarihlerini güncelle
        self.update_week_dates()
        
        # Çalışma saatleri kayıtları
        self.work_hours_data = {}
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        layout = QVBoxLayout(self)
        
        # Üst kısım - Çalışan seçimi ve hafta bilgisi
        top_layout = QHBoxLayout()
        
        # Çalışan seçimi
        employee_layout = QHBoxLayout()
        employee_label = QLabel("Çalışan:")
        self.employee_combo = QComboBox()
        self.employee_combo.currentIndexChanged.connect(self.on_employee_selected)
        
        # Tarih navigasyon kontrolleri
        nav_layout = QHBoxLayout()
        self.prev_week_btn = QPushButton("◀ Önceki Hafta")
        self.next_week_btn = QPushButton("Sonraki Hafta ▶")
        self.week_label = QLabel()
        
        self.prev_week_btn.clicked.connect(self.prev_week)
        self.next_week_btn.clicked.connect(self.next_week)
        
        # Haftalık saatler oluştur butonu
        self.create_hours_btn = QPushButton("Haftalık Çalışma Saati Oluştur")
        self.create_hours_btn.clicked.connect(self.add_work_hours)
        
        # Navigasyon butonlarını ekle
        nav_layout.addWidget(self.prev_week_btn)
        nav_layout.addWidget(self.week_label)
        nav_layout.addWidget(self.next_week_btn)
        
        self.week_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        
        employee_layout.addWidget(employee_label)
        employee_layout.addWidget(self.employee_combo)
        employee_layout.addStretch()
        
        top_layout.addLayout(employee_layout)
        top_layout.addLayout(nav_layout)
        top_layout.addWidget(self.create_hours_btn)
        
        layout.addLayout(top_layout)
        
        # Saat tablosu
        self.hours_table = QTableWidget()
        self.hours_table.setColumnCount(5)
        self.hours_table.setRowCount(7)  # Haftanın 7 günü
        
        # Satır yüksekliğini ayarla
        self.hours_table.verticalHeader().setDefaultSectionSize(55)
        
        # Tablo başlıkları
        headers = ["Gün", "Giriş Saati", "Öğle Başlangıç", "Öğle Bitiş", "Çıkış Saati"]
        self.hours_table.setHorizontalHeaderLabels(headers)
        
        # Tablo stilini ayarla
        self.hours_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.hours_table.verticalHeader().setVisible(False)
        self.hours_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.hours_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
            }
            QLabel {
                qproperty-alignment: AlignCenter;
            }
        """)
        
        # Sağ tıklama menüsü için tabloyu hazırla
        self.hours_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hours_table.customContextMenuRequested.connect(self.showContextMenu)
        
        # Günleri ekle
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        for row, day in enumerate(days):
            day_item = QTableWidgetItem(day)
            day_item.setFlags(day_item.flags() & ~Qt.ItemIsEditable)
            day_item.setTextAlignment(Qt.AlignCenter)
            self.hours_table.setItem(row, 0, day_item)
            
            # Saat düzenleyiciler
            for col in range(1, 5):
                cell_widget = QWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                cell_layout.setSpacing(0)
                cell_layout.setAlignment(Qt.AlignCenter)
                
                # Saat spinbox
                hour_spin = QSpinBox()
                hour_spin.setRange(0, 23)
                hour_spin.setButtonSymbols(QSpinBox.UpDownArrows)
                hour_spin.setAlignment(Qt.AlignCenter)
                hour_spin.setMinimumWidth(35)
                
                # İki nokta üst üste
                colon_label = QLabel(":")
                colon_label.setAlignment(Qt.AlignCenter)
                colon_label.setFixedWidth(5)
                
                # Dakika spinbox
                minute_spin = QSpinBox()
                minute_spin.setRange(0, 59)
                minute_spin.setButtonSymbols(QSpinBox.UpDownArrows)
                minute_spin.setAlignment(Qt.AlignCenter)
                minute_spin.setMinimumWidth(35)
                
                # Düzeni oluştur
                cell_layout.addWidget(hour_spin)
                cell_layout.addWidget(colon_label)
                cell_layout.addWidget(minute_spin)
                
                # Değişiklik sinyallerini bağla
                hour_spin.setProperty("row", row)
                hour_spin.setProperty("col", col)
                minute_spin.setProperty("row", row)
                minute_spin.setProperty("col", col)
                
                hour_spin.valueChanged.connect(self.on_time_spin_changed)
                minute_spin.valueChanged.connect(self.on_time_spin_changed)
                
                # Varsayılan saatleri ayarla
                default_time = None
                if col == 1:  # Giriş
                    default_time = self.default_entry_time
                elif col == 2:  # Öğle başlangıç
                    default_time = self.default_lunch_start
                elif col == 3:  # Öğle bitiş
                    default_time = self.default_lunch_end
                elif col == 4:  # Çıkış
                    default_time = self.default_exit_time
                
                if default_time:
                    hour_spin.setValue(default_time.hour())
                    minute_spin.setValue(default_time.minute())
                
                self.hours_table.setCellWidget(row, col, cell_widget)
        
        layout.addWidget(self.hours_table)
        
        # Alt kısım - Toplam saat bilgisi
        bottom_layout = QHBoxLayout()
        
        self.total_label = QLabel("Toplam Çalışma Saati: 0 saat")
        self.total_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.total_label)
        
        layout.addLayout(bottom_layout)
    
    def on_time_spin_changed(self):
        """Saat veya dakika değiştiğinde çağrılır"""
        sender = self.sender()
        if not sender:
            return
            
        row = sender.property("row")
        col = sender.property("col")
        
        if row is None or col is None:
            return
            
        cell_widget = self.hours_table.cellWidget(row, col)
        if not cell_widget:
            return
            
        layout = cell_widget.layout()
        hour_spin = layout.itemAt(0).widget()
        minute_spin = layout.itemAt(2).widget()
        
        if not hour_spin or not minute_spin:
            return
            
        # Zaman değerleri
        hour = hour_spin.value()
        minute = minute_spin.value()
        
        # Veritabanını güncelle
        self.update_time_value(row, col, hour, minute)
    
    def update_time_value(self, row, col, hour, minute):
        """Belirtilen zaman değerini veritabanında günceller"""
        if not self.current_employee_id or row < 0 or row >= 7:
            return
            
        day_date = self.week_dates[row]
        date_str = day_date.toString("yyyy-MM-dd")
        
        time_type = None
        if col == 1:
            time_type = "entry_time"
        elif col == 2:
            time_type = "lunch_start"
        elif col == 3:
            time_type = "lunch_end"
        elif col == 4:
            time_type = "exit_time"
        
        if time_type:
            time_str = f"{hour:02d}:{minute:02d}"
            self.db.update_work_hours(
                self.current_employee_id,
                date_str,
                time_type,
                time_str
            )
            
            # Toplam saati güncelle
            self.calculate_total_hours()
    
    def load_employees(self):
        """Aktif çalışanları yükler"""
        # Güncel değeri sakla
        current_id = self.current_employee_id
        
        # Combobox'ı temizle
        self.employee_combo.clear()
        
        # Aktif çalışanları al
        employees = self.db.get_employees()
        
        # Combobox'a ekle
        for employee in employees:
            employee_id, name, _, _, _, is_active = employee
            if is_active:
                self.employee_combo.addItem(name, employee_id)
        
        # Eğer önceki seçili çalışan hala listede ise seç
        if current_id:
            for i in range(self.employee_combo.count()):
                if self.employee_combo.itemData(i) == current_id:
                    self.employee_combo.setCurrentIndex(i)
                    break
    
    def on_employee_selected(self, index):
        """Çalışan seçildiğinde çağrılır"""
        if index <= 0:
            self.current_employee_id = None
            self.reset_hours()
            return
        
        self.current_employee_id = self.employee_combo.currentData()
        self.load_work_hours()
    
    def prev_week(self):
        """Önceki haftaya geçer"""
        self.current_week_start = self.current_week_start.addDays(-7)
        self.update_week_dates()
    
    def next_week(self):
        """Sonraki haftaya geçer"""
        self.current_week_start = self.current_week_start.addDays(7)
        self.update_week_dates()
    
    def update_week_dates(self):
        """Hafta tarihlerini günceller"""
        self.week_dates = []
        week_start = self.current_week_start
        
        for i in range(7):
            date = week_start.addDays(i)
            self.week_dates.append(date)
        
        # Hafta etiketini güncelle
        week_start_str = week_start.toString('d MMMM')
        week_end_str = week_start.addDays(6).toString('d MMMM yyyy')
        self.week_label.setText(f"{week_start_str} - {week_end_str}")
        
        # Gün hücrelerini tarihleri olmadan güncelle
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        for row in range(7):
            day_name = days[row]
            day_item = self.hours_table.item(row, 0)
            if day_item:
                day_item.setText(day_name)
        
        # Eğer çalışan seçili ise, verilerini yükle
        if self.current_employee_id:
            self.load_work_hours()
    
    def load_work_hours(self):
        """Seçili çalışanın çalışma saatlerini yükler"""
        if not self.current_employee_id:
            return
            
        # Haftanın başlangıç tarihini alırız (Pazartesi)
        week_date = self.week_dates[0].toString("yyyy-MM-dd")
        
        try:
            # Veritabanından verileri çek
            records = self.db.get_week_work_hours(self.current_employee_id, week_date)
            
            # Verileri sakla
            self.work_hours_data = {}
            
            # Tabloyu temizle
            self.hours_table.clearContents()
            
            # Haftanın günlerini ve saatlerini doldur
            days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            
            for i, record in enumerate(records):
                # Veriyi sakla
                self.work_hours_data[i] = record
                
                # Günü ekle
                day_name = days[i]
                
                # Günün aktif durumuna göre rengini belirle
                day_active = int(record.get('day_active', 1))
                text_color = QColor(0, 0, 0) if day_active else QColor(200, 0, 0)
                
                # Gün adı hücresini ayarla
                day_item = QTableWidgetItem(day_name)
                day_item.setForeground(QBrush(text_color))
                day_item.setTextAlignment(Qt.AlignCenter)
                
                # Pasif günlerde flulaştırma için
                if not day_active:
                    day_item.setBackground(QBrush(QColor(240, 240, 240)))
                
                self.hours_table.setItem(i, 0, day_item)
                
                # Saatleri ayarla
                for col, time_type in enumerate([
                    ('entry_time', 1), 
                    ('lunch_start', 2), 
                    ('lunch_end', 3), 
                    ('exit_time', 4)
                ]):
                    time_key, col_idx = time_type
                    time_value = record.get(time_key, "")
                    
                    if not time_value or time_value == "None":
                        continue
                    
                    # Eğer varsa mevcut hücre widget'i al ve temizle
                    current_widget = self.hours_table.cellWidget(i, col_idx)
                    if current_widget:
                        # Eğer hücrede bir widget varsa, silmek için clear kullanmadan önce widget'i kaldırıyoruz
                        self.hours_table.removeCellWidget(i, col_idx)
                    
                    # Yeni widget oluştur
                    cell_widget = QWidget()
                    cell_layout = QHBoxLayout(cell_widget)
                    cell_layout.setContentsMargins(0, 0, 0, 0)
                    cell_layout.setSpacing(0)
                    cell_layout.setAlignment(Qt.AlignCenter)
                    
                    # Değerleri ayırarak saat ve dakika olarak al
                    try:
                        hour_val, minute_val = map(int, time_value.split(':'))
                    except:
                        hour_val, minute_val = 0, 0
                    
                    # Saat spinbox
                    hour_spin = QSpinBox()
                    hour_spin.setRange(0, 23)
                    hour_spin.setButtonSymbols(QSpinBox.UpDownArrows)
                    hour_spin.setAlignment(Qt.AlignCenter)
                    hour_spin.setMinimumWidth(35)
                    hour_spin.setValue(hour_val)
                    
                    # İki nokta üst üste
                    colon_label = QLabel(":")
                    colon_label.setAlignment(Qt.AlignCenter)
                    colon_label.setFixedWidth(5)
                    
                    # Dakika spinbox
                    minute_spin = QSpinBox()
                    minute_spin.setRange(0, 59)
                    minute_spin.setButtonSymbols(QSpinBox.UpDownArrows)
                    minute_spin.setAlignment(Qt.AlignCenter)
                    minute_spin.setMinimumWidth(35)
                    minute_spin.setValue(minute_val)
                    
                    # Pasif günler için saatleri devre dışı bırak ve flulaştır
                    if not day_active:
                        hour_spin.setEnabled(False)
                        minute_spin.setEnabled(False)
                        cell_widget.setStyleSheet("background-color: #f0f0f0; color: #808080;")
                    
                    # Düzeni oluştur
                    cell_layout.addWidget(hour_spin)
                    cell_layout.addWidget(colon_label)
                    cell_layout.addWidget(minute_spin)
                    
                    # Widgeti hücreye yerleştir
                    self.hours_table.setCellWidget(i, col_idx, cell_widget)
                    
                    # Spinbox sinyallerini bağla
                    hour_spin.valueChanged.connect(
                        lambda value, r=i, c=time_key, hr_spin=hour_spin, min_spin=minute_spin: 
                        self.updateTime(r, c, f"{hr_spin.value():02d}:{min_spin.value():02d}")
                    )
                    minute_spin.valueChanged.connect(
                        lambda value, r=i, c=time_key, hr_spin=hour_spin, min_spin=minute_spin: 
                        self.updateTime(r, c, f"{hr_spin.value():02d}:{min_spin.value():02d}")
                    )
            
            # Toplam saatleri hesapla
            self.calculate_total_hours()
        
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Çalışma saatleri yüklenirken bir hata oluştu: {str(e)}")
    
    def calculate_total_hours(self):
        """Haftalık toplam çalışma saatlerini hesaplar"""
        total_minutes = 0
        
        for row in range(7):  # Haftanın 7 günü
            # Sadece aktif günleri hesaplamaya dahil et
            if row in self.work_hours_data and int(self.work_hours_data[row].get('day_active', 1)) == 0:
                continue
                
            # Giriş saati
            entry_widget = self.hours_table.cellWidget(row, 1)
            if entry_widget:
                layout = entry_widget.layout()
                hour_spin = layout.itemAt(0).widget()
                minute_spin = layout.itemAt(2).widget()
                entry_time = hour_spin.value() * 60 + minute_spin.value()
            else:
                entry_time = 0
                
            # Öğle başlangıç saati
            lunch_start_widget = self.hours_table.cellWidget(row, 2)
            if lunch_start_widget:
                layout = lunch_start_widget.layout()
                hour_spin = layout.itemAt(0).widget()
                minute_spin = layout.itemAt(2).widget()
                lunch_start_time = hour_spin.value() * 60 + minute_spin.value()
            else:
                lunch_start_time = 0
                
            # Öğle bitiş saati
            lunch_end_widget = self.hours_table.cellWidget(row, 3)
            if lunch_end_widget:
                layout = lunch_end_widget.layout()
                hour_spin = layout.itemAt(0).widget()
                minute_spin = layout.itemAt(2).widget()
                lunch_end_time = hour_spin.value() * 60 + minute_spin.value()
            else:
                lunch_end_time = 0
                
            # Çıkış saati
            exit_widget = self.hours_table.cellWidget(row, 4)
            if exit_widget:
                layout = exit_widget.layout()
                hour_spin = layout.itemAt(0).widget()
                minute_spin = layout.itemAt(2).widget()
                exit_time = hour_spin.value() * 60 + minute_spin.value()
            else:
                exit_time = 0
                
            # Çalışma süresi: (Çıkış - Giriş) - (Öğle bitiş - Öğle başlangıç)
            if entry_time > 0 and exit_time > 0:
                working_minutes = (exit_time - entry_time)
                
                # Öğle arası süresini çıkar
                if lunch_start_time > 0 and lunch_end_time > 0:
                    lunch_break = lunch_end_time - lunch_start_time
                    working_minutes -= lunch_break
                    
                total_minutes += working_minutes
        
        # Toplam saatleri göster
        total_hours = total_minutes / 60
        self.total_label.setText(f"Toplam Çalışma Saati: {total_hours:.2f} saat")
    
    def reset_hours(self):
        """Tüm saatleri varsayılan değerlere sıfırlar"""
        for row in range(7):
            # Her gün için saat girişlerini varsayılan değerlere sıfırla
            for col in range(1, 5):
                cell_widget = self.hours_table.cellWidget(row, col)
                if cell_widget:
                    layout = cell_widget.layout()
                    hour_spin = layout.itemAt(0).widget() 
                    minute_spin = layout.itemAt(2).widget()
                    
                    if hour_spin and minute_spin:
                        hour_spin.blockSignals(True)
                        minute_spin.blockSignals(True)
                        
                        if col == 1:  # Giriş
                            hour_spin.setValue(self.default_entry_time.hour())
                            minute_spin.setValue(self.default_entry_time.minute())
                        elif col == 2:  # Öğle başlangıç
                            hour_spin.setValue(self.default_lunch_start.hour())
                            minute_spin.setValue(self.default_lunch_start.minute())
                        elif col == 3:  # Öğle bitiş
                            hour_spin.setValue(self.default_lunch_end.hour())
                            minute_spin.setValue(self.default_lunch_end.minute())
                        elif col == 4:  # Çıkış
                            hour_spin.setValue(self.default_exit_time.hour())
                            minute_spin.setValue(self.default_exit_time.minute())
                            
                        hour_spin.blockSignals(False)
                        minute_spin.blockSignals(False)
        
        self.total_label.setText("Toplam Çalışma Saati: 0 saat")

    def showContextMenu(self, position):
        """Sağ tıklama menüsünü gösterir"""
        # Sağ tıklanan hücreyi al
        row = self.hours_table.rowAt(position.y())
        
        # Eğer satır geçerli değilse veya ilk sütun (gün adı) dışında sağ tıklama yapıldıysa çık
        if row < 0 or self.hours_table.columnAt(position.x()) != 0:
            return

        # Seçilen günün ID'sini al
        if not self.current_employee_id or not hasattr(self, 'work_hours_data') or row not in self.work_hours_data:
            return
        
        # ID değerini al, eğer yoksa çık
        current_day_id = self.work_hours_data[row].get('id')
        if not current_day_id:
            return
            
        # Günün mevcut aktiflik durumunu kontrol et
        is_active = int(self.work_hours_data[row].get('day_active', 1))
        
        # Menüyü oluştur
        menu = QMenu(self)
        
        # Günün durumuna göre menü seçeneği ekle
        if is_active:
            action = menu.addAction("Günü Pasif Yap")
            action.triggered.connect(lambda: self.toggleDayActive(current_day_id, False))
        else:
            action = menu.addAction("Günü Aktif Yap")
            action.triggered.connect(lambda: self.toggleDayActive(current_day_id, True))
        
        # Menüyü göster
        menu.exec_(self.hours_table.mapToGlobal(position))
        
    def toggleDayActive(self, day_id, active_status):
        """Günün aktif/pasif durumunu değiştirir"""
        # Veritabanını güncelle
        if self.db.update_day_active_status(day_id, active_status):
            # Tabloyu yenile
            self.load_work_hours()

    def refresh_employee_list(self):
        """Çalışan listesini yeniler - Ana pencereden sinyal ile çağrılır"""
        # Mevcut çalışan ID'sini sakla
        current_id = self.current_employee_id
        
        # Çalışan listesini yenile
        self.load_employees()
        
        # Eğer önceki seçili çalışan artık listede değilse, ilk çalışanı seç
        if current_id and self.employee_combo.findData(current_id) == -1:
            if self.employee_combo.count() > 0:
                self.employee_combo.setCurrentIndex(0)
                self.on_employee_selected(0)
            else:
                self.current_employee_id = None
                self.hours_table.clearContents()
                self.total_label.setText("Toplam Çalışma Saati: 0.00 saat")

    def add_work_hours(self):
        """Belirtilen tarih için çalışma saati kaydı oluşturur"""
        if not self.current_employee_id:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir çalışan seçin!")
            return
        
        # Varsayılan çalışma saatleri
        default_entry_time = "08:15"
        default_lunch_start = "13:15"
        default_lunch_end = "13:45"
        default_exit_time = "18:45"
            
        # Hafta içindeki günler için kayıt oluştur
        success = False
        for i, date in enumerate(self.week_dates):
            date_str = date.toString("yyyy-MM-dd")
            
            # Bu tarih için kayıt var mı kontrol et
            if not self.db.has_work_hours(self.current_employee_id, date_str):
                # Yeni kayıt oluştur
                self.db.add_work_hours(
                    self.current_employee_id, 
                    date_str,
                    default_entry_time,
                    default_lunch_start,
                    default_lunch_end,
                    default_exit_time
                )
                success = True
        
        if success:
            QMessageBox.information(self, "Başarılı", "Çalışma saatleri oluşturuldu!")
            self.load_work_hours()
        else:
            QMessageBox.information(self, "Bilgi", "Bu hafta için tüm kayıtlar zaten mevcut.")
