import os
import shutil
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Ajustá estas rutas según tu proyecto
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH         = os.path.join(BASE_DIR, 'db', 'stock.db')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH      = os.path.join(BASE_DIR, 'token.json')
BACKUP_DIR      = os.path.join(BASE_DIR, 'backups')

# Nombre de la carpeta que se crea en tu Google Drive
DRIVE_FOLDER_NAME = 'StockManager-Backups'


class CloudBackupService:

    # ------------------------------------------------------------------ #
    # AUTENTICACION                                                        #
    # ------------------------------------------------------------------ #

    def _get_service(self):
        """Obtiene el servicio autenticado de Google Drive."""
        creds = None

        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        # Si no hay credenciales válidas, autenticar
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            # Guardar token para la próxima vez
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())

        return build('drive', 'v3', credentials=creds)

    # ------------------------------------------------------------------ #
    # CARPETA EN DRIVE                                                     #
    # ------------------------------------------------------------------ #

    def _get_or_create_folder(self, service):
        """Busca la carpeta de backups en Drive o la crea si no existe."""
        query = (
            f"name='{DRIVE_FOLDER_NAME}' "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if folders:
            return folders[0]['id']

        # Crear carpeta
        metadata = {
            'name': DRIVE_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=metadata, fields='id').execute()
        return folder['id']

    # ------------------------------------------------------------------ #
    # BACKUP                                                               #
    # ------------------------------------------------------------------ #

    def run(self):
        """
        Crea una copia local de la DB con timestamp y la sube a Drive.
        Retorna el nombre del archivo subido.
        """
        # 1. Crear carpeta local de backups si no existe
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # 2. Copiar la DB con timestamp
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"stock_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2(DB_PATH, backup_path)

        # 3. Subir a Drive
        service   = self._get_service()
        folder_id = self._get_or_create_folder(service)

        media = MediaFileUpload(backup_path, mimetype='application/octet-stream')
        file_metadata = {
            'name': backup_name,
            'parents': [folder_id]
        }
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        # 4. Limpiar backups locales viejos (conservar los últimos 5)
        self._cleanup_local(keep=5)

        return backup_name

    # ------------------------------------------------------------------ #
    # LIMPIEZA LOCAL                                                       #
    # ------------------------------------------------------------------ #

    def _cleanup_local(self, keep=5):
        """Elimina backups locales dejando solo los más recientes."""
        files = sorted([
            os.path.join(BACKUP_DIR, f)
            for f in os.listdir(BACKUP_DIR)
            if f.startswith('stock_backup_') and f.endswith('.db')
        ])

        for old in files[:-keep]:
            os.remove(old)