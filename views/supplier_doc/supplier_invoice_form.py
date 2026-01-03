import customtkinter as ctk
import tkinter as tk
from views.view_helpers import close_win, show_warning
from controllers.supplier_invoice_controller import SupplierInvoiceController
import datetime

class SupplierInvoiceForm():
    def __init__(self, view, frame, supplier_view):
        self.view = view
        self.supplier_view = supplier_view
        self.frame = frame
        self.controller = SupplierInvoiceController(self, self.view, self.supplier_view)

    def setup_variables(self, supplier_var):
        self.supplier_var = tk.StringVar()
        self.supplier_var.set(supplier_var)

        self.invoice_id_var = tk.StringVar()
        self.invoice_type_var = tk.StringVar()
        self.expiration_var = tk.StringVar()
        self.subtotal_var = tk.StringVar()
        self.iva_var = tk.StringVar()
        self.obs_var = tk.StringVar()
        self.discount_var = tk.StringVar()
        self.total_var = tk.StringVar()
        self.state_var = tk.StringVar()

    def open_invoice_form(self, parent, supplier_var):
        btn_color = "#009688"
        btn_hover = "#00796B"

        self.setup_variables(supplier_var)
        actual_date = datetime.datetime.now()
        formated_act_date = actual_date.strftime("%d/%m/%Y")

        if self.supplier_var.get() == "":
            show_warning("Por favor seleccione un Proveedor")
            return

        # Crear ventana modal
        self.invoice_win = ctk.CTkToplevel(self.frame)
        self.invoice_win.title("Registrar nueva Factura")
        self.invoice_win.configure(fg_color="#e0e0e0")
        self.invoice_win.transient(parent)
        self.invoice_win.grab_set()
        self.invoice_win.protocol("WM_DELETE_WINDOW",
                                lambda: close_win(self.invoice_win, parent))

        # Tamaño fijo
        width_win = 500
        height_win = 720

        # Centrar respecto al padre
        x_root = parent.winfo_x()
        y_root = parent.winfo_y()
        width_root = parent.winfo_width()
        height_root = parent.winfo_height()

        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        self.invoice_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        # --- Card principal ---
        card_frame = ctk.CTkFrame(self.invoice_win, fg_color="white", corner_radius=20)
        card_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        title_label = ctk.CTkLabel(
            card_frame,
            text="Nueva Factura",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="black"
        )
        title_label.pack(pady=20)

        # Contenedor del formulario
        form_frame = ctk.CTkFrame(card_frame, fg_color="white")
        form_frame.pack(padx=15, pady=5, fill="x")

        # --- Función auxiliar para campos ---
        def add_field(row, label, widget):
            lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="black"
            )
            lbl.grid(row=row, column=0, sticky="e", padx=(10,10), pady=7)
            widget.grid(row=row, column=1, sticky="w", padx=(10,20), pady=7)

        # Campos
        add_field(0, "CUIT Proveedor:", 
                ctk.CTkEntry(form_frame, textvariable=self.supplier_var, state='readonly', width=250))
        
        add_field(1, "Número Factura:", 
                ctk.CTkEntry(form_frame, textvariable=self.invoice_id_var, width=250))
        
        add_field(2, "Tipo:",
                ctk.CTkComboBox(form_frame, values=["A","B","C","M","-"], variable=self.invoice_type_var, width=250, state="readonly"))
        
        add_field(3, "Vencimiento:",
                ctk.CTkEntry(form_frame, textvariable=self.expiration_var, width=250))
        
        add_field(4, "Observaciones:", 
                ctk.CTkEntry(form_frame, textvariable=self.obs_var, width=250, height=80))
        
        add_field(5, "Estado:", 
                ctk.CTkEntry(form_frame, textvariable=self.state_var, width=250, state="readonly"))
        
        add_field(6, "IVA:",
                ctk.CTkEntry(form_frame, textvariable=self.iva_var, state='readonly', width=250))
        
        add_field(7, "Descuento:", 
                ctk.CTkEntry(form_frame, textvariable=self.discount_var, state='readonly', width=250))
        
        add_field(8, "Subtotal:", 
                ctk.CTkEntry(form_frame, textvariable=self.subtotal_var, state='readonly', width=250))
        
        add_field(9, "Total:", 
                ctk.CTkEntry(form_frame, textvariable=self.total_var, state='readonly', width=250))

        self.invoice_type_var.set("-")
        self.expiration_var.set(formated_act_date)
        self.state_var.set("BORRADOR")
        self.iva_var.set("0")
        self.discount_var.set("0")
        self.subtotal_var.set("0")
        self.total_var.set("0")

        btn_frame = ctk.CTkFrame(card_frame, fg_color="white")
        btn_frame.pack(pady=20)

        # Configurar columnas para botones
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Guardar Factura",
            fg_color=btn_color,
            hover_color=btn_hover,
            height=40,
            width=180,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=lambda: self.controller.add_new_invoice(self.invoice_win, parent)
        )
        save_btn.grid(row=0, column=0, padx=15)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            height=40,
            width=180,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=lambda: close_win(self.invoice_win, parent, self.clear_invoice_form)
        )
        cancel_btn.grid(row=0, column=1, padx=15)

    def clear_invoice_form(self):
        """Limpiar formulario de factura"""
        self.invoice_id_var.set('')
        self.invoice_type_var.set('')
        self.expiration_var.set('')
        self.subtotal_var.set('')
        self.iva_var.set('')
        self.discount_var.set('')
        self.obs_var.set('')
        self.total_var.set('')
        self.state_var.set('')

    def get_invoice_form_data(self):
        """Obtener datos del formulario de factura"""
        return {
            'supplier_cuit': self.supplier_var.get().strip(),
            'invoice_id': self.invoice_id_var.get().strip(),
            'invoice_type': self.invoice_type_var.get().strip(),
            'expiration_date': self.expiration_var.get().strip(),
            'subtotal': self.subtotal_var.get().strip(),
            'iva': self.iva_var.get().strip(),
            'discount': self.discount_var.get().strip(),
            'observations': self.obs_var.get().strip(),
            'total': self.total_var.get().strip(),
            'state': self.state_var.get().strip(),
        }