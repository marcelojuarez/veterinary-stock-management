"""
Sistema de Gestión Veterinaria - Punto de entrada principal
"""
import logging
import os

from views.main_view import App
from services.backup_service import initialize_backup_system
from config.settings import DB_PATH

# ── Logging ────────────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


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

        # ── Interfaz gráfica ───────────────────────────────────────────────
        # El chequeo de actualizaciones se dispara dentro de App.load_system(),
        # después del login, cuando la ventana principal ya está visible.
        logger.info("Creando interfaz gráfica...")
        app = App()

        logger.info("Aplicación iniciada correctamente.")
        logger.info("=" * 60)

        app.run()

        logger.info("Cerrando aplicación...")
        backup_service.stop_auto_backup()
        logger.info("Sistema de backups detenido.")

    except Exception as e:
        logger.error("Error crítico en la aplicación: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()