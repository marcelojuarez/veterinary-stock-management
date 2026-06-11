import logging
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.view_helpers import center_window
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionLogView:
    """
    Vista de registro de sesiones.
    Se integra al notebook de App igual que las demás pestañas:

        from views.session_log_view import SessionLogView
        from controllers.session_log_controller import SessionLogController
        from models.user import User

        user_model = User()
        session_log_controller = SessionLogController(user_model)
        session_log_view = SessionLogView(self.notebook, session_log_controller)
        session_log_controller.set_view(session_log_view)
        self.notebook.add(session_log_view.frame, text='Sesiones')
        session_log_controller.load_last_7_days()
    """

    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")

        self.from_var    = tk.StringVar()
        self.to_var      = tk.StringVar()
        self.user_var    = tk.StringVar()
        self.count_var   = tk.StringVar(value="")

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_table_section()
        self._create_footer()

    # ------------------------------------------------------------------ #
    #  HEADER — título + filtros                                           #
    # ------------------------------------------------------------------ #
    def _create_header(self):
        header = ctk.CTkFrame(self.frame)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(9, weight=1)  # esta columna empuja todo hacia la derecha
        header.grid_columnconfigure(10, weight=0)
        header.grid_columnconfigure(11, weight=0)

        # Título
        ctk.CTkLabel(
            header,
            text="🔐 Registro de sesiones",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=15, pady=15)

        # Desde
        ctk.CTkLabel(
            header, text="Desde:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=1, padx=(15, 4))
        ctk.CTkEntry(
            header, textvariable=self.from_var,
            width=110, height=35, placeholder_text="AAAA-MM-DD"
        ).grid(row=0, column=2, padx=(0, 8))

        # Hasta
        ctk.CTkLabel(
            header, text="Hasta:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=3, padx=(0, 4))
        ctk.CTkEntry(
            header, textvariable=self.to_var,
            width=110, height=35, placeholder_text="AAAA-MM-DD"
        ).grid(row=0, column=4, padx=(0, 12))

        # Usuario
        ctk.CTkLabel(
            header, text="Usuario:", font=ctk.CTkFont(size=12)
        ).grid(row=0, column=5, padx=(0, 4))
        ctk.CTkEntry(
            header, textvariable=self.user_var,
            width=120, height=35, placeholder_text="Todos"
        ).grid(row=0, column=6, padx=(0, 12))

        # Botón Filtrar
        ctk.CTkButton(
            header,
            text="Filtrar",
            width=100, height=35,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_filter,
        ).grid(row=0, column=7, padx=4)

        # Botón Limpiar
        ctk.CTkButton(
            header,
            text="Limpiar",
            width=100, height=35,
            fg_color="#757575", hover_color="#616161",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_clear,
        ).grid(row=0, column=8, padx=4)

        # Contador de registros
        ctk.CTkLabel(
            header, textvariable=self.count_var,
            font=ctk.CTkFont(size=12),
            text_color="#555555",
        ).grid(row=0, column=9, padx=15)

        # Agregar nuevo usuario 
        ctk.CTkButton(
            header,
            text="Agregar nuevo usuario",
            width=100, height=35,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.controller.add_user_dialog,
        ).grid(row=0, column=10, padx=20) 
    
        ctk.CTkButton(
            header,
            text="Eliminar usuario",
            width=140, height=35,
            fg_color="#E74C3C", hover_color="#C0392B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.controller.delete_user_dialog,
        ).grid(row=0, column=11, padx=(0, 20), sticky="e")

    # ------------------------------------------------------------------ #
    #  TABLA                                                               #
    # ------------------------------------------------------------------ #
    def _create_table_section(self):
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            table_frame,
            text="📋 Historial de accesos",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(10, 5))

        # Estilo consistente con el resto del sistema
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "SessionLog.Treeview",
            background="#f9f9f9",
            fieldbackground="#f9f9f9",
            bordercolor="#d0d0d0",
            lightcolor="#d0d0d0",
            darkcolor="#d0d0d0",
            rowheight=22,
            font=("Segoe UI", 9),
        )
        style.configure(
            "SessionLog.Treeview.Heading",
            background="#e6e6e6",
            foreground="#000000",
            font=("Segoe UI", 9, "bold"),
        )
        style.map("SessionLog.Treeview.Heading",
                  background=[("active", "#dcdcdc")])

        cols = ("Usuario", "Inicio de sesión", "Cierre de sesión", "Duración", "Estado")
        self.table = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            height=18, style="SessionLog.Treeview"
        )

        col_specs = {
            "Usuario":           120,
            "Inicio de sesión":  180,
            "Cierre de sesión":  180,
            "Duración":          100,
            "Estado":            100,
        }
        for col, w in col_specs.items():
            self.table.column(col, width=w, anchor="center")
            self.table.heading(col, text=col, anchor="center")

        # Tags de color (mismo patrón que CustomersView)
        self.table.tag_configure("cerrada",  background="#E8F5E9")   # verde claro
        self.table.tag_configure("abierta",  background="#FFF9C4")   # amarillo claro
        self.table.tag_configure("abrupto",  background="#FFEBEE")   # rojo claro

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical",   command=self.table.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right",  fill="y")
        self.table.pack(fill="both", expand=True, padx=(10, 0))

    # ------------------------------------------------------------------ #
    #  FOOTER — tarjetas de resumen                                        #
    # ------------------------------------------------------------------ #
    def _create_footer(self):
        footer = ctk.CTkFrame(self.frame)
        footer.grid(row=2, column=0, padx=10, pady=(0, 15), sticky="ew")
        footer.grid_columnconfigure((0, 1, 2), weight=1)

        def make_card(col, title, bg, fg):
            card = ctk.CTkFrame(footer, fg_color=bg, corner_radius=10)
            card.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
            ctk.CTkLabel(
                card, text=title,
                font=ctk.CTkFont(size=11),
                text_color="#666666",
            ).pack(pady=(8, 2))
            lbl = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=fg,
            )
            lbl.pack(pady=(0, 8))
            return lbl

        self._lbl_total    = make_card(0, "Total sesiones",      "#f5f5f5", "#333333")
        self._lbl_cerradas = make_card(1, "Sesiones cerradas",   "#e8f5e9", "#2E7D32")
        self._lbl_abiertas = make_card(2, "Sesiones sin cerrar", "#fff9c4", "#F57F17")

        # Paginación
        nav_frame = ctk.CTkFrame(footer, fg_color="transparent")
        nav_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10))

        self._btn_prev = ctk.CTkButton(
            nav_frame, text="← Anterior", width=120, height=30,
            fg_color="#757575", hover_color="#616161",
            font=ctk.CTkFont(size=12),
            command=self.controller.prev_page,
        )
        self._btn_prev.grid(row=0, column=0, padx=10)

        self._lbl_page = ctk.CTkLabel(
            nav_frame, text="Página 1 de 1",
            font=ctk.CTkFont(size=12),
        )
        self._lbl_page.grid(row=0, column=1, padx=20)

        self._btn_next = ctk.CTkButton(
            nav_frame, text="Siguiente →", width=120, height=30,
            fg_color="#757575", hover_color="#616161",
            font=ctk.CTkFont(size=12),
            command=self.controller.next_page,
        )
        self._btn_next.grid(row=0, column=2, padx=10)

    # ------------------------------------------------------------------ #
    #  MÉTODOS PÚBLICOS (llamados desde el controlador)                   #
    # ------------------------------------------------------------------ #
    def set_default_dates(self, from_date: str, to_date: str) -> None:
        self.from_var.set(from_date)
        self.to_var.set(to_date)

    def refresh_table(self, rows: list) -> None:
        """
        Recibe lista de tuplas (id, user_id, username, login_at, logout_at)
        y pinta la tabla.
        """
        for item in self.table.get_children():
            self.table.delete(item)

        total = len(rows)
        cerradas = 0
        abiertas = 0

        for row in rows:
            _, _uid, username, login_at, logout_at = row

            login_fmt  = self._fmt_dt(login_at)
            logout_fmt = self._fmt_dt(logout_at) if logout_at else "—"
            duracion   = self._calc_duration(login_at, logout_at)

            if logout_at:
                estado = "Cerrada"
                tag    = "cerrada"
                cerradas += 1
            else:
                estado = "Abierta / no cerrada"
                tag    = "abierta"
                abiertas += 1

            self.table.insert(
                "", "end",
                values=(username, login_fmt, logout_fmt, duracion, estado),
                tags=(tag,),
            )

        # Actualizar contador y tarjetas
        self._lbl_total.configure(text=str(total))
        self._lbl_cerradas.configure(text=str(cerradas))
        self._lbl_abiertas.configure(text=str(abiertas))

    # ------------------------------------------------------------------ #
    #  HELPERS PRIVADOS                                                    #
    # ------------------------------------------------------------------ #
    def _on_filter(self) -> None:
        self.controller.apply_filter(
            self.from_var.get(),
            self.to_var.get(),
            self.user_var.get(),
        )

    def _on_clear(self) -> None:
        self.user_var.set("")
        self.controller.clear_filter()

    @staticmethod
    def _fmt_dt(dt_str: str) -> str:
        if not dt_str:
            return "—"
        return dt_str[:16]  # "AAAA-MM-DD HH:MM"

    @staticmethod
    def _calc_duration(login_at: str, logout_at: str | None) -> str:
        if not logout_at:
            return "—"
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            diff = datetime.strptime(logout_at, fmt) - datetime.strptime(login_at, fmt)
            total_min = int(diff.total_seconds() // 60)
            h, m = divmod(total_min, 60)
            return f"{h}h {m}m" if h else f"{m}m"
        except Exception:
            return "—"

    def show_add_user_dialog(self) -> dict | None:
        width_win, height_win = 450, 340
        win = ctk.CTkToplevel(self.frame)
        win.configure(fg_color="#e0e0e0")
        win.title("Agregar nuevo usuario")
        win.transient(self.frame)
        win.grab_set()
        center_window(win, width_win, height_win)

        username_var = ctk.StringVar()
        password_var = ctk.StringVar()
        result       = {}

        # Card principal
        card_frame = ctk.CTkFrame(win, fg_color="white", corner_radius=20)
        card_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card_frame,
            text="Registrar Nuevo Usuario",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(20, 10))

        # Formulario
        form_frame = ctk.CTkFrame(card_frame, fg_color="#f9f9f9", corner_radius=10)
        form_frame.pack(pady=10, padx=20, fill="x")

        def add_field(row, label, widget):
            ctk.CTkLabel(
                form_frame, text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="black",
            ).grid(row=row, column=0, sticky="e", padx=(10, 10), pady=7)
            widget.grid(row=row, column=1, sticky="w", padx=(10, 10), pady=7)

        add_field(0, "Usuario:",
                ctk.CTkEntry(form_frame, textvariable=username_var, width=200))
        add_field(1, "Contraseña:",
                ctk.CTkEntry(form_frame, textvariable=password_var, width=200, show="*"))
        # Botones
        btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        btn_frame.pack(pady=15)

        def save_and_close():
            if not username_var.get().strip() or not password_var.get().strip():
                messagebox.showwarning("Campos vacíos",
                                    "Usuario y contraseña son obligatorios.",
                                    parent=win)
                return
            result["username"] = username_var.get().strip().lower()
            result["password"] = password_var.get().strip()
            cleanup_and_close()

        def cleanup_and_close():
            try:
                if win.winfo_exists():
                    win.unbind("<Return>")
                    win.grab_release()
                win.destroy()
            except Exception:
                pass

        save_btn = ctk.CTkButton(
            btn_frame, text="Guardar",
            width=150, height=40,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save_and_close,
        )
        save_btn.grid(row=0, column=0, padx=15)

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            width=150, height=40,
            fg_color="#E74C3C", hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=cleanup_and_close,
        ).grid(row=0, column=1, padx=15)

        def on_enter(event):
            if win.winfo_exists():
                save_btn.invoke()

        win.bind("<Return>", on_enter)
        win.protocol("WM_DELETE_WINDOW", cleanup_and_close)

        self.frame.wait_window(win)
        return result if result else None


    def show_delete_user_dialog(self, users: list) -> str | None:
        width_win, height_win = 450, 250
        win = ctk.CTkToplevel(self.frame)
        win.configure(fg_color="#e0e0e0")
        win.title("Eliminar usuario")
        win.transient(self.frame)
        win.grab_set()
        center_window(win, width_win, height_win)

        usernames = [row[0] for row in users]
        selected_var = ctk.StringVar(value=usernames[0] if usernames else "")
        result = {}

        card_frame = ctk.CTkFrame(win, fg_color="white", corner_radius=20)
        card_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card_frame, text="Eliminar Usuario",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(20, 10))

        form_frame = ctk.CTkFrame(card_frame, fg_color="#f9f9f9", corner_radius=10)
        form_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(
            form_frame, text="Usuario:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="black",
        ).grid(row=0, column=0, sticky="e", padx=10, pady=7)

        ctk.CTkComboBox(
            form_frame, values=usernames,
            variable=selected_var, width=200,
            state="readonly",
        ).grid(row=0, column=1, sticky="w", padx=10, pady=7)

        btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        btn_frame.pack(pady=15)

        def confirm_and_close():
            if not selected_var.get():
                messagebox.showwarning("Sin selección", "Seleccioná un usuario.", parent=win)
                return
            if not messagebox.askyesno(
                "Confirmar", f"¿Eliminar al usuario '{selected_var.get()}'?", parent=win
            ):
                return
            result["username"] = selected_var.get()
            cleanup_and_close()

        def cleanup_and_close():
            try:
                if win.winfo_exists():
                    win.grab_release()
                win.destroy()
            except Exception:
                pass

        ctk.CTkButton(
            btn_frame, text="Eliminar",
            width=150, height=40,
            fg_color="#E74C3C", hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=confirm_and_close,
        ).grid(row=0, column=0, padx=15)

        ctk.CTkButton(
            btn_frame, text="Cancelar",
            width=150, height=40,
            fg_color="#757575", hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=cleanup_and_close,
        ).grid(row=0, column=1, padx=15)

        win.protocol("WM_DELETE_WINDOW", cleanup_and_close)
        self.frame.wait_window(win)
        return result if result else None

    def update_pagination(self, page: int, total_pages: int, total: int) -> None:
        self._lbl_page.configure(text=f"Página {page + 1} de {total_pages}")
        self._btn_prev.configure(state="normal" if page > 0 else "disabled")
        self._btn_next.configure(state="normal" if page < total_pages - 1 else "disabled")
        self.count_var.set(f"{total} registro{'s' if total != 1 else ''}")