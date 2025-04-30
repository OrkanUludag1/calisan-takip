import csv
from datetime import datetime, timedelta
from models.database import EmployeeDB

# Excel çıktısı için temel CSV (virgül yerine noktalı virgül kullanılırsa Türkçe Excel'de daha uyumlu olur)

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
    outname = f"haftalik_ozet_{week_start_date}.csv"
    with open(outname, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow([
            'Çalışan', 'Çalışma Saati', 'Eksik Çalışma', 'Fazla Çalışma', 'Yol', 'Yemek', 'Toplam'
        ])
        for emp in details:
            writer.writerow([
                emp['name'],
                format_time(emp['total_hours']),
                f"- {format_time(emp['total_deductions'])}",
                f"{emp.get('total_additions', 0):,.0f} TL",
                f"{emp['transport_allowance']:,.0f} TL",
                f"{emp['food_allowance']:,.0f} TL",
                f"{emp['total_weekly_salary']:,.0f} TL"
            ])
    print(f"Excel (CSV) dosyası oluşturuldu: {outname}")

if __name__ == "__main__":
    main()
