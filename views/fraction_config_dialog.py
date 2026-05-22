"""
views/fraction_config_dialog.py
================================
Ventana modal que se abre desde la vista de stock para configurar
(o desactivar) el fraccionamiento de un producto.

Uso desde stock_view.py:

    from views.fraction_config_dialog import FractionConfigDialog

    def open_fraction_config(self):
        selected = self.get_selected_product()   # devuelve product_id
        if not selected:
            return
        product = self.stock_model.get_product_by_id(selected)
        FractionConfigDialog(
            parent         = self.frame,
            product        = product,
            fraction_model = self.fraction_model,
            on_save        = lambda: self.refresh_stock_table(self.stock_model.get_all_products())
        )
"""

import tkinter as tk
import customtkinter as ctk
from decimal import Decimal, InvalidOperation
from utils.view_helpers import center_window
from utils.utils import format_currency, norm_to_2_dec


class FractionConfigDialog:
    """
    Parámetros:
        parent         : ventana padre (CTkFrame o CTkToplevel)
        product        : tupla devuelta por StockModel.get_product_by_id()
                         (id, name, pack, profit, list_price, discount, cost_price,
                          price, iva, price_with_iva, created_at, last_price_update, quantity)
        fraction_model : instancia de FractionModel
        on_save        : callback sin argumentos que se llama al guardar
    """

    UNITS = ["KG", "GR", "LITRO", "ML", "UNIDAD"]

    # Mapeo sufijos textuales → unidad canónica (orden importa: más largo primero)
    _UNIT_ALIASES = [
        (["LITRO", "LT"],  "LITRO"),
        (["ML"],           "ML"),
        (["KG", "KILO"],   "KG"),
        (["GR", "G"],      "GR"),
    ]

    def _parse_pack(self, pack: str):
        """
        Extrae (qty_str, unit) del campo pack.
        Ejemplos:
            "BOLSA 3KG"   → ("3",   "KG")
            "BOLSA 15KG"  → ("15",  "KG")
            "500ML"       → ("500", "ML")
            "1.5 LITRO"   → ("1.5", "LITRO")
            "250GR"       → ("250", "GR")
            "UNIDAD"      → ("",    "UNIDAD")
        """
        import re
        pack_upper = pack.upper().strip()

        all_aliases = [a for aliases, _ in self._UNIT_ALIASES for a in aliases]
        pattern = r'(\d+(?:[.,]\d+)?)\s*(' + '|'.join(all_aliases) + r')\b'
        match = re.search(pattern, pack_upper)

        if match:
            qty_str  = match.group(1).replace(',', '.')
            raw_unit = match.group(2)
            unit = "KG"
            for aliases, canonical in self._UNIT_ALIASES:
                if raw_unit in aliases:
                    unit = canonical
                    break
            return qty_str, unit

        # Sin número: intentar detectar solo la unidad
        for aliases, canonical in self._UNIT_ALIASES:
            for alias in aliases:
                if alias in pack_upper:
                    return "", canonical

        return "", "KG"

    def __init__(self, parent, product, fraction_model, on_save=None):
        self.product        = product
        self.fraction_model = fraction_model
        self.on_save        = on_save

        self.product_id   = product[0]
        self.product_name = product[1]
        self.product_pack = product[2]
        self.iva_rate     = Decimal(str(product[8])) if product[8] else Decimal('21.00')

        # Cargar config existente si la hay
        self.existing_cfg = fraction_model.get_config(self.product_id)

        # Parsear qty y unidad desde el campo pack (usado si no hay config guardada)
        self._parsed_qty, self._parsed_unit = self._parse_pack(self.product_pack)

        self._build(parent)

    def _build(self, parent):
        win = ctk.CTkToplevel(parent)
        win.title("Configurar fraccionamiento")
        win.transient(parent)
        win.grab_set()
        win.resizable(False, False)
        center_window(win, 480, 500)

        card = ctk.CTkFrame(win, fg_color="white", corner_radius=16)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # ── Título ────────────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="⚙️ Configurar venta fraccionada",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(16, 4))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=2).pack(fill="x", padx=16, pady=(0, 10))

        # ── Info del producto ─────────────────────────────────────────────
        info = ctk.CTkFrame(card, fg_color="#f5f5f5", corner_radius=10)
        info.pack(padx=16, pady=4, fill="x")
        ctk.CTkLabel(
            info,
            text=f"{self.product_name}  ·  {self.product_pack}",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(8, 4))

        # Stock abierto actual
        open_info = self.fraction_model.get_available_stock_info(self.product_id)
        stock_text = open_info.get("display", "Sin datos") if open_info else "No configurado"
        ctk.CTkLabel(
            info,
            text=f"Stock actual: {stock_text}",
            font=ctk.CTkFont(size=11),
            text_color="#666"
        ).pack(pady=(0, 8))

        # ── Switch activar/desactivar ─────────────────────────────────────
        self.active_var = tk.BooleanVar(value=bool(self.existing_cfg))
        switch_frame = ctk.CTkFrame(card, fg_color="transparent")
        switch_frame.pack(padx=16, pady=6, fill="x")

        ctk.CTkLabel(
            switch_frame,
            text="Activar fraccionamiento:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        switch = ctk.CTkSwitch(
            switch_frame,
            variable=self.active_var,
            text="",
            command=self._toggle_fields,
            fg_color="#009688",
            progress_color="#4CAF50"
        )
        switch.pack(side="left", padx=10)

        # ── Formulario de configuración ───────────────────────────────────
        self.form_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.form_frame.pack(padx=16, pady=6, fill="x")
        self.form_frame.columnconfigure(1, weight=1)

        # Unidad de medida
        ctk.CTkLabel(self.form_frame, text="Unidad de venta:",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="e", padx=(0, 12), pady=8)

        self.unit_var = tk.StringVar(
            value=self.existing_cfg["unit"] if self.existing_cfg else self._parsed_unit
        )
        ctk.CTkComboBox(
            self.form_frame, values=self.UNITS,
            variable=self.unit_var, width=140, height=34
        ).grid(row=0, column=1, sticky="w", pady=8)

        # Cantidad por envase
        ctk.CTkLabel(self.form_frame, text="Cantidad por envase:",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=1, column=0, sticky="e", padx=(0, 12), pady=8)

        # Cantidad por envase — pre-rellenada desde el campo pack si no hay config guardada
        qty_default = str(self.existing_cfg["qty_per_package"]) if self.existing_cfg else self._parsed_qty
        self.qty_pkg_var = tk.StringVar(value=qty_default)

        qty_entry = ctk.CTkEntry(
            self.form_frame, textvariable=self.qty_pkg_var,
            width=140, height=34, placeholder_text="ej. 15"
        )
        qty_entry.grid(row=1, column=1, sticky="w", pady=8)

        # Si se auto-completó desde el pack, mostrar de dónde viene
        if not self.existing_cfg and self._parsed_qty:
            hint_text = f"← detectado de \"{self.product_pack}\""
            ctk.CTkLabel(
                self.form_frame,
                text=hint_text,
                font=ctk.CTkFont(size=10),
                text_color="#888"
            ).grid(row=1, column=2, sticky="w", padx=(6, 0), pady=8)

        # Precio fraccionado (sin IVA)
        ctk.CTkLabel(self.form_frame, text="Precio / unidad (sin IVA):",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=2, column=0, sticky="e", padx=(0, 12), pady=8)

        self.frac_price_var = tk.StringVar(
            value=str(self.existing_cfg["fraction_price"]) if self.existing_cfg else ""
        )
        price_entry = ctk.CTkEntry(
            self.form_frame, textvariable=self.frac_price_var,
            width=140, height=34, placeholder_text="ej. 850.00"
        )
        price_entry.grid(row=2, column=1, sticky="w", pady=8)

        # Precio con IVA (informativo)
        ctk.CTkLabel(self.form_frame, text="Precio / unidad (c/IVA):",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=3, column=0, sticky="e", padx=(0, 12), pady=8)

        self.price_iva_var = tk.StringVar(value="—")
        ctk.CTkLabel(
            self.form_frame, textvariable=self.price_iva_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#009688"
        ).grid(row=3, column=1, sticky="w", pady=8)

        def recalc_iva(*_):
            try:
                p    = Decimal(self.frac_price_var.get().replace(',', '.'))
                mult = Decimal('1') + self.iva_rate / Decimal('100')
                self.price_iva_var.set(f"$ {format_currency(norm_to_2_dec(p * mult))}")
            except (InvalidOperation, Exception):
                self.price_iva_var.set("—")

        self.frac_price_var.trace_add("write", recalc_iva)
        recalc_iva()

        # ── Botones ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=16)

        save_btn = ctk.CTkButton(
            btn_frame, text="💾 Guardar", width=140, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#4CAF50", hover_color="#388E3C",
            command=lambda: self._save(win)
        )
        save_btn.grid(row=0, column=0, padx=10)
        win.bind("<Return>", lambda e: save_btn.invoke())

        ctk.CTkButton(
            btn_frame, text="✗ Cancelar", width=140, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#757575", hover_color="#616161",
            command=win.destroy
        ).grid(row=0, column=1, padx=10)

        # Estado inicial del formulario
        self._toggle_fields()

    def _toggle_fields(self):
        """Habilitar/deshabilitar campos según el switch."""
        state = "normal" if self.active_var.get() else "disabled"
        for child in self.form_frame.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass

    def _save(self, win):
        from tkinter import messagebox

        if not self.active_var.get():
            # Desactivar: eliminar config y limpiar bolsas abiertas
            if self.existing_cfg:
                if messagebox.askyesno(
                    "Confirmar",
                    "¿Desactivar el fraccionamiento?\n"
                    "Se eliminarán los registros de bolsas abiertas."
                ):
                    self.fraction_model.remove_config(self.product_id)
                    # Limpiar open_fractions
                    from db.database import db
                    db.execute_query(
                        "DELETE FROM open_fractions WHERE product_id = ?",
                        (self.product_id,)
                    )
                    messagebox.showinfo("OK", "Fraccionamiento desactivado.")
                    if self.on_save:
                        self.on_save()
                    win.destroy()
            else:
                win.destroy()
            return

        # Validar campos
        try:
            qty_pkg = float(self.qty_pkg_var.get().replace(',', '.'))
            if qty_pkg <= 0:
                raise ValueError
        except (ValueError, Exception):
            messagebox.showerror("Error", "Ingrese una cantidad por envase válida (mayor a 0).")
            return

        try:
            frac_price = Decimal(self.frac_price_var.get().replace(',', '.'))
            if frac_price <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messagebox.showerror("Error", "Ingrese un precio válido (mayor a 0).")
            return

        unit = self.unit_var.get()

        self.fraction_model.set_config(
            product_id      = self.product_id,
            unit            = unit,
            qty_per_package = qty_pkg,
            fraction_price  = str(frac_price)
        )

        messagebox.showinfo(
            "Guardado",
            f"Fraccionamiento configurado:\n"
            f"  • Unidad: {unit}\n"
            f"  • Cantidad / envase: {qty_pkg} {unit}\n"
            f"  • Precio / {unit} (sin IVA): ${frac_price}"
        )

        if self.on_save:
            self.on_save()
        win.destroy()