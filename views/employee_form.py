from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from models.database import EmployeeDB
from utils.helpers import format_currency

class EmployeeForm(QWidget):
    """Çalışan yönetimi formu"""
    
    # Çalışan seçildiğinde veya eklendiğinde sinyal gönder
    employee_selected = pyqtSignal(int, str)
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_employee_id = None
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Form alanları - düz layout içinde artık
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Çalışan Adı")
        self.name_edit.setMinimumHeight(30)
        form_layout.addRow("", self.name_edit)
        
        self.weekly_salary_edit = QLineEdit()
        self.weekly_salary_edit.setPlaceholderText("Haftalık Ücret")
        self.weekly_salary_edit.setMinimumHeight(30)
        form_layout.addRow("", self.weekly_salary_edit)
        
        self.daily_food_edit = QLineEdit()
        self.daily_food_edit.setPlaceholderText("Günlük Yemek Ücreti")
        self.daily_food_edit.setMinimumHeight(30)
        form_layout.addRow("", self.daily_food_edit)
        
        self.daily_transport_edit = QLineEdit()
        self.daily_transport_edit.setPlaceholderText("Günlük Yol Ücreti")
        self.daily_transport_edit.setMinimumHeight(30)
        form_layout.addRow("", self.daily_transport_edit)
        
        main_layout.addLayout(form_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 15, 0, 15)
        
        self.add_btn = QPushButton("Ekle")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self.add_employee)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.add_btn)
        
        self.update_btn = QPushButton("Güncelle")
        self.update_btn.setMinimumHeight(40)
        self.update_btn.clicked.connect(self.update_employee)
        self.update_btn.setEnabled(False)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        button_layout.addWidget(self.update_btn)
        
        self.clear_btn = QPushButton("Temizle")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        button_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(button_layout)
        
        # Çalışan listesi - artık doğrudan ekleniyor, grup kutusu içinde değil
        self.employee_list = QTableWidget()
        self.employee_list.setColumnCount(4)
        self.employee_list.setHorizontalHeaderLabels(["İsim", "Haftalık Ücret", "Günlük Yemek", "Günlük Yol"])
        self.employee_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_list.setSelectionMode(QTableWidget.SingleSelection)
        self.employee_list.itemDoubleClicked.connect(self.select_employee)
        self.employee_list.verticalHeader().setVisible(False)  # Satır numaralarını gizle
        self.employee_list.setAlternatingRowColors(True)
        
        # Tüm sütunları eşit genişlikte ayarla
        header = self.employee_list.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        main_layout.addWidget(self.employee_list)
        
        self.setLayout(main_layout)
        
        # Veriyi yükle
        self.load_employees()
    
    def format_currency(self, value):
        """Para birimini formatlar"""
        return format_currency(value)
    
    def add_employee(self):
        """Yeni çalışan ekler"""
        name = self.name_edit.text().strip()
        weekly_salary = self.weekly_salary_edit.text().strip()
        daily_food = self.daily_food_edit.text().strip()
        daily_transport = self.daily_transport_edit.text().strip()
        
        if not name:
            return
        
        try:
            weekly_salary = float(weekly_salary) if weekly_salary else 0
            daily_food = float(daily_food) if daily_food else 0
            daily_transport = float(daily_transport) if daily_transport else 0
            
            employee_id = self.db.add_employee(name, weekly_salary, daily_food, daily_transport)
            self.clear_form()
            self.load_employees()
            
            # Yeni çalışan eklendiğinde sinyal gönder
            self.employee_selected.emit(employee_id, name)
        except ValueError:
            pass
    
    def update_employee(self):
        """Çalışan bilgilerini günceller"""
        if not self.current_employee_id:
            return
        
        name = self.name_edit.text().strip()
        weekly_salary = self.weekly_salary_edit.text().strip()
        daily_food = self.daily_food_edit.text().strip()
        daily_transport = self.daily_transport_edit.text().strip()
        
        if not name:
            return
        
        try:
            weekly_salary = float(weekly_salary) if weekly_salary else 0
            daily_food = float(daily_food) if daily_food else 0
            daily_transport = float(daily_transport) if daily_transport else 0
            
            self.db.update_employee(
                self.current_employee_id, name, weekly_salary, daily_food, daily_transport
            )
            self.clear_form()
            self.load_employees()
        except ValueError:
            pass
    
    def clear_form(self):
        """Form alanlarını temizler"""
        self.name_edit.clear()
        self.weekly_salary_edit.clear()
        self.daily_food_edit.clear()
        self.daily_transport_edit.clear()
        self.current_employee_id = None
        self.update_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
    
    def select_employee(self, item):
        """Tablodan çalışan seçer"""
        row = item.row()
        employee_id = self.employee_list.item(row, 0).data(Qt.UserRole)
        
        employee = self.db.get_employee(employee_id)
        if employee:
            self.current_employee_id = employee_id
            self.name_edit.setText(employee[1])
            self.weekly_salary_edit.setText(str(employee[2]))
            self.daily_food_edit.setText(str(employee[3]))
            self.daily_transport_edit.setText(str(employee[4]))
            self.update_btn.setEnabled(True)
            self.add_btn.setEnabled(False)
            self.employee_selected.emit(employee_id, employee[1])  # Sinyal gönder
    
    def load_employees(self):
        """Çalışanları tabloya yükler"""
        self.employee_list.setRowCount(0)
        
        employees = self.db.get_employees()
        
        for i, employee in enumerate(employees):
            employee_id, name, weekly_salary, daily_food, daily_transport = employee
            
            self.employee_list.insertRow(i)
            
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, employee_id)
            
            # Tüm öğeleri oluştur ve ortala
            items = [
                name_item,
                QTableWidgetItem(self.format_currency(weekly_salary)),
                QTableWidgetItem(self.format_currency(daily_food)),
                QTableWidgetItem(self.format_currency(daily_transport))
            ]
            
            # Tüm öğeleri ekle ve ortala
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)  # Metni ortala
                self.employee_list.setItem(i, col, item)
