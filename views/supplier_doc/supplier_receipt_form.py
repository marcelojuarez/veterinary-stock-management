import datetime
import tkinter as tk
import customtkinter as ctk
from utils.view_helpers import close_win, show_warning

class SupplierReceiptForm():
    def __init__(self, view, frame, receipt_controller, supp_mdl):
        self.view = view
        self.frame = frame
        self.supp_mdl = supp_mdl
        self.controller = receipt_controller
        self.controller.set_form_view(self)

    def setup_variables(self, supplier_id):
        self.supplier_cuit_var = tk.StringVar()
        self.supplier_name_var = tk.StringVar()

        supplier_data = self.supp_mdl.core.find_supplier_by_id(supplier_id)

        self.supplier_cuit_var.set(supplier_data[1])
        self.supplier_name_var.set(supplier_data[2])

        self.receipt_id_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.expiration_var = tk.StringVar()
        self.ob_var = tk.StringVar()
        self.total_var = tk.StringVar()  

    def open_receipt_form(self, parent, supplier_id):
        btn_color = "#009688"
        btn_hover = "#00796B"

        self.setup_variables(supplier_id)
        actual_date = datetime.datetime.now()
        formated_act_date = actual_date.strftime("%d/%m/%Y")

        if self.supplier_cuit_var.get() == "":
            show_warning("Por favor seleccione un Proveedor")
            return

        self.receipt_win = ctk.CTkToplevel(self.frame)

        self.receipt_win.title("Registrar nuevo Remito")
        self.receipt_win.withdraw()
        self.receipt_win.protocol("WM_DELETE_WINDOW",
                                lambda: close_win(self.receipt_win, parent))

        # fondo general gris
        self.receipt_win.configure(fg_color="#e0e0e0")

        # contenedor blanco
        card_frame = ctk.CTkFrame(
            self.receipt_win,
            fg_color="white",
            corner_radius=20
        )
        card_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # titulo
        title_label = ctk.CTkLabel(
            card_frame,
            text="Nuevo Remito",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="black"
        )
        title_label.pack(pady=20)

        # contenedor del formulario
        form_frame = ctk.CTkFrame(card_frame, fg_color="white")
        form_frame.pack(pady=5, padx=10, fill="x")

        # --- Campos ---
        def add_field(row, label, widget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="black"
            )
            field_lbl.grid(row=row, column=0, sticky="e", padx=(10,10), pady=7)

            widget.grid(row=row, column=1, padx=(10,20), pady=7, sticky="w")
            return widget

        # CUIT Proveedor
        add_field(
            0, "CUIT Proveedor:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.supplier_cuit_var, 
                width=200,
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )

        # CUIT Proveedor
        add_field(
            1, "Nombre Proveedor:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.supplier_name_var, 
                width=200,
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )

        # Número Remito
        self.num_entry = add_field(
                        2, "N° Remito:",
                        ctk.CTkEntry(
                            form_frame, 
                            textvariable=self.receipt_id_var, 
                            width=200,
                            font=ctk.CTkFont(size=11),
                        )
                    )
        
        # Fecha 
        add_field(
            3, "Fecha:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.date_var, 
                width=200,
                font=ctk.CTkFont(size=11),
            )
        )

        # Fecha Vencimiento
        add_field(
            4, "Vencimiento:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.expiration_var, 
                width=200,
                font=ctk.CTkFont(size=11)
            )
        )

        # Observaciones
        add_field(
            5, "Observaciones:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.ob_var, 
                width=200, 
                height=80,
                font=ctk.CTkFont(size=11)
            )
        )

        # Total
        add_field(
            6, "Total:",
            ctk.CTkEntry(
                form_frame, 
                textvariable=self.total_var, 
                width=200,
                font=ctk.CTkFont(size=11), 
                state='readonly'
            )
        )
        
        self.date_var.set(formated_act_date)
        self.expiration_var.set(formated_act_date)
        self.total_var.set("0.00")

        # --- Botones inferior ---
        button_frame = ctk.CTkFrame(card_frame, fg_color="white")
        button_frame.pack(pady=20)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Guardar Remito",
            fg_color=btn_color,
            hover_color=btn_hover,
            height=40,
            width=160,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda:self.controller.add_new_receipt(self.receipt_win, parent, supplier_id)
        )
        save_btn.grid(row=0, column=0, padx=15)

        self.receipt_win.bind("<Return>", lambda event: save_btn.invoke())

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancelar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            height=40,
            width=160,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: close_win(self.receipt_win, parent)
        )
        cancel_btn.grid(row=0, column=1, padx=15)

        # centrar ventana
        width_win = 500
        height_win = 550

        x_root = parent.winfo_x() 
        y_root = parent.winfo_y()
        width_root = parent.winfo_width()
        height_root = parent.winfo_height()

        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        self.receipt_win.geometry(f"{width_win}x{height_win}+{x}+{200}")
        self.receipt_win.deiconify()
        self.receipt_win.transient(parent)
        self.receipt_win.grab_set()

        self.setup_final_focus()

    def setup_final_focus(self):
        self.receipt_win.focus_force() 
        self.receipt_win.after(50, lambda: self.num_entry.focus_set())

    ## -- Obtener datos del formulario -- ##
    def get_receipt_form_data(self):
        """Obtener datos del formulario de factura"""
        return {
            'receipt_id': self.receipt_id_var.get().strip(),
            'date': self.date_var.get().strip(),
            'expiration_date': self.expiration_var.get().strip(),
            'observations': self.ob_var.get().strip(),
            'total': self.total_var.get().strip(),
        }