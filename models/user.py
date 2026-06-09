import logging
from datetime import datetime
from utils.view_helpers import show_warning, show_error
from db.database import db

logger = logging.getLogger(__name__)


class User:
    def __init__(self, db_connection=None):
        self.db = db_connection or db

    ## -- Autenticacion -- ##
    def authenticate(self, username: str, password: str):
        """
        Verifica credenciales con argon2.
        """
        try:
            from models.security import validate_password
            user = self.get_user_by_username(username)
            print(f'user: {user}')
            if not user:
                show_error("El usuario ingresado no existe")
                return None
            if validate_password(password, user[2]):  
                return { 'id': user[0], 'username': user[1]}
            
            show_warning("Contraseña Incorrecta")
            return None
        except Exception as e:
            logger.error("Error autenticando usuario: %s", e)
            return None

    def get_user_by_username(self, username: str):
        try:
            return self.db.fetch_one(
                "SELECT * FROM user WHERE username = ?", (username,)
            )
        except Exception as e:
            logger.error("Error buscando usuario: %s", e)
            return None

    def add_new_user(self, user_data: dict):
        query = """
            INSERT INTO user (username, password_hash)
            VALUES (?, ?)
        """
        return self.db.execute_query(
            query, (user_data["username"], user_data["password"])
        )

    ## -- Registro de sesiones -- ##
    
    def register_login(self, user_id: int, username: str) -> int | None:
        """
        Inserta una fila en session_log con login_at = ahora.
        Devuelve el id generado (usado después para registrar logout).
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = """
                INSERT INTO session_log (user_id, username, login_at)
                VALUES (?, ?, ?)
            """
            params = [user_id, username, now]

            session_id = self.db.execute_query(query, params)
            logger.info("Login registrado — user=%s session_id=%s", username, session_id)
            return session_id
        except Exception as e:
            logger.error("Error registrando login: %s", e)
            return None

    def register_logout(self, session_id: int) -> None:
        """Completa la sesión con logout_at = ahora."""
        if not session_id:
            return
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute_query(
                "UPDATE session_log SET logout_at = ? WHERE id = ?",
                (now, session_id),
            )
            logger.info("Logout registrado — session_id=%s", session_id)
        except Exception as e:
            logger.error("Error registrando logout: %s", e)

    def get_session_log(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        username: str | None = None,
    ) -> list:
        """
        Devuelve filas de session_log según filtros opcionales.
        Cada fila: (id, user_id, username, login_at, logout_at)
        """
        try:
            query = "SELECT id, user_id, username, login_at, logout_at FROM session_log WHERE 1=1"
            params: list = []

            if from_date:
                query += " AND DATE(login_at) >= ?"
                params.append(from_date)
            if to_date:
                query += " AND DATE(login_at) <= ?"
                params.append(to_date)
            if username and username.strip():
                query += " AND username LIKE ?"
                params.append(f"%{username.strip()}%")

            query += " ORDER BY login_at DESC"
            return self.db.fetch_all(query, params) or []
        except Exception as e:
            logger.error("Error obteniendo session log: %s", e)
            return []