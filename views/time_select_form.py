from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QFrame, QSizePolicy, QListWidget, 
    QListWidgetItem, QSplitter, QMenu, QInputDialog,
    QDialog, QFormLayout, QPushButton, QLineEdit,
    QMessageBox, QDoubleSpinBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime

from views.zamantakip import ZamanTakipForm
from utils.helpers import format_currency
from views.ozet import OzetForm

class PaymentDialog(QDialog):
    """Ödeme/kesinti eklemek için dialog penceresi"""
    
    def __init__(self, parent=None, title="Ek Ödeme", description_label="Açıklama:", payment_type="bonus", 
                payment_data=None, is_permanent=False):
        super().__init__(parent)
        self.payment_type = payment_type
        self.payment_data = payment_data
        self.is_permanent = is_permanent
        self.title_text = title
        self.description_label = description_label
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title_text)
        self.setFixedWidth(400)
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Tutar alanı
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 100000)
        self.amount_input.setDecimals(2)
        self.amount_input.setSuffix(" ₺")
        self.amount_input.setFixedHeight(30)
        
        # Açıklama alanı
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(100)
        
        form_layout.addRow("Tutar:", self.amount_input)
        form_layout.addRow(self.description_label, self.description_input)
        
        # Mevcut veriyi doldur
        if self.payment_data:
            self.amount_input.setValue(self.payment_data[2])
            self.description_input.setText(self.payment_data[3])
            
        # Butonlar
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
    def get_values(self):
        amount = self.amount_input.value()
        description = self.description_input.toPlainText()
        
        return {
            'amount': amount,
            'description': description,
            'payment_type': self.payment_type,
            'is_permanent': self.is_permanent
        }

