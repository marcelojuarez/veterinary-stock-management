import tkinter as tk
import customtkinter as ctk
from utils.utils import normalize_decimal, normalize_string_to_dec
from decimal import InvalidOperation
from views.view_helpers import close_win, show_error, ask_confirmation

class NewProductForm():
    def __init__(self, controller):
        self.controller = controller
        print(f'new p f {self.controller}')

    def setup_new_product_variables(self):
        """Configurar variables del formulario"""
        self.name_var = tk.StringVar()
        self.pack_var = tk.StringVar()
        self.profit_var = tk.StringVar()
        self.profit = None
        self.price_var = tk.StringVar()
        self.cost_price = None
        self.iva_var = tk.StringVar()
        self.iva = None
        self.iva_amount = tk.StringVar()
        self.qnt_var = tk.StringVar()
        self.sale_price_var = tk.StringVar()
        self.final_price = tk.StringVar() # sale_price + iva_amount
        

    def open_add_window(self, parent):
        """Ventana para agregar nuevo producto con CustomTkinter"""
        add_win = ctk.CTkToplevel(parent)
        add_win.title("Agregar nuevo artículo")

        # se configuran las string vars
        self.setup_new_product_variables()
        
        # Hacer que la ventana sea modal
        add_win.transient(parent)
        add_win.grab_set()
    
        # Centrar la ventana

        width_win = 480
        height_win = 600

        x_parent = parent.winfo_x() 
        y_parent = parent.winfo_y()
        width_parent = parent.winfo_width()
        height_parent = parent.winfo_height()

        # centro
        x = x_parent + (width_parent // 2) - (width_win // 2)
        y = y_parent + (height_parent // 2) - (height_win // 2)

        add_win.geometry(f"{width_win}x{height_win}+{x}+{y}")
        
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

        # contenedor del formulario
        form_frame = ctk.CTkFrame(card_frame, fg_color="white")
        form_frame.pack(pady=5, padx=10, fill="x")
        
        def add_field(row, label, widget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="black"
            )

            field_lbl.grid(row=row, column=0, sticky="e", padx=(10,10), pady=7)
            widget.grid(row=row, column=1, sticky="w", padx=(10,10), pady=7)
        
        add_field(0, "Nombre Artículo: ", 
                ctk.CTkEntry(form_frame, textvariable=self.name_var, width=200))
        
        add_field(
            1,
            "Envase: ",
            ctk.CTkComboBox(
                form_frame,
                values=[
                    "UNIDAD",
                    "10 ML",
                    "20 ML",
                    "25 ML",
                    "50 ML",
                    "90 ML",
                    "100 ML",
                    "200 ML",
                    "250 ML",
                    "300 ML",
                    "500 ML",
                    "400 GR",
                    "5 KG",
                    "10 KG",
                    "12 KG",
                    "15 KG",
                    "20 KG",
                    "25 KG",
                    "40 DS",
                ],
                variable=self.pack_var,
                width=200,
                height=35
            )
        )

        self.pack_var.set("UNIDAD")

        add_field(2, "Stock: ",
                ctk.CTkEntry(form_frame, textvariable=self.qnt_var, state='readonly', width=200))

        self.qnt_var.set("0")
        
        add_field(3, "Precio Costo: ", 
                ctk.CTkEntry(form_frame, textvariable=self.price_var, width=200))
        
        add_field(4, "% Rentabilidad: ",
                ctk.CTkEntry(form_frame, textvariable=self.profit_var, width=200))

        add_field(5, "% Iva: ",
                ctk.CTkComboBox(form_frame, values=["21.00", "10.50", "0.00"], 
                variable=self.iva_var, width=200, height=35))
        
        self.iva_var.set("21.00")

        add_field(6, "Monto IVA: ",
                  ctk.CTkEntry(form_frame, textvariable=self.iva_amount, width=200))
        
        self.iva_amount.set('0.0')

        add_field(7, "Precio venta: ",
                ctk.CTkEntry(form_frame, textvariable=self.sale_price_var, width=200))
        
        self.sale_price_var.set('0.0')

        add_field(8, "Precio venta C/IVA: ",
                ctk.CTkEntry(form_frame, textvariable=self.final_price, width=200))
        
        self.final_price.set('0.0')

        def recalc(*args):
            try:
                self.cost_price = normalize_string_to_dec(self.price_var.get())
                self.profit = normalize_string_to_dec(self.profit_var.get())
                self.iva = normalize_decimal(self.iva_var.get())
                
                if self.cost_price is None or self.profit is None or self.iva is None:
                    return

                # precio con rentabilidad
                profit_rate = self.profit / 100
                profit_amount = normalize_decimal(self.cost_price * profit_rate)
                sale_price = normalize_decimal(self.cost_price + profit_amount)
                
                # precio con rentabilidad e iva
                iva_amount = normalize_decimal(sale_price * (self.iva / 100))
                sale_price_with_iva = normalize_decimal(sale_price + iva_amount)

                self.iva_amount.set(iva_amount)
                self.sale_price_var.set(sale_price)
                self.final_price.set(sale_price_with_iva)
            
            except ValueError as e:
                print(f'{e}')
                return

        self.price_var.trace_add("write", recalc)
        self.profit_var.trace_add("write", recalc)
        self.iva_var.trace_add("write", recalc)

        # Botones
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        add_button = ctk.CTkButton(button_frame, text="Agregar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049", command=lambda:self.confirm_new_product(add_win))
        add_button.grid(row=0, column=0, padx=10)

        add_win.bind("<Return>", lambda event: add_button.invoke())

        cancel_button = ctk.CTkButton(button_frame, text="Cancelar", width=120, height=35, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#757575", hover_color="#616161", command=lambda: close_win(add_win, parent))
        cancel_button.grid(row=0, column=1, padx=10)

    def confirm_new_product(self, parent):
        if self.cost_price is not None:
            self.price_var.set(self.cost_price)

        if self.profit is not None:
            self.profit_var.set(self.profit)

        if self.iva is not None:
            self.iva_var.set(self.iva)

        data = (
            f"Nombre: {self.name_var.get().upper()}\n"
            f"Pack: {self.pack_var.get()}\n"
            f"Cantidad: {self.qnt_var.get()}\n"
            f"Precio costo $: {self.price_var.get()}\n"
            f"Rentabilidad %: {self.profit_var.get()}\n"
            f"IVA %:  {self.iva_var.get()}\n"
            f"Monto IVA $: {self.iva_amount.get()}\n"
            f"Precio venta $: {self.sale_price_var.get()}\n"
            f"Precio venta C/IVA $: {self.final_price.get()}"
        )

        if ask_confirmation(data, 'Desea confirmar la carga de este producto?'):
            self.controller.add_new_product(parent)
    
    ## -- Obtener los datos de un nuevo producto -- ##
    def get_new_product_data(self):
        """Obtener datos del formulario"""
        return {
            'Name': self.name_var.get().strip(),
            'Package': self.pack_var.get().strip(),
            'Profit': self.profit_var.get().strip(),
            'CostPrice': self.price_var.get().strip(),
            'Iva': self.iva_var.get().strip(),
            'Stock': self.qnt_var.get().strip(),
            'SalePrice': self.sale_price_var.get().strip(),
            'PriceWIva': self.final_price.get().strip()
        }