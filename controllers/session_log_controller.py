import logging
from datetime import datetime, timedelta
from tkinter import messagebox

logger = logging.getLogger(__name__)


class SessionLogController:
    def __init__(self, user_model):
        self.model = user_model
        self.view = None
        self.current_page = 0
        self.page_size = 50
        self._last_filters = {"from_date": None, "to_date": None, "username": None}

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
        page: int = 0,
    ) -> None:
        if not self.view:
            return
        self.current_page = page
        self._last_filters = {"from_date": from_date, "to_date": to_date, "username": username}
        offset = page * self.page_size
        rows, total = self.model.get_session_log(from_date, to_date, username, self.page_size, offset)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.view.refresh_table(rows)
        self.view.update_pagination(page, total_pages, total)

    def load_last_7_days(self) -> None:
        """Carga los últimos 7 días (carga inicial por defecto)."""
        from_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
        to_date   = datetime.now().strftime("%Y-%m-%d")
        if self.view:
            self.view.set_default_dates(from_date, to_date)
        self.load_log(from_date=from_date, to_date=to_date)

    def apply_filter(self, from_date: str, to_date: str, username: str) -> None:
        fd = from_date.strip() or None
        td = to_date.strip() or None
        us = username.strip() or None
        self.load_log(from_date=fd, to_date=td, username=us, page=0)

    def add_user_dialog(self) -> None:
        data = self.view.show_add_user_dialog()
        if data:
            success, message = self.model.add_new_user(data)
            if success:
                messagebox.showinfo("Éxito", f"Usuario '{data['username']}' creado correctamente.")
            else:
                messagebox.showerror("Error", message)

    def delete_user_dialog(self) -> None:
        users = self.model.get_all_users()
        if not users:
            messagebox.showwarning("Sin usuarios", "No hay usuarios registrados.")
            return
        data = self.view.show_delete_user_dialog(users)
        if data:
            if data["username"] == "admin":
                messagebox.showerror("Error", "El usuario 'admin' no puede ser eliminado.")
                return
            success, message = self.model.delete_user(data["username"])
            if success:
                messagebox.showinfo("Éxito", f"Usuario '{data['username']}' eliminado correctamente.")
            else:
                messagebox.showerror("Error", message)

    def clear_filter(self) -> None:
        """Limpia filtros y recarga los últimos 7 días."""
        self.load_last_7_days()

    def next_page(self) -> None:
        self.load_log(**self._last_filters, page=self.current_page + 1)

    def prev_page(self) -> None:
        if self.current_page > 0:
            self.load_log(**self._last_filters, page=self.current_page - 1)