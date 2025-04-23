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

class EmployeeDialog(QDialog):
    """Çalışan bilgilerini düzenlemek için dialog penceresi"""
    def __init__(self, parent=None, employee=None):
        super().__init__(parent)
        self.employee = employee
        self.initUI()
    def initUI(self):
        self.setWindowTitle("Çalışan Bilgileri")
        self.setModal(True)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.weekly_salary_input = QLineEdit()
        self.daily_food_input = QLineEdit()
        self.daily_transport_input = QLineEdit()
        form_layout.addRow("İsim:", self.name_input)
        form_layout.addRow("Haftalık Ücret:", self.weekly_salary_input)
        form_layout.addRow("Günlük Yemek:", self.daily_food_input)
        form_layout.addRow("Günlük Yol:", self.daily_transport_input)
        if self.employee:
            self.name_input.setText(self.employee[1])
            self.weekly_salary_input.setText(str(self.employee[2]))
            self.daily_food_input.setText(str(self.employee[3]))
            self.daily_transport_input.setText(str(self.employee[4]))
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        cancel_btn = QPushButton("İptal")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        self.setFixedWidth(300)
    def get_values(self):
        name = self.name_input.text().strip()
        if not name:
            return None
        try:
            weekly_salary = float(self.weekly_salary_input.text()) if self.weekly_salary_input.text().strip() else 0
        except ValueError:
            weekly_salary = 0
        try:
            daily_food = float(self.daily_food_input.text()) if self.daily_food_input.text().strip() else 0
        except ValueError:
            daily_food = 0
        try:
            daily_transport = float(self.daily_transport_input.text()) if self.daily_transport_input.text().strip() else 0
        except ValueError:
            daily_transport = 0
        return {
            'name': name,
            'weekly_salary': weekly_salary,
            'daily_food': daily_food,
            'daily_transport': daily_transport
        }

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
        self.initUI()
    
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
        self.employee_list.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #2a5885; color: white; font-weight: bold; font-size: 14px; padding: 6px 0; border: none; }")
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
        self.employee_list.doubleClicked.connect(self.edit_employee)
        # Satır yüksekliğini sabitle
        self.employee_list.verticalHeader().setDefaultSectionSize(34)
        self.employee_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.employee_list.customContextMenuRequested.connect(self.show_context_menu)
        self.load_employees()

    def load_employees(self):
        """Çalışanları tabloya yükler"""
        self.employee_list.setRowCount(0)  # Tüm satırları temizle
        employees = self.db.get_employees()
        for employee_id, name, weekly_salary, daily_food, daily_transport, is_active in employees:
            row = self.employee_list.rowCount()
            self.employee_list.insertRow(row)
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, employee_id)
            name_item.setData(Qt.UserRole + 1, is_active)
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            if not is_active:
                font = name_item.font()
                font.setItalic(True)
                name_item.setFont(font)
                name_item.setForeground(QBrush(QColor("#b0b0b0")))
                # Sadece isim göster, diğer hücreleri boş ve disable yap
                for col in range(1, 4):
                    empty_item = QTableWidgetItem("")
                    empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEnabled)
                    self.employee_list.setItem(row, col, empty_item)
            else:
                # Aktif çalışanlar için tüm verileri göster
                salary_item = QTableWidgetItem(format_currency(weekly_salary * 50))
                food_item = QTableWidgetItem(format_currency(daily_food))
                transport_item = QTableWidgetItem(format_currency(daily_transport))
                for item in [salary_item, food_item, transport_item]:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.employee_list.setItem(row, 1, salary_item)
                self.employee_list.setItem(row, 2, food_item)
                self.employee_list.setItem(row, 3, transport_item)
            self.employee_list.setItem(row, 0, name_item)
        self.employee_list.resizeRowsToContents()

    def format_currency(self, value):
        """Para birimini formatlar"""
        return f"{value:,.2f} ₺".replace(",", ".")

    def edit_employee(self, item=None, employee_id=None):
        """Çalışan bilgilerini düzenler"""
        if item and item.row() == 0:  # Başlık satırı
            return
        if not employee_id and item:
            row = item.row()
            employee_id = self.employee_list.item(row, 0).data(Qt.UserRole)
        if employee_id:
            employee = self.db.get_employee(employee_id)
            if employee:
                dialog = EmployeeDialog(self, employee)
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
        if item and item.row() > -1:  # Sadece gerçek çalışan satırlarında
            row = item.row()
            employee_id = self.employee_list.item(row, 0).data(Qt.UserRole)
            is_active = self.employee_list.item(row, 0).data(Qt.UserRole + 1)
            edit_action = menu.addAction("Düzenle")
            edit_action.triggered.connect(lambda: self.edit_employee(employee_id=employee_id))
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

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = Calisanlar()
    window.setWindowTitle("Çalışanlar")
    window.resize(700, 500)
    window.show()
    sys.exit(app.exec_())
