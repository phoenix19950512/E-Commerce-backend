import pandas as pd
from sqlalchemy import create_engine
from app.config import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

def export_to_csv():
    engine = create_engine(settings.DATABASE_URL)
    df = pd.read_sql('SELECT * FROM your_table', con=engine)
    df.to_csv('/path/to/exported_file.csv', index=False)

def upload_to_google_sheets(csv_file_path):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = 'path/to/credentials.json'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)

    spreadsheet_id = 'your_spreadsheet_id'
    range_name = 'Sheet1!A1'

    with open(csv_file_path, 'rb') as csv_file:
        body = {
            'data': [{
                'range': range_name,
                'values': [line.split(',') for line in csv_file.read().decode('utf-8').splitlines()]
            }],
            'valueInputOption': 'RAW'
        }
        service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
