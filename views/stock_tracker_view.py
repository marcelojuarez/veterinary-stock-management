"""
Rastreador de producto.
Muestra en una sola ventana todos los documentos y registros donde aparece
un producto: ventas, compras, facturas de venta, remitos y movimientos de stock.
Es de solo lectura (no modifica nada).
"""

from tkinter import ttk
import customtkinter as ctk

from utils.view_helpers import center_window
from utils.utils import iso_to_traditional, format_currency


class StockTrackerView:
    def __init__(self, stock_model):
        self.stock_model = stock_model

    # ── Helpers de formato ───────────────────────────────────────────────
    @staticmethod
    def _date(value):
        if not value:
            return "—"
        return iso_to_traditional(str(value)[:10])

    @staticmethod
    def _money(value):
        try:
            return format_currency(value)
        except Exception:
            return str(value)

    @staticmethod
    def _qty(quantity, is_fractional=False, unit=None):
        if is_fractional:
            return f"{quantity} {unit or ''}".strip()
        return str(quantity)

    # ── Ventana principal ────────────────────────────────────────────────
    def open(self, parent, product_id, product_name):
        refs = self.stock_model.get_product_references(product_id)

        win = ctk.CTkToplevel(parent)
        win.title(f"Rastreo de producto — {product_name}")
        win.transient(parent)
        win.grab_set()
        center_window(win, 940, 600)

        # Encabezado
        header = ctk.CTkFrame(win, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            header, text=f"🔎 {product_name}",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text=f"Código {product_id}",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(anchor="w")

        total = sum(len(v) for v in refs.values())
        resumen = (
            f"Ventas: {len(refs['sales'])}    ·    Compras: {len(refs['purchases'])}    ·    "
            f"Facturas: {len(refs['invoices'])}    ·    Remitos: {len(refs['remitos'])}    ·    "
            f"Movimientos: {len(refs['movements'])}"
        )
        ctk.CTkLabel(
            header,
            text=(resumen if total else "Este producto no aparece en ningún documento ni movimiento."),
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(6, 0))

        # Pestañas
        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=16, pady=(8, 14))

        self._add_tab(
            notebook, f"Ventas ({len(refs['sales'])})",
            ["Venta", "Fecha", "Cliente", "Cant.", "Precio", "Subtotal", "Estado"],
            [80, 90, 210, 70, 100, 110, 90],
            [(f"#{r[0]}", self._date(r[1]), r[2], self._qty(r[3], r[7], r[8]),
              self._money(r[4]), self._money(r[5]), r[6]) for r in refs["sales"]],
        )
        self._add_tab(
            notebook, f"Compras ({len(refs['purchases'])})",
            ["Compra", "Fecha", "Proveedor", "Cant.", "Costo", "Total", "Estado"],
            [80, 90, 210, 80, 100, 110, 90],
            [(f"#{r[0]}", self._date(r[1]), r[2],
              str(r[3]) + (f"  +{r[7]} bonif." if r[7] else ""),
              self._money(r[4]), self._money(r[5]), r[6]) for r in refs["purchases"]],
        )
        self._add_tab(
            notebook, f"Facturas ({len(refs['invoices'])})",
            ["Factura", "Fecha", "Cliente", "Cant.", "Precio", "Subtotal", "Estado"],
            [110, 90, 210, 70, 100, 110, 90],
            [(r[0], self._date(r[1]), r[2], str(r[3]),
              self._money(r[4]), self._money(r[5]), r[6]) for r in refs["invoices"]],
        )
        self._add_tab(
            notebook, f"Remitos ({len(refs['remitos'])})",
            ["Remito", "Fecha", "Cliente", "Cant.", "Estado"],
            [120, 90, 260, 80, 110],
            [(r[0], self._date(r[1]), r[2], str(r[3]), r[4]) for r in refs["remitos"]],
        )
        self._add_tab(
            notebook, f"Movimientos ({len(refs['movements'])})",
            ["Fecha", "Tipo", "Detalle", "Antes", "Después", "Costo", "Precio"],
            [95, 90, 240, 70, 70, 100, 100],
            [(self._date(r[0]), r[1], r[2],
              "—" if r[3] is None else str(r[3]),
              "—" if r[4] is None else str(r[4]),
              self._money(r[5]) if r[5] else "—",
              self._money(r[6]) if r[6] else "—") for r in refs["movements"]],
        )

        win.lift()
        win.focus_force()

    # ── Constructor de pestaña con tabla ─────────────────────────────────
    def _add_tab(self, notebook, title, headers, widths, rows):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        if not rows:
            ctk.CTkLabel(
                frame, text="Sin registros en esta categoría.",
                font=ctk.CTkFont(size=13), text_color="gray"
            ).pack(pady=40)
            return

        tree = ttk.Treeview(frame, columns=headers, show="headings", height=15)
        for head, width in zip(headers, widths):
            tree.heading(head, text=head)
            anchor = "w" if head in ("Cliente", "Proveedor", "Detalle") else "center"
            tree.column(head, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for row in rows:
            tree.insert("", "end", values=row)
