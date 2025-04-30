import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDialog,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QMenu, QMessageBox,
    QPushButton, QHBoxLayout, QDoubleSpinBox, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont

from models.database import EmployeeDB
from utils.helpers import format_currency

class Kayitlar(QWidget):
    """Kayıtlar (Süre) arayüzü"""
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        if db is None:
            self.db = EmployeeDB()
        else:
            self.db = db
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Kayıtlar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        # Basit örnek tablo (detaylar isteğe göre genişletilebilir)
        self.kayit_list = QTableWidget()
        self.kayit_list.setColumnCount(3)
        self.kayit_list.setHorizontalHeaderLabels(["Tarih", "Tutar", "Açıklama"])
        self.kayit_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.kayit_list.verticalHeader().setVisible(False)
        self.kayit_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.kayit_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.kayit_list.setSelectionMode(QTableWidget.SingleSelection)
        self.kayit_list.setAlternatingRowColors(True)
        self.kayit_list.setStyleSheet("QTableWidget { font-size: 13px; }")
        self.kayit_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.kayit_list)
        # Burada load_kayitlar çağrısı yapılabilir
        self.load_kayitlar()

    def load_kayitlar(self):
        # Örnek: veritabanından kayıtları çekip tabloya ekleyin
        self.kayit_list.setRowCount(0)
        # Gerçek uygulamada db'den kayıtlar alınmalı
        # Örnek veri:
        kayitlar = [
            ("2024-04-23", 500.0, "Yemek avansı"),
            ("2024-04-24", 1200.0, "Yol ücreti")
        ]
        for tarih, tutar, aciklama in kayitlar:
            row = self.kayit_list.rowCount()
            self.kayit_list.insertRow(row)
            tarih_item = QTableWidgetItem(tarih)
            tutar_item = QTableWidgetItem(format_currency(tutar))
            aciklama_item = QTableWidgetItem(aciklama)
            for item in [tarih_item, tutar_item, aciklama_item]:
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.kayit_list.setItem(row, 0, tarih_item)
            self.kayit_list.setItem(row, 1, tutar_item)
            self.kayit_list.setItem(row, 2, aciklama_item)
        self.kayit_list.resizeRowsToContents()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = Kayitlar()
    window.setWindowTitle("Kayıtlar")
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())