class PaymentListDialog(QDialog):
    """Ödeme/kesinti listesini gösteren ve silme imkanı sunan dialog penceresi"""
    
    def __init__(self, parent=None, db=None, employee_id=None, week_start_date=None):
        super().__init__(parent)
        self.db = db
        self.employee_id = employee_id
        self.week_start_date = week_start_date
        self.payments = []
        self.initUI()
        self.load_payments()
        
    def initUI(self):
        self.setWindowTitle("Ödeme ve Kesintiler")
        self.setFixedSize(600, 400)
        main_layout = QVBoxLayout(self)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Tür", "Tutar", "Açıklama", "Sabit"])
        
        # Tablo ayarları
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 40)  # ID
        self.table.setColumnWidth(1, 80)  # Tür
        self.table.setColumnWidth(2, 80)  # Tutar
        self.table.setColumnWidth(4, 60)  # Sabit
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        self.delete_btn = QPushButton("Sil")
        self.delete_btn.clicked.connect(self.delete_payment)
        
        self.close_btn = QPushButton("Kapat")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)
        
    def load_payments(self):
        """Ödeme/kesintileri yükler"""
        self.payments = self.db.get_weekly_payments(self.employee_id, self.week_start_date)
        
        self.table.setRowCount(len(self.payments))
        
        for i, payment in enumerate(self.payments):
            payment_id, payment_type, amount, description, is_permanent = payment
            
            # ID
            id_item = QTableWidgetItem(str(payment_id))
            self.table.setItem(i, 0, id_item)
            
            # Tür
            type_text = "Ek Ödeme" if payment_type == "bonus" else "Kesinti"
            type_item = QTableWidgetItem(type_text)
            self.table.setItem(i, 1, type_item)
            
            # Tutar
            amount_text = f"{amount:.2f} ₺"
            amount_item = QTableWidgetItem(amount_text)
            self.table.setItem(i, 2, amount_item)
            
            # Açıklama
            desc_item = QTableWidgetItem(description)
            self.table.setItem(i, 3, desc_item)
            
            # Sabit
            is_permanent_text = "Evet" if is_permanent else "Hayır"
            is_permanent_item = QTableWidgetItem(is_permanent_text)
            self.table.setItem(i, 4, is_permanent_item)
            
    def delete_payment(self):
        """Seçili ödeme/kesintiyi siler"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek bir kayıt seçin!")
            return
            
        payment_id = int(self.table.item(selected_row, 0).text())
        
        # Onay sorgusu
        reply = QMessageBox.question(
            self, "Onay", 
            "Seçili kaydı silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Veritabanından sil
            success = self.db.delete_payment(payment_id)
            
            if success:
                # Tablodan satırı kaldır
                self.table.removeRow(selected_row)
                QMessageBox.information(self, "Bilgi", "Kayıt başarıyla silindi!")
                
                # Dialog'u kabul ederek kapatalım (güncelleme yapılması için)
                self.accept()
            else:
                QMessageBox.critical(self, "Hata", "Kayıt silinirken bir hata oluştu!")

class TimeSelectForm(QWidget):
    """Süre seçim formu"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_time_form = None
        self.employees = []
        self.zamantakip = None  # Zaman takibi formuna erişim için özellik
        
        self.initUI()
        self.load_employees()
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sol: Çalışan listesi ve zaman takip formu
        self.splitter = QSplitter(Qt.Horizontal)
        self.employee_list = QListWidget()
        self.employee_list.setMinimumWidth(180)
        self.employee_list.setStyleSheet("font-size: 15px;")
        self.employee_list.currentItemChanged.connect(self.on_employee_selected)
        self.splitter.addWidget(self.employee_list)

        # Orta: ZamanTakipForm
        self.current_time_form = None
        self.time_form_container = QWidget()
        self.time_form_layout = QVBoxLayout(self.time_form_container)
        self.time_form_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.time_form_container)

        # Sağ: OzetForm (çalışan özeti)
        self.ozet_container = QWidget()
        self.ozet_layout = QVBoxLayout(self.ozet_container)
        self.ozet_layout.setContentsMargins(0, 0, 0, 0)
        self.ozet_widget = None
        self.splitter.addWidget(self.ozet_container)
        self.splitter.setSizes([200, 600, 300])

        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)
        self.load_employees()

    def on_employee_selected(self, current, previous):
        if not current:
            return
        employee_name = current.text()
        employee_id = current.data(Qt.UserRole)
        self.load_employee(employee_id, employee_name)

    def load_employee(self, employee_id, employee_name):
        # Orta alanı güncelle
        if self.current_time_form:
            self.time_form_layout.removeWidget(self.current_time_form)
            self.current_time_form.deleteLater()
            self.current_time_form = None
        self.current_time_form = ZamanTakipForm(self.db, employee_id=employee_id)
        self.time_form_layout.addWidget(self.current_time_form)

        # Sağdaki özet alanını güncelle
        if self.ozet_widget:
            self.ozet_layout.removeWidget(self.ozet_widget)
            self.ozet_widget.deleteLater()
            self.ozet_widget = None
        # Haftalık özet verisini hazırla
        summary_data = self.get_employee_weekly_summary(employee_id)
        self.ozet_widget = OzetForm(employee_name, summary_data)
        self.ozet_layout.addWidget(self.ozet_widget)

    def load_employees(self):
        """Çalışanları yükler ve listeye ekler"""
        self.employee_list.clear()
        self.employees = self.db.get_active_employees()
        
        # Çalışanları haftalık ücrete göre sırala (en yüksekten en düşüğe)
        sorted_employees = sorted(self.employees, key=lambda emp: emp[2], reverse=True)
        self.employees = sorted_employees
        
        for employee_id, name, weekly_salary, _, _, _ in self.employees:
            item = QListWidgetItem(name)  # Sadece ismi göster
            item.setData(Qt.UserRole, employee_id)
            self.employee_list.addItem(item)
        
        # İlk çalışanı seç ve yükle
        if self.employees and len(self.employees) > 0:
            self.employee_list.setCurrentRow(0)  # Bu otomatik olarak on_employee_selected'ı tetikleyecek
        
    def get_employee_weekly_summary(self, employee_id):
        # Burada veritabanından veya mevcut formlardan ilgili çalışanın haftalık özet verisi çekilmeli
        # Şimdilik örnek veri ile dolduruluyor
        return {
            "total_hours": 45,
            "weekly_salary": 8000,
            "meal_allowance": 500,
            "transport_allowance": 400,
            "total_additions": 250,
            "total_deductions": 100,
            "total_weekly_salary": 9050
        }

    def show_employee_context_menu(self, position):
        """Çalışan listesinde sağ tık menüsünü gösterir"""
        # Tıklanan öğeyi al
        item = self.employee_list.itemAt(position)
        if not item:
            return
            
        # Çalışan ID'sini al
        employee_id = item.data(Qt.UserRole)
        if not employee_id:
            return
            
        # Geçerli çalışanı bul
        employee = None
        for emp in self.employees:
            if emp[0] == employee_id:
                employee = emp
                break
                
        if not employee:
            return
            
        # Mevcut haftanın başlangıç tarihini al
        current_week_start = None
        if self.current_time_form:
            current_week_start = self.current_time_form.current_week_start
        
        # Menüyü oluştur
        menu = QMenu(self)
        
        # Ek ödeme menü öğesi
        add_bonus_action = menu.addAction("Ek Ödeme Ekle")
        
        # Kesinti menü öğesi
        add_deduction_action = menu.addAction("Kesinti Ekle")
        
        # Sabit ek ödeme menü öğesi
        add_permanent_action = menu.addAction("Sabit Ek Ödeme Ekle")
        
        # Düzenle menü öğesi
        edit_employee_action = menu.addAction("Düzenle")
        
        # Ayırıcı çizgi
        menu.addSeparator()
        
        # Ödemeleri listele ve yönet menü öğesi
        list_payments_action = menu.addAction("Ödemeleri Listele ve Yönet")
        
        # Menüyü göster ve seçilen eylemi al
        action = menu.exec_(self.employee_list.mapToGlobal(position))
        
        # Eyleme göre işlem yap
        if action == add_bonus_action:
            self.add_payment(employee_id, "bonus", "Ek Ödeme", "Açıklama:", False)
        elif action == add_deduction_action:
            self.add_payment(employee_id, "deduction", "Kesinti", "Kesinti Nedeni:", False)
        elif action == add_permanent_action:
            self.add_payment(employee_id, "bonus", "Sabit Ek Ödeme", "Açıklama:", True)
        elif action == list_payments_action:
            self.list_payments(employee_id)
        elif action == edit_employee_action:
            from views.employee_form import EmployeeDialog
            dialog = EmployeeDialog(self, employee=employee)
            if dialog.exec_() == dialog.Accepted:
                self.load_employees()

    def add_payment(self, employee_id, payment_type, title, description_label, is_permanent):
        """Ödeme/kesinti eklemek için dialog gösterir"""
        # Mevcut haftanın başlangıç tarihini al
        if not self.current_time_form or not self.current_time_form.current_week_start:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir haftayı seçin!")
            return
            
        week_start_date = self.current_time_form.current_week_start
        
        # Ödeme/kesinti dialog penceresini göster
        dialog = PaymentDialog(
            self, 
            title=title, 
            description_label=description_label,
            payment_type=payment_type,
            is_permanent=is_permanent
        )
        
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            if values:
                # Veritabanına ödeme/kesinti ekle
                self.db.add_payment(
                    employee_id,
                    week_start_date,
                    values['payment_type'],
                    values['amount'],
                    values['description'],
                    1 if values['is_permanent'] else 0
                )
                
                # Formu güncelle
                if self.current_time_form:
                    self.current_time_form.calculate_total_hours()
                    
                QMessageBox.information(self, "Bilgi", "İşlem başarıyla kaydedildi!")

    def list_payments(self, employee_id):
        """Ödeme/kesintileri listeler ve silme imkanı sunar"""
        # Mevcut haftanın başlangıç tarihini al
        if not self.current_time_form or not self.current_time_form.current_week_start:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir hafta seçin!")
            return
            
        week_start_date = self.current_time_form.current_week_start
        
        # Ödeme listesi dialogunu göster
        dialog = PaymentListDialog(
            self,
            db=self.db,
            employee_id=employee_id,
            week_start_date=week_start_date
        )
        
        if dialog.exec_() == QDialog.Accepted:
            # Formu güncelle
            if self.current_time_form:
                self.current_time_form.calculate_total_hours()

    @property
    def time_tracking_form(self):
        # Geriye mevcut zaman takip formunu döndürür
        return self.current_time_form
