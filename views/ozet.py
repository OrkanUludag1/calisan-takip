import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QFont
from utils.helpers import format_currency

class OzetForm(QWidget):
    """Çalışana özel haftalık özet formu"""
    def __init__(self, employee_name, summary_data, parent=None):
        super().__init__(parent)
        self.employee_name = employee_name
        self.summary_data = summary_data  # dict veya uygun veri
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Başlık
        title = QLabel(f"{self.employee_name} - Haftalık Özet")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4a86e8;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)

        # Özet Tablosu - Dikey (başlıklar sol sütunda)
        headers = [
            "Toplam Saat", "Haftalık Ücret", "Yemek", "Yol", "Ek Ödemeler", "Kesintiler", "Toplam"
        ]
        table = QTableWidget(len(headers), 1)
        table.setHorizontalHeaderLabels(["Değer"])
        table.setVerticalHeaderLabels(headers)
        # Arka plan rengi ve font için ortak stil
        ortak_renk = "#f8f8f8"
        table.setStyleSheet(f"QTableWidget, QTableView {{ border: none; gridline-color: transparent; }} QHeaderView::section {{ background-color: {ortak_renk}; color: #4a86e8; font-weight: bold; border: none; }}")
        table.verticalHeader().setStyleSheet(f"QHeaderView::section {{ background-color: {ortak_renk}; color: #4a86e8; font-weight: bold; border: none; }}")
        table.horizontalHeader().setStyleSheet(f"QHeaderView::section {{ background-color: {ortak_renk}; color: #4a86e8; border: none; }}")
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(False)
        # Satır yüksekliğini eşitle
        for row in range(table.rowCount()):
            table.setRowHeight(row, 38)
        # Verileri doldur
        if self.summary_data:
            values = [
                str(self.summary_data.get("total_hours", "-")),
                format_currency(self.summary_data.get("weekly_salary", 0)),
                format_currency(self.summary_data.get("meal_allowance", 0)),
                format_currency(self.summary_data.get("transport_allowance", 0)),
                format_currency(self.summary_data.get("total_additions", 0)),
                format_currency(self.summary_data.get("total_deductions", 0)),
                format_currency(self.summary_data.get("total_weekly_salary", 0))
            ]
            for row, value in enumerate(values):
                item = QTableWidgetItem(value)
                if row == len(values) - 1:
                    item.setBackground(QBrush(QColor("#e8f0fe")))
                    item.setForeground(QBrush(QColor("#4a86e8")))
                    font = QFont()
                    font.setBold(True)
                    font.setPointSize(10)
                    item.setFont(font)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 0, item)
        layout.addWidget(table)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    # Örnek veri
    example_summary = {
        "total_hours": 45,
        "weekly_salary": 8000,
        "meal_allowance": 500,
        "transport_allowance": 400,
        "total_additions": 250,
        "total_deductions": 100,
        "total_weekly_salary": 9050
    }
    app = QApplication(sys.argv)
    window = OzetForm("Ali Yılmaz", example_summary)
    window.setWindowTitle("Haftalık Özet - Demo")
    window.resize(900, 220)
    window.show()
    sys.exit(app.exec_())
