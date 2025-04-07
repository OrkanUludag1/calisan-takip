from PyQt5.QtCore import Qt, QTime
from PyQt5.QtWidgets import QTimeEdit, QItemDelegate

def format_currency(value):
    """Para birimini formatlar: Binlik ayırıcı, TL ibaresi ve 5'e yuvarlama"""
    try:
        # Değeri float'a çevir
        value = float(value)
        
        # Birler basamağını 5'e yuvarla
        value = round(value / 5) * 5
        
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
