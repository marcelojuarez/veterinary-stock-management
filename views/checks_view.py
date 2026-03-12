"""
Vista de gestión de cheques/eCheq en cartera.
Permite ver cheques EN_CARTERA, COBRADO, ENDOSADO, RECHAZADO,
cambiar su estado y endosarlos a compras de proveedores.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.view_helpers import center_window
from decimal import Decimal

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Colores por estado
STATUS_COLORS = {
    "EN_CARTERA": "#1565C0",   # azul
    "COBRADO":    "#2E7D32",   # verde
    "ENDOSADO":   "#6D4C41",   # marrón
    "RECHAZADO":  "#C62828",   # rojo
}

STATUS_LABELS = {
    "EN_CARTERA": "🟦 EN CARTERA",
    "COBRADO":    "🟩 COBRADO",
    "ENDOSADO":   "🟫 ENDOSADO",
    "RECHAZADO":  "🟥 RECHAZADO",
}


class ChecksView:
    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")

        self.filter_var = ctk.StringVar(value="EN_CARTERA")

        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_stats_bar()
        self._create_table()
        self._create_footer()

    # ----------------------------------------------------------------
    # HEADER
    # ----------------------------------------------------------------
    def _create_header(self):
        header = ctk.CTkFrame(self.frame)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="🏦 Cartera de Cheques",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        # Filtro por estado
        filter_frame = ctk.CTkFrame(header, fg_color="transparent")
        filter_frame.grid(row=0, column=2, padx=15, pady=8)

        ctk.CTkLabel(filter_frame, text="Filtrar:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 6))

        ctk.CTkComboBox(
            filter_frame,
            variable=self.filter_var,
            values=["TODOS", "EN_CARTERA", "COBRADO", "ENDOSADO", "RECHAZADO"],
            width=160,
            command=lambda _: self.controller.load_checks(self.filter_var.get())
        ).pack(side="left")

    # ----------------------------------------------------------------
    # STATS BAR
    # ----------------------------------------------------------------
    def _create_stats_bar(self):
        stats_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._stats_cards = {}
        specs = [
            ("en_cartera_count", "EN CARTERA",     "#1565C0", "#E3F2FD"),
            ("en_cartera_total", "TOTAL CARTERA $", "#2E7D32", "#E8F5E9"),
            ("cobrado_count",    "COBRADOS",        "#F57F17", "#FFFDE7"),
            ("endosado_count",   "ENDOSADOS",       "#6D4C41", "#EFEBE9"),
        ]
        for col, (key, label, fg, bg) in enumerate(specs):
            card = ctk.CTkFrame(stats_frame, fg_color=bg, corner_radius=10)
            card.grid(row=0, column=col, padx=6, sticky="ew")
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(size=11), text_color="#555").pack(pady=(8, 2))
            val_lbl = ctk.CTkLabel(card, text="—",
                                   font=ctk.CTkFont(size=16, weight="bold"),
                                   text_color=fg)
            val_lbl.pack(pady=(0, 8))
            self._stats_cards[key] = val_lbl

    # ----------------------------------------------------------------
    # TABLA
    # ----------------------------------------------------------------
    def _create_table(self):
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=2, column=0, padx=10, pady=4, sticky="nsew")
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(table_frame, text="📋 Cheques",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Checks.Treeview",
                         background="#f9f9f9", fieldbackground="#f9f9f9",
                         rowheight=22, font=("Segoe UI", 8))
        style.configure("Checks.Treeview.Heading",
                         background="#e6e6e6", foreground="#000",
                         font=("Segoe UI", 9, "bold"))
        style.map("Checks.Treeview.Heading", background=[("active", "#dcdcdc")])

        cols = ("ID", "Número", "Banco", "Tipo",
                "Monto", "Emisión", "Vencimiento", "Estado", "Cliente")
        self.table = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            height=14, style="Checks.Treeview"
        )

        widths = {
            "ID": 40, "Número": 110, "Banco": 150, "Tipo": 65,
            "Monto": 90, "Emisión": 85,
            "Vencimiento": 90, "Estado": 95, "Cliente": 170,
        }
        for col in cols:
            self.table.column(col, anchor="center", width=widths.get(col, 100))
            self.table.heading(col, text=col, anchor="center")

        # Tags de color por estado
        self.table.tag_configure("EN_CARTERA", background="#E3F2FD")
        self.table.tag_configure("COBRADO",    background="#E8F5E9")
        self.table.tag_configure("ENDOSADO",   background="#EFEBE9")
        self.table.tag_configure("RECHAZADO",  background="#FFEBEE")

        sy = ttk.Scrollbar(table_frame, orient="vertical",   command=self.table.yview)
        sx = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sx.pack(side="bottom", fill="x")
        sy.pack(side="right",  fill="y")
        self.table.pack(fill="both", expand=True, padx=(10, 0))

    # ----------------------------------------------------------------
    # FOOTER BUTTONS
    # ----------------------------------------------------------------
    def _create_footer(self):
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.grid(row=3, column=0, padx=10, pady=12, sticky="ew")
        footer.grid_columnconfigure((0, 1, 2), weight=1)
        W, H = 200, 38

        ctk.CTkButton(
            footer, text="✅ Marcar Cobrado", width=W, height=H,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_cobrar
        ).grid(row=0, column=0, padx=8)

        '''
        ctk.CTkButton(
            footer, text="🏭 Endosar a proveedor", width=W, height=H,
            fg_color="#6D4C41", hover_color="#5D4037",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_endosar
        ).grid(row=0, column=1, padx=8)
        '''

        ctk.CTkButton(
            footer, text="❌ Marcar Rechazado", width=W, height=H,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_rechazar
        ).grid(row=0, column=1, padx=8)

        ctk.CTkButton(
            footer, text="🔄 Actualizar", width=W, height=H,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.controller.load_checks(self.filter_var.get())
        ).grid(row=0, column=2, padx=8)

    # ----------------------------------------------------------------
    # ACCIONES
    # ----------------------------------------------------------------
    def _get_selected_check(self):
        sel = self.table.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un cheque primero.")
            return None
        item = self.table.item(sel[0])
        check_id = item["values"][0]
        # Los tags contienen el status raw (EN_CARTERA, COBRADO, etc.)
        tags = item.get("tags", ())
        raw_status = tags[0] if tags else ""
        return check_id, raw_status

    def _on_cobrar(self):
        res = self._get_selected_check()
        if not res:
            return
        check_id, status = res
        if status != "EN_CARTERA":
            messagebox.showwarning("Atención",
                f"Solo se puede cobrar un cheque EN_CARTERA (estado actual: {status}).")
            return
        if messagebox.askyesno("Confirmar", "¿Marcar este cheque como COBRADO?"):
            self.controller.mark_cobrado(check_id)

    def _on_endosar(self):
        res = self._get_selected_check()
        if not res:
            return
        check_id, status = res
        if status != "EN_CARTERA":
            messagebox.showwarning("Atención",
                f"Solo se puede endosar un cheque EN_CARTERA (estado actual: {status}).")
            return
        self._open_endorse_window(check_id)

    def _on_rechazar(self):
        res = self._get_selected_check()
        if not res:
            return
        check_id, status = res
        if status not in ("EN_CARTERA", "ENDOSADO"):
            messagebox.showwarning("Atención", "No se puede rechazar en este estado.")
            return
        if messagebox.askyesno("Confirmar", "¿Marcar este cheque como RECHAZADO?"):
            self.controller.mark_rechazado(check_id)

    def _open_endorse_window(self, check_id):
        """Ventana para elegir a qué compra de proveedor se endosa."""
        purchases = self.controller.get_open_purchases()
        if not purchases:
            messagebox.showinfo("Sin compras", "No hay compras abiertas a proveedores.")
            return

        win = ctk.CTkToplevel(self.frame)
        win.title("Endosar cheque a proveedor")
        win.transient(self.frame)
        win.grab_set()
        center_window(win, 600, 600)

        ctk.CTkLabel(win, text="Seleccione la compra de proveedor:",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 8))

        cols = ("ID. C", "Proveedor", "Fecha", "Total", "Pendiente")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=10)
        for col, w in zip(cols, [50, 200, 130, 110, 120]):
            tree.column(col, width=w, anchor="center")
            tree.heading(col, text=col)
        for p in purchases:
            tree.insert("", "end", values=p)
        tree.pack(fill="both", expand=True, padx=16, pady=4)

        def confirm():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Atención", "Seleccione una compra.")
                return
            purchase_id = tree.item(sel[0])["values"][0]
            self.controller.endorse_check(check_id, purchase_id)
            win.destroy()

        btn_f = ctk.CTkFrame(win, fg_color="transparent")
        btn_f.pack(pady=12)
        ctk.CTkButton(btn_f, text="Endosar", fg_color="#6D4C41", hover_color="#5D4037", font=ctk.CTkFont(size=12, weight="bold"), height=30, width=100,
                      command=confirm).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_f, text="Cancelar", fg_color="#757575", hover_color="#616161", font=ctk.CTkFont(size=12, weight="bold"), height=30, width=100, 
                      command=win.destroy).grid(row=0, column=1, padx=10)

    # ----------------------------------------------------------------
    # REFRESH
    # ----------------------------------------------------------------
    def refresh_table(self, checks):
        for row in self.table.get_children():
            self.table.delete(row)

        for c in checks:
            # c: id, number, bank, type, amount, issue_date,
            #    due_date, status, origin, client_payment_id, purchase_id, notes, client_name
            status = c[7]
            display = STATUS_LABELS.get(status, status)
            client_name = c[12] or "—"
            self.table.insert("", "end", tags=(status,), values=(
                c[0],                       # ID
                c[1],                       # Número
                c[2],                       # Banco
                c[3],                       # Tipo
                f"${c[4]}",                 # Monto
                c[5],                       # Emisión
                c[6],                       # Vencimiento
                display,                    # Estado
                client_name,                # Cliente
            ))

    def update_stats(self, checks):
        en_cartera = [c for c in checks if c[7] == "EN_CARTERA"]
        cobrados   = [c for c in checks if c[7] == "COBRADO"]
        endosados  = [c for c in checks if c[7] == "ENDOSADO"]

        total_cartera = sum(Decimal(c[4]) for c in en_cartera)

        self._stats_cards["en_cartera_count"].configure(text=str(len(en_cartera)))
        self._stats_cards["en_cartera_total"].configure(text=f"${total_cartera:.2f}")
        self._stats_cards["cobrado_count"].configure(text=str(len(cobrados)))
        self._stats_cards["endosado_count"].configure(text=str(len(endosados)))

    def show_success(self, msg): messagebox.showinfo("Éxito", msg)
    def show_error(self,   msg): messagebox.showerror("Error", msg)
    def show_warning(self, msg): messagebox.showwarning("Atención", msg)