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
from views.weekly_summary_form import WeeklySummaryForm
from views.calisanlar import Calisanlar
from views.calisanlist import CalisanList

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
        self.setGeometry(100, 100, 1300, 700)
        self.setWindowIcon(QIcon("icon.png"))
        
        # Pencere boyutunu sabitle
        self.setFixedSize(1300, 700)
        
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
                background-color: #3498db;
                color: white;
                border-bottom-color: #3498db;
            }
            QTabBar::tab:hover:!selected {
                background-color: #dee2e6;
            }
        """)
        
        # Kişiler sekmesi (calisanlar.py)
        self.calisanlar_widget = Calisanlar(db=self.db)
        self.tabs.insertTab(0, self.calisanlar_widget, "KİŞİLER")
        
        # KAYITLAR sekmesi (Kişiler'den hemen sonra)
        kayitlar_tab = QWidget()
        kayitlar_layout = QHBoxLayout(kayitlar_tab)
        kayitlar_layout.setContentsMargins(0, 0, 0, 0)
        kayitlar_layout.setSpacing(0)

        self.calisanlist_widget = CalisanList(db=self.db)
        kayitlar_layout.addWidget(self.calisanlist_widget, 1)

        from PyQt5.QtWidgets import QLabel
        orta_placeholder = QLabel("Orta Alan (Kayıtlar)")
        orta_placeholder.setStyleSheet("background:#f5f5f5; color:#888; font-size:16px; text-align:center;")
        orta_placeholder.setAlignment(Qt.AlignCenter)
        kayitlar_layout.addWidget(orta_placeholder, 3)

        sag_placeholder = QLabel("Sağ Alan (Özet veya Detay)")
        sag_placeholder.setStyleSheet("background:#fafafa; color:#aaa; font-size:16px; text-align:center;")
        sag_placeholder.setAlignment(Qt.AlignCenter)
        kayitlar_layout.addWidget(sag_placeholder, 2)

        self.tabs.insertTab(1, kayitlar_tab, "KAYITLAR")

        # --- Calisanlar sekmesindeki değişiklikler CalisanList'e yansısın ---
        self.calisanlar_widget.employee_updated.connect(self.calisanlist_widget.load_employees)
        self.calisanlar_widget.employee_added.connect(self.calisanlist_widget.load_employees)
        self.calisanlar_widget.employee_deleted.connect(self.calisanlist_widget.load_employees)

        # Süre seçim formu
        self.time_select_form = TimeSelectForm(db=self.db)
        self.tabs.addTab(self.time_select_form, "SÜRE")
        
        # Haftalık özet formu
        self.weekly_summary_form = WeeklySummaryForm(db=self.db)
        self.tabs.addTab(self.weekly_summary_form, "HAFTALIK")
        
        # Zaman takibi formundan gelen sinyali haftalık özet formuna bağla
        # Bu sayede zaman değiştiğinde haftalık özet otomatik olarak güncellenecek
        self.time_select_form.time_tracking_form.time_changed_signal.connect(self.weekly_summary_form.load_active_employees)
        
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
