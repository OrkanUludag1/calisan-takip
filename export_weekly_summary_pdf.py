from fpdf import FPDF
from datetime import datetime, timedelta
from models.database import EmployeeDB

# A4 boyutları (mm)
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
MARGIN = 10

# Kutucuk ayarları
COLS = 3
ROWS = 4
BOX_PADDING = 4
BOX_WIDTH = (PAGE_WIDTH - 2 * MARGIN) / COLS
BOX_HEIGHT = (PAGE_HEIGHT - 2 * MARGIN) / ROWS


def get_monday(date):
    return date - timedelta(days=date.weekday())

def format_time(minutes):
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h:02d}:{m:02d}"

def main():
    db = EmployeeDB()
    today = datetime.now().date()
    monday = get_monday(today)
    week_start_date = monday.strftime('%Y-%m-%d')
    summary = db.get_weekly_summary(week_start_date)
    if not summary or not summary.get('details'):
        print('Bu haftaya ait özet veri bulunamadı.')
        return
    details = summary['details']
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=MARGIN)
    # Türkçe karakter desteği için TTF font ekle
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 10)
    
    for idx, emp in enumerate(details):
        col = idx % COLS
        row = (idx // COLS) % ROWS
        page = idx // (COLS * ROWS)
        if idx > 0 and idx % (COLS * ROWS) == 0:
            pdf.add_page()
        x = MARGIN + col * BOX_WIDTH
        y = MARGIN + row * BOX_HEIGHT
        pdf.set_xy(x, y)
        # Kutu çerçevesi
        pdf.set_draw_color(120, 120, 120)
        pdf.rect(x, y, BOX_WIDTH, BOX_HEIGHT)
        # Başlık
        pdf.set_font('DejaVu', 'B', 12)
        pdf.set_xy(x, y + BOX_PADDING)
        pdf.cell(BOX_WIDTH, 8, emp['name'], align='C', ln=2)
        pdf.set_font('DejaVu', '', 10)
        # İçerik
        lines = [
            ("Çalışma Saati", format_time(emp['total_hours'])),
            ("Eksik Çalışma", f"- {format_time(emp['total_deductions'])}"),
            ("Fazla Çalışma", f"{emp.get('total_additions', 0):,.0f} TL"),
            ("Yol", f"{emp['transport_allowance']:,.0f} TL"),
            ("Yemek", f"{emp['food_allowance']:,.0f} TL"),
            ("Toplam", f"{emp['total_weekly_salary']:,.0f} TL")
        ]
        y_cursor = y + 14
        for label, value in lines:
            pdf.set_xy(x + BOX_PADDING, y_cursor)
            pdf.cell(BOX_WIDTH - 2 * BOX_PADDING, 7, f"{label}: {value}", align='L')
            y_cursor += 7
    outname = f"haftalik_ozet_{week_start_date}.pdf"
    pdf.output(outname)
    print(f"PDF oluşturuldu: {outname}")

if __name__ == "__main__":
    main()
