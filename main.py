import sys
import warnings

# PyQt5 uyarılarını gizle
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from models.database import EmployeeDB
from views.employee_form import EmployeeForm
from views.time_select_form import TimeSelectForm
from views.weekly_summary_form import WeeklySummaryForm
from views.calisanlar import Calisanlar
from views.calisanlist import CalisanList
from views.zamantakip import ZamanTakipForm

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

        # Orta alan üstüne çalışan adı için QLabel
        self.selected_employee_label = QLabel()
        self.selected_employee_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2a5885; padding: 8px 0 16px 0;")
        self.selected_employee_label.setAlignment(Qt.AlignCenter)
        self.selected_employee_label.setText("")

        # Orta layout için dikey bir layout oluştur
        self.orta_layout = QVBoxLayout()
        self.orta_layout.setContentsMargins(0, 0, 0, 0)
        self.orta_layout.setSpacing(0)
        self.orta_layout.addWidget(self.selected_employee_label)
        # Haftalar için ComboBox ekle
        self.week_combo = QComboBox()
        self.week_combo.setStyleSheet("font-size: 18px; padding: 6px 10px;")
        self.orta_layout.addWidget(self.week_combo)
        from views.zaman import ZamanTakipForm
        self.zaman_takip_form = ZamanTakipForm(self.db)
        self.orta_layout.addWidget(self.zaman_takip_form)
        self.populate_weeks()

        # QWidget ile orta alanı sarmala
        self.orta_widget = QWidget()
        self.orta_widget.setLayout(self.orta_layout)
        kayitlar_layout.addWidget(self.calisanlist_widget, 1)
        kayitlar_layout.addWidget(self.orta_widget, 3)

        sag_placeholder = QLabel("Sağ Alan (Özet veya Detay)")
        sag_placeholder.setStyleSheet("background:#fafafa; color:#aaa; font-size:16px; text-align:center;")
        sag_placeholder.setAlignment(Qt.AlignCenter)
        kayitlar_layout.addWidget(sag_placeholder, 2)

        self.tabs.insertTab(1, kayitlar_tab, "KAYITLAR")

        # --- Calisanlar sekmesindeki değişiklikler CalisanList'e yansısın ---
        self.calisanlar_widget.employee_updated.connect(self.calisanlist_widget.load_employees)
        self.calisanlar_widget.employee_added.connect(self.calisanlist_widget.load_employees)
        self.calisanlar_widget.employee_deleted.connect(self.calisanlist_widget.load_employees)

        # Çalışan seçilince label ve zaman takip güncellensin
        self.calisanlist_widget.employee_selected.connect(self.update_selected_employee)
        # İlk çalışanı seçili göster
        self.init_selected_employee()

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

    def init_selected_employee(self):
        # İlk çalışanı otomatik seç ve label+formu ayarla
        if self.calisanlist_widget.rowCount() > 0:
            item = self.calisanlist_widget.item(0, 0)
            if item:
                employee_id = item.data(Qt.UserRole)
                employee_name = item.text()
                self.update_selected_employee(employee_id, employee_name)

    def update_selected_employee(self, employee_id, employee_name):
        self.selected_employee_label.setText(employee_name)
        # self.zaman_takip_form.set_employee(employee_id, employee_name)

    def populate_weeks(self):
        from datetime import datetime, timedelta
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'tr_TR.UTF-8')
        except:
            pass
        # Veritabanından çalışılmış haftaları bul
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT DISTINCT date FROM work_hours ORDER BY date")
        dates = [row[0] for row in cursor.fetchall()]
        week_starts = set()
        for d in dates:
            dt = datetime.strptime(d, "%Y-%m-%d")
            monday = dt - timedelta(days=dt.weekday())
            week_starts.add(monday.date())
        week_starts = sorted(list(week_starts))
        self.week_combo.clear()
        for ws in week_starts:
            week_end = ws + timedelta(days=6)
            # Türkçe tarih aralığı formatı
            start_str = ws.strftime("%d %B")
            end_str = week_end.strftime("%d %B %Y")
            label = f"{start_str} - {end_str}"
            self.week_combo.addItem(label, ws.strftime("%Y-%m-%d"))
        # Eğer hiç veri yoksa bugünkü haftayı ekle
        if not week_starts:
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            week_end = monday + timedelta(days=6)
            start_str = monday.strftime("%d %B")
            end_str = week_end.strftime("%d %B %Y")
            label = f"{start_str} - {end_str}"
            self.week_combo.addItem(label, monday.strftime("%Y-%m-%d"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Modern görünüm
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
