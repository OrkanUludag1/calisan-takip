# Rapor sekmesi için başlangıç dosyası

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QComboBox, QHeaderView)
from PyQt5.QtCore import Qt
from datetime import datetime, timedelta

class Rapor(QWidget):
    """Tüm çalışanlar için özet tabloyu gösteren sekme."""
    def __init__(self, db):
        super().__init__()
        self.db = db
        if hasattr(self.db, 'data_changed'):
            try:
                self.db.data_changed.disconnect(self.load_weeks)
            except Exception:
                pass
            self.db.data_changed.connect(self.load_weeks)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel("Hafta Seçiniz:")
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self.load_report)
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Adı", "Normal Çalışma Saati", "Fazla Çalışma Saati", "Normal Çalışma Ücreti", "Fazla Çalışma Ücreti", "Yemek", "Yol", "Eklenti", "Kesinti", "Toplam Ödenecek"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_weeks()

    def load_weeks(self):
        self.combo.blockSignals(True)
        self.combo.clear()
        # Yalnızca gerçekten veri olan haftaları göster
        weeks_with_data = self.db.get_available_weeks()  # work_hours tablosundan benzersiz haftalar
        self.summaries = []
        for week_start in weeks_with_data:
            try:
                start = datetime.strptime(week_start, "%Y-%m-%d")
                end = start + timedelta(days=6)
                label = f"{start.day:02d} {self.month_name(start.month)} - {end.day:02d} {self.month_name(end.month)} {end.year}"
            except Exception:
                label = week_start
            self.combo.addItem(label)
            self.summaries.append({'week_start_date': week_start})
        self.combo.blockSignals(False)
        if self.summaries:
            self.combo.setCurrentIndex(0)
            self.load_report()
        else:
            self.table.setRowCount(0)

    def month_name(self, month):
        months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        return months[month]

    def format_hour(self, hour_val):
        try:
            hour_val = float(hour_val)
        except (ValueError, TypeError):
            return "-"
        hours = int(hour_val)
        minutes = int(round((hour_val - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    def format_money(self, value):
        try:
            val = float(value)
        except (ValueError, TypeError):
            return "-"
        val = int(round(val / 10.0) * 10)  # 10'a yuvarla
        return f"{val:,.0f} TL".replace(",", ".")

    def load_report(self):
        idx = self.combo.currentIndex()
        if not hasattr(self, 'summaries') or idx < 0 or not self.summaries:
            self.table.setRowCount(0)
            return
        week = self.summaries[idx]['week_start_date']
        summary = self.db.get_weekly_summary(week)
        if not summary or not summary.get('details'):
            self.table.setRowCount(0)
            return
        details = summary['details']
        self.table.setRowCount(len(details))
        for row, emp in enumerate(details):
            name = emp['name']
            normal_saat = self.format_hour(emp.get('normal_hours', emp.get('total_hours', 0)))
            fazla_saat = self.format_hour(emp.get('overtime_hours', 0))
            normal_ucret = self.format_money(emp['weekly_salary'])
            fazla_ucret = self.format_money(emp.get('overtime_salary', 0))
            yemek = self.format_money(emp['food_allowance'])
            yol = self.format_money(emp['transport_allowance'])
            eklenti = self.format_money(emp['total_additions'])
            kesinti = self.format_money(emp['total_deductions'])
            toplam = self.format_money(emp['total_weekly_salary'])
            values = [name, normal_saat, fazla_saat, normal_ucret, fazla_ucret, yemek, yol, eklenti, kesinti, toplam]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
