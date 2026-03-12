import tkinter as tk
import customtkinter as ctk
from decimal import Decimal
from utils.view_helpers import close_win, ask_confirmation
from utils.utils import string_to_2_dec, string_to_flex_dec, string_to_dec, norm_to_2_dec, flex_dec

class NewPurchaseItemForm():
    def __init__(self, controller, stock_model):
        self.controller = controller
        self.stock_model = stock_model

    # Configuracion de Variables - Items de compra
    def setup_purchase_items_variables(self, purchase_id):
        self.purchase_id = tk.StringVar()
        self.purchase_id.set(purchase_id)
        self.product_id = tk.StringVar()
        self.product_name = tk.StringVar()
        self.product_pack = tk.StringVar()
        self.quantity = tk.StringVar()
        self.qty = None
        self.kg_per_unit_var = tk.StringVar()
        self.kg_calculated_var = tk.StringVar() 
        self.list_price_var = tk.StringVar()
        self.list_price = None
        self.cost_price_var = tk.StringVar()
        self.iva_rate = tk.StringVar()
        self.iva = None
        self.discount_var = tk.StringVar()
        self.discount = None
        self.discount_amount = tk.StringVar()
        self.subtotal = tk.StringVar()
        self.iva_amount = tk.StringVar()
        self.total_item_var = tk.StringVar()

    # Formulario para agregar items en la compra
    def open_add_purchase_item(self, purchase_id, parent, discrimina_iva=True):

        self.setup_purchase_items_variables(purchase_id)
        self.discrimina_iva = discrimina_iva

        add_win = ctk.CTkToplevel(parent)
        add_win.configure(fg_color="#e0e0e0")
        add_win.title("Agregar nuevo artículo")
        add_win.transient(parent)
        add_win.grab_set()

        add_win.geometry("850x580+{}+{}".format(
            add_win.winfo_screenwidth()//2 - 200,
            add_win.winfo_screenheight()//2 - 250
        ))

        card_frame = ctk.CTkFrame(add_win, fg_color='white', corner_radius=20)
        card_frame.pack(fill='both', expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            card_frame,
            text="Nuevo Artículo",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 5))

        if not self.discrimina_iva:
            ctk.CTkLabel(
                card_frame,
                text="⚠  Factura sin IVA discriminado — IVA forzado a 0%",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff",
                fg_color="#E65100",
                corner_radius=8
            ).pack(fill="x", padx=20, pady=(0, 8), ipady=5)

        form_frame = ctk.CTkFrame(card_frame, fg_color='white')
        form_frame.pack(pady=5, padx=(10,0), fill='x')

        def add_field(row, column, label, widget, label_color="#333333"):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight='bold'),
                text_color=label_color,
            )
            field_lbl.grid(row=row, column=column, sticky="e", padx=10, pady=7)
            widget.grid(row=row, column=column+1, padx=(10,20), pady=7, sticky='w')
            return field_lbl

        add_field(0, 0, "Id Compra:",
                ctk.CTkEntry(form_frame, textvariable=self.purchase_id, state='readonly', width=200))

        add_field(1, 0, "Id Producto:",
                ctk.CTkEntry(form_frame, textvariable=self.product_id, state='readonly', width=200))

        add_field(2, 0, "Nombre:",
                ctk.CTkEntry(form_frame, textvariable=self.product_name, width=200))

        add_field(3, 0, "Envase:",
            ctk.CTkComboBox(
                form_frame,
                values=["UNIDAD", "ML", "GR", "KG"],
                variable=self.product_pack,
                state='readonly',
                width=200
            )
        )

        add_field(4, 0, "Stock:",
                ctk.CTkEntry(form_frame, textvariable=self.quantity, width=200))
        
        self.kg_u_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.kg_per_unit_var,
            width=200,
            state="disabled",
            placeholder_text="Ej: 15"
        )
        self.kg_u_label = add_field(5, 0, "KG/U:", self.kg_u_entry, label_color="#999999")

        # Stock KG — readonly, calculado automáticamente
        self.kg_calc_entry = ctk.CTkEntry(
            form_frame,
            textvariable=self.kg_calculated_var,
            width=200,
            state="readonly"
        )
        self.kg_calc_label = add_field(6, 0, "Stock KG:", self.kg_calc_entry, label_color="#999999")

        add_field(7, 0, "Precio Lista:",
                ctk.CTkEntry(form_frame, textvariable=self.list_price_var, width=200))

        add_field(0, 2, "% Dto:",
                ctk.CTkEntry(form_frame, textvariable=self.discount_var, width=200))

        add_field(1, 2, "Precio Costo:",
                ctk.CTkEntry(form_frame, textvariable=self.cost_price_var, state='readonly', width=200))

        iva_combo = ctk.CTkComboBox(
            form_frame, values=["21.00", "10.50", "0.00"],
            variable=self.iva_rate,
            state='readonly' if self.discrimina_iva else 'disabled',
            width=200
        )
        add_field(2, 2, "Porcentaje Iva:", iva_combo)

        add_field(3, 2, "Total Descuento:",
                ctk.CTkEntry(form_frame, textvariable=self.discount_amount, state='readonly', width=200))

        add_field(4, 2, "SubTotal:",
                ctk.CTkEntry(form_frame, textvariable=self.subtotal, state='readonly', width=200))

        add_field(5, 2, "Importe Iva:",
                ctk.CTkEntry(form_frame, textvariable=self.iva_amount, state='readonly', width=200))

        add_field(6, 2, "Total:",
                ctk.CTkEntry(form_frame, textvariable=self.total_item_var, state='readonly', width=200))

        if not self.discrimina_iva:
            self.iva_rate.set("0.00")

        def update_kg_fields(*args):
            """Muestra/oculta campos KG según el envase seleccionado"""
            if self.product_pack.get() == "KG":
                self.kg_u_entry.configure(state="normal")
                self.kg_u_label.configure(text_color="#333333")
                self.kg_calc_label.configure(text_color="#333333")
            else:
                self.kg_u_entry.configure(state="disabled")
                self.kg_per_unit_var.set("")
                self.kg_calculated_var.set("")
                self.kg_u_label.configure(text_color="#999999")
                self.kg_calc_label.configure(text_color="#999999")

        self.product_pack.trace_add("write", update_kg_fields)

        def recalc(*args):
            self.qty = string_to_dec(self.quantity.get())

            # Calcular stock en KG si aplica
            if self.product_pack.get() == "KG":
                try:
                    kg_per_unit = self.kg_per_unit_var.get().strip()
                    if kg_per_unit and self.qty:
                        kg_total = norm_to_2_dec(self.qty * Decimal(kg_per_unit))
                        self.kg_calculated_var.set(str(kg_total))
                    else:
                        self.kg_calculated_var.set("")
                except Exception:
                    self.kg_calculated_var.set("")
            else:
                self.kg_calculated_var.set("")

            self.list_price = string_to_flex_dec(self.list_price_var.get())
            self.discount = string_to_2_dec(self.discount_var.get())

            if not self.discrimina_iva:
                self.iva_rate.set("0.00")
            self.iva = string_to_flex_dec(self.iva_rate.get())

            if self.list_price is None or self.iva is None or self.discount is None or self.qty is None:
                return

            base_amount = norm_to_2_dec(self.qty * self.list_price)
            discount_rate = self.discount / Decimal('100')
            unit_d_amount = self.list_price * discount_rate
            cost_price = self.list_price - unit_d_amount
            subtotal = norm_to_2_dec(self.qty * cost_price)

            if self.discrimina_iva:
                iva_amount = norm_to_2_dec(subtotal * (self.iva / Decimal('100')))
            else:
                iva_amount = Decimal('0.00')

            discount_amount = base_amount - subtotal
            total = subtotal + iva_amount

            cost_price = flex_dec(cost_price)
            discount_amount = norm_to_2_dec(discount_amount)
            total = norm_to_2_dec(total)

            self.cost_price_var.set(cost_price)
            self.discount_amount.set(discount_amount)
            self.subtotal.set(subtotal)
            self.iva_amount.set(iva_amount)
            self.total_item_var.set(total)

        self.quantity.trace_add("write", recalc)
        self.list_price_var.trace_add("write", recalc)
        self.iva_rate.trace_add("write", recalc)
        self.discount_var.trace_add("write", recalc)
        self.kg_per_unit_var.trace_add("write", recalc)

        # Botones
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        add_button = ctk.CTkButton(button_frame, text="Agregar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049", command=lambda: self.confirm_new_p_item(add_win, parent))
        add_button.grid(row=0, column=0, padx=10)

        add_win.bind("<Return>", lambda event: add_button.invoke())

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command=lambda: close_win(add_win, parent))
        cancel_button.grid(row=0, column=1, padx=10)

    def confirm_new_p_item(self, win, parent):
        if self.qty is not None:
            self.quantity.set(self.qty)
        if self.list_price is not None:
            self.list_price_var.set(self.list_price)
        if self.discount is not None:
            self.discount_var.set(self.discount)
        if self.iva is not None:
            self.iva_rate.set(self.iva)

        kg_line = f"KG/U: {self.kg_per_unit_var.get()}" if self.product_pack.get() == "KG" else ""
        final_qty = self.kg_calculated_var.get().strip() if self.product_pack.get() == "KG" else self.quantity.get().strip()

        data = (
            f"Nombre: {self.product_name.get().upper()}\n"
            f"Pack: {self.product_pack.get()}\n"
            f"{kg_line}"
            f"Cantidad: {final_qty}\n"
            f"Precio lista: ${self.list_price_var.get()}\n"
            f"Descuento %: {self.discount_var.get()}\n"
            f"Precio costo: ${self.cost_price_var.get()}\n"
            f"IVA %: {self.iva_rate.get()}\n"
            f"Monto Descuento: ${self.discount_amount.get()}\n"
            f"Subtotal: ${self.subtotal.get()}\n"
            f"Monto IVA $: {self.iva_amount.get()}\n"
            f"Total: ${self.total_item_var.get()}"
        )

        if ask_confirmation(data, '¿Desea confirmar la carga de este producto?'):
            self.controller.add_purchase_item(win, parent)

    ## -- Carga los datos asociados a un producto -- ##
    def load_item_info(self, product_id):
        product_data = self.stock_model.get_product_by_id(product_id)

        self.product_id.set(product_data[0])
        self.product_name.set(product_data[1])
        self.product_pack.set(product_data[2])
        self.list_price_var.set(product_data[5])
        self.iva_rate.set(product_data[9])

        # Precargar KG/U si el producto es KG
        kg_per_unit = product_data[3]
        if kg_per_unit and self.product_pack.get() == "KG":
            self.kg_per_unit_var.set(kg_per_unit)
            self.kg_u_entry.configure(state="normal")
            self.kg_u_label.configure(text_color="#333333")
            self.kg_calc_label.configure(text_color="#333333")
        else:
            self.kg_per_unit_var.set("")

    ## -- Obtiene los datos de los items de compra -- ##
    def get_purchase_item_data(self):
        pack = self.product_pack.get().strip()
        final_qty = self.kg_calculated_var.get().strip() if pack == "KG" else self.quantity.get().strip()

        return {
            'Purchase_id': self.purchase_id.get().strip(),
            'Product_id': self.product_id.get().strip(),
            'Product_name': self.product_name.get().strip(),
            'Pack': pack,
            'Qty': final_qty,
            'KgPerUnit': self.kg_per_unit_var.get().strip() or None,
            'List_price': self.list_price_var.get().strip(),
            'Discount': self.discount_var.get().strip(),
            'Cost_price': self.cost_price_var.get().strip(),
            'Iva_rate': self.iva_rate.get().strip(),
            'Discount_amount': self.discount_amount.get().strip(),
            'Subtotal': self.subtotal.get().strip(),
            'Iva_amount': self.iva_amount.get().strip(),
            'Total': self.total_item_var.get().strip()
        }