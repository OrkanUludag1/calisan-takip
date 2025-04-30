from PyQt5.QtCore import Qt, QTime, QDate
from PyQt5.QtWidgets import QTimeEdit, QItemDelegate

def format_currency(value):
    """Para birimini formatlar: Binlik ayırıcı, TL ibaresi ve 10'a yuvarlama"""
    try:
        # Değeri float'a çevir
        value = float(value)
        
        # 10 ve katlarına yuvarla
        value = round(value / 10) * 10
        
        # Binlik ayırıcı ekle
        formatted = "{:,.0f}".format(value).replace(",", ".")
        
        # TL ibaresi ekle
        return f"{formatted} TL"
    except (ValueError, TypeError):
        return "0 TL"

def calculate_working_hours(entry_time, lunch_start, lunch_end, exit_time):
    """Çalışma saatlerini hesaplar"""
    if not all([entry_time, lunch_start, lunch_end, exit_time]):
        return 0
    
    # QTime nesnelerini dakika cinsinden hesapla
    entry_minutes = entry_time.hour() * 60 + entry_time.minute()
    lunch_start_minutes = lunch_start.hour() * 60 + lunch_start.minute()
    lunch_end_minutes = lunch_end.hour() * 60 + lunch_end.minute()
    exit_minutes = exit_time.hour() * 60 + exit_time.minute()
    
    # Öğle molası öncesi ve sonrası çalışma sürelerini hesapla
    morning_work = lunch_start_minutes - entry_minutes
    afternoon_work = exit_minutes - lunch_end_minutes
    
    # Toplam çalışma süresi (saat cinsinden)
    total_hours = (morning_work + afternoon_work) / 60
    
    return total_hours

def calculate_daily_normal_and_overtime(entry_time, lunch_start, lunch_end, exit_time, current_day=None):
    """
    Bir gün için normal ve fazla mesai saatlerini hesaplar.
    - Hafta içi: 18:45'e kadar olan saatler normal, sonrası fazla mesai.
    - Cumartesi/Pazar: tüm saatler fazla mesai.
    entry_time, lunch_start, lunch_end, exit_time: QTime nesneleri
    current_day: QDate nesnesi (isteğe bağlı, hafta sonu kontrolü için)
    """
    if not all([entry_time, lunch_start, lunch_end, exit_time]):
        return 0.0, 0.0

    entry_minutes = entry_time.hour() * 60 + entry_time.minute()
    lunch_start_minutes = lunch_start.hour() * 60 + lunch_start.minute()
    lunch_end_minutes = lunch_end.hour() * 60 + lunch_end.minute()
    exit_minutes = exit_time.hour() * 60 + exit_time.minute()

    morning_work = lunch_start_minutes - entry_minutes
    afternoon_work = exit_minutes - lunch_end_minutes
    day_hours = (morning_work + afternoon_work) / 60.0

    # Hafta sonu kontrolü
    weekday = None
    if current_day:
        try:
            weekday = current_day.dayOfWeek() - 1  # Pazartesi=0, Pazar=6
        except Exception:
            weekday = None
    if weekday in [5, 6]:  # Cumartesi/Pazar
        return 0.0, day_hours if day_hours > 0 else 0.0

    # Hafta içi için 18:45 sonrası fazla mesai
    overtime_start_minutes = 18 * 60 + 45
    day_end_minutes = exit_minutes
    normal_end_minutes = min(day_end_minutes, overtime_start_minutes)
    # Sabah çalışma
    morning_seconds = (lunch_start_minutes * 60) - (entry_minutes * 60)
    morning_hours = morning_seconds / 3600.0 if morning_seconds > 0 else 0
    # Akşam çalışma (öğle bitişi -> normal bitiş)
    afternoon_seconds = (normal_end_minutes * 60) - (lunch_end_minutes * 60)
    afternoon_hours = afternoon_seconds / 3600.0 if afternoon_seconds > 0 else 0
    normal_hours = morning_hours + afternoon_hours
    # Fazla mesai: 18:45 sonrası
    overtime_hours = 0.0
    if day_end_minutes > overtime_start_minutes:
        overtime_minutes = day_end_minutes - overtime_start_minutes
        overtime_hours = overtime_minutes / 60.0
    return normal_hours if normal_hours > 0 else 0.0, overtime_hours if overtime_hours > 0 else 0.0

class TimeEditDelegate(QItemDelegate):
    """Zaman düzenleme delegesi"""
    def createEditor(self, parent, option, index):
        editor = QTimeEdit(parent)
        editor.setDisplayFormat("HH:mm")
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value:
            time = QTime.fromString(value, "HH:mm")
            editor.setTime(time)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.time().toString("HH:mm"), Qt.EditRole)
