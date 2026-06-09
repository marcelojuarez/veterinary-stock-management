"""
Sistema de Gestión Veterinaria - Punto de entrada principal
"""
import logging
import os
import sys

# ── Logging (must run before any import that uses logging) ────────────────────
def _get_writable_logs_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.environ.get('LOCALAPPDATA', '.'), 'StockManager', 'logs')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

_logs_dir = _get_writable_logs_dir()
os.makedirs(_logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(_logs_dir, "app.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

from views.main_view import App
from services.backup_service import initialize_backup_system
from services.cloud_backup_service import CloudBackupService
from config.settings import DB_PATH


def main():
    try:
        logger.info("=" * 60)
        logger.info("Iniciando aplicación...")

        # ── Sistema de backups ─────────────────────────────────────────────
        logger.info("Inicializando sistema de backups...")
        backup_service = initialize_backup_system(
            db_path=DB_PATH,
            auto_start=True,
        )
        logger.info(
            "Backups inicializados - Auto-backup: %s",
            backup_service.config.get("auto_backup_enabled"),
        )

        # ── Backup en la nube ──────────────────────────────────────────────
        cloud_service = CloudBackupService()
        if cloud_service.is_authenticated():
            cloud_service.start_auto_cloud_backup()
            logger.info("Auto cloud backup iniciado.")
        else:
            logger.info("Cloud backup no configurado — se omite auto backup en Drive.")

        # ── Interfaz gráfica ───────────────────────────────────────────────
        logger.info("Creando interfaz gráfica...")
        app = App(cloud_service=cloud_service)

        logger.info("Aplicación iniciada correctamente.")
        logger.info("=" * 60)

        app.run()

        logger.info("Cerrando aplicación...")
        backup_service.stop_auto_backup()
        cloud_service.stop_auto_cloud_backup()
        logger.info("Sistema de backups detenido.")

    except Exception as e:
        logger.error("Error crítico en la aplicación: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()