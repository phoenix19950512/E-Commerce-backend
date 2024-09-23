import pandas as pd
from sqlalchemy import create_engine, inspect
from app.config import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

def export_to_csv():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    for table in table_names:
        df = pd.read_sql(f'SELECT * FROM {table}', con=engine)
        csv_file_path = f'/path/to/exported_files/{table}.csv'
        df.to_csv(csv_file_path, index=False)
        upload_to_google_sheets(csv_file_path, table)

def upload_to_google_sheets(csv_file_path, table_name):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = 'path/to/credentials.json'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)

    spreadsheet_id = '1Ww0nxJ6Mp7FM5O1hjXkXmZMS4eNQ8VnzUrdDJaSb9F8'
    range_name = f'{table_name}!A1'

    with open(csv_file_path, 'r') as csv_file:
        values = [line.strip().split(',') for line in csv_file.readlines()]

    body = {
        'values': values
    }

    try:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
    except Exception as e:
        print(f"Failed to upload {csv_file_path} to Google Sheets: {e}")
