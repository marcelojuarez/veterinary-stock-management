import tkinter as tk
import customtkinter as ctk
from datetime import datetime
from utils.utils import iso_to_traditional, format_currency
from utils.view_helpers import close_win, show_warning
from utils.invoice_utils import pay_period_control, calculate_exp_date

class SupplierInvoiceForm():
    def __init__(self, view, frame, invoice_controller, supp_mdl):
        self.view = view
        self.frame = frame
        self.supp_mdl = supp_mdl
        self.controller = invoice_controller
        self.controller.set_form_view(self)

    def setup_variables(self, supplier_id):
        self.supplier_cuit_var = tk.StringVar()
        self.supplier_name_var = tk.StringVar()
        
        supplier_data = self.supp_mdl.core.find_supplier_by_id(supplier_id)

        self.supplier_cuit_var.set(supplier_data[1])
        self.supplier_name_var.set(supplier_data[2])

        # Condicion IVA proveedor
        self.s_iva_c_var = tk.StringVar()
        self.s_iva_c_var.set(supplier_data[9])

        self.invoice_id_var = tk.StringVar()
        self.invoice_type_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.expiration_var = tk.StringVar()
        self.iva_var = tk.StringVar()
        self.obs_var = tk.StringVar()
        self.pay_cond_var = tk.StringVar()
        self.pay_period_var = tk.StringVar()

        self.discount_var = tk.StringVar()
        
        # Percepciones
        self.iibb_per_var = tk.StringVar()
        self.iva_per_var = tk.StringVar()

        self.subtotal_var = tk.StringVar()
        self.total_var = tk.StringVar()

    def open_invoice_form(self, parent, supplier_id):
        btn_color = "#009688"
        btn_hover = "#00796B"

        self.setup_variables(supplier_id)

        if self.supplier_cuit_var.get() == "":
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
        width_win = 800
        height_win = 560

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
        def add_field(row, column, label, widget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight='bold'),
                text_color='black',
            )
            field_lbl.grid(row=row, column=column, sticky="e", padx=10, pady=7)

            widget.grid(row=row, column=column+1, padx=(10,20), pady=7, sticky='w')

            return widget

        ## CAMPOS

        # CUIT Proveedor
        add_field(
            0, 0, "CUIT Proveedor:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.supplier_cuit_var, 
                state='readonly', 
                width=160, 
                font=ctk.CTkFont(size=11)
            )
        )
        
        # Nombre proveedor
        add_field(
            1, 0, "Nombre Proveedor:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.supplier_name_var,
                state='readonly', 
                width=180,
                font=ctk.CTkFont(size=11)
            )
        )

        # Número Factura
        add_field(
            2, 0, "Número Factura:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.invoice_id_var,
                width=160,
                font=ctk.CTkFont(size=11)
            )
        )

        # Condicion IVA proveedor
        add_field(
            3, 0, "Cond. IVA Proveedor:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.s_iva_c_var, 
                width=160,
                font=ctk.CTkFont(size=11),
                state="readonly"
            )
        )
        
        # Tipo Factura
        invoice_type = add_field(
                            4, 0,  "Tipo:",
                            ctk.CTkComboBox(
                                form_frame, 
                                variable=self.invoice_type_var, 
                                width=160,
                                font=ctk.CTkFont(size=11),
                                state="readonly"
                            )
                        )
        
        ## Tipo de Factura segun cond IVA proveedor
        if self.s_iva_c_var.get() == "RESP. INSCRIPTO" or self.s_iva_c_var.get() == "RESP. INS":
            invoice_type.configure(values=['A', 'M'])
            self.invoice_type_var.set('A')
        
        elif self.s_iva_c_var.get() == "MONOTRIBUTISTA":
            invoice_type.configure(values=['C'])
            self.invoice_type_var.set('C')

        elif self.s_iva_c_var.get() in ("EXENTO", "NO RESPONSABLE"):
            invoice_type.configure(values=['B'])                                
            self.invoice_type_var.set('B')
        
        # Observaciones
        add_field(
            5, 0, "Observaciones:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.obs_var, 
                width=160, 
                height=60,
                font=ctk.CTkFont(size=11)
            )
        )
        
        # Condicion de Pago
        add_field(
            6, 0, "Cond. De Pago:", 
            ctk.CTkComboBox(
                form_frame, 
                values=["CTA CTE", "CONTADO"], 
                variable=self.pay_cond_var, 
                width=160, 
                font=ctk.CTkFont(size=11),
                state="readonly"
            )
        )

        # Plazo en Dias
        pay_period_wid = add_field(
                                    7, 0, "Plazo en dias:", 
                                    ctk.CTkComboBox(
                                        form_frame,
                                        values=["7", "15", "30", "45", "60", "90"], 
                                        variable=self.pay_period_var, 
                                        width=100, 
                                        font=ctk.CTkFont(size=11),
                                        state="readonly"
                                    )
                                )

        # Fecha
        add_field(
            0, 2, "Fecha:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.date_var, 
                width=160, 
                font=ctk.CTkFont(size=11),
            )
        )

        # Fecha Vencimiento
        add_field(
            1, 2, "Fecha Venc:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.expiration_var,
                width=160,
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )
        
        # Monto IVA
        add_field(
            2, 2,"Monto IVA:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.iva_var, 
                width=160,
                font=ctk.CTkFont(size=11),
                state='readonly',
            )
        )
        
        # Descuento
        add_field(
            3, 2,"Descuento:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.discount_var, 
                width=160,
                font=ctk.CTkFont(size=11),
            )
        )
        
        # Subtotal
        add_field(
            4, 2, "Subtotal:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.subtotal_var, 
                width=160,
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )
        
        # Percepcion IIBB
        add_field(
            5, 2, "Percepcion IIBB:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.iibb_per_var,
                width=160,
                font=ctk.CTkFont(size=11),
            )
        )
        
        # Percepcion IVA
        add_field(
            6, 2, "Percepcion IVA:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.iva_per_var, 
                width=160,
                font=ctk.CTkFont(size=11),
            )
        )
        
        # Total
        add_field(
            7, 2, "Total:", 
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.total_var, 
                width=160,
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )

        self.pay_cond_var.set("CTA CTE")
        self.pay_period_var.set("30")
        self.iva_var.set("0.00")
        self.subtotal_var.set("0.00")
        self.total_var.set("0.00")

        self.pay_cond_var.trace_add(
            "write", 
            lambda *args: pay_period_control(
                        self.pay_cond_var, 
                        self.pay_period_var,
                        pay_period_wid
                    )
        )

        self.date_var.trace_add(
            "write", 
            lambda *args: calculate_exp_date(
                self.date_var,
                self.pay_period_var,
                self.expiration_var
            )
        )
        self.pay_period_var.trace_add(
            "write", 
            lambda *args: calculate_exp_date(
                self.date_var,
                self.pay_period_var,
                self.expiration_var
            )
        )

        self.date_var.set(iso_to_traditional(str(datetime.now().date())))

        btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Guardar factura",
            fg_color=btn_color,
            hover_color=btn_hover,
            height=40,
            width=160,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.controller.add_new_invoice(self.invoice_win, parent, supplier_id)
        )
        save_btn.grid(row=0, column=0, padx=15)

        self.invoice_win.bind("<Return>", lambda event: save_btn.invoke())

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            height=40,
            width=160,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: close_win(self.invoice_win, parent)
        )
        cancel_btn.grid(row=0, column=1, padx=15)
        
    ## -- Obtener datos del formulario -- ##
    def get_invoice_form_data(self):
        """Obtener datos del formulario de factura"""
        return {
            'invoice_id': self.invoice_id_var.get().strip(),
            'invoice_type': self.invoice_type_var.get().strip(),
            'date': self.date_var.get().strip(),
            'expiration_date': self.expiration_var.get().strip(),
            's_iva_c': self.s_iva_c_var.get().strip(),
            'discount': self.discount_var.get().strip(),
            'observations': self.obs_var.get().strip(),
            'pay_cond': self.pay_cond_var.get().strip(),
            'pay_period': self.pay_period_var.get().strip(),
            'iibb_per': self.iibb_per_var.get().strip(),
            'iva_per': self.iva_per_var.get().strip(),
            'subtotal': self.subtotal_var.get().strip(),
            'iva': self.iva_var.get().strip(),
            'total': self.total_var.get().strip(),
        }