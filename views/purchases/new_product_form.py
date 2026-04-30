import tkinter as tk
import customtkinter as ctk

from decimal import Decimal
from utils.view_helpers import center_window, close_win, ask_confirmation
from utils.utils import flex_dec, string_to_flex_dec, string_to_2_dec

class NewProductForm():
    def __init__(self, controller):
        self.controller = controller

    def setup_new_product_variables(self):
        """Configurar variables del formulario"""
        self.name_var = tk.StringVar()
        self.pack_var = tk.StringVar()
        self.profit_var = tk.StringVar()
        self.profit = None
        self.list_price_var = tk.StringVar()
        self.list_price = None
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
        width_win = 560
        height_win = 480

        x_parent = parent.winfo_x() 
        y_parent = parent.winfo_y()
        width_parent = parent.winfo_width()
        height_parent = parent.winfo_height()

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
        title_label.pack(pady=(20, 10))

        # Separador visual
        sep = ctk.CTkFrame(card_frame, fg_color="#e0e0e0", height=2)
        sep.pack(fill="x", padx=20, pady=(0, 10))

        # contenedor del formulario — 2 columnas
        form_frame = ctk.CTkFrame(card_frame, fg_color="white")
        form_frame.pack(pady=5, padx=10, fill="x")
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        
        def add_field(row, col, label, widget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#333333"
            )
            field_lbl.grid(row=row, column=col*2, sticky="e", padx=(15, 8), pady=6)
            widget.grid(row=row, column=col*2+1, sticky="w", padx=(0, 15), pady=6)

        # Columna izquierda
        add_field(0, 0, "Nombre:", 
                ctk.CTkEntry(form_frame, textvariable=self.name_var, width=180))
        
        add_field(1, 0, "Envase:",
            ctk.CTkComboBox(
                form_frame,
                values=["UNIDAD","10ML","20ML","25ML","50ML","90ML","100ML",
                        "200ML","250ML","300ML","500ML","400GR","5KG","10KG",
                        "12KG","15KG","20KG","25KG","40DS"],
                variable=self.pack_var, width=180, height=34
            )
        )
        self.pack_var.set("UNIDAD")

        add_field(2, 0, "Stock:",
                ctk.CTkEntry(form_frame, textvariable=self.qnt_var, state='readonly', width=180))
        self.qnt_var.set("0")

        add_field(3, 0, "% IVA:",
                ctk.CTkComboBox(form_frame, values=["21.00", "10.50", "0.00"],
                variable=self.iva_var, state='readonly', width=180, height=34))
        self.iva_var.set("21.00")

        # Columna derecha — precios
        add_field(0, 1, "Precio Lista:",
                ctk.CTkEntry(form_frame, textvariable=self.list_price_var, width=180))
        
        add_field(1, 1, "% Rentabilidad:",
                ctk.CTkEntry(form_frame, textvariable=self.profit_var, width=180))

        add_field(2, 1, "Precio Venta:",
                ctk.CTkEntry(form_frame, textvariable=self.sale_price_var, width=180))
        self.sale_price_var.set('0.0')

        add_field(3, 1, "Monto IVA:",
                  ctk.CTkEntry(form_frame, textvariable=self.iva_amount, width=180))
        self.iva_amount.set('0.0')

        # Precio final — fila completa destacada
        final_lbl = ctk.CTkLabel(
            form_frame,
            text="Precio C/IVA:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#333333"
        )
        final_lbl.grid(row=4, column=0, sticky="e", padx=(15, 8), pady=(10, 6))
        final_entry = ctk.CTkEntry(
            form_frame, textvariable=self.final_price,
            width=180, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#E8F5E9", border_color="#4CAF50"
        )
        final_entry.grid(row=4, column=1, sticky="w", padx=(0, 15), pady=(10, 6))
        self.final_price.set('0.0')

        def recalc(*args):
            try:
                self.list_price = string_to_flex_dec(self.list_price_var.get())
                self.profit = string_to_2_dec(self.profit_var.get())
                self.iva = string_to_flex_dec(self.iva_var.get())
                
                if self.list_price is None or self.profit is None or self.iva is None:
                    return

                # tasas
                profit_rate = self.profit / Decimal('100')
                iva_rate = self.iva / Decimal('100')

                # calculos (sin normalizar)
                profit_amount = self.list_price * profit_rate
                sale_price = self.list_price + profit_amount
                iva_amount = sale_price * iva_rate
                sale_price_with_iva = sale_price + iva_amount

                # normalizacion final
                sale_price = flex_dec(sale_price)
                iva_amount = flex_dec(iva_amount)
                sale_price_with_iva = flex_dec(sale_price_with_iva)

                self.iva_amount.set(iva_amount)
                self.sale_price_var.set(sale_price)
                self.final_price.set(sale_price_with_iva)
            
            except ValueError as e:
                print(f'{e}')
                return

        self.list_price_var.trace_add("write", recalc)
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
        if self.list_price is not None:
            self.list_price_var.set(self.list_price)

        if self.profit is not None:
            self.profit_var.set(self.profit)

        if self.iva is not None:
            self.iva_var.set(self.iva)

        data = (
            f"Nombre: {self.name_var.get().upper()}\n"
            f"Pack: {self.pack_var.get()}\n"
            f"Cantidad: {self.qnt_var.get()}\n"
            f"Precio Lista $: {self.list_price_var.get()}\n"
            f"Rentabilidad %: {self.profit_var.get()}\n"
            f"IVA %:  {self.iva_var.get()}\n"
            f"Monto IVA $: {self.iva_amount.get()}\n"
            f"Precio venta $: {self.sale_price_var.get()}\n"
            f"Precio venta C/IVA $: {self.final_price.get()}"
        )

        if ask_confirmation(data, '¿Confirma la carga de este producto?'):
            self.controller.add_new_product(parent)
    
    ## -- Obtener los datos de un nuevo producto -- ##
    def get_new_product_data(self):
        """Obtener datos del formulario"""
        return {
            'Name': self.name_var.get().strip(),
            'Package': self.pack_var.get().strip(),
            'Profit': self.profit_var.get().strip(),
            'ListPrice': self.list_price_var.get().strip(),
            'Iva': self.iva_var.get().strip(),
            'Stock': self.qnt_var.get().strip(),
            'SalePrice': self.sale_price_var.get().strip(),
            'PriceWIva': self.final_price.get().strip()
        }