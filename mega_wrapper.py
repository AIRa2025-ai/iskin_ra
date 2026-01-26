# drive_wrapper.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDS") or "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/drive']

def connect_to_drive():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=credentials)
    return service

def upload_file_sync(local_path):
    """
    Загружает файл на Google Drive, возвращает ID загруженного файла.
    """
    service = connect_to_drive()
    file_metadata = {'name': os.path.basename(local_path)}
    media = MediaFileUpload(local_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')
