from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDialog,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QMenu, QMessageBox,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QColor, QBrush, QFont
import sqlite3

from models.database import EmployeeDB
from utils.helpers import format_currency

class SelectAllLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mouse_selected = False

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()
        self._mouse_selected = False

    def mouseReleaseEvent(self, event):
        if not self._mouse_selected and self.hasFocus():
            self.selectAll()
            self._mouse_selected = True
        super().mouseReleaseEvent(event)

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
        
        self.name_input = SelectAllLineEdit()
        self.weekly_salary_input = SelectAllLineEdit()
        self.daily_food_input = SelectAllLineEdit()
        self.daily_transport_input = SelectAllLineEdit()
        
        form_layout.addRow("İsim:", self.name_input)
        form_layout.addRow("Haftalık Ücret:", self.weekly_salary_input)
        form_layout.addRow("Günlük Yemek:", self.daily_food_input)
        form_layout.addRow("Günlük Yol:", self.daily_transport_input)
        
        # Eğer çalışan varsa bilgileri doldur
        if self.employee:
            self.name_input.setText(self.employee[1])
            self.weekly_salary_input.setText(format_currency(self.employee[2]))
            self.daily_food_input.setText(format_currency(self.employee[3]))
            self.daily_transport_input.setText(format_currency(self.employee[4]))
        
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
        name = self.name_input.text().strip()
        if not name:
            return None
        # Eski değerleri al
        old_weekly = self.employee[2] if self.employee else 0
        old_food = self.employee[3] if self.employee else 0
        old_transport = self.employee[4] if self.employee else 0
        # Haftalık Ücret
        ws_text = self.weekly_salary_input.text().replace("TL", "").replace(".", "").replace(",", "").strip()
        try:
            weekly_salary = int(ws_text) if ws_text else old_weekly
        except ValueError:
            weekly_salary = old_weekly
        # Günlük Yemek
        food_text = self.daily_food_input.text().replace("TL", "").replace(".", "").replace(",", "").strip()
        try:
            daily_food = int(food_text) if food_text else old_food
        except ValueError:
            daily_food = old_food
        # Günlük Yol
        transport_text = self.daily_transport_input.text().replace("TL", "").replace(".", "").replace(",", "").strip()
        try:
            daily_transport = int(transport_text) if transport_text else old_transport
        except ValueError:
            daily_transport = old_transport
        return {
            'name': name,
            'weekly_salary': weekly_salary,
            'daily_food': daily_food,
            'daily_transport': daily_transport
        }

