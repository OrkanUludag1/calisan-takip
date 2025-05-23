from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QFrame, QSizePolicy, QListWidget, 
    QListWidgetItem, QSplitter, QMenu, QInputDialog,
    QDialog, QFormLayout, QPushButton, QLineEdit,
    QMessageBox, QDoubleSpinBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont
from datetime import datetime

from views.time_tracking_form import TimeTrackingForm
from utils.helpers import format_currency

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

class EmployeeLoaderWorker(QThread):
    employees_loaded = pyqtSignal(list)

    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file

    def run(self):
        import sqlite3
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, weekly_salary, daily_food, daily_transport, is_active
            FROM employees
            WHERE is_active = 1
            ORDER BY name
        ''')
        employees = cursor.fetchall()
        conn.close()
        self.employees_loaded.emit(employees)

class TimeSelectForm(QWidget):
    """Süre seçim formu"""
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_time_form = None
        self.employees = []
        self._active_dialogs = []  # Açık dialog referanslarını tutmak için
        self.time_tracking_form = None  # Zaman takibi formuna erişim için özellik
        self.selected_week = None  # Seçili hafta (global)
        self.initUI()
        # --- Otomatik güncelleme: DB değişince çalışan listesini güncelle ---
        self.load_employees()
    
    def initUI(self):
        """Kullanıcı arayüzünü başlatır"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Hafta seçimi combobox'ı artık ortalanacak şekilde üstte
        week_combo_layout = QHBoxLayout()
        week_combo_layout.addStretch()
        self.week_combo = QComboBox()
        self.week_combo.setFixedWidth(200)
        self.week_combo.setEditable(False)
        self.week_combo.currentIndexChanged.connect(self.on_week_combo_changed)
        week_combo_layout.addWidget(self.week_combo)
        week_combo_layout.addStretch()
        main_layout.addLayout(week_combo_layout)
        
        # 'Haftalık Özet' başlığı tamamen kaldırıldı
        # summary_title = QLabel("Haftalık Özet")
        # summary_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4a86e8;")
        # main_layout.addWidget(summary_title, alignment=Qt.AlignCenter)

        # Ana içerik splitter
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(0)  # Ayırıcı çizgiyi kaldır
        content_splitter.setChildrenCollapsible(False)  # Bölümlerin tamamen kapanmasını engelle
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
            }
        """)
        
        # Form konteyneri
        form_container = QWidget()
        self.time_form_container = QVBoxLayout(form_container)
        self.time_form_container.setContentsMargins(0, 0, 0, 0)
        
        # Çalışan listesi
        self.employee_list = QListWidget()
        self.employee_list.setMaximumWidth(200)  # Listenin maksimum genişliği
        self.employee_list.setStyleSheet("""
            QListWidget {
                border: none;  /* Çerçeveyi kaldır */
                padding: 5px;
                margin-top: 32px;  /* TimeTrackingForm'daki tablolarla aynı hizaya getirmek için üstten margin */
                background-color: #f8f9fa;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #e8f0fe;
            }
        """)
        
        # Bir çalışan seçildiğinde
        self.employee_list.currentItemChanged.connect(self.on_employee_selected)
        
        # Sağ tık menüsü için context menu ayarla
        self.employee_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.employee_list.customContextMenuRequested.connect(self.show_employee_context_menu)
        
        # Splitter'a ekle (önce liste, sonra form)
        content_splitter.addWidget(self.employee_list)
        content_splitter.addWidget(form_container)
        
        # Genişlik oranlarını ayarla (liste 1:5 form olacak şekilde)
        content_splitter.setSizes([160, 800])
        
        main_layout.addWidget(content_splitter)
        
        # Hafta combobox'unu güncelle
        self.update_week_combo()

    def update_week_combo(self):
        """Veritabanındaki haftaları combobox'a yükler ve seçim yapar"""
        from PyQt5.QtCore import QDate
        self.week_combo.blockSignals(True)
        self.week_combo.clear()
        weeks = self.db.get_available_weeks() if hasattr(self.db, 'get_available_weeks') else []
        weeks = sorted(set(weeks), reverse=True)
        for w in weeks:
            # Görsel olarak "21-27 Nisan 2025" gibi göster
            try:
                start_dt = QDate.fromString(w, "yyyy-MM-dd")
                end_dt = start_dt.addDays(6)
                label = f"{start_dt.toString('d MMMM')} - {end_dt.toString('d MMMM yyyy')}"
                self.week_combo.addItem(label, w)
            except Exception:
                self.week_combo.addItem(w, w)
        # Varsayılan seçim: Çalışılan gün hangi haftadaysa o hafta seçili gelsin
        if not self.selected_week:
            today = QDate.currentDate()
            # Haftanın başlangıcı (Pazartesi)
            days_to_monday = today.dayOfWeek() - 1
            monday = today.addDays(-days_to_monday)
            week_str = monday.toString("yyyy-MM-dd")
            idx = self.week_combo.findData(week_str)
            if idx >= 0:
                self.week_combo.setCurrentIndex(idx)
                self.selected_week = week_str
            else:
                self.week_combo.setCurrentIndex(0)
                self.selected_week = self.week_combo.itemData(0)
        else:
            idx = self.week_combo.findData(self.selected_week)
            if idx >= 0:
                self.week_combo.setCurrentIndex(idx)
            else:
                self.week_combo.setCurrentIndex(0)
                self.selected_week = self.week_combo.itemData(0)
        self.week_combo.blockSignals(False)
        # Seçimi güncelle (sinyali tetiklememek için doğrudan fonksiyonu çağırma)
        self.on_week_combo_changed(self.week_combo.currentIndex())

    def on_week_combo_changed(self, idx):
        """Hafta combobox değiştiğinde çağrılır"""
        week_str = self.week_combo.itemData(idx)
        if week_str:
            self.selected_week = week_str
            # Aktif çalışan formuna haftayı bildir
            if self.current_time_form:
                self.current_time_form.set_week(week_str)

    def load_employees(self):
        try:
            self.db.data_changed.disconnect(self.load_employees)
        except Exception:
            pass
        if getattr(self, '_is_updating', False):
            try:
                self.db.data_changed.connect(self.load_employees)
            except Exception:
                pass
            return
        # --- SEÇİLİ ÇALIŞANI KAYDET ---
        selected_employee_id = None
        current_item = self.employee_list.currentItem() if hasattr(self, 'employee_list') else None
        if current_item:
            selected_employee_id = current_item.data(Qt.UserRole)
        self._selected_employee_id = selected_employee_id
        self._is_updating = True
        try:
            self.employee_list.clear()
            # Worker başlat
            self.worker = EmployeeLoaderWorker(self.db.db_file)
            self.worker.employees_loaded.connect(self.on_employees_loaded)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.start()
        except Exception as e:
            pass
        # _is_updating ve reconnect işlemleri artık on_employees_loaded içinde yapılacak

    def on_employees_loaded(self, employees):
        try:
            # Çalışanları haftalık ücrete göre sırala (en yüksekten en düşüğe)
            sorted_employees = sorted(employees, key=lambda emp: emp[2], reverse=True)
            self.employees = sorted_employees
            selected_row = 0
            selected_employee_id = getattr(self, '_selected_employee_id', None)
            for idx, (employee_id, name, weekly_salary, _, _, _) in enumerate(self.employees):
                item = QListWidgetItem(name)  # Sadece ismi göster
                item.setData(Qt.UserRole, employee_id)
                self.employee_list.addItem(item)
                # Eğer kaydedilen çalışan ID'siyle eşleşirse, seçilecek satırı belirle
                if selected_employee_id is not None and employee_id == selected_employee_id:
                    selected_row = idx
            # Önceki seçimi koru, yoksa ilk çalışanı seç
            if self.employees and len(self.employees) > 0:
                self.employee_list.setCurrentRow(selected_row)  # Bu otomatik olarak on_employee_selected'ı tetikleyecek
        finally:
            self._is_updating = False
            try:
                self.db.data_changed.connect(self.load_employees)
            except Exception:
                pass
    
    def on_employee_selected(self, current, previous):
        """Listeden bir çalışan seçildiğinde"""
        if not current:
            return
        employee_id = current.data(Qt.UserRole)
        name = current.text()
        self.load_employee(employee_id, name)
    
    def load_employee(self, employee_id, employee_name):
        """Belirli bir çalışanı yükler"""
        # Eğer mevcut bir form varsa, onu silmek yerine güncelle
        if self.current_time_form:
            self.current_time_form.set_employee(employee_id, employee_name)
            # Seçili haftayı bildir
            if self.selected_week:
                self.current_time_form.set_week(self.selected_week)
            return  # Yeni form yaratmaya gerek yok

        # Eğer hiç form yoksa (ilk açılış), yeni oluştur
        self.current_time_form = TimeTrackingForm(self.db, employee_id)
        self.time_tracking_form = self.current_time_form
        self.current_time_form.set_employee(employee_id, employee_name)
        if self.selected_week:
            self.current_time_form.set_week(self.selected_week)
        self.time_form_container.addWidget(self.current_time_form)
    
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
        self._active_dialogs.append(dialog)
        def cleanup():
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
        dialog.finished.connect(cleanup)
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
        self._active_dialogs.append(dialog)
        def cleanup():
            if dialog in self._active_dialogs:
                self._active_dialogs.remove(dialog)
        dialog.finished.connect(cleanup)
        if dialog.exec_() == QDialog.Accepted:
            # Formu güncelle
            if self.current_time_form:
                self.current_time_form.calculate_total_hours()
