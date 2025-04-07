from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDialog,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QMenu, QMessageBox,
    QPushButton, QHBoxLayout
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
        """Dialog penceresini hazırlar"""
        self.setWindowTitle("Çalışan Bilgileri")
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        # Form alanları
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.weekly_salary_input = QLineEdit()
        self.daily_food_input = QLineEdit()
        self.daily_transport_input = QLineEdit()
        
        form_layout.addRow("İsim:", self.name_input)
        form_layout.addRow("Haftalık Ücret:", self.weekly_salary_input)
        form_layout.addRow("Günlük Yemek:", self.daily_food_input)
        form_layout.addRow("Günlük Yol:", self.daily_transport_input)
        
        # Eğer çalışan varsa bilgileri doldur
        if self.employee:
            self.name_input.setText(self.employee[1])
            self.weekly_salary_input.setText(str(self.employee[2]))
            self.daily_food_input.setText(str(self.employee[3]))
            self.daily_transport_input.setText(str(self.employee[4]))
        
        # Butonlar
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        cancel_btn = QPushButton("İptal")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        # Layout'ları birleştir
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # Pencere boyutunu ayarla
        self.setFixedWidth(300)
    
    def get_values(self):
        """Form değerlerini döndürür"""
        try:
            return {
                'name': self.name_input.text().strip(),
                'weekly_salary': float(self.weekly_salary_input.text()),
                'daily_food': float(self.daily_food_input.text()),
                'daily_transport': float(self.daily_transport_input.text())
            }
        except ValueError:
            return None

