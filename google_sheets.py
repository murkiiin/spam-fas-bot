
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка доступа к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("psyched-oarlock-459923-v5-482eb62dd0ac.json", scope)
client = gspread.authorize(creds)

# Укажите здесь название вашей Google Таблицы
SPREADSHEET_NAME = "Жалобы в ФАС"

def append_complaint(data: dict, user: dict):
    try:
        sheet = client.open(SPREADSHEET_NAME).sheet1
        sheet.append_row([
            data.get("type"),
            data.get("offender"),
            data.get("dt"),
            "Да" if data.get("robot") else "Нет",
            data.get("content"),
            data.get("region"),
            user.get("fio"),
            user.get("email"),
            user.get("phone"),
            user.get("address")
        ])
    except Exception as e:
        print(f"Ошибка при отправке в Google Sheets: {e}")
