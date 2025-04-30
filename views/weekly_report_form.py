from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSizePolicy,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QListWidget,
    QPushButton, QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QColor, QBrush, QFont
from datetime import datetime, timedelta

from models.database import EmployeeDB
from utils.helpers import format_currency, calculate_daily_normal_and_overtime

class WeeklyReportForm(QWidget):
    """Haftalık Rapor sekmesi: Seçili haftaya göre tüm aktif çalışanların hakedişlerini tablo olarak gösterir."""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_week = QDate.currentDate()
        self.fixed_row_height = 40  # Sabit satır yüksekliği
        self._summary_warning_shown = False  # Instance-level flag
        self.initUI()
        self.load_weeks()
        self.load_report()
        # --- Otomatik güncelleme: DB değişince raporu güncelle ---
        self.db.data_changed.connect(self.load_report)
        # Çift tıklama sinyali ekle
        self.table.cellDoubleClicked.connect(self.show_employee_week_details)
        # --- Otomatik güncelleme: Süre sekmesindeki değişikliği dinle ---
        from views.time_tracking_form import TimeTrackingForm
        self.time_tracking_form_ref = None
        try:
            # Eğer ana ekranda TimeTrackingForm örneği varsa sinyale bağlan
            self.time_tracking_form_ref = self.parent().findChild(TimeTrackingForm)
            if self.time_tracking_form_ref:
                self.time_tracking_form_ref.data_changed.connect(self.load_report)
        except Exception:
            pass

    def initUI(self):
        layout = QVBoxLayout(self)
        # Hafta seçimi ve toplam tutar sağda
        controls = QHBoxLayout()
        # Sadece combobox sola dayalı
        self.week_combo = QComboBox()
        self.week_combo.setMinimumWidth(200)
        self.week_combo.currentIndexChanged.connect(self.on_week_changed)
        controls.addWidget(self.week_combo, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        # PDF'ye Aktar butonu
        self.export_pdf_btn = QPushButton("PDF'ye Aktar")
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        controls.addWidget(self.export_pdf_btn, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        # Önizle butonu
        self.preview_btn = QPushButton("Önizle")
        self.preview_btn.clicked.connect(self.preview_summary_boxes)
        controls.addWidget(self.preview_btn, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        # Yazdır butonu
        self.print_preview_to_printer_btn = QPushButton("Yazdır")
        self.print_preview_to_printer_btn.clicked.connect(self.print_preview_to_printer)
        controls.addWidget(self.print_preview_to_printer_btn, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        # Toplam tutar etiketi (sağda büyük font)
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2d3436; padding-left: 30px; padding-right: 6px;")
        controls.addStretch()
        controls.addWidget(self.total_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(controls)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Çalışan", "Haftalık Ücret", "Normal Ç. Saati", "Normal Ç. Ücreti", "Fazla Ç. Saati", "Fazla Ç. Ücreti", "Yemek", "Yol", "Ek Ödemeler", "Kesintiler", "Toplam"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        # Tablo başlık renkleri (lacivert)
        header = self.table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #153866; color: white; font-weight: bold; }")
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_weeks(self):
        self.week_combo.clear()
        # Bugünün dahil olduğu haftanın Pazartesi'sini bul
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        current_week_str = monday.strftime("%Y-%m-%d")
        selected_idx = 0
        if hasattr(self.db, 'get_available_weeks'):
            weeks = self.db.get_available_weeks()
            weeks = sorted(set(weeks), reverse=True)
            for i, w in enumerate(weeks):
                try:
                    start_dt = QDate.fromString(w, "yyyy-MM-dd")
                    end_dt = start_dt.addDays(6)
                    label = f"{start_dt.toString('d MMMM')} - {end_dt.toString('d MMMM yyyy')}"
                    self.week_combo.addItem(label, w)
                except Exception:
                    self.week_combo.addItem(w, w)
                # Eğer bugünün tarihi bu aralıktaysa indexi kaydet
                if start_dt.isValid() and end_dt.isValid():
                    q_today = QDate(today.year, today.month, today.day)
                    if q_today >= start_dt and q_today <= end_dt:
                        selected_idx = i
            self.week_combo.setCurrentIndex(selected_idx)

    def on_week_changed(self, idx):
        self.load_report()

    def load_report(self):
        try:
            self.db.data_changed.disconnect(self.load_report)
        except Exception:
            pass
        if getattr(self, '_is_updating', False):
            return
        self._is_updating = True
        try:
            # Uyarı kutusu tekrarını engellemek için: her çağrı başında flag'i False yap
            self._summary_warning_shown = False
            week_str = self.week_combo.currentData()
            if not week_str:
                return
            # --- ÇALIŞANLARI YÜKLE ---
            # Hem aktif çalışanları hem de o hafta giriş kaydı olan pasif çalışanları dahil et
            active_employees = self.db.get_active_employees()
            employees_with_entry = self.db.get_employees_with_entries_for_week(week_str)
            # ID bazında birleşim (aktifler + o hafta giriş yapan pasifler)
            active_ids = {emp['id'] for emp in active_employees}
            all_employees = active_employees.copy()
            for emp in employees_with_entry:
                if emp['id'] not in active_ids:
                    all_employees.append(emp)
            employee_rows = []
            toplam_odenecek = 0
            for emp in all_employees:
                employee_id = emp['id'] if isinstance(emp, dict) else emp[0]
                employee_name = emp['name'] if isinstance(emp, dict) else emp[1]
                week_records = self.db.get_week_work_hours(employee_id, week_str)
                # Eğer o haftada hiç çalışma kaydı yoksa ek sabit ödemeler de eklenmesin
                if not week_records or all(
                    (not rec.get('entry_time') or not rec.get('exit_time')) or not rec.get('day_active', 1)
                    for rec in week_records
                ):
                    continue
                total_seconds = 0
                normal_seconds = 0
                overtime_seconds = 0
                active_days = 0
                food_count = 0
                for rec in week_records:
                    if rec.get('day_active', 1):
                        giris = rec['entry_time']
                        cikis = rec['exit_time']
                        ogle_bas = rec.get('lunch_start')
                        ogle_bit = rec.get('lunch_end')
                        current_day = rec.get('date')
                        if giris and cikis and ogle_bas and ogle_bit:
                            t1 = QTime.fromString(giris, "HH:mm")
                            t2 = QTime.fromString(ogle_bas, "HH:mm")
                            t3 = QTime.fromString(ogle_bit, "HH:mm")
                            t4 = QTime.fromString(cikis, "HH:mm")
                            qdate = QDate.fromString(current_day, "yyyy-MM-dd") if isinstance(current_day, str) else current_day
                            norm, over = calculate_daily_normal_and_overtime(t1, t2, t3, t4, qdate)
                            normal_seconds += int(norm * 3600)
                            overtime_seconds += int(over * 3600)
                            total_seconds += int((norm + over) * 3600)
                            active_days += 1
                            # YEMEK PARASI HESAPLAMA
                            daily_food = 0
                            if (norm + over) > 5:
                                daily_food += 1
                            if (t4.hour() > 20) or (t4.hour() == 20 and t4.minute() > 0):
                                daily_food += 1
                            food_count += daily_food
                def seconds_to_hhmm(seconds):
                    h = seconds // 3600
                    m = (seconds % 3600) // 60
                    return f"{h:02d}:{m:02d}"
                normal_hours_str = seconds_to_hhmm(normal_seconds)
                overtime_hours_str = seconds_to_hhmm(overtime_seconds)
                total_hours_str = seconds_to_hhmm(total_seconds)
                weekly_salary = emp['weekly_salary'] if isinstance(emp, dict) else emp[2]
                # Saatlik ücreti doğrudan kullan (veritabanında haftalık/50 olarak saklandığı için)
                hourly_rate = emp['weekly_salary']  # Artık bu saatlik ücret
                normal_pay = (normal_seconds / 3600) * hourly_rate
                overtime_pay = (overtime_seconds / 3600) * hourly_rate * 1.5
                weekly_salary_earned = normal_pay + overtime_pay
                food_allowance = food_count * (emp['daily_food'] if isinstance(emp, dict) else emp[3])
                transport_allowance = active_days * (emp['daily_transport'] if isinstance(emp, dict) else emp[4])
                calisma_var = any(rec.get('day_active', 1) and rec.get('entry_time') and rec.get('exit_time') for rec in week_records)
                total_additions = self.db.get_employee_additions(employee_id, week_str, include_permanent_if_no_work=calisma_var)
                payments = self.db.get_weekly_payments(employee_id, week_str)
                total_deductions = 0
                for payment in payments:
                    payment_type_lower = payment[1].lower() if payment[1] else ""
                    if payment_type_lower in ["kesinti", "ceza", "borç", "borc", "avans", "deduction"]:
                        total_deductions += payment[2]
                total_weekly_salary = weekly_salary_earned + food_allowance + transport_allowance + total_additions - total_deductions
                if total_weekly_salary == 0:
                    continue
                employee_rows.append({
                    'name': employee_name,
                    'total_seconds': total_seconds,
                    'total_hours_str': total_hours_str,
                    'normal_hours_str': normal_hours_str,
                    'overtime_hours_str': overtime_hours_str,
                    'normal_pay': normal_pay,
                    'overtime_pay': overtime_pay,
                    'weekly_salary': weekly_salary,
                    'weekly_salary_earned': weekly_salary_earned,
                    'food_allowance': food_allowance,
                    'transport_allowance': transport_allowance,
                    'total_additions': total_additions,
                    'total_deductions': total_deductions,
                    'total_weekly_salary': total_weekly_salary
                })
            # Haftalık ücrete göre azalan sırala
            employee_rows.sort(key=lambda x: x['weekly_salary'] * 50, reverse=True)
            # Haftalık özet formundaki toplamlarla karşılaştırmak için summary verilerini çek
            try:
                from views.weekly_summary_form import WeeklySummaryForm
                summary_form = None
                for widget in self.parent().findChildren(WeeklySummaryForm):
                    summary_form = widget
                    break
                summary_mismatch = False
                if summary_form:
                    summary_table = summary_form.summary_table
                    for row, emp in enumerate(employee_rows):
                        # Summary formunda aynı isimli çalışanı bul
                        found = False
                        for srow in range(summary_table.rowCount()):
                            if summary_table.item(srow, 0) and summary_table.item(srow, 0).text() == emp['name']:
                                summary_total = summary_table.item(srow, 7).text().replace("₺", "").replace(",", ".").strip()
                                try:
                                    summary_total_val = float(summary_total)
                                    if abs(summary_total_val - toplam) > 0.01:
                                        summary_mismatch = True
                                        break
                                except Exception:
                                    pass
                                found = True
                                break
                        if not found:
                            summary_mismatch = True
                            break
                if summary_mismatch:
                    if not self._summary_warning_shown:
                        self._summary_warning_shown = True
                        QMessageBox.warning(self, "Uyarı", "Haftalık özet ile haftalık raporun toplam sütunu uyuşmuyor! Lütfen kontrol edin.")
            except Exception:
                pass

            self.table.setRowCount(0)
            for row, emp in enumerate(employee_rows):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(emp['name']))
                # Haftalık Ücret (sağa yaslı)
                haftalik_ucret_item = QTableWidgetItem(format_currency(emp['weekly_salary'] * 50))
                haftalik_ucret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 1, haftalik_ucret_item)
                # Normal Ç. Saati (ortala)
                normal_saat_item = QTableWidgetItem(emp['normal_hours_str'])
                normal_saat_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, normal_saat_item)
                # Normal Ç. Ücreti (bold)
                normal_ucret_item = QTableWidgetItem(format_currency(emp['normal_pay']))
                normal_ucret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                font_normal = QFont()
                font_normal.setBold(True)
                normal_ucret_item.setFont(font_normal)
                self.table.setItem(row, 3, normal_ucret_item)
                # Fazla Ç. Saati (ortala)
                fazla_saat_item = QTableWidgetItem(emp['overtime_hours_str'])
                fazla_saat_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 4, fazla_saat_item)
                # Fazla Ç. Ücreti (bold)
                fazla_ucret_item = QTableWidgetItem(format_currency(emp['overtime_pay']))
                fazla_ucret_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                font_fazla = QFont()
                font_fazla.setBold(True)
                fazla_ucret_item.setFont(font_fazla)
                self.table.setItem(row, 5, fazla_ucret_item)
                # Yemek (sağa yaslı)
                food_item = QTableWidgetItem(format_currency(emp['food_allowance']))
                food_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 6, food_item)
                # Yol (sağa yaslı)
                transport_item = QTableWidgetItem(format_currency(emp['transport_allowance']))
                transport_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 7, transport_item)
                # Ek Ödemeler (sağa yaslı)
                additions_item = QTableWidgetItem(format_currency(emp['total_additions']))
                additions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 8, additions_item)
                # Kesintiler (sağa yaslı)
                deductions_item = QTableWidgetItem(format_currency(emp['total_deductions']))
                deductions_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 9, deductions_item)
                # Toplam (sağa yaslı, bold)
                total_item = QTableWidgetItem(format_currency(round(emp['total_weekly_salary'] / 10) * 10))
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                font = QFont()
                font.setBold(True)
                font.setPointSize(14)
                total_item.setFont(font)
                self.table.setItem(row, 10, total_item)
                toplam_odenecek += round(emp['total_weekly_salary'] / 10) * 10
            self.total_label.setText(format_currency(toplam_odenecek))
            # Tablo font ve satır yüksekliği Kişiler sekmesi ile aynı olsun
            table_font = QFont("Arial", 12)
            self.table.setFont(table_font)
            for row in range(self.table.rowCount()):
                self.table.setRowHeight(row, 34)
            # Tabloyu ekrana yay ve sütun genişliklerini eşit yap
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
            for i in range(self.table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            # Satır yüksekliğini her zaman sabit tut
            for row in range(self.table.rowCount()):
                self.table.setRowHeight(row, self.fixed_row_height)

            # Toplam tutarı sağda büyük fontla göster (sadece tutar)
        finally:
            self._is_updating = False

    def export_to_pdf(self):
        from PyQt5.QtPrintSupport import QPrinter
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from PyQt5.QtGui import QPainter, QFont, QColor
        from PyQt5.QtCore import Qt
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPageSize(QPrinter.A4)
        file_path, _ = QFileDialog.getSaveFileName(self, "PDF olarak kaydet", "Haftalik_Ozet.pdf", "PDF Dosyası (*.pdf)")
        if not file_path:
            return
        printer.setOutputFileName(file_path)
        painter = QPainter(printer)
        margin = 30
        page_width = printer.pageRect().width() - 2 * margin
        page_height = printer.pageRect().height() - 2 * margin
        x = margin
        y = margin
        col_count = 4
        box_width = int(page_width / col_count) - 8
        box_height = 140
        row_height = box_height + 10
        font_title = QFont("Arial", 8, QFont.Bold)
        font_label = QFont("Arial", 7)
        font_val = QFont("Arial", 8, QFont.Bold)
        font_total = QFont("Arial", 9, QFont.Bold)
        employees = []
        for row in range(self.table.rowCount()):
            emp = {}
            emp['name'] = self.table.item(row, 0).text()
            emp['normal_hour'] = self.table.item(row, 2).text()
            emp['overtime_hour'] = self.table.item(row, 4).text()
            emp['normal_pay'] = self.table.item(row, 3).text()
            emp['overtime_pay'] = self.table.item(row, 5).text()
            emp['food'] = self.table.item(row, 6).text()
            emp['transport'] = self.table.item(row, 7).text()
            emp['addition'] = self.table.item(row, 8).text()
            emp['deduction'] = self.table.item(row, 9).text()
            emp['total'] = self.table.item(row, 10).text()
            employees.append(emp)
        for idx, emp in enumerate(employees):
            col = idx % col_count
            row = idx // col_count
            box_x = x + col * (box_width + 8)
            box_y = y + row * row_height
            if box_y + box_height > page_height + margin:
                printer.newPage()
                box_y = margin
            # Her çalışan için sadece dış kenarlık (gri ve hafif radiuslu)
            painter.setPen(QColor(176, 176, 176))  # gri renk
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(box_x, box_y, box_width, box_height, 10, 10)
            # İsim yukarıda ortada
            painter.setFont(font_title)
            painter.setPen(Qt.black)
            painter.drawText(box_x, box_y + 18, box_width, 14, Qt.AlignCenter, emp['name'])
            # 2 sütunlu veriler
            painter.setFont(font_label)
            y_cursor = box_y + 34
            label_x = box_x + 8
            value_x = box_x + int(box_width / 2) + 2
            row_h = 11
            painter.drawText(label_x, y_cursor, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Normal Saat")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['normal_hour'])
            painter.setFont(font_label)
            painter.drawText(label_x, y_cursor + row_h, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Fazla Saat")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor + row_h, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['overtime_hour'])
            painter.setFont(font_label)
            painter.drawText(label_x, y_cursor + 2*row_h, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Normal Ücret")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor + 2*row_h, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['normal_pay'])
            painter.setFont(font_label)
            painter.drawText(label_x, y_cursor + 3*row_h, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Fazla Ücret")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor + 3*row_h, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['overtime_pay'])
            painter.setFont(font_label)
            painter.drawText(label_x, y_cursor + 4*row_h, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Yemek")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor + 4*row_h, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['food'])
            painter.setFont(font_label)
            painter.drawText(label_x, y_cursor + 5*row_h, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Yol")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor + 5*row_h, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['transport'])
            painter.setFont(font_label)
            painter.drawText(label_x, y_cursor + 6*row_h, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Eklenti")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor + 6*row_h, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['addition'])
            painter.setFont(font_label)
            painter.drawText(label_x, y_cursor + 7*row_h, int(box_width / 2) - 12, row_h, Qt.AlignLeft, "Kesinti")
            painter.setFont(font_val)
            painter.drawText(value_x, y_cursor + 7*row_h, int(box_width / 2) - 12, row_h, Qt.AlignRight, emp['deduction'])
            # Toplam aşağıda ortada
            painter.setFont(font_label)
            painter.drawText(box_x, box_y + box_height - 28, box_width, 12, Qt.AlignCenter, "Toplam")
            painter.setFont(font_total)
            painter.setPen(Qt.black)
            painter.drawText(box_x, box_y + box_height - 14, box_width, 14, Qt.AlignCenter, emp['total'])
        painter.end()
        QMessageBox.information(self, "Başarılı", f"PDF olarak kaydedildi:\n{file_path}")

    def preview_summary_boxes(self):
        from PyQt5.QtWidgets import QDialog, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
        from PyQt5.QtGui import QFont
        from PyQt5.QtCore import Qt
        dialog = QDialog(self)
        dialog.setWindowTitle("Önizleme - Haftalık Özet Kutuları")
        dialog.resize(1200, 900)
        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        col_count = 5
        row_layout = None
        font_title = QFont("Arial", 9, QFont.Bold)
        font_label = QFont("Arial", 8)
        font_val = QFont("Arial", 9, QFont.Bold)
        font_total = QFont("Arial", 10, QFont.Bold)
        employees = []
        for row in range(self.table.rowCount()):
            emp = {}
            emp['name'] = self.table.item(row, 0).text()
            emp['normal_hour'] = self.table.item(row, 2).text()
            emp['overtime_hour'] = self.table.item(row, 4).text()
            emp['normal_pay'] = self.table.item(row, 3).text()
            emp['overtime_pay'] = self.table.item(row, 5).text()
            emp['food'] = self.table.item(row, 6).text()
            emp['transport'] = self.table.item(row, 7).text()
            emp['addition'] = self.table.item(row, 8).text()
            emp['deduction'] = self.table.item(row, 9).text()
            emp['total'] = self.table.item(row, 10).text()
            employees.append(emp)
        for idx, emp in enumerate(employees):
            if idx % col_count == 0:
                row_layout = QHBoxLayout()
                layout.addLayout(row_layout)
            box = QWidget()
            box.setFixedSize(180, 260)
            box.setStyleSheet("background: transparent; border: 2px solid #b0b0b0; border-radius: 10px;")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(8, 2, 8, 2)
            # İsim yukarıda ortada
            title = QLabel(emp['name'])
            title.setFont(font_title)
            title.setStyleSheet("color: #153866; margin-bottom: 4px;")
            title.setAlignment(Qt.AlignCenter)
            box_layout.addWidget(title)
            # 2 sütunlu grid
            grid = QGridLayout()
            grid.setHorizontalSpacing(6)
            grid.setVerticalSpacing(2)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.addWidget(QLabel("Normal Saat", alignment=Qt.AlignLeft), 0, 0)
            grid.addWidget(QLabel(emp['normal_hour'], alignment=Qt.AlignRight), 0, 1)
            grid.addWidget(QLabel("Fazla Saat", alignment=Qt.AlignLeft), 1, 0)
            grid.addWidget(QLabel(emp['overtime_hour'], alignment=Qt.AlignRight), 1, 1)
            grid.addWidget(QLabel("Normal Ücret", alignment=Qt.AlignLeft), 2, 0)
            grid.addWidget(QLabel(emp['normal_pay'], alignment=Qt.AlignRight), 2, 1)
            grid.addWidget(QLabel("Fazla Ücret", alignment=Qt.AlignLeft), 3, 0)
            grid.addWidget(QLabel(emp['overtime_pay'], alignment=Qt.AlignRight), 3, 1)
            grid.addWidget(QLabel("Yemek", alignment=Qt.AlignLeft), 4, 0)
            grid.addWidget(QLabel(emp['food'], alignment=Qt.AlignRight), 4, 1)
            grid.addWidget(QLabel("Yol", alignment=Qt.AlignLeft), 5, 0)
            grid.addWidget(QLabel(emp['transport'], alignment=Qt.AlignRight), 5, 1)
            grid.addWidget(QLabel("Eklenti", alignment=Qt.AlignLeft), 6, 0)
            grid.addWidget(QLabel(emp['addition'], alignment=Qt.AlignRight), 6, 1)
            grid.addWidget(QLabel("Kesinti", alignment=Qt.AlignLeft), 7, 0)
            grid.addWidget(QLabel(emp['deduction'], alignment=Qt.AlignRight), 7, 1)
            # Font ayarları
            for i in range(8):
                grid.itemAtPosition(i, 0).widget().setFont(font_label)
                grid.itemAtPosition(i, 1).widget().setFont(font_val)
                grid.itemAtPosition(i, 1).widget().setStyleSheet("color: #153866;")
            box_layout.addLayout(grid)
            # Toplam aşağıda ortada
            total_lbl = QLabel("Toplam")
            total_lbl.setFont(font_label)
            total_lbl.setAlignment(Qt.AlignCenter)
            total_val = QLabel(emp['total'])
            total_val.setFont(font_total)
            total_val.setStyleSheet("color: #153866; font-weight: bold; margin-bottom: 2px;")
            total_val.setAlignment(Qt.AlignCenter)
            box_layout.addWidget(total_lbl)
            box_layout.addWidget(total_val)
            row_layout.addWidget(box)
        layout.addStretch()
        scroll.setWidget(content)
        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(scroll)
        dialog.setLayout(dlg_layout)
        dialog.exec_()

    def print_preview_to_printer(self):
        from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt5.QtWidgets import QDialog, QScrollArea
        from PyQt5.QtGui import QPainter
        from PyQt5.QtCore import Qt
        # Önizleme widget'ını hazırla
        dialog = QDialog(self)
        dialog.setWindowTitle("Önizleme - Haftalık Özet Kutuları")
        dialog.resize(1200, 900)
        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        col_count = 5
        row_layout = None
        font_title = QFont("Arial", 9, QFont.Bold)
        font_label = QFont("Arial", 8)
        font_val = QFont("Arial", 9, QFont.Bold)
        font_total = QFont("Arial", 10, QFont.Bold)
        employees = []
        for row in range(self.table.rowCount()):
            emp = {}
            emp['name'] = self.table.item(row, 0).text()
            emp['normal_hour'] = self.table.item(row, 2).text()
            emp['overtime_hour'] = self.table.item(row, 4).text()
            emp['normal_pay'] = self.table.item(row, 3).text()
            emp['overtime_pay'] = self.table.item(row, 5).text()
            emp['food'] = self.table.item(row, 6).text()
            emp['transport'] = self.table.item(row, 7).text()
            emp['addition'] = self.table.item(row, 8).text()
            emp['deduction'] = self.table.item(row, 9).text()
            emp['total'] = self.table.item(row, 10).text()
            employees.append(emp)
        for idx, emp in enumerate(employees):
            if idx % col_count == 0:
                row_layout = QHBoxLayout()
                layout.addLayout(row_layout)
            box = QWidget()
            box.setFixedSize(180, 260)
            box.setStyleSheet("background: transparent; border: 2px solid #b0b0b0; border-radius: 10px;")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(8, 2, 8, 2)
            # İsim yukarıda ortada
            title = QLabel(emp['name'])
            title.setFont(font_title)
            title.setStyleSheet("color: #153866; margin-bottom: 4px;")
            title.setAlignment(Qt.AlignCenter)
            box_layout.addWidget(title)
            # 2 sütunlu grid
            grid = QGridLayout()
            grid.setHorizontalSpacing(6)
            grid.setVerticalSpacing(2)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.addWidget(QLabel("Normal Saat", alignment=Qt.AlignLeft), 0, 0)
            grid.addWidget(QLabel(emp['normal_hour'], alignment=Qt.AlignRight), 0, 1)
            grid.addWidget(QLabel("Fazla Saat", alignment=Qt.AlignLeft), 1, 0)
            grid.addWidget(QLabel(emp['overtime_hour'], alignment=Qt.AlignRight), 1, 1)
            grid.addWidget(QLabel("Normal Ücret", alignment=Qt.AlignLeft), 2, 0)
            grid.addWidget(QLabel(emp['normal_pay'], alignment=Qt.AlignRight), 2, 1)
            grid.addWidget(QLabel("Fazla Ücret", alignment=Qt.AlignLeft), 3, 0)
            grid.addWidget(QLabel(emp['overtime_pay'], alignment=Qt.AlignRight), 3, 1)
            grid.addWidget(QLabel("Yemek", alignment=Qt.AlignLeft), 4, 0)
            grid.addWidget(QLabel(emp['food'], alignment=Qt.AlignRight), 4, 1)
            grid.addWidget(QLabel("Yol", alignment=Qt.AlignLeft), 5, 0)
            grid.addWidget(QLabel(emp['transport'], alignment=Qt.AlignRight), 5, 1)
            grid.addWidget(QLabel("Eklenti", alignment=Qt.AlignLeft), 6, 0)
            grid.addWidget(QLabel(emp['addition'], alignment=Qt.AlignRight), 6, 1)
            grid.addWidget(QLabel("Kesinti", alignment=Qt.AlignLeft), 7, 0)
            grid.addWidget(QLabel(emp['deduction'], alignment=Qt.AlignRight), 7, 1)
            # Font ayarları
            for i in range(8):
                grid.itemAtPosition(i, 0).widget().setFont(font_label)
                grid.itemAtPosition(i, 1).widget().setFont(font_val)
                grid.itemAtPosition(i, 1).widget().setStyleSheet("color: #153866;")
            box_layout.addLayout(grid)
            # Toplam aşağıda ortada
            total_lbl = QLabel("Toplam")
            total_lbl.setFont(font_label)
            total_lbl.setAlignment(Qt.AlignCenter)
            total_val = QLabel(emp['total'])
            total_val.setFont(font_total)
            total_val.setStyleSheet("color: #153866; font-weight: bold; margin-bottom: 2px;")
            total_val.setAlignment(Qt.AlignCenter)
            box_layout.addWidget(total_lbl)
            box_layout.addWidget(total_val)
            row_layout.addWidget(box)
        layout.addStretch()
        scroll.setWidget(content)
        dlg_layout = QVBoxLayout(dialog)
        dlg_layout.addWidget(scroll)
        dialog.setLayout(dlg_layout)
        dialog.setWindowFlags(Qt.Widget)
        dialog.show()
        dialog.repaint()
        pixmap = dialog.grab()
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        print_dialog = QPrintDialog(printer, self)
        print_dialog.setWindowTitle("Yazdır")
        if print_dialog.exec_() != QPrintDialog.Accepted:
            dialog.close()
            return
        painter = QPainter(printer)
        page_rect = printer.pageRect()
        scaled = pixmap.scaled(page_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (page_rect.width() - scaled.width()) // 2
        y = (page_rect.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        dialog.close()

    def show_employee_week_details(self, row, column):
        """Bir çalışanın haftalık detaylarını gösteren popup açar."""
        from datetime import datetime
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
        from PyQt5.QtCore import Qt
        def saat_fark(baslangic, bitis):
            if not baslangic or not bitis:
                return 0
            f = '%H:%M'
            dt1 = datetime.strptime(baslangic, f)
            dt2 = datetime.strptime(bitis, f)
            return (dt2 - dt1).total_seconds() / 3600

        employee_name = self.table.item(row, 0).text()
        week_index = self.week_combo.currentIndex()
        week_start = self.week_combo.itemData(week_index)
        # Çalışan adından ID bul
        employee_id = None
        for emp in self.db.get_employees():
            if emp['name'].strip().upper() == employee_name.strip().upper():
                employee_id = emp['id']
                break
        detaylar = []
        # Haftanın tüm günlerini Pazartesi'den Pazar'a sırayla ekle
        try:
            week_start_dt = datetime.strptime(week_start, "%Y-%m-%d")
            gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            # Gün verilerini dict olarak hazırla (tarih → day dict)
            week_data_dict = {}
            if employee_id:
                try:
                    week_data = self.db.get_week_work_hours(employee_id, week_start)
                    for day in week_data:
                        week_data_dict[day.get('date')] = day
                except Exception:
                    week_data_dict = {}
            for i in range(7):
                curr_date = week_start_dt + timedelta(days=i)
                date_str = curr_date.strftime('%Y-%m-%d')
                gun_adi = gunler[i]
                day = week_data_dict.get(date_str)
                if day and (day.get('day_active', 1) == 1 or day.get('is_active', 1) == 1):
                    entry = day.get('entry_time') or ''
                    lunch_start = day.get('lunch_start') or ''
                    lunch_end = day.get('lunch_end') or ''
                    exit = day.get('exit_time') or ''
                    calisma_saat = 0
                    if entry and exit:
                        calisma_saat = saat_fark(entry, exit)
                        if lunch_start and lunch_end:
                            calisma_saat -= saat_fark(lunch_start, lunch_end)
                        calisma_saat = max(calisma_saat, 0)
                        calisma_saat = round(calisma_saat, 2)
                    saat_int = int(calisma_saat)
                    dakika = int(round((calisma_saat - saat_int) * 60))
                    hhmm = f"{saat_int:02d}:{dakika:02d}"
                    detaylar.append((gun_adi, entry, lunch_start, lunch_end, exit, hhmm))
                else:
                    # Pasif gün: sadece gün adı dolu, saatler boş
                    detaylar.append((gun_adi, '', '', '', '', ''))
        except Exception:
            detaylar = []
        # Haftanın başlangıç ve bitiş tarihlerini Türkçe ve uzun formatta hazırla
        try:
            week_start_dt = datetime.strptime(week_start, "%Y-%m-%d")
            week_end_dt = week_start_dt.replace(day=week_start_dt.day + 6)
            week_end_dt = week_start_dt + timedelta(days=6)
            aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            start_str = f"{week_start_dt.day} {aylar[week_start_dt.month-1]}"
            end_str = f"{week_end_dt.day} {aylar[week_end_dt.month-1]} {week_end_dt.year}"
            hafta_str = f"{start_str} - {end_str}"
        except:
            hafta_str = week_start
        # Ayrıntılı tablo popup
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{employee_name}")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        # --- ÜST BİLGİ ALANI ---
        info_row = QWidget()
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)
        font_style = "font-size: 18px; font-weight: bold;"
        hafta_label = QLabel(f"{hafta_str}")
        hafta_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hafta_label.setStyleSheet(font_style)
        info_layout.addWidget(hafta_label, alignment=Qt.AlignLeft)
        # Toplam kutusu için çerçeveli ve flu görünüm
        toplam_frame = QWidget()
        toplam_layout = QVBoxLayout()
        toplam_layout.setContentsMargins(0, 0, 0, 0)
        toplam_layout.setSpacing(2)
        # Haftalık tablodan toplam değeri güvenli şekilde al
        toplam_deger = ""
        try:
            # self.table: ana haftalık tablo
            # row: popup'u açan satır
            if hasattr(self, 'table') and row is not None:
                toplam_item = self.table.item(row, self.table.columnCount()-1)
                if toplam_item:
                    toplam_deger = toplam_item.text()
        except Exception:
            toplam_deger = ""
        toplam_label = QLabel(f"{toplam_deger}")
        toplam_label.setAlignment(Qt.AlignCenter)
        toplam_label.setStyleSheet("font-size: 17px; font-weight: bold; color: #222;")
        toplam_layout.addWidget(toplam_label)
        toplam_frame.setLayout(toplam_layout)
        toplam_frame.setStyleSheet("background: rgba(245,247,250,0.7); border: 1.2px solid #d0d5dd; border-radius: 8px; padding: 6px 16px;")
        info_layout.addWidget(toplam_frame, alignment=Qt.AlignRight)
        info_row.setLayout(info_layout)
        layout.addWidget(info_row)
        # --- TABLO SONRASI ÖZET ALANI ---
        # Sütun başlıklarına göre indeksleri bul
        column_map = {}
        try:
            if hasattr(self, 'table'):
                for i in range(self.table.columnCount()):
                    header = self.table.horizontalHeaderItem(i).text().strip().lower()
                    column_map[header] = i
        except Exception:
            pass
        # İlgili başlıkları bul
        idx_food = column_map.get("yemek", 6)
        idx_transport = column_map.get("yol", 7)
        idx_ek = column_map.get("ek ödemeler", 8)
        idx_kesinti = column_map.get("kesintiler", 9)
        summary_titles = ["Yemek", "Yol", "Eklenti", "Kesinti"]
        summary_values = ["", "", "", ""]
        try:
            if hasattr(self, 'table') and row is not None:
                food = self.table.item(row, idx_food).text() if self.table.item(row, idx_food) else ""
                transport = self.table.item(row, idx_transport).text() if self.table.item(row, idx_transport) else ""
                eklenti = self.table.item(row, idx_ek).text() if self.table.item(row, idx_ek) else ""
                kesinti = self.table.item(row, idx_kesinti).text() if self.table.item(row, idx_kesinti) else ""
                summary_values = [food, transport, eklenti, kesinti]
        except Exception:
            pass
        summary_row = QWidget()
        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(0, 10, 0, 0)
        summary_layout.setSpacing(25)
        for title, val in zip(summary_titles, summary_values):
            # Başlık ve veri için çerçeveli, küçük ve flu kutu
            frame = QWidget()
            frame_layout = QVBoxLayout()
            frame_layout.setContentsMargins(0, 0, 0, 0)
            frame_layout.setSpacing(2)
            lbl_title = QLabel(f"{title}")
            lbl_title.setStyleSheet("font-size: 11px; color: #666;")
            lbl_title.setAlignment(Qt.AlignCenter)
            lbl_val = QLabel(f"{val}")
            lbl_val.setStyleSheet("font-size: 12px; font-weight: bold; color: #222;")
            lbl_val.setAlignment(Qt.AlignCenter)
            frame_layout.addWidget(lbl_title)
            frame_layout.addWidget(lbl_val)
            frame.setLayout(frame_layout)
            # Sadece başlık ve veri için kutuya flu (yarı saydam, soft) çerçeve
            frame.setStyleSheet("background: rgba(245,247,250,0.7); border: 1.2px solid #d0d5dd; border-radius: 8px; padding: 4px 8px;")
            summary_layout.addWidget(frame)
        summary_row.setLayout(summary_layout)
        layout.addWidget(summary_row)
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Tarih", "Giriş", "Öğle Başlangıç", "Öğle Bitiş", "Çıkış", "Toplam Saat"])
        table.setRowCount(len(detaylar))
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)  # Sıra numaralarını gizle
        for i, (date, entry, lunch_start, lunch_end, exit, calisma_saat) in enumerate(detaylar):
            is_pasif = (entry == '' and lunch_start == '' and lunch_end == '' and exit == '' and calisma_saat == '')
            for j, val in enumerate([date, entry, lunch_start, lunch_end, exit, calisma_saat]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if i == 0:
                    table.horizontalHeaderItem(j).setFont(QFont())
                    table.horizontalHeaderItem(j).setFont(QFont())
                if is_pasif:
                    italic_font = QFont()
                    italic_font.setItalic(True)
                    item.setFont(italic_font)
                    item.setForeground(Qt.gray)
                # Toplam Saat sütunu bold olsun
                if j == 5 and not is_pasif:
                    bold_font = QFont()
                    bold_font.setBold(True)
                    item.setFont(bold_font)
                table.setItem(i, j, item)
        if not detaylar:
            table.setRowCount(1)
            item = QTableWidgetItem("Kayıt bulunamadı.")
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, 0, item)
        # Sütun genişlikleri ve tablo genişliği
        column_widths = [100] * 6
        for i, w in enumerate(column_widths):
            table.setColumnWidth(i, w)
        table.setFixedWidth(600)
        # Header ve satır yüksekliği sabit
        header_height = 40
        row_height = 40
        table.horizontalHeader().setFixedHeight(header_height)
        for row in range(table.rowCount()):
            table.setRowHeight(row, row_height)
        table.setFixedHeight(320)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Tabloyu yatayda ortala, dikeyde yukarı yasla
        table_container = QWidget()
        table_container_layout = QHBoxLayout()
        table_container_layout.addStretch()
        table_container_layout.addWidget(table)
        table_container_layout.addStretch()
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container.setLayout(table_container_layout)
        layout.addWidget(table_container, alignment=Qt.AlignTop)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        # Popup genişliği 620 px
        dialog.setFixedSize(620, 500)
        dialog.exec_()
