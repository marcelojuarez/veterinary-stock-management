"""
Servicio de Actualización Automática
Consulta GitHub para verificar si hay una nueva versión disponible
y gestiona la descarga e instalación silenciosa.
"""

import os
import json
import logging
import hashlib
import tempfile
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
from packaging import version  # pip install packaging

logger = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────────────
# URL RAW del version.json en tu repositorio GitHub (rama main/master)
VERSION_JSON_URL = (
    "https://raw.githubusercontent.com/marcelojuarez/veterinary-stock-management/main/version.json"
)

# Archivo local que guarda la versión instalada actualmente.
# En desarrollo: root del proyecto. En frozen (PyInstaller --onefile): sys._MEIPASS root.
import sys as _sys
LOCAL_VERSION_FILE = (
    Path(_sys._MEIPASS) / "local_version.json"
    if getattr(_sys, "frozen", False)
    else Path(__file__).parent.parent / "local_version.json"
)

# Versión del ejecutable actual (se sincroniza con local_version.json al compilar)
CURRENT_VERSION = "1.0.0"
# ───────────────────────────────────────────────────────────────────────────────


class UpdateInfo:
    """Datos de la actualización disponible."""

    def __init__(self, data: dict):
        self.latest_version: str = data.get("version", "0.0.0")
        self.release_date: str = data.get("release_date", "")
        self.release_notes: str = data.get("release_notes", "")
        self.installer_url: str = data.get("installer_url", "")
        self.checksum_sha256: str = data.get("checksum_sha256", "")
        self.mandatory: bool = data.get("mandatory", False)

    def is_newer_than(self, current: str) -> bool:
        try:
            return version.parse(self.latest_version) > version.parse(current)
        except Exception:
            return False


class UpdateService:
    """
    Gestiona el ciclo completo de actualización:
      1. Consultar version.json remoto
      2. Comparar con versión local
      3. Descargar instalador si hay novedad
      4. Verificar checksum SHA-256
      5. Ejecutar instalador (cierra la app vieja automáticamente)
    """

    TIMEOUT_SECONDS = 10
    CHUNK_SIZE = 8192

    def __init__(self, current_version: str = CURRENT_VERSION):
        self.current_version = current_version
        self._download_thread: Optional[threading.Thread] = None
        self._cancel_download = threading.Event()

    # ── Chequeo remoto ─────────────────────────────────────────────────────────

    def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Consulta el version.json remoto.
        Retorna UpdateInfo si hay una versión más nueva, o None.
        Lanza excepción si no hay conexión (manejalo en el caller).
        """
        logger.info("Consultando actualizaciones en %s", VERSION_JSON_URL)
        try:
            req = urllib.request.Request(
                VERSION_JSON_URL,
                headers={"Cache-Control": "no-cache", "User-Agent": "StockManager-Updater/1.0"},
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            info = UpdateInfo(data)
            logger.info(
                "Versión remota: %s | Versión local: %s",
                info.latest_version,
                self.current_version,
            )

            if info.is_newer_than(self.current_version):
                logger.info("¡Nueva versión disponible!")
                return info

            logger.info("El sistema está actualizado.")
            return None

        except urllib.error.URLError as e:
            logger.warning("Sin conexión o URL inválida: %s", e)
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Error al parsear version.json: %s", e)
            return None

    # ── Descarga ───────────────────────────────────────────────────────────────

    def download_installer(
        self,
        update_info: UpdateInfo,
        progress_callback=None,
    ) -> Optional[Path]:
        """
        Descarga el instalador a una carpeta temporal.
        progress_callback(percent: int) se llama durante la descarga.
        Retorna la ruta al archivo descargado o None si falló/canceló.
        """
        self._cancel_download.clear()
        dest = Path(tempfile.gettempdir()) / f"StockManagerSetup_{update_info.latest_version}.exe"

        logger.info("Descargando instalador desde %s", update_info.installer_url)
        try:
            req = urllib.request.Request(
                update_info.installer_url,
                headers={"User-Agent": "StockManager-Updater/1.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                hasher = hashlib.sha256()

                with open(dest, "wb") as f:
                    while True:
                        if self._cancel_download.is_set():
                            logger.info("Descarga cancelada por el usuario.")
                            dest.unlink(missing_ok=True)
                            return None

                        chunk = resp.read(self.CHUNK_SIZE)
                        if not chunk:
                            break

                        f.write(chunk)
                        hasher.update(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total:
                            progress_callback(int(downloaded / total * 100))

            # ── Verificación de integridad ──────────────────────────────────
            if update_info.checksum_sha256:
                actual = hasher.hexdigest()
                if actual.lower() != update_info.checksum_sha256.lower():
                    logger.error(
                        "Checksum inválido. Esperado: %s | Obtenido: %s",
                        update_info.checksum_sha256,
                        actual,
                    )
                    dest.unlink(missing_ok=True)
                    return None
                logger.info("Checksum verificado correctamente.")
            else:
                logger.warning("No se proporcionó checksum; saltando verificación.")

            logger.info("Instalador descargado en %s", dest)
            return dest

        except Exception as e:
            logger.error("Error durante la descarga: %s", e)
            dest.unlink(missing_ok=True)
            return None

    def cancel_download(self):
        self._cancel_download.set()

    # ── Instalación ────────────────────────────────────────────────────────────

    def install_update(self, installer_path: Path):
        """
        Lanza un VBScript con wscript.exe que espera activamente a que el
        proceso StockManager.exe desaparezca del sistema antes de correr el
        instalador. Más robusto que un sleep fijo porque PyInstaller --onefile
        tiene un proceso bootstrap que puede demorar unos segundos en morir.
        Esta función NO retorna.
        """
        if not installer_path.exists():
            logger.error("No se encontró el instalador en %s", installer_path)
            return

        logger.info("Preparando actualización desde %s", installer_path)

        exe_name = "StockManager.exe"
        # Chr(34) = comilla doble en VBScript
        vbs_content = (
            'Set sh  = CreateObject("WScript.Shell")\n'
            'Set wmi = GetObject("winmgmts:{impersonationLevel=impersonate}!\\\\.\\root\\cimv2")\n'
            'Dim i\n'
            'For i = 0 To 60\n'
            '    WScript.Sleep 1000\n'
            f'    Set procs = wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name=\'{exe_name}\'")\n'
            '    If procs.Count = 0 Then Exit For\n'
            'Next\n'
            'WScript.Sleep 1000\n'
            f'sh.Run Chr(34) & "{installer_path}" & Chr(34)'
            ' & " /SILENT /NOCLOSEAPPLICATIONS", 0, False\n'
        )
        vbs_path = Path(tempfile.gettempdir()) / "stockmanager_update.vbs"
        vbs_path.write_text(vbs_content, encoding="ascii")

        subprocess.Popen(
            ["wscript.exe", str(vbs_path)],
            creationflags=subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        logger.info("Cerrando aplicación para completar la instalación...")
        os._exit(0)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def get_current_version() -> str:
        """Lee la versión desde local_version.json (generado al compilar)."""
        if LOCAL_VERSION_FILE.exists():
            try:
                with open(LOCAL_VERSION_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("version", CURRENT_VERSION)
            except Exception:
                pass
        return CURRENT_VERSION