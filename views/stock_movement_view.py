import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from utils.utils import traditional_to_iso, iso_to_traditional
from utils.view_helpers import center_window


EVENT_LABELS = {
    'COMPRA':       '🛒 Compra',
    'VENTA':        '🧾 Venta',
    'PRECIO':       '✏️ Precio',
    'PRECIO_MASIVO':'📈 Precio masivo',
}

EVENT_COLORS = {
    'COMPRA':       '#E3F2FD',
    'VENTA':        '#E8F5E9',
    'PRECIO':       '#FFF3E0',
    'PRECIO_MASIVO':'#F3E5F5',
}


class StockMovementView:
    def __init__(self, movement_model):
        self.movement = movement_model

    # ------------------------------------------------------------------ #
    # VENTANA PRINCIPAL                                                   #
    # ------------------------------------------------------------------ #

    def open(self, parent, product_id=None, product_name=None):
        """
        Si se pasa product_id abre el historial filtrado por ese producto.
        Si no, abre el historial global.
        """
        win = ctk.CTkToplevel(parent)
        win.title("Historial de Movimientos de Stock")
        win.transient(parent)
        win.grab_set()
        win.withdraw()

        title_text = (
            f"Historial: {product_name}" if product_name
            else "Historial global de movimientos"
        )

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(win, fg_color="#3A3251", height=55, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"📋  {title_text}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=12)

        # ── Filtros ──────────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(win, fg_color="#f5f5f5", corner_radius=8)
        filter_frame.pack(fill="x", padx=15, pady=10)

        # Fechas
        hoy = datetime.now()
        hace_30 = hoy - timedelta(days=30)

        fecha_desde_var = tk.StringVar(value=hace_30.strftime("%d/%m/%Y"))
        fecha_hasta_var = tk.StringVar(value=hoy.strftime("%d/%m/%Y"))

        ctk.CTkLabel(filter_frame, text="Desde:", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=0, padx=(15, 5), pady=10)

        DateEntry(
            filter_frame,
            textvariable=fecha_desde_var,
            width=11,
            background="#3A3251",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy"
        ).grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(filter_frame, text="Hasta:", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=2, padx=(15, 5), pady=10)

        DateEntry(
            filter_frame,
            textvariable=fecha_hasta_var,
            width=11,
            background="#3A3251",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy"
        ).grid(row=0, column=3, padx=5, pady=10)

        # Tipo de evento
        ctk.CTkLabel(filter_frame, text="Tipo:", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=4, padx=(15, 5), pady=10)

        event_var = tk.StringVar(value="Todos")
        ctk.CTkComboBox(
            filter_frame,
            variable=event_var,
            values=["Todos", "Compra", "Venta", "Precio", "Precio masivo"],
            width=130,
            state="readonly"
        ).grid(row=0, column=5, padx=5, pady=10)

        # Botones rápidos
        quick_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        quick_frame.grid(row=0, column=6, padx=15, pady=10)

        def set_today():
            fecha_desde_var.set(hoy.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            load()

        def set_week():
            inicio = hoy - timedelta(days=hoy.weekday())
            fecha_desde_var.set(inicio.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            load()

        def set_month():
            inicio = hoy.replace(day=1)
            fecha_desde_var.set(inicio.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            load()

        for txt, cmd in [("Hoy", set_today), ("Semana", set_week), ("Mes", set_month)]:
            ctk.CTkButton(
                quick_frame, text=txt, width=65, height=28,
                fg_color="#3A3251", hover_color="#1e1a2e",
                command=cmd
            ).pack(side="left", padx=2)

        ctk.CTkButton(
            filter_frame, text="🔍 Filtrar", width=100, height=32,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: load()
        ).grid(row=0, column=7, padx=15, pady=10)

        # ── Resumen ──────────────────────────────────────────────────────
        summary_var = tk.StringVar(value="")
        ctk.CTkLabel(
            win,
            textvariable=summary_var,
            font=ctk.CTkFont(size=12),
            text_color="#555555"
        ).pack(anchor="w", padx=20)

        # ── Tabla ────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(win)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        cols = ("Fecha", "Producto", "Tipo", "Detalle",
                "Stock Ant.", "Stock Act.",
                "Costo Ant.", "Costo Act.",
                "Precio Ant.", "Precio Act.")

        style = ttk.Style()
        style.configure("Mov.Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Mov.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=18,
            style="Mov.Treeview"
        )

        col_widths = [130, 220, 110, 220, 80, 80, 90, 90, 90, 90]
        for col, w in zip(cols, col_widths):
            tree.column(col, width=w, anchor="center" if col != "Producto" and col != "Detalle" else "w")
            tree.heading(col, text=col)

        # Tags de color por tipo
        for key, color in EVENT_COLORS.items():
            tree.tag_configure(key, background=color)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # ── Botón cerrar ─────────────────────────────────────────────────
        ctk.CTkButton(
            win, text="Cerrar", width=120, height=35,
            fg_color="#E74C3C", hover_color="#C0392B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=win.destroy
        ).pack(pady=10)

        # ── Función de carga ─────────────────────────────────────────────
        def load():
            for row in tree.get_children():
                tree.delete(row)

            d_from = traditional_to_iso(fecha_desde_var.get())
            d_to   = traditional_to_iso(fecha_hasta_var.get())

            rows = self.movement.get_by_date_range(
                d_from, d_to,
                product_id=product_id  # None = global
            )

            # Filtro por tipo de evento
            event_map = {
                "Compra":       "COMPRA",
                "Venta":        "VENTA",
                "Precio":       "PRECIO",
                "Precio masivo":"PRECIO_MASIVO",
            }
            selected = event_var.get()
            if selected != "Todos":
                rows = [r for r in rows if r[4] == event_map.get(selected)]

            for r in rows:
                # r = (id, product_id, product_name, date, event_type,
                #      detail, qty_before, qty_after,
                #      cost_before, cost_after, price_before, price_after)
                _, _, p_name, date, ev_type, detail, \
                    qty_b, qty_a, cost_b, cost_a, price_b, price_a = r

                # Formatear fecha
                try:
                    date_fmt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_fmt = date

                def fmt(v):
                    return f"${v}" if v not in (None, "") else "—"

                def fmt_qty(v):
                    return str(v) if v is not None else "—"

                tree.insert("", "end", values=(
                    date_fmt,
                    p_name,
                    EVENT_LABELS.get(ev_type, ev_type),
                    detail or "—",
                    fmt_qty(qty_b),
                    fmt_qty(qty_a),
                    fmt(cost_b),
                    fmt(cost_a),
                    fmt(price_b),
                    fmt(price_a),
                ), tags=(ev_type,))

            summary_var.set(f"  {len(rows)} movimientos encontrados")

        # Carga inicial
        load()

        center_window(win, 1200, 700)
        win.deiconify()