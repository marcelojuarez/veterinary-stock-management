
"""
Sistema de Gestión - Punto de entrada principal
"""
from views.main_view import App
from services.backup_service import initialize_backup_system
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Función principal"""
    try:
        # Crear directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        logger.info("=" * 60)
        logger.info("Iniciando aplicación...")
        
        # Inicializar sistema de backups
        logger.info("Inicializando sistema de backups...")
        backup_service = initialize_backup_system(
            db_path='db/stock.db',
            auto_start=True  # Iniciar backups automáticos
        )
        logger.info(f"Sistema de backups inicializado - Auto-backup: {backup_service.config.get('auto_backup_enabled')}")
        
        # Crear aplicación
        logger.info("Creando interfaz gráfica...")
        app = App()
        
        logger.info("Aplicación iniciada correctamente")
        logger.info("=" * 60)
        
        # Ejecutar aplicación
        app.run()
        
        # Detener backups al cerrar
        logger.info("Cerrando aplicación...")
        backup_service.stop_auto_backup()
        logger.info("Sistema de backups detenido")
        
    except Exception as e:
        logger.error(f"Error crítico en la aplicación: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()