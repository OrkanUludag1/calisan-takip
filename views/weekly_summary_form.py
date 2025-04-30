from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QSizePolicy, QPushButton, QComboBox,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTime, QDate
from PyQt5.QtGui import QColor, QBrush, QFont, QPainter
from PyQt5.QtPrintSupport import QPrinter

from models.database import EmployeeDB
from utils.helpers import format_currency, calculate_daily_normal_and_overtime
from datetime import datetime, timedelta

class WeeklySummaryForm(QWidget):
    """Haftalık özet formu - Tüm aktif çalışanların haftalık özetini gösterir"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_date = datetime.now()
        self.current_week_start = self.get_week_start_date(self.current_date)
        self.employee_data = []  # Çalışan verilerini saklamak için
        
        self.db.data_changed.connect(self.reload_summary)
        
        self.initUI()
        self.load_available_weeks()
        self.load_weekly_data()
        self.load_and_calculate_employees()
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
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
        
        self.main_layout.addLayout(title_layout)
        
        # Hafta seçimi ve butonlar
        controls_layout = QHBoxLayout()
        
        # Hafta seçim kutusu
        controls_layout.addWidget(QLabel("Hafta Seçimi:"))
        self.week_combo = QComboBox()
        self.week_combo.setMinimumWidth(200)
        self.week_combo.currentIndexChanged.connect(self.on_week_changed)
        controls_layout.addWidget(self.week_combo)
        
        controls_layout.addStretch()

        # PDF'ye Aktar butonu
        self.export_pdf_btn = QPushButton("PDF'ye Aktar")
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        controls_layout.addWidget(self.export_pdf_btn)

        self.main_layout.addLayout(controls_layout)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        self.main_layout.addWidget(line)
        
        # Tablo
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(13)
        self.summary_table.setHorizontalHeaderLabels([
            "Çalışan",
            "Haftalık Ücret",
            "Toplam Saat",
            "Normal Saat",
            "Normal Ç. Ücreti",
            "Fazla Ç. Saati",
            "Fazla Ç. Ücreti",
            "Yemek",
            "Yol",
            "Ek Ödemeler",
            "Kesintiler",
            "Toplam",
            "Saatlik Ücret"
        ])
        self.summary_table.setColumnWidth(0, 200)
        self.summary_table.setColumnWidth(1, 150)
        self.summary_table.setColumnWidth(2, 120)
        self.summary_table.setColumnWidth(3, 120)
        self.summary_table.setColumnWidth(4, 120)
        self.summary_table.setColumnWidth(5, 120)
        self.summary_table.setColumnWidth(6, 150)
        self.summary_table.setColumnWidth(7, 120)
        self.summary_table.setColumnWidth(8, 120)
        self.summary_table.setColumnWidth(9, 150)
        self.summary_table.setColumnWidth(10, 150)
        self.summary_table.setColumnWidth(11, 180)
        self.summary_table.setColumnWidth(12, 150)
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.verticalHeader().setVisible(False)
        header = self.summary_table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #4a86e8; color: white; }")
        self.summary_table.verticalHeader().setDefaultSectionSize(40)
        self.summary_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.summary_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_layout.addWidget(self.summary_table)
        
        # Alt kısımda boşluk bırak
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(spacer)
    
    def get_week_start_date(self, date):
        """Verilen tarihin ait olduğu haftanın Pazartesi gününü döndürür (saat bilgisi olmadan)."""
        if isinstance(date, str):
            # Tarih string ise önce datetime nesnesine çevir
            from datetime import datetime as dt
            try:
                date = dt.strptime(date, "%Y-%m-%d")
            except Exception:
                pass
        weekday = date.weekday()
        monday = date - timedelta(days=weekday)
        # Sadece tarih kısmı, saat sıfırlanır
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
        """Veritabanı için tarihi YYYY-MM-DD formatına çevirir ve haftanın Pazartesi'sini döndürür."""
        week_start = self.get_week_start_date(date)
        return week_start.strftime("%Y-%m-%d")
    
    def parse_date_from_db(self, date_str):
        """Veritabanından gelen tarih stringini datetime nesnesine çevirir"""
        return datetime.strptime(date_str, '%Y-%m-%d')
    
    def load_available_weeks(self):
        """Veritabanındaki haftaları combobox'a yükler ve seçim yapar (TimeSelectForm ile uyumlu)"""
        from PyQt5.QtCore import QDate
        current_data = self.week_combo.currentData()
        self.week_combo.blockSignals(True)
        self.week_combo.clear()
        # Haftaları veritabanından çek
        if hasattr(self.db, 'get_available_weeks'):
            weeks = self.db.get_available_weeks()
            # Sadece o haftada aktif çalışanlardan en az birinin çalışma kaydı varsa göster
            filtered_weeks = []
            for w in weeks:
                aktif_var = False
                employees = self.db.get_active_employees()
                for emp in employees:
                    employee_id = emp['id'] if isinstance(emp, dict) else emp[0]
                    week_records = self.db.get_week_work_hours(employee_id, w)
                    if week_records and any([rec.get('day_active', 1) for rec in week_records]):
                        aktif_var = True
                        break
                if aktif_var:
                    filtered_weeks.append(w)
            weeks = filtered_weeks
        else:
            # Eski sistemle uyumluluk için haftalık özetlerden çek
            saved_summaries = self.db.get_available_weekly_summaries()
            weeks = [s['week_start_date'] for s in saved_summaries]
        weeks = sorted(set(weeks), reverse=True)
        for w in weeks:
            try:
                start_dt = QDate.fromString(w, "yyyy-MM-dd")
                end_dt = start_dt.addDays(6)
                label = f"{start_dt.toString('d MMMM')} - {end_dt.toString('d MMMM yyyy')}"
                self.week_combo.addItem(label, w)
            except Exception:
                self.week_combo.addItem(w, w)
        # Önceki seçimi tekrar ayarla
        idx = self.week_combo.findData(current_data) if current_data else 0
        if idx is None or idx < 0:
            idx = 0
        self.week_combo.setCurrentIndex(idx)
        self.week_combo.blockSignals(False)
        # Seçimi güncelle
        self.on_week_changed(self.week_combo.currentIndex())
    
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
        """O haftada veri girişi olan çalışanları yükler ve tabloya ekler (her bir çalışanın haftalık ayrıntılı özeti)"""
        print("[DEBUG] load_and_calculate_employees fonksiyonu çağrıldı")
        try:
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write("[DEBUG] load_and_calculate_employees fonksiyonu çağrıldı\n")
        except Exception:
            pass
        # Hangi haftanın sorgulandığını debug için yazdır
        week_start_str = self.format_date_for_db(self.current_week_start)
        print(f"[DEBUG] Haftalık özet için sorgulanan hafta başlangıcı: {week_start_str}")
        self.employee_data = []
        total_weekly_sum = 0
        self.summary_table.clearContents()
        self.summary_table.setRowCount(0)
        self.summary_table.setColumnCount(13)
        self.summary_table.setHorizontalHeaderLabels([
            "Çalışan",
            "Haftalık Ücret",
            "Toplam Saat",
            "Normal Saat",
            "Normal Ç. Ücreti",
            "Fazla Ç. Saati",
            "Fazla Ç. Ücreti",
            "Yemek",
            "Yol",
            "Ek Ödemeler",
            "Kesintiler",
            "Toplam",
            "Saatlik Ücret"
        ])
        employees = self.db.get_employees_with_entries_for_week(week_start_str)
        print(f"[DEBUG] Haftada veri girişi olan çalışanlar: {employees}")
        row = 0
        def float_to_time_str(hours):
            # Saat:dakika formatı
            h = int(hours)
            m = int(round((hours - h) * 60))
            if m == 60:
                h += 1
                m = 0
            return f"{h:02d}:{m:02d}"
        for emp in employees:
            print(f"[DEBUG] Çalışan: {emp['name']}")
            try:
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"[DEBUG] Çalışan: {emp['name']}\n")
            except Exception:
                pass
            employee_id = emp['id']
            employee_name = emp['name']
            week_records = self.db.get_week_work_hours(employee_id, week_start_str)
            if not week_records:
                continue
            total_hours = 0
            normal_hours = 0
            overtime_hours = 0
            active_days = 0
            food_days = 0
            for rec in week_records:
                if rec.get('day_active', 1):
                    giris = rec['entry_time']
                    cikis = rec['exit_time']
                    ogle_bas = rec.get('lunch_start')
                    ogle_bit = rec.get('lunch_end')
                    current_day = rec.get('date')
                    if giris and cikis and ogle_bas and ogle_bit:
                        try:
                            from PyQt5.QtCore import QTime, QDate
                            t1 = QTime.fromString(giris, "HH:mm")
                            t2 = QTime.fromString(ogle_bas, "HH:mm")
                            t3 = QTime.fromString(ogle_bit, "HH:mm")
                            t4 = QTime.fromString(cikis, "HH:mm")
                            qdate = QDate.fromString(current_day, "yyyy-MM-dd") if isinstance(current_day, str) else current_day
                            from utils.helpers import calculate_daily_normal_and_overtime
                            norm, over = calculate_daily_normal_and_overtime(t1, t2, t3, t4, qdate)
                            # Konsola yazmanın yanında dosyaya da logla
                            try:
                                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                                    f.write(f"[DEBUG] GÜN: {current_day} | GİRİŞ: {giris} | ÇIKIŞ: {cikis} | NORM: {norm} | OVER: {over}\n")
                            except Exception as e:
                                pass
                            print(f"[DEBUG] GÜN: {current_day} | GİRİŞ: {giris} | ÇIKIŞ: {cikis} | NORM: {norm} | OVER: {over}")
                            normal_hours += norm
                            overtime_hours += over
                            total_hours += norm + over
                            active_days += 1
                            if (norm + over) >= 5:
                                food_days += 1
                        except Exception:
                            pass
            weekly_salary_base = emp['weekly_salary']
            hourly_rate = weekly_salary_base / 50
            normal_pay = normal_hours * hourly_rate
            overtime_pay = overtime_hours * hourly_rate * 1.5
            weekly_salary_earned = normal_pay + overtime_pay
            food_allowance = food_days * emp['daily_food']
            transport_allowance = active_days * emp['daily_transport']
            calisma_var = (normal_hours + overtime_hours) > 0
            total_additions = self.db.get_employee_additions(employee_id, week_start_str, include_permanent_if_no_work=calisma_var)
            payments = self.db.get_weekly_payments(employee_id, week_start_str)
            total_deductions = 0
            for payment in payments:
                payment_type_lower = payment[1].lower() if payment[1] else ""
                if payment_type_lower in ["kesinti", "ceza", "borç", "borc", "avans", "deduction"]:
                    total_deductions += payment[2]
            total_weekly_salary = weekly_salary_earned + food_allowance + transport_allowance + total_additions - total_deductions
            self.employee_data.append({
                'id': employee_id,
                'name': employee_name,
                'total_hours': total_hours,
                'normal_hours': normal_hours,
                'overtime_hours': overtime_hours,
                'normal_pay': normal_pay,
                'overtime_pay': overtime_pay,
                'weekly_salary': weekly_salary_earned,
                'food_allowance': food_allowance,
                'transport_allowance': transport_allowance,
                'total_additions': total_additions,
                'total_deductions': total_deductions,
                'total_weekly_salary': total_weekly_salary,
                'weekly_salary_base': weekly_salary_base,
                'hourly_rate': hourly_rate
            })
            self.summary_table.insertRow(row)
            self.summary_table.setItem(row, 0, QTableWidgetItem(employee_name))
            haftalik_ucret_item = QTableWidgetItem(format_currency(weekly_salary_base))
            haftalik_ucret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 1, haftalik_ucret_item)
            toplam_saat_item = QTableWidgetItem(float_to_time_str(total_hours))
            toplam_saat_item.setTextAlignment(Qt.AlignCenter)
            self.summary_table.setItem(row, 2, toplam_saat_item)
            normal_saat_item = QTableWidgetItem(float_to_time_str(normal_hours))
            normal_saat_item.setTextAlignment(Qt.AlignCenter)
            self.summary_table.setItem(row, 3, normal_saat_item)
            normal_ucret_item = QTableWidgetItem(format_currency(normal_pay))
            normal_ucret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 4, normal_ucret_item)
            fazla_saat_item = QTableWidgetItem(float_to_time_str(overtime_hours))
            fazla_saat_item.setTextAlignment(Qt.AlignCenter)
            self.summary_table.setItem(row, 5, fazla_saat_item)
            fazla_ucret_item = QTableWidgetItem(format_currency(overtime_pay))
            fazla_ucret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 6, fazla_ucret_item)
            food_item = QTableWidgetItem(format_currency(food_allowance))
            food_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 7, food_item)
            transport_item = QTableWidgetItem(format_currency(transport_allowance))
            transport_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 8, transport_item)
            additions_item = QTableWidgetItem(format_currency(total_additions))
            additions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 9, additions_item)
            deductions_item = QTableWidgetItem(format_currency(total_deductions))
            deductions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 10, deductions_item)
            rounded_total_weekly_salary = round(total_weekly_salary / 10) * 10
            total_item = QTableWidgetItem(format_currency(rounded_total_weekly_salary))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setBackground(QBrush(QColor("#e8f0fe")))
            total_item.setForeground(QBrush(QColor("#4a86e8")))
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            total_item.setFont(font)
            self.summary_table.setItem(row, 11, total_item)
            saatlik_ucret_item = QTableWidgetItem(format_currency(hourly_rate))
            saatlik_ucret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.summary_table.setItem(row, 12, saatlik_ucret_item)
            total_weekly_sum += rounded_total_weekly_salary
            row += 1
        rounded_total_weekly_sum = round(total_weekly_sum / 10) * 10
        self.total_amount.setText(format_currency(rounded_total_weekly_sum))
        self.adjust_table_size()
        return
    
    def load_weekly_data(self):
        """Haftalık verileri yükler"""
        self.load_and_calculate_employees()
    
    def save_weekly_summary(self):
        """Haftalık özeti veritabanına kaydeder (isteğe bağlı, otomatik kaydetme kaldırıldı)"""
        pass  # Artık özet kaydı tutulmuyor, sadece canlı gösterim var
    
    def load_saved_summary(self, summary):
        """Kaydedilmiş haftalık özeti yükler (artık kullanılmıyor)"""
        pass
    
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

    def reload_summary(self):
        self.load_available_weeks()
        self.load_weekly_data()
        self.load_and_calculate_employees()

    def export_to_pdf(self):
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from PyQt5.QtGui import QPainter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        file_path, _ = QFileDialog.getSaveFileName(self, "PDF olarak kaydet", "Haftalik_Ozet.pdf", "PDF Dosyası (*.pdf)")
        if not file_path:
            return
        printer.setOutputFileName(file_path)
        painter = QPainter(printer)
        # Tabloyu çizdir
        self.summary_table.render(painter)
        painter.end()
        QMessageBox.information(self, "Başarılı", f"PDF olarak kaydedildi:\n{file_path}")