class EmployeeForm(QWidget):
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
        
        # Çalışan listesi
        self.employee_list = QTableWidget()
        self.employee_list.setColumnCount(4)
        
        # Başlıkları gizle
        self.employee_list.verticalHeader().setVisible(False)
        self.employee_list.horizontalHeader().setVisible(True)
        self.employee_list.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #153866; color: white; font-weight: bold; }")
        
        # İlk satırı başlık olarak ayarla
        self.employee_list.insertRow(0)
        headers = ["İsim", "Haftalık Ücret", "Günlük Yemek", "Günlük Yol"]
        
        for col, header in enumerate(headers):
            item = QTableWidgetItem(header)
            item.setBackground(QColor("#4a86e8"))
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
        
        # Kaydırma çubuklarını kaldır
        self.employee_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.employee_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Başlık gizli olsa da horizontalHeader var, sadece görünmüyor
        # İçeriğe göre genişlik ayarla
        header = self.employee_list.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Dikey başlık gizli olduğu için doğrudan satır yüksekliğini ayarlama
        self.employee_list.resizeRowsToContents()
        
        # Çift tıklama ile düzenleme
        self.employee_list.doubleClicked.connect(self.edit_employee)
        
        # Sağ tık menüsü için context menu event'i ekle
        self.employee_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.employee_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Tabloyu ortalamak için yatay layout oluştur
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(self.employee_list)
        h_layout.addStretch()
        
        # Layout'ları birleştir
        layout.addLayout(h_layout, 1)  # Stretch factor 1 ile esnek yükseklik sağla
        
        # Çalışanları yükle
        self.load_employees()
    
    def show_context_menu(self, position):
        """Sağ tık menüsünü gösterir"""
        # Tıklanan öğeyi al
        item = self.employee_list.itemAt(position)
        
        # Menüyü oluştur
        menu = QMenu(self)
        
        # Geçerli bir öğe yoksa veya başlık satırına tıklandıysa
        if not item or item.row() == 0:
            # Çalışan Ekle seçeneğini göster
            add_action = menu.addAction("Çalışan Ekle")
            add_action.triggered.connect(self.add_employee)
            action = menu.exec_(self.employee_list.mapToGlobal(position))
            return
        
        # Çalışanın ID'sini ve aktif durumunu al
        employee_id = item.data(Qt.UserRole)
        is_active = item.data(Qt.UserRole + 1)
        
        # Diğer menü eylemleri
        edit_action = menu.addAction("Düzenle")
        edit_action.triggered.connect(lambda: self.edit_employee(employee_id=employee_id))
        
        menu.addSeparator()
        
        # Aktif durumuna göre eylem ekle
        activate_action = None
        deactivate_action = None
        
        if is_active:
            deactivate_action = menu.addAction("Pasif Yap")
            deactivate_action.triggered.connect(lambda: self.toggle_employee_active(employee_id, False))
        else:
            activate_action = menu.addAction("Aktif Yap")
            activate_action.triggered.connect(lambda: self.toggle_employee_active(employee_id, True))
        
        # Çalışan Sil seçeneği
        menu.addSeparator()
        delete_action = menu.addAction("Çalışan Sil")
            
        # Menüyü göster
        action = menu.exec_(self.employee_list.mapToGlobal(position))
        
        # Seçilen eyleme göre işlem yap
        if action is not None:
            if deactivate_action is not None and action == deactivate_action:
                # Aktif/Pasif durumunu değiştir
                self.toggle_employee_active(employee_id, False)
            
            elif activate_action is not None and action == activate_action:
                # Aktif/Pasif durumunu değiştir
                self.toggle_employee_active(employee_id, True)
            
            elif action == edit_action:
                self.edit_employee(employee_id=employee_id)
                
            elif action == delete_action:
                # Silme onayı iste
                reply = QMessageBox.question(
                    self, 
                    'Çalışanı Sil',
                    f'"{item.text()}" isimli çalışanı silmek istediğinize emin misiniz?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Çalışanı sil
                    self.db.delete_employee(employee_id)
                    self.employee_deleted.emit()  # Sinyal yayınla
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
                
                self.employee_added.emit()  # Sinyal yayınla
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
                        self.employee_updated.emit()  # Sinyal yayınla
                        self.load_employees()
    
    def toggle_employee_active(self, employee_id, active_status):
        """Çalışanın aktif/pasif durumunu değiştirir"""
        if self.db.toggle_employee_active(employee_id, active_status):
            self.employee_updated.emit()  # Sinyal yayınla
            self.load_employees()
    
    def load_employees(self):
        """Çalışanları tabloya yükler"""
        # Başlık satırını koru, diğerlerini temizle
        while self.employee_list.rowCount() > 1:
            self.employee_list.removeRow(1)
        
        # Veritabanı sınıfını kullanarak çalışanları al
        employees = self.db.get_employees()
        
        for employee_id, name, weekly_salary, daily_food, daily_transport, is_active in employees:
            row = self.employee_list.rowCount()
            self.employee_list.insertRow(row)
            
            # İsim hücresine ID'yi ve aktif durumunu gizli veri olarak ekle
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, employee_id)
            name_item.setData(Qt.UserRole + 1, is_active)
            
            # Saatlik ücreti haftalık ücrete çevir (50 ile çarp)
            weekly_salary_value = weekly_salary * 50
            
            # Diğer verileri ekle
            salary_item = QTableWidgetItem(self.format_currency(weekly_salary_value))
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
                
                # Pasif çalışanları daha belirgin şekilde göster
                if not is_active:
                    font = item.font()
                    font.setItalic(True)
                    font.setStrikeOut(True)  # Üstü çizili göster
                    item.setFont(font)
                    item.setForeground(QBrush(QColor("#FF6B6B")))  # Kırmızımsı renk
        
        # Satır yüksekliklerini içeriğe göre ayarla
        self.employee_list.resizeRowsToContents()
    
    def format_currency(self, value):
        """Para birimini formatlar"""
        return f"{value:,.2f} ₺".replace(",", ".")
