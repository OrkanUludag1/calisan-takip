import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDialog,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QMenu, QMessageBox,
    QPushButton, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont

from models.database import EmployeeDB
from utils.helpers import format_currency
from views.employee_form import EmployeeDialog

class Calisanlar(QWidget):
    """Çalışan formu"""
    
    # Sinyaller
    employee_added = pyqtSignal()       # Yeni çalışan eklendiğinde
    employee_updated = pyqtSignal()     # Çalışan güncellendiğinde
    employee_deleted = pyqtSignal()     # Çalışan silindiğinde
    
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        if db is None:
            self.db = EmployeeDB()
        else:
            self.db = db
        self.current_employee_id = None
        self._active_dialogs = []  # Açık dialog referanslarını tutmak için
        self.initUI()
        # --- Otomatik güncelleme: DB değişince tabloyu güncelle ---
        if hasattr(self.db, 'data_changed'):
            try:
                self.db.data_changed.disconnect(self.load_employees)
            except Exception:
                pass
            self.db.data_changed.connect(self.load_employees)
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        # Çalışan listesi
        self.employee_list = QTableWidget()
        self.employee_list.setColumnCount(4)
        self.employee_list.setHorizontalHeaderLabels(["İsim", "Haftalık Ücret", "Günlük Yemek", "Günlük Yol"])
        self.employee_list.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #153866; color: white; font-weight: bold; }")
        self.employee_list.setStyleSheet(
            "QTableWidget { font-size: 14px; } "
            "QTableWidget::item { font-size: 14px; height: 34px; } "
            "QTableWidget::item:selected { background: #DCE6F1; }"
        )
        self.employee_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employee_list.verticalHeader().setVisible(False)
        self.employee_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.employee_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_list.setSelectionMode(QTableWidget.SingleSelection)
        self.employee_list.setAlternatingRowColors(True)
        self.employee_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.employee_list)
        # self.employee_list.doubleClicked.connect(self.edit_employee)  # <-- Bu satırı kaldır veya yoruma al
        # Satır yüksekliğini sabitle
        self.employee_list.verticalHeader().setDefaultSectionSize(34)
        self.employee_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.employee_list.customContextMenuRequested.connect(self.show_context_menu)
        self.load_employees()

    def load_employees(self):
        if getattr(self, '_is_updating', False):
            return
        self._is_updating = True
        try:
            # print("[DEBUG] load_employees çağrıldı")
            """Çalışanları tabloya yükler"""
            self.employee_list.setRowCount(0)  # Tüm satırları temizle
            employees = self.db.get_employees()
            for employee_id, name, weekly_salary, daily_food, daily_transport, is_active in employees:
                row = self.employee_list.rowCount()
                self.employee_list.insertRow(row)
                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.UserRole, employee_id)
                name_item.setData(Qt.UserRole + 1, is_active)
                weekly_salary_value = weekly_salary * 50
                salary_item = QTableWidgetItem(self.format_currency(weekly_salary_value))
                food_item = QTableWidgetItem(self.format_currency(daily_food))
                transport_item = QTableWidgetItem(self.format_currency(daily_transport))
                self.employee_list.setItem(row, 0, name_item)
                self.employee_list.setItem(row, 1, salary_item)
                self.employee_list.setItem(row, 2, food_item)
                self.employee_list.setItem(row, 3, transport_item)
                items = [name_item, salary_item, food_item, transport_item]
                for item in items:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    if not is_active:
                        font = item.font()
                        font.setItalic(True)
                        font.setStrikeOut(True)
                        item.setFont(font)
                        item.setForeground(QBrush(QColor("#FF6B6B")))
        finally:
            self._is_updating = False
        self.employee_list.resizeRowsToContents()

    def format_currency(self, value):
        """Para birimini formatlar: Ondalık yok, binlik nokta, TL"""
        try:
            value = int(round(float(value)))
            return f"{value:,}".replace(",", ".") + " TL"
        except Exception:
            return "0 TL"

    def edit_employee(self, item=None, employee_id=None):
        """Çalışan bilgilerini düzenler"""
        if item and not employee_id:
            row = item.row()
            employee_id = self.employee_list.item(row, 0).data(Qt.UserRole)
        if employee_id:
            employee = self.db.get_employee(employee_id)
            if employee:
                dialog = EmployeeDialog(self, employee)
                # print(f"[DEBUG] Dialog açıldı (edit_employee): {dialog}")
                self._active_dialogs.append(dialog)
                def cleanup():
                    # print(f"[DEBUG] Dialog kapandı (edit_employee): {dialog}")
                    if dialog in self._active_dialogs:
                        self._active_dialogs.remove(dialog)
                dialog.finished.connect(cleanup)
                if dialog.exec_() == QDialog.Accepted:
                    values = dialog.get_values()
                    if values:
                        self.db.update_employee(
                            employee_id,
                            values['name'],
                            values['weekly_salary'],
                            values['daily_food'],
                            values['daily_transport']
                        )
                        self.employee_updated.emit()
                        self.load_employees()

    def add_employee(self):
        """Yeni çalışan ekler"""
        dialog = EmployeeDialog(self)
        # print(f"[DEBUG] Dialog açıldı (add_employee): {dialog}")
        self._active_dialogs.append(dialog)
        def cleanup():
            # print(f"[DEBUG] Dialog kapandı (add_employee): {dialog}")
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
        dialog.finished.connect(cleanup)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            if values:
                employees = self.db.get_employees()
                for emp in employees:
                    if emp[1].strip().lower() == values['name'].strip().lower():
                        QMessageBox.warning(
                            self,
                            "Çalışan Eklenemedi",
                            f"\"{values['name']}\" isimli çalışan zaten mevcut. Lütfen farklı bir isim giriniz.",
                            QMessageBox.Ok
                        )
                        return
                employee_id = self.db.add_employee(
                    values['name'],
                    values['weekly_salary'],
                    values['daily_food'],
                    values['daily_transport']
                )
                self.employee_added.emit()
                self.load_employees()

    def toggle_employee_active(self, employee_id, active_status):
        """Çalışanın aktif/pasif durumunu değiştirir"""
        if self.db.toggle_employee_active(employee_id, active_status):
            self.employee_updated.emit()
            self.load_employees()

    def delete_employee_with_confirm(self, item, employee_id):
        reply = QMessageBox.question(
            self,
            'Çalışanı Sil',
            f'"{item.text()}" isimli çalışanı silmek istediğinize emin misiniz?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_employee(employee_id)
            self.employee_deleted.emit()
            self.load_employees()

    def show_context_menu(self, position):
        """Sağ tık menüsünü gösterir"""
        item = self.employee_list.itemAt(position)
        menu = QMenu(self)
        add_action = menu.addAction("Çalışan Ekle")
        add_action.triggered.connect(self.add_employee)
        if item:
            row = item.row()
            employee_id = self.employee_list.item(row, 0).data(Qt.UserRole)
            is_active = self.employee_list.item(row, 0).data(Qt.UserRole + 1)
            edit_action = menu.addAction("Düzenle")
            edit_action.triggered.connect(lambda: self.edit_employee(item))
            if is_active:
                toggle_action = menu.addAction("Pasif Yap")
                toggle_action.triggered.connect(lambda: self.toggle_employee_active(employee_id, False))
            else:
                toggle_action = menu.addAction("Aktif Yap")
                toggle_action.triggered.connect(lambda: self.toggle_employee_active(employee_id, True))
            menu.addSeparator()
            delete_action = menu.addAction("Çalışan Sil")
            delete_action.triggered.connect(lambda: self.delete_employee_with_confirm(item, employee_id))
        menu.exec_(self.employee_list.mapToGlobal(position))
