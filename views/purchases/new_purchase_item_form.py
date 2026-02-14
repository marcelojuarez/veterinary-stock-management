import tkinter as tk
import customtkinter as ctk
from decimal import Decimal
from utils.utils import normalize_to_2_decimals, normalize_string_to_dec, normalize_int_to_dec
from views.view_helpers import close_win, ask_confirmation

class NewPurchaseItemForm():
    def __init__(self, controller, stock_model):
        self.controller = controller
        self.stock_model = stock_model

    # Configuracion de Variables - Items de compra
    def setup_purchase_items_variables(self, purchase_id):
        # variables producto
        self.purchase_id = tk.StringVar()
        self.purchase_id.set(purchase_id)

        self.product_id = tk.StringVar()
        self.product_name = tk.StringVar()
        self.product_pack = tk.StringVar()
        self.quantity = tk.StringVar()
        self.qty = None
        self.cost_price = tk.StringVar()
        self.cost = None
        self.iva_rate = tk.StringVar()
        self.iva = None
        
        self.discount_var = tk.StringVar()
        self.discount = None
        self.discount_amount = tk.StringVar()

        self.subtotal = tk.StringVar()
        
        self.iva_amount = tk.StringVar()
        self.total_item_var = tk.StringVar()

    # Formulario para agregar items en la compra
    def open_add_purchase_item(self, purchase_id, parent):

        self.setup_purchase_items_variables(purchase_id)

        self.cost = Decimal('0.00')
        self.iva = Decimal('0.00')

        """Ventana para agregar nuevo producto con CustomTkinter"""
        add_win = ctk.CTkToplevel(parent)
        add_win.configure(fg_color="#e0e0e0")
        add_win.title("Agregar nuevo artículo")
        
        # Hacer que la ventana sea modalxz
        add_win.transient(parent)
        add_win.grab_set()

        # Centrar la ventana
        add_win.geometry("800x450+{}+{}".format(
            add_win.winfo_screenwidth()//2 - 200,
            add_win.winfo_screenheight()//2 - 250
        ))

        card_frame = ctk.CTkFrame(
            add_win,
            fg_color='white',
            corner_radius=20
        )
        card_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Título
        title_label = ctk.CTkLabel(
            card_frame,
            text="Nuevo Artículo",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)

        form_frame = ctk.CTkFrame(card_frame, fg_color='white')
        form_frame.pack(pady=5, padx=(10,0), fill='x')

        def add_field(row, column, label, widget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight='bold'),
                text_color='black',
            )
            field_lbl.grid(row=row, column=column, sticky="e", padx=10, pady=7)

            widget.grid(row=row, column=column+1, padx=(10,20), pady=7, sticky='w')

        add_field(0, 0,"Id Compra:",
                ctk.CTkEntry(form_frame, textvariable=self.purchase_id, state='readonly', width=200))
        
        add_field(1, 0, "Id Producto:",
                ctk.CTkEntry(form_frame, textvariable=self.product_id, state='readonly', width=200))
        
        add_field(2, 0, "Nombre:",
                ctk.CTkEntry(form_frame, textvariable=self.product_name, width=200))
        
        add_field(3, 0, "Envase:",
                ctk.CTkComboBox(form_frame,  values=["UNIDAD", "CAJA", "FRASCO", "AMPOLLA", "SOBRE", "OTRO"], 
                                variable=self.product_pack, state='readonly', width=200))
        
        add_field(4, 0, "Stock:",
                ctk.CTkEntry(form_frame, textvariable=self.quantity, width=200))
        
        add_field(5, 0, "Precio Costo:",
                ctk.CTkEntry(form_frame, textvariable=self.cost_price, width=200))

        add_field(0, 2, "Porcentaje Iva:",
                ctk.CTkComboBox(form_frame, values=["21.00", "10.50", "0.00"], 
                                variable=self.iva_rate, state='readonly', width=200))

        add_field(1, 2, "Porcentaje Descuento:",
                ctk.CTkEntry(form_frame, textvariable=self.discount_var, width=200))
        
        add_field(2, 2, "Monto Descuento:",
                ctk.CTkEntry(form_frame, textvariable=self.discount_amount, state='readonly', width=200))
        
        add_field(3, 2, "SubTotal:",
                ctk.CTkEntry(form_frame, textvariable=self.subtotal, state='readonly', width=200))
        
        add_field(4, 2, "Importe Iva:",
                ctk.CTkEntry(form_frame, textvariable=self.iva_amount, state='readonly', width=200))

        add_field(5, 2, "Total:",
                ctk.CTkEntry(form_frame, textvariable=self.total_item_var, state='readonly', width=200))

        def recalc(*args):
            ## stock
            self.qty = normalize_int_to_dec(self.quantity.get())

            ## precio - iva - descuento
            self.cost = normalize_string_to_dec(self.cost_price.get())
            self.iva = normalize_string_to_dec(self.iva_rate.get())
            self.discount = normalize_string_to_dec(self.discount_var.get())

            if self.cost is None or self.iva is None or self.discount is None or self.qty is None:
                return

            # Calculos (sin normalizar)
            base_amount = self.qty * self.cost
            discount_rate = self.discount / Decimal('100')
            discount_amount = base_amount * discount_rate            

            subtotal = normalize_to_2_decimals(self.qty * self.cost - discount_amount)
            iva_amount = normalize_to_2_decimals(subtotal * (self.iva / Decimal('100')))
            total = subtotal + iva_amount

            # normalizacion final
            discount_amount = normalize_to_2_decimals(discount_amount)
            total = normalize_to_2_decimals(total)

            self.discount_amount.set(discount_amount)
            self.subtotal.set(subtotal)
            self.iva_amount.set(iva_amount)
            self.total_item_var.set(total)

        self.quantity.trace_add("write", recalc)
        self.cost_price.trace_add("write", recalc)
        self.iva_rate.trace_add("write", recalc)
        self.discount_var.trace_add("write", recalc) 

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

        if self.cost is not None:
            self.cost_price.set(self.cost)

        if self.discount is not None:
            self.discount_var.set(self.discount)

        if self.iva is not None:
            self.iva_rate.set(self.iva)

        data = (
            f"Nombre: {self.product_name.get().upper()}\n"
            f"Pack: {self.product_pack.get()}\n"
            f"Cantidad: {self.quantity.get()}\n"
            f"Precio costo: ${self.cost_price.get()}\n"
            f"IVA %:  {self.iva_rate.get()}\n"
            f"Monto IVA $: {self.iva_amount.get()}\n"
            f"Descuento %: {self.discount_var.get()}\n"
            f"Monto Descuento: ${self.discount_amount.get()}\n"
            f"Subtotal: ${self.subtotal.get()}\n"
            f"Total: ${self.total_item_var.get()}"
        )

        if ask_confirmation(data, 'Desea confirmar la carga de este producto?'):
            self.controller.add_purchase_item(win, parent)

    ## -- Carga los datos asociados a un producto -- ##
    def load_item_info(self, product_id):
        product_data = self.stock_model.get_product_by_id(product_id)

        self.product_id.set(product_data[0])
        self.product_name.set(product_data[1])
        self.product_pack.set(product_data[2])
        self.cost_price.set(product_data[4])
        self.iva_rate.set(product_data[6])

    ## -- Obtiene los datos de los items de compra -- ##
    def get_purchase_item_data(self):
        return{
            'Purchase_id': self.purchase_id.get().strip(),
            'Product_id': self.product_id.get().strip(),
            'Product_name': self.product_name.get().strip(),
            'Pack': self.product_pack.get().strip(),
            'Qty': self.quantity.get().strip(), 
            'Cost': self.cost_price.get().strip(),
            'Iva_rate': self.iva_rate.get().strip(),
            'Discount': self.discount_var.get().strip(),
            'Discount_amount': self.discount_amount.get().strip(),
            'Subtotal': self.subtotal.get().strip(),
            'Iva_amount': self.iva_amount.get().strip(),
            'Total': self.total_item_var.get().strip()
        }