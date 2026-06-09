import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionLogController:
    def __init__(self, user_model):
        self.model = user_model
        self.view = None

    def set_view(self, view):
        self.view = view

    # ------------------------------------------------------------------ #
    #  CARGA / FILTRADO                                                    #
    # ------------------------------------------------------------------ #
    def load_log(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        username: str | None = None,
    ) -> None:
        """Obtiene filas del modelo y las envía a la vista."""
        if not self.view:
            return
        rows = self.model.get_session_log(from_date, to_date, username)
        self.view.refresh_table(rows)

    def load_last_7_days(self) -> None:
        """Carga los últimos 7 días (carga inicial por defecto)."""
        from_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
        to_date   = datetime.now().strftime("%Y-%m-%d")
        if self.view:
            self.view.set_default_dates(from_date, to_date)
        self.load_log(from_date=from_date, to_date=to_date)

    def apply_filter(self, from_date: str, to_date: str, username: str) -> None:
        """Llamado desde la vista al presionar Filtrar."""
        fd = from_date.strip() or None
        td = to_date.strip() or None
        us = username.strip() or None
        self.load_log(from_date=fd, to_date=td, username=us)

    def clear_filter(self) -> None:
        """Limpia filtros y recarga los últimos 7 días."""
        self.load_last_7_days()