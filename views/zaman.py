import sys
import os

# Ana dizini Python yoluna ekle (doğrudan çalıştırma için)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from models.database import EmployeeDB
from views.zamantakip import ZamanTakipForm

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = EmployeeDB('employee.db')
    # Varsayılan olarak ilk aktif çalışanı seçerek başlat
    employees = db.get_active_employees()
    employee_id = employees[0][0] if employees else None
    window = ZamanTakipForm(db, employee_id=employee_id)
    window.setWindowTitle("Zaman Takibi")
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec_())
