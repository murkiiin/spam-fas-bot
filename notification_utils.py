
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

SPREADSHEET_NAME = "Жалобы в ФАС"

# Авторизация для Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("psyched-oarlock-459923-v5-482eb62dd0ac.json", scope)
client = gspread.authorize(creds)

def notify_admin(bot, chat_id, data):
    """Отправка уведомления о новой жалобе"""
    text = (
        f"✅ <b>Новая жалоба</b>\n"
        f"Тип: {data['type']}\n"
        f"Номер: {data['offender']}\n"
        f"Регион: {data['region']}\n"
        f"Время: {data['dt']}"
    )
    return bot.send_message(chat_id, text, parse_mode="HTML")


def search_complaints_by_phone(phone_fragment):
    """Поиск жалоб по номеру или части номера"""
    sheet = client.open(SPREADSHEET_NAME).sheet1
    rows = sheet.get_all_values()
    header = rows[0]
    data = rows[1:]
    df = pd.DataFrame(data, columns=header)
    return df[df["Номер"].str.contains(phone_fragment, na=False, case=False)]


def export_complaints_to_excel(file_path="complaints_export.xlsx"):
    """Экспорт всех жалоб в Excel"""
    sheet = client.open(SPREADSHEET_NAME).sheet1
    rows = sheet.get_all_values()
    header = rows[0]
    data = rows[1:]
    df = pd.DataFrame(data, columns=header)
    df.to_excel(file_path, index=False)
    return file_path
