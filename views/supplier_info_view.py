import tkinter as tk
from tksheet import Sheet
import customtkinter as ctk
from utils.utils import format_currency
from utils.view_helpers import center_window

class SupplierInfoView():
    def __init__(self, parent, supplier_controller, supplier_model):
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        self.controller = supplier_controller
        self.model = supplier_model

    def open_info_window(self, supplier_data, debt, parent):
        self.frame.update_idletasks()

        info_win = ctk.CTkToplevel(self.frame)
        info_win.title(f'Proveedor: {supplier_data[2]} -- {supplier_data[1]}')
        info_win.transient(parent)
        info_win.grab_set()
        center_window(info_win, 1200, 600)

        info_win.grid_rowconfigure(0, weight=1)
        info_win.grid_rowconfigure(1, weight=0)
        info_win.grid_columnconfigure(0, weight=3)
        info_win.grid_columnconfigure(1, weight=1)

        # --- Tksheet con productos ---
        products = self.model.purchase.get_all_products_by_supplier_id(supplier_id=supplier_data[0])
        products = [(p[0], p[1], p[2], p[5]) for p in products]

        sheet = Sheet(info_win)
        sheet.grid(row=0, column=0, sticky="nsew", pady=(10, 0))
        sheet.headers(["Id", "Nombre Artículo", "Envase", "Stock"])
        sheet.set_sheet_data(products)
        sheet.set_column_widths([50, 300, 200, 50])

        # --- Panel derecho ---
        self.debt = tk.StringVar(value=f'{debt}')
        self.last_update_debt = tk.StringVar(value=supplier_data[10])

        right_frame = ctk.CTkFrame(info_win, corner_radius=14, fg_color="#ffffff")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=(10, 0))
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=0)
        right_frame.grid_rowconfigure(1, weight=1)

        # --- Card de deuda ---
        debt_card = ctk.CTkFrame(
            right_frame,
            corner_radius=12,
            fg_color="#f0faf5",
            border_width=2,
            border_color="#a8dfc4"
        )
        debt_card.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        debt_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(debt_card, text="💰", font=ctk.CTkFont(size=28)).grid(row=0, column=0, pady=(16, 2))
        ctk.CTkLabel(
            debt_card, text="Deuda del Proveedor",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#6b7280"
        ).grid(row=1, column=0, pady=(0, 4))
        ctk.CTkFrame(debt_card, height=2, fg_color="#a8dfc4", corner_radius=2).grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 8)
        )
        self.lbl_debt = ctk.CTkLabel(
            debt_card, text=f'${format_currency(self.debt.get())}',
            font=ctk.CTkFont(size=24, weight="bold"), text_color="#059649"
        )
        self.lbl_debt.grid(row=3, column=0, pady=(0, 10))
        ctk.CTkFrame(debt_card, height=1, fg_color="#d1fae5", corner_radius=2).grid(
            row=4, column=0, sticky="ew", padx=16, pady=(0, 8)
        )
        ctk.CTkLabel(
            debt_card, text="Última actualización",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#9ca3af"
        ).grid(row=5, column=0, pady=(0, 2))
        ctk.CTkLabel(
            debt_card, textvariable=self.last_update_debt,
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151"
        ).grid(row=6, column=0, pady=(0, 14))

        # --- Card de datos del proveedor ---
        info_card = ctk.CTkFrame(
            right_frame, corner_radius=12,
            fg_color="#fafafa", border_width=2, border_color="#e5e7eb"
        )
        info_card.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        info_card.grid_columnconfigure(1, weight=1)
        info_card.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            info_card, text="📋  Datos del Proveedor",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151"
        ).grid(row=0, column=0, columnspan=4, padx=14, pady=(12, 4), sticky="w")
        ctk.CTkFrame(info_card, height=1, fg_color="#e5e7eb", corner_radius=2).grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 8)
        )

        fields = [
            ("CUIT",          1),
            ("Nombre",        2),
            ("Dirección",     3),
            ("Ciudad",        4),
            ("Provincia",     5),
            ("País",          6),
            ("Teléfono",      7),
            ("Email",         8),
            ("Condición IVA", 9),
        ]

        self.field_vars = {}
        self.field_widgets = {}  # guarda referencia a cada widget

        for i, (label, idx) in enumerate(fields):
            grid_row = 2 + i // 2
            col_label = (i % 2) * 2
            col_entry = col_label + 1

            ctk.CTkLabel(
                info_card, text=label,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#6b7280"
            ).grid(row=grid_row, column=col_label, padx=(12, 4), pady=4, sticky="w")

            var = tk.StringVar(value=supplier_data[idx] or "")
            self.field_vars[label] = var

            if label == "Condición IVA":
                widget = ctk.CTkComboBox(
                    info_card,
                    variable=var,
                    values=["RESP. INSCRIPTO", "MONOTRIBUTISTA", "EXENTO", "NO RESPONSABLE"],
                    font=ctk.CTkFont(size=11),
                    height=28,
                    state="disabled",
                    fg_color="#f3f4f6",
                    border_color="#e5e7eb",
                    text_color="#111827"
                )
            else:
                widget = ctk.CTkEntry(
                    info_card,
                    textvariable=var,
                    font=ctk.CTkFont(size=11),
                    height=28,
                    state="readonly",
                    fg_color="#f3f4f6",
                    border_color="#e5e7eb",
                    text_color="#111827"
                )

            widget.grid(row=grid_row, column=col_entry, padx=(0, 10), pady=4, sticky="ew")
            self.field_widgets[label] = widget

        # --- Botones editar / cancelar ---
        btn_row = 2 + (len(fields) + 1) // 2
        btn_frame_card = ctk.CTkFrame(info_card, fg_color="transparent")
        btn_frame_card.grid(row=btn_row, column=0, columnspan=4, padx=10, pady=(8, 12), sticky="e")

        def on_edit():
            for lbl, w in self.field_widgets.items():
                w.configure(state="normal", fg_color="white", border_color="#009688")
            self._original_values = {lbl: var.get() for lbl, var in self.field_vars.items()}
            edit_btn.configure(text="💾  Guardar", fg_color="#2563eb", hover_color="#1d4ed8", command=on_save)  # ← on_save directo
            cancel_edit_btn.configure(state="normal", fg_color="#6b7280", hover_color="#4b5563")

        def on_save():
            success = self.controller.update_supplier_data(
                supplier_id=supplier_data[0],
                supplier_data=self.get_new_supplier_data()
            )
            if success:
                for lbl, w in self.field_widgets.items():
                    if lbl == "Condición IVA":
                        w.configure(state="disabled", fg_color="#f3f4f6", border_color="#e5e7eb")
                    else:
                        w.configure(state="readonly", fg_color="#f3f4f6", border_color="#e5e7eb")
                edit_btn.configure(text="✏️  Editar", fg_color="#009688", hover_color="#00796B", command=on_edit)
                cancel_edit_btn.configure(state="disabled", fg_color="#9ca3af", hover_color="#9ca3af")

        def on_cancel():
            # Restaurar valores originales
            for lbl, val in self._original_values.items():
                self.field_vars[lbl].set(val)
            # Volver a readonly
            for lbl, w in self.field_widgets.items():
                if lbl == "Condición IVA":
                    w.configure(state="disabled", fg_color="#f3f4f6", border_color="#e5e7eb")
                else:
                    w.configure(state="readonly", fg_color="#f3f4f6", border_color="#e5e7eb")
            edit_btn.configure(text="✏️  Editar", fg_color="#009688", hover_color="#00796B", command=on_edit)
            cancel_edit_btn.configure(state="disabled", fg_color="#9ca3af", hover_color="#9ca3af")

        edit_btn = ctk.CTkButton(
            btn_frame_card, text="✏️  Editar",
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=30, width=100, command=on_edit
        )
        edit_btn.pack(side="left", padx=(0, 6))

        cancel_edit_btn = ctk.CTkButton(
            btn_frame_card, text="✖  Cancelar",
            fg_color="#9ca3af", hover_color="#9ca3af",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=30, width=100, state="disabled"
        )
        cancel_edit_btn.pack(side="left")
        cancel_edit_btn.configure(command=on_cancel)

        # --- Botón cerrar ---
        btn_frame = ctk.CTkFrame(info_win, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=10)
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text='Cerrar',
            fg_color="#E74C3C", hover_color="#C0392B",
            text_color="white", font=ctk.CTkFont(size=13, weight="bold"),
            command=info_win.destroy
        ).grid(row=0, column=0, columnspan=2)


    def get_new_supplier_data(self) -> dict:
        return {
            "cuit":          self.field_vars["CUIT"].get().strip(),
            "name":          self.field_vars["Nombre"].get().strip(),
            "address":       self.field_vars["Dirección"].get().strip(),
            "city":          self.field_vars["Ciudad"].get().strip(),
            "province":      self.field_vars["Provincia"].get().strip(),
            "country":       self.field_vars["País"].get().strip(),
            "phone":         self.field_vars["Teléfono"].get().strip(),
            "email":         self.field_vars["Email"].get().strip(),
            "iva_condition": self.field_vars["Condición IVA"].get().strip(),
        }