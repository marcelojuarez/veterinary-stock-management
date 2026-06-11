import logging
from datetime import datetime
from utils.view_helpers import show_warning, show_error
from db.database import db
from models.security import gen_password

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

    def add_new_user(self, user_data: dict) -> tuple[bool, str]:
        try:
            existing = self.get_user_by_username(user_data["username"])
            if existing:
                return False, f"El usuario '{user_data['username']}' ya existe."

            hashed = gen_password(user_data["password"])
            query = "INSERT INTO user (username, password_hash) VALUES (?, ?)"
            self.db.execute_query(query, (user_data["username"], hashed))
            return True, "OK"

        except Exception as e:
            logger.error("Error al agregar usuario: %s", e)
            return False, str(e)
        
    def get_all_users(self) -> list:
        try:
            return self.db.fetch_all("SELECT username FROM user", []) or []
        except Exception as e:
            logger.error("Error obteniendo usuarios: %s", e)
            return []

    def delete_user(self, username: str) -> tuple[bool, str]:
        try:
            existing = self.get_user_by_username(username)
            if not existing:
                return False, f"El usuario '{username}' no existe."
            
            self.db.execute_query("DELETE FROM user WHERE username = ?", (username,))
            return True, "OK"
        except Exception as e:
            logger.error("Error al eliminar usuario: %s", e)
            return False, str(e)
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
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int]:
        try:
            base = "FROM session_log WHERE 1=1"
            params: list = []

            if from_date:
                base += " AND DATE(login_at) >= ?"
                params.append(from_date)
            if to_date:
                base += " AND DATE(login_at) <= ?"
                params.append(to_date)
            if username and username.strip():
                base += " AND username LIKE ?"
                params.append(f"%{username.strip()}%")

            total = self.db.fetch_one(f"SELECT COUNT(*) {base}", params)[0]

            query = f"SELECT id, user_id, username, login_at, logout_at {base} ORDER BY login_at DESC LIMIT ? OFFSET ?"
            rows = self.db.fetch_all(query, params + [limit, offset]) or []

            return rows, total
        except Exception as e:
            logger.error("Error obteniendo session log: %s", e)
            return [], 0