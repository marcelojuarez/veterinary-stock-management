import json
import logging
import os
import shutil
import sys
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config.settings import DB_PATH

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def _get_data_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(os.environ['LOCALAPPDATA']) / 'StockManager'
    return Path(__file__).parent.parent

_DATA_DIR        = _get_data_dir()
CREDENTIALS_PATH = str(_DATA_DIR / 'credentials.json')
TOKEN_PATH       = str(_DATA_DIR / 'token.json')
ACCOUNT_PATH     = str(_DATA_DIR / 'drive_account.txt')  # cached email
BACKUP_DIR       = str(_DATA_DIR / 'backups')

DRIVE_FOLDER_NAME = 'StockManager-Backups'

# Times (HH:MM, 24 h) at which the automatic cloud backup runs each day.
CLOUD_BACKUP_TIMES = ["09:00", "18:00"]


class CloudBackupService:

    def __init__(self):
        self._cloud_thread: threading.Thread | None = None
        self._stop_cloud = False

    # ------------------------------------------------------------------ #
    # SETUP / CREDENTIAL MANAGEMENT                                        #
    # ------------------------------------------------------------------ #

    def _ensure_credentials(self):
        """
        Makes sure credentials.json is in the expected data directory.
        When running as a frozen app, copies it from the PyInstaller bundle
        (sys._MEIPASS) if it hasn't been placed there yet.
        Raises FileNotFoundError with a clear message if not found anywhere.
        """
        if os.path.exists(CREDENTIALS_PATH):
            return

        # Try PyInstaller bundle directory
        if getattr(sys, 'frozen', False):
            bundled = Path(sys._MEIPASS) / 'credentials.json'
            if bundled.exists():
                os.makedirs(str(_DATA_DIR), exist_ok=True)
                shutil.copy2(str(bundled), CREDENTIALS_PATH)
                return

        raise FileNotFoundError(
            f"No se encontró credentials.json.\n\n"
            f"Ruta esperada: {CREDENTIALS_PATH}\n\n"
            f"Usá el botón 'Configurar Google Drive' para importarlo."
        )

    def is_configured(self) -> bool:
        """True if credentials.json is available (app can attempt auth)."""
        try:
            self._ensure_credentials()
            return True
        except FileNotFoundError:
            return False

    def is_authenticated(self) -> bool:
        """True if there is a valid (or refreshable) token stored."""
        if not os.path.exists(TOKEN_PATH):
            return False
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            return creds.valid or (creds.expired and bool(creds.refresh_token))
        except Exception:
            return False

    def get_connected_account(self) -> str | None:
        """Returns the cached Google account email, or None if not authenticated."""
        if os.path.exists(ACCOUNT_PATH):
            try:
                return Path(ACCOUNT_PATH).read_text(encoding='utf-8').strip() or None
            except Exception:
                pass
        return None

    def authenticate(self) -> str:
        """
        Triggers the OAuth browser flow so the user can authorise a Google account.
        Saves token.json and caches the account email.
        Returns the email address of the connected account.
        """
        self._ensure_credentials()
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        os.makedirs(str(_DATA_DIR), exist_ok=True)
        with open(TOKEN_PATH, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())

        # Fetch and cache the account email
        email = 'cuenta desconocida'
        try:
            service = build('drive', 'v3', credentials=creds)
            about   = service.about().get(fields='user').execute()
            email   = about.get('user', {}).get('emailAddress', email)
        except Exception:
            pass

        Path(ACCOUNT_PATH).write_text(email, encoding='utf-8')
        return email

    def disconnect(self):
        """Removes the stored token and cached account so the next run re-authenticates."""
        for path in (TOKEN_PATH, ACCOUNT_PATH):
            if os.path.exists(path):
                os.remove(path)

    def import_credentials(self, source_path: str):
        """
        Copies a credentials.json from an arbitrary path into the data directory.
        Call this from the UI when the user browses for the file.
        """
        os.makedirs(str(_DATA_DIR), exist_ok=True)
        shutil.copy2(source_path, CREDENTIALS_PATH)

    # ------------------------------------------------------------------ #
    # AUTHENTICATION (internal)                                            #
    # ------------------------------------------------------------------ #

    def _get_service(self):
        """Returns an authenticated Google Drive service, refreshing token if needed."""
        self._ensure_credentials()

        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w', encoding='utf-8') as f:
                    f.write(creds.to_json())
            else:
                # No valid token — caller should use authenticate() first
                raise RuntimeError(
                    "No hay una cuenta de Google conectada.\n"
                    "Usá 'Configurar Google Drive' para autorizar el acceso."
                )

        return build('drive', 'v3', credentials=creds)

    # ------------------------------------------------------------------ #
    # DRIVE FOLDER                                                         #
    # ------------------------------------------------------------------ #

    def _get_or_create_folder(self, service):
        query = (
            f"name='{DRIVE_FOLDER_NAME}' "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])
        if folders:
            return folders[0]['id']

        metadata = {
            'name': DRIVE_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        folder = service.files().create(body=metadata, fields='id').execute()
        return folder['id']

    # ------------------------------------------------------------------ #
    # BACKUP                                                               #
    # ------------------------------------------------------------------ #

    def run(self):
        """Creates a timestamped local copy of the DB and uploads it to Drive."""
        os.makedirs(BACKUP_DIR, exist_ok=True)

        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"stock_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        src = sqlite3.connect(str(DB_PATH))
        dst = sqlite3.connect(backup_path)
        src.backup(dst)
        dst.close()
        src.close()

        service   = self._get_service()
        folder_id = self._get_or_create_folder(service)

        media = MediaFileUpload(backup_path, mimetype='application/octet-stream')
        service.files().create(
            body={'name': backup_name, 'parents': [folder_id]},
            media_body=media,
            fields='id',
        ).execute()

        self._cleanup_local(keep=5)
        return backup_name

    # ------------------------------------------------------------------ #
    # LOCAL CLEANUP                                                        #
    # ------------------------------------------------------------------ #

    def _cleanup_local(self, keep=5):
        files = sorted([
            os.path.join(BACKUP_DIR, f)
            for f in os.listdir(BACKUP_DIR)
            if f.startswith('stock_backup_') and f.endswith('.db')
        ])
        for old in files[:-keep]:
            os.remove(old)

    # ------------------------------------------------------------------ #
    # AUTOMATIC CLOUD BACKUP                                               #
    # ------------------------------------------------------------------ #

    def start_auto_cloud_backup(self):
        """Start the background thread that uploads to Drive at CLOUD_BACKUP_TIMES."""
        if self._cloud_thread and self._cloud_thread.is_alive():
            return
        self._stop_cloud = False
        self._cloud_thread = threading.Thread(
            target=self._cloud_backup_loop, daemon=True, name="CloudAutoBackup"
        )
        self._cloud_thread.start()
        logging.info("Auto cloud backup started — scheduled at %s", CLOUD_BACKUP_TIMES)

    def stop_auto_cloud_backup(self):
        """Signal the auto-backup thread to stop."""
        self._stop_cloud = True
        logging.info("Auto cloud backup stopped")

    def is_auto_running(self) -> bool:
        return bool(self._cloud_thread and self._cloud_thread.is_alive())

    def _cloud_backup_loop(self):
        """Check every minute whether it is time to run a scheduled cloud backup."""
        done_today: set[str] = set()

        while not self._stop_cloud:
            try:
                now   = datetime.now()
                today = now.date()

                # Reset tracking at midnight
                if now.hour == 0 and now.minute == 0:
                    done_today.clear()

                current_hhmm = now.strftime("%H:%M")
                for slot in CLOUD_BACKUP_TIMES:
                    key = f"{today}_{slot}"
                    if current_hhmm == slot and key not in done_today:
                        done_today.add(key)  # mark before running to avoid duplicate attempts
                        if self.is_authenticated():
                            try:
                                name = self.run()
                                logging.info("Scheduled cloud backup completed: %s", name)
                            except Exception as e:
                                logging.error("Scheduled cloud backup failed: %s", e)
                        else:
                            logging.info("Scheduled cloud backup skipped — no account connected")

            except Exception as e:
                logging.error("Error in cloud backup loop: %s", e)

            time.sleep(60)