class EmployeeForm(QWidget):
    employee_selected = pyqtSignal(int, str)  # id, name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = EmployeeDB()
        self.current_employee_id = None
        self.initUI()
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        layout = QVBoxLayout(self)
        
        # Çalışan listesi
        self.employee_list = QTableWidget()
        self.employee_list.setColumnCount(4)
        
        # Başlıkları gizle
        self.employee_list.verticalHeader().setVisible(False)
        self.employee_list.horizontalHeader().setVisible(False)
        
        # İlk satırı başlık olarak ayarla
        self.employee_list.insertRow(0)
        headers = ["İsim", "Haftalık Ücret", "Günlük Yemek", "Günlük Yol"]
        
        for col, header in enumerate(headers):
            item = QTableWidgetItem(header)
            item.setBackground(QColor("#34495e"))
            item.setForeground(QBrush(QColor("white")))
            item.setFont(QFont("", -1, QFont.Bold))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable)
            item.setTextAlignment(Qt.AlignCenter)
            self.employee_list.setItem(0, col, item)
        
        # Sütun genişliklerini ayarla
        self.employee_list.setColumnWidth(0, 200)  # İsim sütunu
        for i in range(1, 4):  # Ücret sütunları
            self.employee_list.setColumnWidth(i, 150)
        
        self.employee_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_list.setSelectionMode(QTableWidget.SingleSelection)
        
        # Çift tıklama ile düzenleme
        self.employee_list.doubleClicked.connect(self.edit_employee)
        
        # Sağ tık menüsü için context menu event'i ekle
        self.employee_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.employee_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Layout'ları birleştir
        layout.addWidget(self.employee_list)
        
        # Çalışanları yükle
        self.load_employees()
    
    def show_context_menu(self, position):
        """Sağ tık menüsünü gösterir"""
        # Seçili satırı al
        row = self.employee_list.rowAt(position.y())
        
        # Menüyü oluştur
        menu = QMenu()
        
        # Yeni çalışan ekleme seçeneği
        new_action = menu.addAction("➕ Yeni Çalışan")
        
        # Eğer bir çalışan seçili değilse sadece yeni çalışan seçeneğini göster
        if row < 0 or row == 0:  # Başlık satırı veya boş alan
            action = menu.exec_(self.employee_list.viewport().mapToGlobal(position))
            if action == new_action:
                self.add_employee()
            return
        
        # Seçili çalışanın bilgilerini al
        name_item = self.employee_list.item(row, 0)  # İsim sütunu
        if not name_item:
            return
        
        employee_id = name_item.data(Qt.UserRole)
        is_active = name_item.data(Qt.UserRole + 1)
        if not employee_id:
            return
        
        # Diğer menü öğelerini ekle
        menu.addSeparator()
        status_action = menu.addAction("🔴 Pasif Yap" if is_active else "🟢 Aktif Yap")
        menu.addSeparator()
        edit_action = menu.addAction("✏️ Düzenle")
        delete_action = menu.addAction("🗑️ Sil")
        
        # Menü stilini ayarla
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #bdc3c7;
                margin: 5px 15px;
            }
        """)
        
        # Seçilen işlemi gerçekleştir
        action = menu.exec_(self.employee_list.viewport().mapToGlobal(position))
        
        if action == new_action:
            self.add_employee()
        
        elif action == status_action:
            # Aktif/Pasif durumunu değiştir
            new_status = 0 if is_active else 1
            self.db.update_employee_status(employee_id, new_status)
            self.load_employees()
        
        elif action == edit_action:
            self.edit_employee(employee_id=employee_id)
        
        elif action == delete_action:
            # Silme onayı iste
            reply = QMessageBox.question(
                self, 
                'Çalışanı Sil',
                f'"{name_item.text()}" isimli çalışanı silmek istediğinize emin misiniz?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Çalışanı sil
                self.db.delete_employee(employee_id)
                self.load_employees()
    
    def add_employee(self):
        """Yeni çalışan ekler"""
        dialog = EmployeeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            if values:
                employee_id = self.db.add_employee(
                    values['name'],
                    values['weekly_salary'],
                    values['daily_food'],
                    values['daily_transport']
                )
                
                if employee_id is False:
                    # Aynı isimde çalışan var
                    QMessageBox.warning(
                        self,
                        "Çalışan Eklenemedi",
                        f"\"{values['name']}\" isimli çalışan zaten mevcut. Lütfen farklı bir isim giriniz.",
                        QMessageBox.Ok
                    )
                    return
                
                self.employee_selected.emit(employee_id, values['name'])
                self.load_employees()
    
    def edit_employee(self, item=None, employee_id=None):
        """Çalışan bilgilerini düzenler"""
        if item and item.row() == 0:  # Başlık satırı
            return
            
        if item and not employee_id:
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
                        self.load_employees()
    
    def load_employees(self):
        """Çalışanları tabloya yükler"""
        # Başlık satırını koru, diğerlerini temizle
        while self.employee_list.rowCount() > 1:
            self.employee_list.removeRow(1)
        
        employees = self.db.get_employees()
        
        for employee_id, name, weekly_salary, daily_food, daily_transport, is_active in employees:
            row = self.employee_list.rowCount()
            self.employee_list.insertRow(row)
            
            # İsim hücresine ID'yi ve aktif durumunu gizli veri olarak ekle
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, employee_id)
            name_item.setData(Qt.UserRole + 1, is_active)
            
            # Diğer verileri ekle
            salary_item = QTableWidgetItem(self.format_currency(weekly_salary))
            food_item = QTableWidgetItem(self.format_currency(daily_food))
            transport_item = QTableWidgetItem(self.format_currency(daily_transport))
            
            # Hücreleri tabloya ekle
            self.employee_list.setItem(row, 0, name_item)
            self.employee_list.setItem(row, 1, salary_item)
            self.employee_list.setItem(row, 2, food_item)
            self.employee_list.setItem(row, 3, transport_item)
            
            # Hücreleri ortala ve düzenle
            items = [name_item, salary_item, food_item, transport_item]
            for item in items:
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                # Pasif çalışanları soluk göster
                if not is_active:
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                    item.setForeground(QBrush(QColor("#999999")))

    def format_currency(self, value):
        """Para birimini formatlar"""
        return f"{value:,.2f} ₺".replace(",", ".")
