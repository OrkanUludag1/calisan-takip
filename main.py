import sys
import warnings

# PyQt5 uyarılarını gizle
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from models.database import EmployeeDB
from views.employee_form import EmployeeForm
from views.time_tracking_form import TimeTrackingForm

class MainWindow(QMainWindow):
    """Ana pencere sınıfı"""
    
    def __init__(self):
        super().__init__()
        self.db = EmployeeDB()
        self.employee_tabs = {}  # Çalışan sekmeleri için sözlük
        self.initUI()
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        self.setWindowTitle("Çalışan Takip Sistemi")
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon("icon.png"))
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 10px 20px;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #f8f9fa;
                border-bottom-color: #f8f9fa;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #dee2e6;
            }
        """)
        
        # Çalışan formu
        self.employee_form = EmployeeForm(db=self.db)
        self.employee_form.employee_selected.connect(self.on_employee_selected)
        self.tabs.addTab(self.employee_form, "Çalışan Yönetimi")
        
        # Tüm çalışanlar için sekmeleri oluştur
        self.load_employee_tabs()
        
        main_layout.addWidget(self.tabs)
        
        # Genel stil
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f8f9fa;
                color: #212529;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit, QComboBox, QDateEdit, QTimeEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                selection-background-color: #3498db;
            }
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                gridline-color: #dcdcdc;
                selection-background-color: #3498db;
                selection-color: white;
                alternate-background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: 1px solid #dcdcdc;
                border-bottom-width: 2px;
                border-bottom-color: #bdc3c7;
                font-weight: bold;
            }
            QLabel {
                color: #495057;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
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

    def load_employee_tabs(self):
        """Tüm çalışanlar için sekmeleri yükler"""
        # Önce mevcut sekmeleri temizle (ilk sekme hariç)
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)
        
        self.employee_tabs = {}  # Sekme sözlüğünü temizle
        
        # Tüm çalışanları al
        employees = self.db.get_employees()
        
        # Her çalışan için sekme oluştur
        for employee_id, name, _, _, _, is_active in employees:
            # Sadece aktif çalışanlar için sekme oluştur
            if is_active:
                self.create_employee_tab(employee_id, name)
    
    def create_employee_tab(self, employee_id, name):
        """Belirli bir çalışan için sekme oluşturur"""
        # Bu çalışan için zaten bir sekme varsa, tekrar oluşturma
        if employee_id in self.employee_tabs:
            return
        
        # Çalışan için zaman takip formu oluştur
        time_form = TimeTrackingForm(self.db)
        time_form.current_employee_id = employee_id
        
        # Çalışan combobox'ını güncelle
        for i in range(time_form.employee_combo.count()):
            if time_form.employee_combo.itemData(i) == employee_id:
                time_form.employee_combo.setCurrentIndex(i)
                break
        
        # Verileri yükle
        time_form.load_saved_records()
        time_form.calculate_total_hours()
        
        # Sekmeyi ekle
        tab_index = self.tabs.addTab(time_form, f"{name}")
        self.employee_tabs[employee_id] = tab_index
    
    def on_employee_selected(self, employee_id, name):
        """Çalışan seçildiğinde çağrılır"""
        try:
            # Çalışan için sekme oluştur veya varsa o sekmeye geç
            if employee_id in self.employee_tabs:
                # Var olan sekmeye geç
                self.tabs.setCurrentIndex(self.employee_tabs[employee_id])
            else:
                # Yeni sekme oluştur
                self.create_employee_tab(employee_id, name)
                # Yeni sekmeye geç
                self.tabs.setCurrentIndex(self.tabs.count() - 1)
        except Exception as e:
            print(f"Hata: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern görünüm
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
