"""
Sistema de Gestión Veterinaria - Punto de entrada principal
"""
import logging
import os
import threading
import tkinter as tk

from views.main_view import App
from services.backup_service import initialize_backup_system
from services.update_service import UpdateService
from views.update_dialog import UpdateDialog

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


# ── Chequeo de actualizaciones ─────────────────────────────────────────────────

def check_updates_async(app_root: tk.Tk):
    """
    Corre el chequeo de versión en un hilo secundario para no bloquear
    la apertura de la UI. Si hay update disponible, muestra el diálogo
    en el hilo principal de Tkinter mediante `after`.
    """
    update_service = UpdateService(current_version=UpdateService.get_current_version())

    def _worker():
        try:
            update_info = update_service.check_for_updates()
            if update_info:
                # Programar el diálogo en el hilo de Tk
                app_root.after(0, lambda: _show_update_dialog(app_root, update_info, update_service))
            else:
                logger.info("No hay actualizaciones disponibles.")
        except Exception as e:
            logger.warning("No se pudo verificar actualizaciones: %s", e)

    thread = threading.Thread(target=_worker, daemon=True, name="UpdateChecker")
    thread.start()


def _show_update_dialog(root: tk.Tk, update_info, service: UpdateService):
    """Muestra el diálogo modal de actualización en el hilo principal."""
    current = UpdateService.get_current_version()
    dialog = UpdateDialog(
        parent=root,
        update_info=update_info,
        current_version=current,
        service=service,
        on_postpone=lambda: logger.info("Usuario pospuso la actualización."),
    )
    dialog.wait_window()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    try:
        logger.info("=" * 60)
        logger.info("Iniciando aplicación...")

        # ── Sistema de backups ─────────────────────────────────────────────
        logger.info("Inicializando sistema de backups...")
        backup_service = initialize_backup_system(
            db_path="db/stock.db",
            auto_start=True,
        )
        logger.info(
            "Backups inicializados - Auto-backup: %s",
            backup_service.config.get("auto_backup_enabled"),
        )

        # ── Interfaz gráfica ───────────────────────────────────────────────
        logger.info("Creando interfaz gráfica...")
        app = App()

        # ── Chequeo de actualizaciones (no bloquea la UI) ──────────────────
        # Se ejecuta después de que la ventana principal esté visible.
        # 1500 ms de delay para que la app cargue completamente antes del popup.
        app.root.after(1500, lambda: check_updates_async(app.root))

        logger.info("Aplicación iniciada correctamente.")
        logger.info("=" * 60)

        # ── Loop principal ─────────────────────────────────────────────────
        app.run()

        # ── Cierre limpio ──────────────────────────────────────────────────
        logger.info("Cerrando aplicación...")
        backup_service.stop_auto_backup()
        logger.info("Sistema de backups detenido.")

    except Exception as e:
        logger.error("Error crítico en la aplicación: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()