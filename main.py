import sys
import warnings

# PyQt5 uyarılarını gizle
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from models.database import EmployeeDB
from views.employee_form import EmployeeForm
from views.time_select_form import TimeSelectForm
from views.calisanlar import Calisanlar
from views.weekly_report_form import WeeklyReportForm
# from views.rapor import Rapor  # KALDIRILDI

class MainWindow(QMainWindow):
    """Ana pencere sınıfı"""
    
    def __init__(self):
        super().__init__()
        self.db = EmployeeDB()
        
        # Tüm çalışan isimlerini büyük harfe çevir
        self.db.update_all_employee_names_to_uppercase()
        
        self.initUI()
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        self.setWindowTitle("Çalışan Takip Sistemi")
        self.setGeometry(100, 100, 1300, 900)
        self.setWindowIcon(QIcon("icon.png"))
        
        # Pencere boyutunu sabitle
        self.setFixedSize(1300, 900)
        
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
            }
            QTabBar::tab {
                background: #f8f9fa;
                color: #2d3436;
                min-width: 90px;
                min-height: 26px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-family: Arial, Helvetica, sans-serif;
                font-weight: 500;
                padding: 6px 18px;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                transition: background 0.2s, color 0.2s;
                text-align: center;
            }
            QTabBar::tab:selected {
                background: #e3eafc;
                color: #1a237e;
                border-bottom: 2px solid #1a237e;
            }
            QTabBar::tab:hover:!selected {
                background: #e0e7ff;
                color: #1a237e;
            }
        """)

        # Sekmeleri oluştur
        self.calisanlar_widget = Calisanlar(db=self.db)
        self.tabs.addTab(self.calisanlar_widget, "KİŞİLER")
        self.time_select_form = TimeSelectForm(self.db)
        self.tabs.addTab(self.time_select_form, "SÜRE")
        self.weekly_report_form = WeeklyReportForm(self.db)
        self.tabs.addTab(self.weekly_report_form, "ÖZET")
        # Rapor sekmesi kaldırıldı
        # self.rapor = Rapor(self.db)
        # self.tabs.addTab(self.rapor, "Rapor")

        main_layout.addWidget(self.tabs)
        
        # --- SIGNAL CONNECTIONS ARTIK SADECE BURADA ---
        self.db.data_changed.connect(self.time_select_form.load_employees)

        # --- SENKRONİZASYON ---
        # Süre sekmesindeki TimeTrackingForm değiştiğinde haftalık raporu güncelle
        def connect_data_changed():
            try:
                if self.time_select_form.current_time_form:
                    self.time_select_form.current_time_form.data_changed.connect(self.time_select_form.load_employees)
            except Exception:
                pass
        # İlk çalışan yüklendiğinde bağlantıyı kur
        orig_load_employee = getattr(self.time_select_form, 'load_employee', None)
        def load_employee_and_connect(*args, **kwargs):
            result = orig_load_employee(*args, **kwargs)
            connect_data_changed()
            return result
        if orig_load_employee:
            self.time_select_form.load_employee = load_employee_and_connect
        # Eğer ilk açılışta form varsa bağla
        connect_data_changed()

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
                text-align: center;
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
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #bdc3c7;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 1px solid #3498db;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern görünüm
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
