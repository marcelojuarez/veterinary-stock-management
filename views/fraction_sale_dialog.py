"""
views/fraction_sale_dialog.py
==============================
Ventana modal que se abre cuando el usuario selecciona un producto
fraccionable y hace clic en "Agregar producto".

Muestra:
  - Nombre del producto
  - Stock disponible en unidades fraccionadas (ej. 37.5 kg en 3 bolsas)
  - Campo para ingresar la cantidad a vender
  - Precio por unidad fraccionada
  - Subtotal calculado en tiempo real

Al confirmar llama a:
    controller.add_product_to_sale(..., is_fractional=True, ...)
"""

import tkinter as tk
import customtkinter as ctk
from decimal import Decimal, InvalidOperation
from utils.view_helpers import center_window
from utils.utils import norm_to_2_dec, format_currency


class FractionSaleDialog:
    """
    Uso desde sales_view.py:

        if self.fraction_model.is_fractional(product_id):
            FractionSaleDialog(
                parent       = self.frame,
                controller   = self.controller,
                fraction_model = self.fraction_model,
                product_id   = product_id,
                name         = name,
                pack         = pack,
                iva_rate     = iva_rate,
                on_confirm   = lambda: (self.refresh_sale_table(), self.update_total())
            )
        else:
            # flujo normal existente
    """

    def __init__(self, parent, controller, fraction_model,
                 product_id, name, pack, iva_rate, on_confirm):
        self.controller     = controller
        self.fraction_model = fraction_model
        self.product_id     = product_id
        self.name           = name
        self.pack           = pack
        self.iva_rate       = Decimal(str(iva_rate))
        self.on_confirm     = on_confirm

        # Obtener datos de fraccionamiento
        self.cfg  = fraction_model.get_config(product_id)
        self.info = fraction_model.get_available_stock_info(product_id)

        self._build_window(parent)

    def _build_window(self, parent):
        win = ctk.CTkToplevel(parent)
        win.title("Venta fraccionada")
        win.transient(parent)
        win.grab_set()
        win.resizable(False, False)
        center_window(win, 440, 400)

        card = ctk.CTkFrame(win, fg_color="white", corner_radius=16)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # ── Título ────────────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="⚖️ Venta por fracción",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(pady=(16, 4))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=2).pack(fill="x", padx=16, pady=(0, 10))

        # ── Info del producto ─────────────────────────────────────────────
        info_frame = ctk.CTkFrame(card, fg_color="#f5f5f5", corner_radius=10)
        info_frame.pack(padx=16, pady=4, fill="x")

        ctk.CTkLabel(
            info_frame,
            text=f"{self.name}  ·  {self.pack}",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            info_frame,
            text=f"Stock disponible:  {self.info.get('display', '—')}",
            font=ctk.CTkFont(size=12),
            text_color="#555"
        ).pack(pady=(0, 8))

        # ── Formulario ────────────────────────────────────────────────────
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=16, pady=10, fill="x")
        form.columnconfigure(1, weight=1)

        unit_label = self.cfg["unit"] if self.cfg else "unidad"

        # Cantidad
        ctk.CTkLabel(form, text=f"Cantidad ({unit_label}):",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="e", padx=(0, 10), pady=6)

        self.qty_var = tk.StringVar(value="")
        qty_entry = ctk.CTkEntry(form, textvariable=self.qty_var, width=120,
                                 height=34, justify="center",
                                 font=ctk.CTkFont(size=13))
        qty_entry.grid(row=0, column=1, sticky="w", pady=6)
        qty_entry.focus()

        # Precio unitario
        ctk.CTkLabel(form, text=f"Precio / {unit_label} (c/IVA):",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=1, column=0, sticky="e", padx=(0, 10), pady=6)

        # Calcular precio con IVA desde fraction_price (sin IVA)
        base_price = self.cfg["fraction_price"] if self.cfg else Decimal('0')
        iva_mult   = Decimal('1') + self.iva_rate / Decimal('100')
        price_with_iva = norm_to_2_dec(base_price * iva_mult)
        self.price_var = tk.StringVar(value=str(price_with_iva))

        ctk.CTkEntry(form, textvariable=self.price_var, width=120, height=34,
                     justify="center", font=ctk.CTkFont(size=13)).grid(
            row=1, column=1, sticky="w", pady=6)

        # Subtotal en tiempo real
        ctk.CTkLabel(form, text="Subtotal:",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=2, column=0, sticky="e", padx=(0, 10), pady=6)

        self.subtotal_var = tk.StringVar(value="$ —")
        ctk.CTkLabel(form, textvariable=self.subtotal_var,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#009688").grid(row=2, column=1, sticky="w", pady=6)

        def recalc(*_):
            try:
                q = Decimal(self.qty_var.get().replace(',', '.'))
                p = Decimal(self.price_var.get().replace(',', '.'))
                self.subtotal_var.set(f"$ {format_currency(norm_to_2_dec(q * p))}")
            except (InvalidOperation, Exception):
                self.subtotal_var.set("$ —")

        self.qty_var.trace_add("write", recalc)
        self.price_var.trace_add("write", recalc)

        # ── Botones ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=16)

        confirm_btn = ctk.CTkButton(
            btn_frame, text="Agregar", width=140, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#4CAF50", hover_color="#388E3C",
            command=lambda: self._confirm(win)
        )
        confirm_btn.grid(row=0, column=0, padx=10)
        win.bind("<Return>", lambda e: confirm_btn.invoke())

        ctk.CTkButton(
            btn_frame, text="✗ Cancelar", width=140, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#757575", hover_color="#616161",
            command=win.destroy
        ).grid(row=0, column=1, padx=10)

        self._win = win

    def _confirm(self, win):
        try:
            qty   = Decimal(self.qty_var.get().replace(',', '.'))
            price = Decimal(self.price_var.get().replace(',', '.'))
        except (InvalidOperation, Exception):
            from tkinter import messagebox
            messagebox.showerror("Error", "Ingrese valores numéricos válidos.")
            return

        if qty <= 0:
            from tkinter import messagebox
            messagebox.showwarning("Advertencia", "La cantidad debe ser mayor a 0.")
            return

        unit = self.cfg["unit"] if self.cfg else "unidad"
        total_available = self.info.get("total_units", Decimal('0'))

        if qty > total_available:
            from tkinter import messagebox
            messagebox.showwarning(
                "Stock insuficiente",
                f"Solicitado: {qty} {unit}\nDisponible: {total_available} {unit}"
            )
            return

        ok = self.controller.add_product_to_sale(
            product_id    = self.product_id,
            name          = self.name,
            pack          = self.pack,
            price         = price,
            stock         = total_available,
            qty_input     = qty,
            is_fractional = True,
            unit          = unit,
            fraction_price= price
        )

        if ok:
            self.on_confirm()
            win.destroy()