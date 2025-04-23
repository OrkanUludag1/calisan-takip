from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QApplication, QMenu, QMessageBox
from PyQt5.QtCore import Qt
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import EmployeeDB

class CalisanList(QTableWidget):
    """Çalışanları tablo şeklinde gösteren, sadece isim sütunu ve başlık satırı boş (tam genişlik) widget"""
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels([""])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: #2a5885; color: white; font-weight: bold; font-size: 14px; padding: 6px 0; border: none; }"
        )
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(self.SelectRows)
        self.setEditTriggers(self.NoEditTriggers)
        self.setStyleSheet(
            "QTableWidget { background: white; font-size: 14px; border: none; } "
            "QTableWidget::item { font-size: 14px; height: 34px; } "
            "QTableWidget::item:selected { background: #e0edfa; color: #2a5885; } "
        )
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        self.setMinimumWidth(120)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.load_employees()

    def load_employees(self):
        self.setRowCount(0)
        employees = self.db.get_active_employees()
        sorted_employees = sorted(employees, key=lambda emp: emp[2], reverse=True)
        for employee_id, name, *_ in sorted_employees:
            row = self.rowCount()
            self.insertRow(row)
            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.UserRole, employee_id)
            item_name.setTextAlignment(Qt.AlignCenter)
            item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 0, item_name)
            self.setRowHeight(row, 34)
        self.horizontalHeader().setSectionResizeMode(0, self.horizontalHeader().Stretch)
        if self.rowCount() > 0:
            self.selectRow(0)

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if not item:
            return
        menu = QMenu(self)
        add_bonus_action = menu.addAction("Ek Ödeme Ekle")
        add_deduction_action = menu.addAction("Kesinti Ekle")
        add_permanent_action = menu.addAction("Sabit Ek Ödeme Ekle")
        menu.addSeparator()
        list_payments_action = menu.addAction("Ödemeleri Listele ve Yönet")
        action = menu.exec_(self.viewport().mapToGlobal(position))
        row = item.row()
        employee_id = self.item(row, 0).data(Qt.UserRole)
        employee_name = self.item(row, 0).text()
        if action == add_bonus_action:
            QMessageBox.information(self, "Bilgi", f"Ek ödeme ekle > {employee_name} (id: {employee_id})")
        elif action == add_deduction_action:
            QMessageBox.information(self, "Bilgi", f"Kesinti ekle > {employee_name} (id: {employee_id})")
        elif action == add_permanent_action:
            QMessageBox.information(self, "Bilgi", f"Sabit ek ödeme ekle > {employee_name} (id: {employee_id})")
        elif action == list_payments_action:
            QMessageBox.information(self, "Bilgi", f"Ödemeleri listele ve yönet > {employee_name} (id: {employee_id})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = EmployeeDB()
    w = CalisanList(db)
    w.setWindowTitle("Çalışan Listesi")
    w.resize(220, 400)
    w.show()
    sys.exit(app.exec_())
