from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QSplitter, QFrame, QListWidgetItem
from PyQt5.QtCore import Qt
import gc
from .time_select_form import TimeSelectForm
from views.time_tracking_form import TimeTrackingForm

class TimeSelectFormAlt(TimeSelectForm):
    """Alternatif layout ile Süre sekmesi"""
    def initUI(self):
        main_layout = QHBoxLayout(self)  # Dikey yerine yatay ana layout
        main_layout.setSpacing(20)

        # Sol tarafta hafta seçimi ve çalışan listesi
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        week_label = QLabel("Hafta Seç:")
        week_label.setAlignment(Qt.AlignLeft)
        self.week_combo = QComboBox()
        self.week_combo.setFixedWidth(180)
        self.week_combo.setEditable(False)
        self.week_combo.currentIndexChanged.connect(self.on_week_combo_changed)
        left_panel.addWidget(week_label)
        left_panel.addWidget(self.week_combo)
        left_panel.addSpacing(10)
        self.employee_list = QListWidget()
        self.employee_list.currentRowChanged.connect(self.on_employee_selected)
        # SÜRE sekmesindeki gibi context menu ayarları
        self.employee_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.employee_list.customContextMenuRequested.connect(self.show_employee_context_menu)
        left_panel.addWidget(self.employee_list, stretch=1)

        # Sağda form (time tracking)
        self.time_form_container = QVBoxLayout()
        self.time_form_container.setSpacing(10)
        form_frame = QFrame()
        form_frame.setLayout(self.time_form_container)
        form_frame.setMinimumWidth(700)

        # Splitter ile iki paneli ayır
        splitter = QSplitter()
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        splitter.addWidget(left_widget)
        splitter.addWidget(form_frame)
        splitter.setSizes([120, 1000])

        main_layout.addWidget(splitter)
        self.update_week_combo()
        self.load_employees()

    def on_employee_selected(self, row):
        if row < 0 or row >= len(self.employees):
            return
        employee_id, employee_name, *_ = self.employees[row]
        self.load_employee(employee_id, employee_name)

    def show_employee_context_menu(self, position):
        # Base class fonksiyonunu çağır (TimeSelectForm)
        super().show_employee_context_menu(position)

    def on_employees_loaded(self, employees):
        # SÜRE sekmesindeki gibi çalışanları sırala ve ekle
        try:
            sorted_employees = sorted(employees, key=lambda emp: emp[2], reverse=True)
            self.employees = sorted_employees
            selected_row = 0
            selected_employee_id = getattr(self, '_selected_employee_id', None)
            self.employee_list.clear()
            for idx, (employee_id, name, weekly_salary, _, _, _) in enumerate(self.employees):
                item = QListWidgetItem(name)  # Sadece ismi göster
                item.setData(Qt.UserRole, employee_id)
                self.employee_list.addItem(item)
                if selected_employee_id is not None and employee_id == selected_employee_id:
                    selected_row = idx
            if self.employees and len(self.employees) > 0:
                self.employee_list.setCurrentRow(selected_row)
        finally:
            self._is_updating = False
            # self.db.data_changed.connect(self.load_employees)  # KALDIRILDI: Sadece çalışan işlemlerinde bağlanmalı
            try:
                pass
            except Exception:
                pass

    def load_employee(self, employee_id, employee_name):
        # Önce mevcut formu tamamen temizle
        if self.current_time_form:
            if hasattr(self.current_time_form, 'disconnect_all_signals'):
                self.current_time_form.disconnect_all_signals()
            self.current_time_form.setParent(None)
            self.current_time_form.deleteLater()
            self.current_time_form = None
            QApplication.processEvents()
            gc.collect()
        # time_form_container içindeki tüm widget ve layout'ları temizle
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                child_layout = item.layout()
                if widget:
                    widget.setParent(None)
                if child_layout:
                    clear_layout(child_layout)
                    child_layout.deleteLater()
        clear_layout(self.time_form_container)
        # Yeni time tracking form oluştur
        self.current_time_form = TimeTrackingForm(self.db, employee_id)
        # Ana layout'u yatay olarak ikiye böl
        hbox = QHBoxLayout()
        hbox.setSpacing(20)
        # Sadece ana formu ekle (alt widget'ları değil)
        hbox.addWidget(self.current_time_form)
        self.time_form_container.addLayout(hbox)
        # Haftayı bildir
        if self.selected_week:
            self.current_time_form.set_week(self.selected_week)
