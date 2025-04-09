from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QSizePolicy, QPushButton, QComboBox,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QColor, QBrush, QFont

from models.database import EmployeeDB
from utils.helpers import format_currency
from datetime import datetime, timedelta

class WeeklySummaryForm(QWidget):
    """Haftalık özet formu - Tüm aktif çalışanların haftalık özetini gösterir"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_date = datetime.now()
        self.current_week_start = self.get_week_start_date(self.current_date)
        self.employee_data = []  # Çalışan verilerini saklamak için
        
        self.initUI()
        self.load_available_weeks()
        self.load_weekly_data()
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Başlık ve toplam ödenecek kısmı
        title_layout = QHBoxLayout()
        
        # Sol tarafta hafta bilgisi
        self.week_label = QLabel(f"Haftalık Özet: {self.format_week_date_range(self.current_week_start)}")
        self.week_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a86e8;")
        title_layout.addWidget(self.week_label)
        
        title_layout.addStretch()
        
        # Sağ tarafta toplam ödenecek tutar
        self.total_label = QLabel("Toplam Ödenecek: ")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(self.total_label)
        
        self.total_amount = QLabel("0,00 ₺")
        self.total_amount.setStyleSheet("font-size: 20px; font-weight: bold; color: #4a86e8;")
        title_layout.addWidget(self.total_amount)
        
        main_layout.addLayout(title_layout)
        
        # Hafta seçimi ve butonlar
        controls_layout = QHBoxLayout()
        
        # Hafta seçim kutusu
        controls_layout.addWidget(QLabel("Hafta Seçimi:"))
        self.week_combo = QComboBox()
        self.week_combo.setMinimumWidth(200)
        self.week_combo.currentIndexChanged.connect(self.on_week_changed)
        controls_layout.addWidget(self.week_combo)
        
        controls_layout.addStretch()
        
        main_layout.addLayout(controls_layout)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(line)
        
        # Tablo
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(8)
        self.summary_table.setHorizontalHeaderLabels([
            "Çalışan", "Toplam Saat", "Haftalık Ücret", "Yemek", "Yol", 
            "Ek Ödemeler", "Kesintiler", "Toplam"
        ])
        
        # Tablo ayarları
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        
        # Tablo başlık renkleri
        header = self.summary_table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #4a86e8; color: white; }")
        
        # Sütun genişlikleri - daha geniş ayarla
        self.summary_table.setColumnWidth(0, 200)  # Çalışan ismi
        self.summary_table.setColumnWidth(1, 120)  # Toplam saat
        self.summary_table.setColumnWidth(2, 150)  # Haftalık ücret
        self.summary_table.setColumnWidth(3, 120)  # Yemek
        self.summary_table.setColumnWidth(4, 120)  # Yol
        self.summary_table.setColumnWidth(5, 150)  # Ek ödemeler
        self.summary_table.setColumnWidth(6, 150)  # Kesintiler
        self.summary_table.setColumnWidth(7, 180)  # Toplam
        
        # Satır yüksekliği
        self.summary_table.verticalHeader().setDefaultSectionSize(40)  # Satır yüksekliğini artır
        
        # Tablo içeriğinin tam görünmesi için kaydırma çubuklarını kaldır
        self.summary_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.summary_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        main_layout.addWidget(self.summary_table, 1, Qt.AlignCenter)  # Ağırlık faktörünü 1 olarak ayarla
        
        # Alt kısımda boşluk bırak
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(spacer)
    
    def get_week_start_date(self, date):
        """Verilen tarihin haftasının başlangıç tarihini (Pazartesi) döndürür"""
        # Haftanın gününü bul (0: Pazartesi, 6: Pazar)
        weekday = date.weekday()
        
        # Pazartesi gününe git
        monday = date - timedelta(days=weekday)
        
        # Sadece tarih kısmını al (saat bilgisi olmadan)
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def format_week_date_range(self, start_date):
        """Hafta tarih aralığını formatlı olarak döndürür"""
        end_date = start_date + timedelta(days=6)
        
        # Tarih formatı: "1 Ocak - 7 Ocak 2023"
        months_tr = [
            "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
        ]
        
        start_month = months_tr[start_date.month - 1]
        end_month = months_tr[end_date.month - 1]
        
        if start_date.month == end_date.month:
            # Aynı ay içindeyse: "1 - 7 Ocak 2023"
            return f"{start_date.day} - {end_date.day} {start_month} {start_date.year}"
        else:
            # Farklı aylardaysa: "28 Aralık 2022 - 3 Ocak 2023"
            return f"{start_date.day} {start_month} - {end_date.day} {end_month} {start_date.year}"
    
    def format_date_for_db(self, date):
        """Tarihi veritabanı için formatlı olarak döndürür (YYYY-MM-DD)"""
        return date.strftime('%Y-%m-%d')
    
    def parse_date_from_db(self, date_str):
        """Veritabanından gelen tarih stringini datetime nesnesine çevirir"""
        return datetime.strptime(date_str, '%Y-%m-%d')
    
    def load_available_weeks(self):
        """Veritabanında kayıtlı haftalık özetleri yükler"""
        # Mevcut seçimi hatırla
        current_text = self.week_combo.currentText()
        
        # Combobox'ı temizle
        self.week_combo.clear()
        
        # Kaydedilmiş haftalık özetleri al
        saved_summaries = self.db.get_available_weekly_summaries()
        
        # Sadece kaydedilmiş haftaları ekle
        weeks = []
        
        # Kaydedilmiş haftaları ekle
        for summary in saved_summaries:
            week_start = self.parse_date_from_db(summary['week_start_date'])
            week_str = self.format_week_date_range(week_start)
            weeks.append((week_str, week_start))
        
        # Eğer hiç kayıtlı hafta yoksa, mevcut haftayı ekle
        if not weeks:
            current_week = self.get_week_start_date(datetime.now())
            week_str = self.format_week_date_range(current_week)
            weeks.append((week_str, current_week))
        
        # Haftaları tarihe göre sırala (en yeni en üstte)
        weeks.sort(key=lambda x: x[1], reverse=True)
        
        # Combobox'a ekle
        for week_str, week_date in weeks:
            self.week_combo.addItem(week_str, self.format_date_for_db(week_date))
        
        # Eğer önceki seçim varsa, onu tekrar seç
        if current_text:
            index = self.week_combo.findText(current_text)
            if index >= 0:
                self.week_combo.setCurrentIndex(index)
            else:
                self.week_combo.setCurrentIndex(0)  # İlk öğeyi seç
        else:
            self.week_combo.setCurrentIndex(0)  # İlk öğeyi seç
    
    def on_week_changed(self, index):
        """Hafta seçimi değiştiğinde çağrılır"""
        if index < 0:
            return
        
        # Seçilen haftanın başlangıç tarihini al
        selected_week_db_date = self.week_combo.itemData(index)
        self.current_week_start = self.parse_date_from_db(selected_week_db_date)
        
        # Hafta etiketini güncelle
        self.week_label.setText(f"Haftalık Özet: {self.format_week_date_range(self.current_week_start)}")
        
        # Verileri yükle
        self.load_weekly_data()
    
    def load_weekly_data(self):
        """Seçilen hafta için verileri yükler"""
        # Veritabanı formatında hafta başlangıç tarihi
        week_start_db = self.format_date_for_db(self.current_week_start)
        
        # Önce veritabanında kayıtlı özet var mı kontrol et
        saved_summary = self.db.get_weekly_summary(week_start_db)
        
        if saved_summary:
            # Kaydedilmiş özeti yükle
            self.load_saved_summary(saved_summary)
        else:
            # Aktif çalışanları yükle ve hesapla
            self.load_and_calculate_employees()
    
    def load_saved_summary(self, summary):
        """Kaydedilmiş haftalık özeti yükler"""
        # Tabloyu temizle
        self.summary_table.setRowCount(0)
        
        # Çalışan verilerini temizle
        self.employee_data = []
        
        # Toplam tutarı güncelle
        self.total_amount.setText(format_currency(summary['total_amount']))
        
        # Çalışan detaylarını tabloya ekle
        for employee in summary['details']:
            # Çalışan verilerini sakla
            self.employee_data.append(employee)
            
            # Tabloya ekle
            row = self.summary_table.rowCount()
            self.summary_table.insertRow(row)
            
            # Çalışan adı
            self.summary_table.setItem(row, 0, QTableWidgetItem(employee['name']))
            
            # Toplam saat
            hours_item = QTableWidgetItem(f"{employee['total_hours']:.1f} saat")
            hours_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 1, hours_item)
            
            # Haftalık ücret
            salary_item = QTableWidgetItem(format_currency(employee['weekly_salary']))
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 2, salary_item)
            
            # Yemek
            food_item = QTableWidgetItem(format_currency(employee['food_allowance']))
            food_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 3, food_item)
            
            # Yol
            transport_item = QTableWidgetItem(format_currency(employee['transport_allowance']))
            transport_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 4, transport_item)
            
            # Ek ödemeler
            additions_item = QTableWidgetItem(format_currency(employee['total_additions']))
            additions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 5, additions_item)
            
            # Kesintiler
            deductions_item = QTableWidgetItem(format_currency(employee['total_deductions']))
            deductions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 6, deductions_item)
            
            # Toplam
            total_item = QTableWidgetItem(format_currency(employee['total_weekly_salary']))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Toplam sütununu vurgula
            total_item.setBackground(QBrush(QColor("#e8f0fe")))
            total_item.setForeground(QBrush(QColor("#4a86e8")))
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)  # Yazı tipi boyutunu artır
            total_item.setFont(font)
            self.summary_table.setItem(row, 7, total_item)
        
        # Tablo boyutunu ayarla
        self.adjust_table_size()
    
    def load_active_employees(self):
        """Aktif çalışanları yükler"""
        active_employees = []
        employees = self.db.get_employees()
        
        for emp in employees:
            if emp['is_active']:
                active_employees.append({
                    'id': emp['id'],
                    'name': emp['name']
                })
        
        return active_employees
        
    def load_and_calculate_employees(self):
        """Aktif çalışanları yükler ve tabloya ekler"""
        # Aktif çalışanları getir
        employees = self.db.get_employees()
        
        # Çalışanları ve haftalık ücretlerini tutacak liste
        self.employee_data = []
        
        # Toplam değer
        total_weekly_sum = 0
        
        # Tablo satır sayısını sıfırla
        self.summary_table.setRowCount(0)
        
        # Her çalışan için haftalık verileri hesapla
        for emp in employees:
            if not emp['is_active']:
                continue
                
            employee_id = emp['id']
            employee_name = emp['name']
            # Saatlik ücret (veritabanında saklanan değer)
            hourly_rate = emp['weekly_salary']
            
            # Haftalık çalışma saatlerini al - string formatında tarih gönder
            week_start_db = self.format_date_for_db(self.current_week_start)
            work_hours = self.db.get_week_work_hours(employee_id, week_start_db)
            
            # Toplam çalışma saati
            total_hours = 0
            active_days = 0
            
            # Her gün için çalışma saatlerini hesapla
            for day_data in work_hours:
                # Gün aktif mi kontrol et
                if not day_data['day_active']:
                    continue
                
                # Aktif gün sayısını artır
                active_days += 1
                
                # Zaman değerlerini al
                entry_time = day_data['entry_time']
                lunch_start = day_data['lunch_start']
                lunch_end = day_data['lunch_end']
                exit_time = day_data['exit_time']
                
                # Zaman değerleri boş olabilir, kontrol et
                if not entry_time or not lunch_start or not lunch_end or not exit_time:
                    continue
                
                # String formatındaki saatleri datetime.time nesnesine çevir
                try:
                    entry_time = datetime.strptime(entry_time, "%H:%M").time()
                    lunch_start = datetime.strptime(lunch_start, "%H:%M").time()
                    lunch_end = datetime.strptime(lunch_end, "%H:%M").time()
                    exit_time = datetime.strptime(exit_time, "%H:%M").time()
                except ValueError:
                    continue
                
                # Sabah çalışma saatleri (saat cinsinden)
                morning_hours = 0
                if entry_time <= lunch_start:  # Normal durum
                    morning_seconds = (lunch_start.hour * 3600 + lunch_start.minute * 60) - (entry_time.hour * 3600 + entry_time.minute * 60)
                    morning_hours = morning_seconds / 3600.0
                
                # Öğleden sonra çalışma saatleri (saat cinsinden)
                afternoon_hours = 0
                if lunch_end <= exit_time:  # Normal durum
                    afternoon_seconds = (exit_time.hour * 3600 + exit_time.minute * 60) - (lunch_end.hour * 3600 + lunch_end.minute * 60)
                    afternoon_hours = afternoon_seconds / 3600.0
                
                # Toplam çalışma saatleri (saat cinsinden)
                day_hours = morning_hours + afternoon_hours
                
                # Negatif değerleri düzelt (zaman çakışmaları veya hatalı giriş)
                if day_hours < 0:
                    day_hours = 0
                
                # Toplam saatlere ekle
                total_hours += day_hours
            
            # Toplam saati saat ve dakika olarak ayır
            total_hours_int = int(total_hours)  # Tam saat kısmı
            total_minutes = int((total_hours - total_hours_int) * 60)  # Dakika kısmı
            
            # Haftalık kazanç = toplam çalışma saati * saatlik ücret
            weekly_salary_earned = total_hours * hourly_rate
            
            # Yol ve yemek ödemeleri (aktif gün sayısına göre)
            food_allowance = active_days * emp['daily_food']  # Günlük yemek ücreti
            transport_allowance = active_days * emp['daily_transport']  # Günlük yol ücreti
            
            # Ek ödemeler ve kesintileri al
            payments = self.db.get_weekly_payments(employee_id, week_start_db)
            
            # Ek ödemeler ve kesintileri hesapla
            total_additions = 0
            total_deductions = 0
            
            for payment_id, payment_type, amount, description, is_permanent in payments:
                # Ödeme tipini küçük harfe çevir
                payment_type_lower = payment_type.lower() if payment_type else ""
                
                # Eklenti olarak kabul edilen tipler
                if payment_type_lower in ["eklenti", "bonus", "prim", "ek ödeme", "ek odeme", "ikramiye"]:
                    total_additions += amount
                # Kesinti olarak kabul edilen tipler
                elif payment_type_lower in ["kesinti", "ceza", "borç", "borc", "avans", "deduction"]:
                    total_deductions += amount
            
            # Toplam haftalık ücret
            total_weekly_salary = weekly_salary_earned + food_allowance + transport_allowance + total_additions - total_deductions
            
            # Toplama ekle
            total_weekly_sum += total_weekly_salary
            
            # Çalışan verilerini listeye ekle
            self.employee_data.append({
                'id': employee_id,
                'name': employee_name,
                'total_hours': total_hours,
                'total_hours_formatted': f"{total_hours_int}:{total_minutes:02d}",
                'weekly_salary': weekly_salary_earned,  
                'food_allowance': food_allowance,
                'transport_allowance': transport_allowance,
                'total_additions': total_additions,
                'total_deductions': total_deductions,
                'total_weekly_salary': total_weekly_salary
            })
        
        # Çalışanları haftalık ücretlerine göre azalan sırada sırala
        self.employee_data.sort(key=lambda x: x['total_weekly_salary'], reverse=True)
        
        # Tabloya ekle
        self.summary_table.setRowCount(len(self.employee_data))
        
        # Her çalışan için satır ekle
        for row, employee in enumerate(self.employee_data):
            # Çalışan ismi
            name_item = QTableWidgetItem(employee['name'])
            self.summary_table.setItem(row, 0, name_item)
            
            # Toplam saat
            hours_item = QTableWidgetItem(employee['total_hours_formatted'])
            hours_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 1, hours_item)
            
            # Haftalık ücret
            salary_item = QTableWidgetItem(format_currency(employee['weekly_salary']))
            salary_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 2, salary_item)
            
            # Yemek
            food_item = QTableWidgetItem(format_currency(employee['food_allowance']))
            food_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 3, food_item)
            
            # Yol
            transport_item = QTableWidgetItem(format_currency(employee['transport_allowance']))
            transport_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 4, transport_item)
            
            # Ek ödemeler
            additions_item = QTableWidgetItem(format_currency(employee['total_additions']))
            additions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 5, additions_item)
            
            # Kesintiler
            deductions_item = QTableWidgetItem(format_currency(employee['total_deductions']))
            deductions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 6, deductions_item)
            
            # Toplam
            total_item = QTableWidgetItem(format_currency(employee['total_weekly_salary']))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Toplam sütununu vurgula
            total_item.setBackground(QBrush(QColor("#e8f0fe")))
            total_item.setForeground(QBrush(QColor("#4a86e8")))
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)  # Yazı tipi boyutunu artır
            total_item.setFont(font)
            self.summary_table.setItem(row, 7, total_item)
        
        # Toplam etiketi güncelle
        self.total_amount.setText(format_currency(total_weekly_sum))
        
        # Tablo boyutunu ayarla
        self.adjust_table_size()
        self.save_weekly_summary()  # Otomatik kaydetme
    
    def save_weekly_summary(self):
        """Haftalık özeti veritabanına kaydeder"""
        if not self.employee_data:
            return
        
        # Toplam tutarı hesapla
        total_amount = sum(employee['total_weekly_salary'] for employee in self.employee_data)
        
        # Veritabanı formatında hafta başlangıç tarihi
        week_start_db = self.format_date_for_db(self.current_week_start)
        
        # Veritabanına kaydet
        summary_id = self.db.save_weekly_summary(week_start_db, total_amount, self.employee_data)
        
        # Hafta listesini güncelle
        if summary_id:
            self.load_available_weeks()
    
    def adjust_table_size(self):
        """Tablo boyutunu içeriğe göre ayarla"""
        # Satır sayısını al
        row_count = self.summary_table.rowCount()
        
        # Satır sayısına göre tablo yüksekliğini ayarla (her satır 40 piksel)
        # En az 8 satır göster, daha azsa bile 8 satırlık yer ayır
        min_rows = 8
        rows_to_show = max(row_count, min_rows)
        
        # Başlık yüksekliği için ekstra piksel ekle
        header_height = 30
        
        # Toplam yükseklik: (satır sayısı * satır yüksekliği) + başlık yüksekliği
        table_height = (rows_to_show * 40) + header_height
        
        # Tablo genişliği - tüm sütunların toplam genişliği
        total_width = 0
        for i in range(self.summary_table.columnCount()):
            total_width += self.summary_table.columnWidth(i)
        
        # Kenarlıklar için ekstra piksel ekle
        border_padding = 5
        table_width = total_width + border_padding
        
        # Sabit boyut sınırlamasını kaldır, minimum boyut ayarla
        self.summary_table.setMinimumSize(table_width, table_height)
        
        # Sütunların içeriğe göre genişlemesini sağla
        header = self.summary_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Son sütunu genişletebilir yap
        header.setStretchLastSection(True)
        
        # Tüm hücrelerin içeriğinin tam görünmesini sağla
        for row in range(self.summary_table.rowCount()):
            self.summary_table.setRowHeight(row, 40)  # Sabit satır yüksekliği
