
# -*- coding: utf-8 -*-
"""
Sistema de Backup Automático para Base de Datos SQLite
Proporciona múltiples estrategias de respaldo y recuperación
"""
import sqlite3
import shutil
import os
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import zipfile
import logging

Path("logs").mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    filename='logs/backup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class BackupService:
    """Servicio de backup automático para la base de datos"""
    
    def __init__(self, db_path, backup_dir='backups', config_path='config/backup_config.json'):
        """
        Inicializar el servicio de backup
        
        Args:
            db_path: Ruta a la base de datos principal
            backup_dir: Directorio donde se guardarán los backups
            config_path: Ruta al archivo de configuración
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.config_path = Path(config_path)
        
        # Crear directorios necesarios
        self.backup_dir.mkdir(exist_ok=True)
        
        # Cargar o crear configuración
        self.config = self.load_config()
        
        # Control del thread de backup automático
        self.backup_thread = None
        self.stop_backup = False
        
        logging.info(f"BackupService inicializado. DB: {self.db_path}")
    
    def load_config(self):
        """Cargar configuración de backup"""
        default_config = {
            "auto_backup_enabled": True,
            "backup_interval_minutes": 30,  # Backup cada 30 minutos
            "max_backups": 50,  # Mantener últimos 50 backups
            "compress_backups": True,
            "daily_backup_time": "02:00",  # Backup diario a las 2 AM
            "weekly_backup_day": 0,  # 0 = Lunes
            "retention_days": 30  # Mantener backups por 30 días
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Combinar con defaults por si faltan claves
                    return {**default_config, **config}
        except Exception as e:
            logging.error(f"Error cargando config: {e}")
        
        # Guardar configuración por defecto
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config=None):
        """Guardar configuración"""
        if config:
            self.config = config
        
        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logging.info("Configuración guardada")
        except Exception as e:
            logging.error(f"Error guardando config: {e}")
    
    def create_backup(self, backup_type="manual"):
        """
        Crear backup de la base de datos
        
        Args:
            backup_type: Tipo de backup ('manual', 'auto', 'daily', 'weekly')
        
        Returns:
            Path al archivo de backup creado o None si falla
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            
            # Verificar que la base de datos existe
            if not self.db_path.exists():
                logging.error(f"Base de datos no encontrada: {self.db_path}")
                return None
            
            # Usar el método de backup de SQLite (más seguro que shutil.copy)
            backup_file = self.backup_dir / f"{backup_name}.db"
            
            # Conexión a la base de datos original
            source_conn = sqlite3.connect(str(self.db_path))
            
            # Crear archivo de backup
            backup_conn = sqlite3.connect(str(backup_file))
            
            # Realizar backup usando el API de SQLite
            source_conn.backup(backup_conn)
            
            # Cerrar conexiones
            backup_conn.close()
            source_conn.close()
            
            # Comprimir si está habilitado
            if self.config.get('compress_backups', True):
                compressed_file = self.compress_backup(backup_file)
                if compressed_file:
                    backup_file.unlink()  # Eliminar archivo sin comprimir
                    backup_file = compressed_file
            
            # Información del backup
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            logging.info(f"Backup creado: {backup_file.name} ({size_mb:.2f} MB)")
            
            # Limpiar backups antiguos
            self.cleanup_old_backups()
            
            return backup_file
            
        except Exception as e:
            logging.error(f"Error creando backup: {e}")
            return None
    
    def compress_backup(self, backup_file):
        """Comprimir archivo de backup con ZIP"""
        try:
            zip_file = backup_file.with_suffix('.zip')
            
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(backup_file, backup_file.name)
            
            return zip_file
            
        except Exception as e:
            logging.error(f"Error comprimiendo backup: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """
        Restaurar base de datos desde un backup
        
        Args:
            backup_path: Ruta al archivo de backup
        
        Returns:
            True si la restauración fue exitosa
        """
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                logging.error(f"Backup no encontrado: {backup_path}")
                return False
            
            # Crear backup de seguridad antes de restaurar
            safety_backup = self.backup_dir / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if self.db_path.exists():
                shutil.copy2(self.db_path, safety_backup)
                logging.info(f"Backup de seguridad creado: {safety_backup}")
            
            # Descomprimir si es necesario
            restore_file = backup_path
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    # Extraer el primer archivo .db encontrado
                    for name in zf.namelist():
                        if name.endswith('.db'):
                            restore_file = self.backup_dir / 'temp_restore.db'
                            with open(restore_file, 'wb') as f:
                                f.write(zf.read(name))
                            break
            
            # Verificar integridad del backup
            if not self.verify_database_integrity(restore_file):
                logging.error("Backup corrupto, restauración cancelada")
                if restore_file != backup_path:
                    restore_file.unlink()
                return False
            
            # Restaurar
            shutil.copy2(restore_file, self.db_path)
            
            # Limpiar archivo temporal
            if restore_file != backup_path:
                restore_file.unlink()
            
            logging.info(f"Base de datos restaurada desde: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error restaurando backup: {e}")
            return False
    
    def verify_database_integrity(self, db_path):
        """Verificar integridad de una base de datos SQLite"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            
            is_ok = result[0] == 'ok'
            if is_ok:
                logging.info(f"Integridad verificada: {db_path}")
            else:
                logging.error(f"Integridad fallida: {db_path} - {result}")
            
            return is_ok
            
        except Exception as e:
            logging.error(f"Error verificando integridad: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Eliminar backups antiguos según configuración"""
        try:
            max_backups = self.config.get('max_backups', 50)
            retention_days = self.config.get('retention_days', 30)
            
            # Obtener todos los backups
            backups = sorted(
                self.backup_dir.glob('backup_*'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Eliminar por cantidad
            if len(backups) > max_backups:
                for backup in backups[max_backups:]:
                    backup.unlink()
                    logging.info(f"Backup eliminado (límite cantidad): {backup.name}")
            
            # Eliminar por antigüedad
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            for backup in backups:
                mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
                if mod_time < cutoff_date:
                    backup.unlink()
                    logging.info(f"Backup eliminado (antigüedad): {backup.name}")
            
        except Exception as e:
            logging.error(f"Error limpiando backups: {e}")
    
    def list_backups(self):
        """Listar todos los backups disponibles"""
        try:
            backups = []
            for backup_file in sorted(self.backup_dir.glob('backup_*'), reverse=True):
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size_mb': stat.st_size / (1024 * 1024),
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': stat.st_mtime
                })
            return backups
            
        except Exception as e:
            logging.error(f"Error listando backups: {e}")
            return []
    
    def start_auto_backup(self):
        """Iniciar servicio de backup automático"""
        if self.backup_thread and self.backup_thread.is_alive():
            logging.warning("Backup automático ya está ejecutándose")
            return
        
        self.stop_backup = False
        self.backup_thread = threading.Thread(target=self._auto_backup_loop, daemon=True)
        self.backup_thread.start()
        logging.info("Backup automático iniciado")
    
    def stop_auto_backup(self):
        """Detener servicio de backup automático"""
        self.stop_backup = True
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        logging.info("Backup automático detenido")
    
    def _auto_backup_loop(self):
        """Loop principal del backup automático"""
        interval_minutes = self.config.get('backup_interval_minutes', 30)
        interval_seconds = interval_minutes * 60
        
        while not self.stop_backup:
            try:
                # Crear backup automático
                self.create_backup(backup_type="auto")
                
                # Esperar el intervalo configurado
                for _ in range(int(interval_seconds)):
                    if self.stop_backup:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Error en loop de backup automático: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def get_status(self):
        """Obtener estado actual del servicio de backup"""
        try:
            backups = self.list_backups()
            total_size = sum(b['size_mb'] for b in backups)
            
            last_backup = backups[0] if backups else None
            
            return {
                'auto_backup_enabled': self.config.get('auto_backup_enabled', False),
                'is_running': self.backup_thread and self.backup_thread.is_alive(),
                'total_backups': len(backups),
                'total_size_mb': total_size,
                'last_backup': last_backup,
                'db_exists': self.db_path.exists(),
                'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0,
                'config': self.config
            }
            
        except Exception as e:
            logging.error(f"Error obteniendo estado: {e}")
            return {}


# Instancia global del servicio de backup
_backup_service = None

def get_backup_service(db_path=None):
    """Obtener instancia global del servicio de backup"""
    global _backup_service
    if _backup_service is None:
        from config.settings import DB_PATH
        _backup_service = BackupService(db_path or DB_PATH)
    return _backup_service


def initialize_backup_system(db_path=None, auto_start=True):
    """
    Inicializar el sistema de backup
    
    Args:
        db_path: Ruta a la base de datos
        auto_start: Si True, inicia el backup automático
    
    Returns:
        Instancia de BackupService
    """
    service = get_backup_service(db_path)
    
    if auto_start and service.config.get('auto_backup_enabled', True):
        service.start_auto_backup()
        logging.info("Sistema de backup inicializado y auto-backup iniciado")
    
    return service


if __name__ == "__main__":
    # Prueba del sistema de backup
    print("=== Sistema de Backup - Prueba ===")
    
    from config.settings import DB_PATH
    service = BackupService(DB_PATH)
    
    # Crear backup manual
    print("\n1. Creando backup manual...")
    backup_file = service.create_backup('manual')
    if backup_file:
        print(f"   ✓ Backup creado: {backup_file}")
    
    # Listar backups
    print("\n2. Listando backups...")
    backups = service.list_backups()
    for backup in backups[:5]:  # Mostrar últimos 5
        print(f"   • {backup['name']} - {backup['size_mb']:.2f} MB - {backup['date']}")
    
    # Estado del servicio
    print("\n3. Estado del servicio:")
    status = service.get_status()
    print(f"   • Backups totales: {status['total_backups']}")
    print(f"   • Tamaño total: {status['total_size_mb']:.2f} MB")
    print(f"   • BD existe: {status['db_exists']}")
    print(f"   • Tamaño BD: {status['db_size_mb']:.2f} MB")
    
    print("\n=== Prueba completada ===")