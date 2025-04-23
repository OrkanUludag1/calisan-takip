# Gerekli modüllerin import edilmesi
import os
import sys
try:
    # Normal import yöntemi (ana uygulamadan çağrıldığında)
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QTableWidget, QTableWidgetItem, QHeaderView, 
        QTimeEdit, QCheckBox, QComboBox, QDateEdit,
        QPushButton, QGraphicsOpacityEffect, QAbstractSpinBox,
        QFrame, QSizePolicy, QDateEdit, QMenu, QAction, QGridLayout, QApplication
    )
    from PyQt5.QtCore import Qt, QDate, QTime, QTimer, pyqtSignal, QPoint
    from PyQt5.QtGui import QColor, QBrush, QPainter, QPen, QFont
    from datetime import datetime, timedelta

    from models.database import EmployeeDB
    from utils.helpers import format_currency, calculate_working_hours
except ModuleNotFoundError:
    # Dosya doğrudan çalıştırıldığında
    pass

# Özel TimeEdit sınıfı
class CustomTimeEdit(QTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("HH:mm")
        self.setReadOnly(False)
        self.setKeyboardTracking(True)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # ... (DEVAMI time_tracking_form.py'den kopyalandı)
        self.first_digit = -1  # İlk basılan rakam
        self.current_section = None  # Şu anki seçili bölüm
        self.is_strikeout = False  # Üstü çizili mi?
        self.is_inactive = False  # Pasif mi?
        # Stil ayarları
        self.setStyleSheet("""
            CustomTimeEdit { 
                padding: 6px; 
                qproperty-alignment: AlignCenter;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                color: #333;
            }
            CustomTimeEdit:focus { 
                border: 1px solid #4a86e8;
                background-color: #e8f0fe;
            }
        """)
    def setStrikeOut(self, strikeout):
        self.is_strikeout = strikeout
        self.update()
    def setInactive(self, inactive):
        self.is_inactive = inactive
        self.update()
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_inactive:
            painter = QPainter(self)
            painter.setPen(QPen(QColor("#b0b0b0")))
            text = self.time().toString("HH:mm")
            font = self.font()
            rect = self.rect()
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, text)
    def mousePressEvent(self, event):
        pos = event.pos()
        rect = self.rect()
        hour_region = rect.width() / 2
        if pos.x() < hour_region:
            self.setSelectedSection(QTimeEdit.HourSection)
            self.current_section = QTimeEdit.HourSection
        else:
            self.setSelectedSection(QTimeEdit.MinuteSection)
            self.current_section = QTimeEdit.MinuteSection
        self.first_digit = -1
        super().mousePressEvent(event)
    def wheelEvent(self, event):
        event.ignore()
    def keyPressEvent(self, event):
        if event.key() >= Qt.Key_0 and event.key() <= Qt.Key_9:
            digit = event.key() - Qt.Key_0
            current_time = self.time()
            hour = current_time.hour()
            minute = current_time.minute()
            section = self.currentSection()
            self.current_section = section
            if section == QTimeEdit.HourSection:
                if self.first_digit == -1:
                    self.first_digit = digit
                    if digit > 2:
                        hour = digit
                        self.first_digit = -1
                        self.setSelectedSection(QTimeEdit.MinuteSection)
                    else:
                        hour = digit * 10 + (hour % 10)
                else:
                    if self.first_digit == 2 and digit > 3:
                        digit = 3
                    hour = self.first_digit * 10 + digit
                    self.first_digit = -1
                    self.setSelectedSection(QTimeEdit.MinuteSection)
            elif section == QTimeEdit.MinuteSection:
                if self.first_digit == -1:
                    self.first_digit = digit
                    if digit > 5:
                        minute = digit
                        self.first_digit = -1
                        self.setSelectedSection(QTimeEdit.HourSection)
                    else:
                        minute = digit * 10 + (minute % 10)
                else:
                    minute = self.first_digit * 10 + digit
                    self.first_digit = -1
                    self.setSelectedSection(QTimeEdit.HourSection)
            new_time = QTime(hour, minute)
            self.setTime(new_time)
            return
        elif event.key() == Qt.Key_Backspace:
            self.first_digit = -1
            super().keyPressEvent(event)
        elif event.key() == Qt.Key_Tab:
            self.first_digit = -1
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class ZamanTakipForm(QWidget):
    """Zaman takibi formu"""
    time_changed_signal = pyqtSignal()
    def __init__(self, db, employee_id=None):
        super().__init__()
        self.db = db
        self.current_employee_id = employee_id
        self.current_date = QDate.currentDate()
        self.day_active_status = []
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(10000)
        days_to_monday = self.current_date.dayOfWeek() - 1
        week_start = self.current_date.addDays(-days_to_monday)
        self.current_week_start = week_start.toString("yyyy-MM-dd")
        self.initUI()
    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        header_layout = QHBoxLayout()
        self.employee_name_label = QLabel("")
        self.employee_name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
        """)
        header_layout.addWidget(self.employee_name_label)
        header_layout.addStretch()
        content_layout = QHBoxLayout()
        self.days_table = QTableWidget()
        self.days_table.setColumnCount(5)
        self.days_table.setHorizontalHeaderLabels(["Gün", "Giriş", "Öğle Başlangıç", "Öğle Bitiş", "Çıkış"])
        self.days_table.verticalHeader().setDefaultSectionSize(40)
        self.days_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.days_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.days_table.verticalHeader().setVisible(False)
        self.days_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.days_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.days_table.customContextMenuRequested.connect(self.show_context_menu)
        self.days_table.setAlternatingRowColors(True)
        self.days_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.days_table.setSelectionMode(QTableWidget.SingleSelection)
        self.days_table.verticalHeader().setDefaultSectionSize(34)
        self.days_table.setStyleSheet("""
            QTableWidget {
                background: #f8f9fa;
                font-size: 15px;
                border: 1px solid #bdc3c7;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 6px 0;
                border: none;
            }
            QTableWidget::item {
                font-size: 15px;
                height: 34px;
            }
            QTableWidget::item:!enabled {
                color: #b0b0b0;
                background: #f0f0f0;
            }
            QTableWidget::item:selected {
                background: #e0edfa;
                color: #2a5885;
            }
        """)
        self.days_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: #2a5885; color: white; font-weight: bold; font-size: 14px; padding: 6px 0; border: none; }"
        )
        content_layout.addWidget(self.days_table)
        main_layout.addLayout(header_layout)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
        self.load_week_days()
    def auto_save_all(self):
        """Tüm satırları otomatik kaydeder"""
        if not self.current_employee_id:
            return
        for row in range(7):
            self.auto_save_row(row)
    def auto_save_row(self, row):
        # Her satırdaki saat verilerini kaydeder
        if not self.day_active_status[row]:
            return
        entry = self.days_table.cellWidget(row, 1).time().toString("HH:mm")
        lunch_start = self.days_table.cellWidget(row, 2).time().toString("HH:mm")
        lunch_end = self.days_table.cellWidget(row, 3).time().toString("HH:mm")
        exit_ = self.days_table.cellWidget(row, 4).time().toString("HH:mm")
        # Burada veritabanına kaydetme işlemi yapılabilir
        # self.db.save_work_hours(self.current_employee_id, tarih, entry, lunch_start, lunch_end, exit_)
        pass
    def show_context_menu(self, position):
        # Sağ tıklanan satırı bul
        row = self.days_table.rowAt(position.y())
        if row < 0:
            return
        menu = QMenu(self)
        is_active = True
        if hasattr(self, 'day_active_status') and len(self.day_active_status) > row:
            is_active = self.day_active_status[row]
        if is_active:
            toggle_action = menu.addAction("Günü Pasif Yap")
            toggle_action.triggered.connect(lambda: self.toggle_day_status(row, False))
        else:
            toggle_action = menu.addAction("Günü Aktif Yap")
            toggle_action.triggered.connect(lambda: self.toggle_day_status(row, True))
        menu.exec_(self.days_table.viewport().mapToGlobal(position))
    def toggle_day_status(self, row, active_status):
        # Günün aktif/pasif durumunu değiştir ve tabloyu güncelle
        self.day_active_status[row] = active_status
        item = self.days_table.item(row, 0)
        if item:
            font = item.font()
            if active_status:
                item.setFlags(item.flags() | Qt.ItemIsEnabled)
                font.setItalic(False)
                item.setForeground(QBrush(QColor("#333")))
                # Widget yoksa oluştur ve ekle
                for col in range(1, 5):
                    if not self.days_table.cellWidget(row, col):
                        time_edit = CustomTimeEdit()
                        # Varsayılan saatler
                        if col == 1:
                            time_edit.setTime(QTime(8, 15))
                        elif col == 2:
                            time_edit.setTime(QTime(13, 15))
                        elif col == 3:
                            time_edit.setTime(QTime(13, 45))
                        elif col == 4:
                            time_edit.setTime(QTime(18, 45))
                        self.days_table.setCellWidget(row, col, time_edit)
                    widget = self.days_table.cellWidget(row, col)
                    if widget:
                        widget.setEnabled(True)
                        widget.setInactive(False)
                        widget.show()
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                font.setItalic(True)
                item.setForeground(QBrush(QColor("#b0b0b0")))
                # Widget'ları tamamen kaldır
                for col in range(1, 5):
                    widget = self.days_table.cellWidget(row, col)
                    if widget:
                        widget.deleteLater()
                        self.days_table.removeCellWidget(row, col)
            item.setFont(font)
    def load_week_days(self):
        # Haftanın günlerini ve saat widget'larını tabloya yükle
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        self.days_table.setRowCount(7)
        self.day_active_status = [True, True, True, True, True, False, False]
        for i, day in enumerate(days):
            item = QTableWidgetItem(day)
            item.setTextAlignment(Qt.AlignCenter)
            if not self.day_active_status[i]:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
                item.setForeground(QBrush(QColor("#b0b0b0")))
            self.days_table.setItem(i, 0, item)
            # Sadece aktif günlere widget ekle
            if self.day_active_status[i]:
                for col in range(1, 5):
                    time_edit = CustomTimeEdit()
                    # Varsayılan saatler
                    if col == 1:
                        time_edit.setTime(QTime(8, 15))
                    elif col == 2:
                        time_edit.setTime(QTime(13, 15))
                    elif col == 3:
                        time_edit.setTime(QTime(13, 45))
                    elif col == 4:
                        time_edit.setTime(QTime(18, 45))
                    self.days_table.setCellWidget(i, col, time_edit)
    # ... (DEVAMI mevcut koddan kopyalandı)
