from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, 
    QVBoxLayout, QWidget, QTabBar
)
from PyQt5.QtCore import Qt, pyqtSignal

import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from models.database import EmployeeDB
from views.employee_form import EmployeeForm
from views.work_hours_form import WorkHoursForm

class MainWindow(QMainWindow):
    """Ana pencere sınıfı"""
    
    # Çalışan listesi değiştiğinde yayınlanacak sinyal
    employee_list_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.db = EmployeeDB()
        self.initUI()
    
    def initUI(self):
        """Ana pencere arayüzünü başlatır"""
        self.setWindowTitle('Çalışan Takip')
        self.setGeometry(100, 100, 1200, 800)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Sekme boyutlarını ayarla
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                top: -1px; /* sekme çizgisini düzelt */
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                min-width: 150px; /* minimum genişlik */
                max-width: 150px; /* maksimum genişlik */
                padding: 10px 5px; /* yatay padding'i azalt */
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #dee2e6;
            }
        """)
        
        # Çalışan yönetimi sekmesi
        self.employee_tab = QWidget()
        employee_layout = QVBoxLayout(self.employee_tab)
        
        # Çalışan formu
        self.employee_form = EmployeeForm(parent=self)
        employee_layout.addWidget(self.employee_form)
        
        # Çalışan formu sinyallerini bağla
        self.employee_form.employee_added.connect(self.on_employee_list_changed)
        self.employee_form.employee_updated.connect(self.on_employee_list_changed)
        self.employee_form.employee_deleted.connect(self.on_employee_list_changed)
        
        # Çalışma saatleri sekmesi
        self.work_hours_tab = QWidget()
        work_hours_layout = QVBoxLayout(self.work_hours_tab)
        
        # Çalışma saatleri formu
        self.work_hours_form = WorkHoursForm(parent=self)
        work_hours_layout.addWidget(self.work_hours_form)
        
        # Çalışan listesi değiştiğinde çalışma saatleri formunu güncelle
        self.employee_list_changed.connect(self.work_hours_form.refresh_employee_list)
        
        # Sekmeleri ekle
        self.tab_widget.addTab(self.employee_tab, "Çalışanlar")
        self.tab_widget.addTab(self.work_hours_tab, "Çalışma Saatleri")
        
        layout.addWidget(self.tab_widget)
        
        # Genel stil
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2472a4;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
    def on_employee_list_changed(self):
        """Çalışan listesi değiştiğinde çağrılır"""
        # Çalışan listesi değişti sinyalini yayınla
        self.employee_list_changed.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern görünüm
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
