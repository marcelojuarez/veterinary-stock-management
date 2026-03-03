import tkinter as tk
from tksheet import Sheet
import customtkinter as ctk
from utils.utils import iso_to_traditional
from services.purchase_detail import PurchaseDetail
from utils.invoice_utils import pay_period_control, calculate_exp_date
from utils.view_helpers import close_win, ask_confirmation, show_success, show_warning, show_error

class PurchaseInfoInvoiceView():
    def __init__(self, model, controller):
        self.model = model
        self.controller = controller
        self.purchase_detail = PurchaseDetail(model)

    def show_purchase_info(self, parent, values):
        try:
            self.invoice_state = tk.StringVar()
            self.invoice_state.set(values[6])

            purchase_info = ctk.CTkToplevel(parent)
            purchase_info.configure(fg_color="#B0A8A8")
            purchase_info.withdraw() # Se oculta la ventana

            purchase_info.title("Informacion de la Compra")
            purchase_info.protocol(
                "WM_DELETE_WINDOW",
                lambda: close_win(purchase_info, parent)
            )

            main_frame = ctk.CTkFrame(purchase_info, corner_radius=12, fg_color="white")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            header_frame = ctk.CTkFrame(main_frame, height=50, fg_color="white")
            header_frame.pack(fill="x", padx=10, pady=10)
            header_frame.pack_propagate(False)

            header = ctk.CTkLabel(
                header_frame,
                text=f"Detalle de la compra: (ID: {values[0]}) - {self.invoice_state.get()}",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            header.pack(side='left', anchor='w', padx=5)

            self.confirm_btn = ctk.CTkButton(
                header_frame,
                text='Confirmar Compra',
                width=130,
                fg_color = "#009688",
                hover_color = "#00796B",
                font=ctk.CTkFont(size=15, weight="bold"),
                command= lambda: self.confirm_purchase(values[0])
            )
            self.confirm_btn.pack(side='right', anchor='w', padx=5)

            self.info_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="white")
            self.info_frame.pack(fill="x", padx=10, pady=(0, 20)) 

            self.purchase_id = values[0]
            purchase_data = self.model.purchase.get_purchase_by_id(self.purchase_id)

            doc_type = purchase_data[2] if purchase_data else None
            if doc_type == "REMITO":
                self.show_invoice_fields(doc_id=None)
            else:
                print(f"pruchase data 3: {purchase_data[3]}")
                self.show_invoice_fields(doc_id=purchase_data[3])

            # Productos asociados a la compra
            sep = ctk.CTkLabel(
                main_frame,
                text='Productos asociados a la compra',
                font=ctk.CTkFont(size=20, weight="bold")
            )

            sep.pack(anchor="w", padx=20, pady=(5, 5))

            table_frame = ctk.CTkFrame(main_frame, corner_radius=10)
            table_frame.pack(fill="both", expand=True, padx=10)

            headers = ["Id", "Nombre", "Envase", "Cantidad", "Precio Lista", "Dto %", 'Precio Costo', "Iva %", 
                        "Monto Descuento", "Subtotal", "Monto Iva", "Total"]

            self.sheet = Sheet(
                table_frame,
                headers=headers,
                show_x_scrollbar=True,
                show_y_scrollbar=True
            )
            self.sheet.enable_bindings((
                "single_select",
                "column_width_resize",
                "double_click_column_resize",
            ))

            self.sheet.set_options(row_select=True)
            self.sheet.pack(fill="both", expand=True, padx=5, pady=5)

            self.load_data_into_the_sheet()

            btn_frame = ctk.CTkFrame(main_frame, height=50, fg_color="white")
            btn_frame.pack(fill='x', padx=10, pady=5)
            btn_frame.pack_propagate(False)

            btn_frame.columnconfigure(0, weight=1)
            btn_frame.columnconfigure(1, weight=1)
            btn_frame.columnconfigure(2, weight=1)

            self.save_btn = ctk.CTkButton(
                btn_frame,
                text="Guardar",
                fg_color="#3A3251",
                hover_color="#3A3251",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=120,
                state='disabled',
                command=lambda: self.save(values[0])
            )
            self.save_btn.grid(row=0, column=0, padx=10)

            self.edit_btn = ctk.CTkButton(
                btn_frame,
                text="Editar",
                fg_color="#2980B9",
                hover_color="#0B5D94",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=120,
                command=lambda: self.edit(values[0])
            )
            self.edit_btn.grid(row=0, column=1, padx=10)

            self.del_item_btn = ctk.CTkButton(
                btn_frame,
                text="Eliminar Item",
                fg_color="#2980B9",
                hover_color="#0B5D94",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=120,
                command=self.handle_delete_purchase_item
            )
            self.del_item_btn.grid(row=0, column=2, padx=10)

            self.print_info = ctk.CTkButton(
                btn_frame,
                text="Imprimir Detalle",
                fg_color="#0B9E97",
                hover_color="#087E78",
                font=ctk.CTkFont(size=13, weight="bold"),
                command= lambda: self.gen_purchase_detail_pdf()
            )
            self.print_info.grid(row=0, column=3, padx=10)

            close_btn = ctk.CTkButton(
                btn_frame,
                text="Cerrar",
                fg_color="#E74C3C",
                hover_color="#C0392B",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=120,
                command=lambda: close_win(purchase_info, parent, parent.focus_force)
            )
            close_btn.grid(row=0, column=4, padx=10)

            width_win = 950
            height_win = 750

            x_root = parent.winfo_x()
            y_root = parent.winfo_y()
            width_root = parent.winfo_width()
            height_root = parent.winfo_height()

            x = x_root + (width_root // 2) - (width_win // 2)
            y = y_root + (height_root // 2) - (height_win // 2)

            purchase_info.geometry(f"{width_win}x{height_win}+{x}+{y}")
            purchase_info.resizable(False, False)

            purchase_info.deiconify()

            purchase_info.transient(parent)
            purchase_info.grab_set()

        except ValueError as e:
            print(f'Error{e}')

        except Exception as e:
            print(f'Error{e}')

    ## -- Renderiza los campos de la factura y carga sus datos-- ##
    def show_invoice_fields(self, doc_id):
        self._loading = False
        self.invoice_vars = {
                'number': tk.StringVar(),
                'type': tk.StringVar(),
                'date': tk.StringVar(),
                'expiration': tk.StringVar(),
                's_iva_c': tk.StringVar(),
                'pay_cond': tk.StringVar(),
                'pay_period': tk.StringVar(),
                'obs': tk.StringVar(),
                'orig_subtotal': tk.StringVar(),
                'discount': tk.StringVar(),
                'discount_amount': tk.StringVar(),
                'subtotal_w_discount': tk.StringVar(),
                'iva': tk.StringVar(),
                'iibb_per': tk.StringVar(),
                'iva_per': tk.StringVar(),
                'total': tk.StringVar()
            }
        
        self.load_invoice_data(doc_id)

        if self.invoice_state.get() != "BORRADOR":
            self.confirm_btn.configure(state=tk.DISABLED)

        def add_field(row, column, label, widget):
            field_lbl = ctk.CTkLabel(
                self.info_frame,
                text=label,
                font=ctk.CTkFont(size=13, weight='bold'),
                text_color='black',
            )
            field_lbl.grid(row=row, column=column, sticky="e", padx=10, pady=7)

            widget.grid(row=row, column=column+1, padx=(10,20), pady=7, sticky='w')

            return widget

        # NUMERO DE FACTURA
        self.num_entry = add_field(
                        0, 0, "Número de Factura: ", 
                        ctk.CTkEntry(
                            self.info_frame, 
                            textvariable=self.invoice_vars["number"], 
                            width=120, 
                            font=ctk.CTkFont(size=11),
                            state='readonly'
                        )
                    )

        # TIPO DE FACTURA
        add_field(
            1, 0, "Tipo de Factura: ", 
            ctk.CTkEntry(
                self.info_frame,
                textvariable=self.invoice_vars["type"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )

        # FECHA
        self.date_entry = add_field(
                        2, 0, "Fecha: ", 
                        ctk.CTkEntry(
                            self.info_frame, 
                            textvariable=self.invoice_vars["date"], 
                            width=120,
                            font=ctk.CTkFont(size=11),
                            state='readonly' 
                        )
                    )

        # FECHA DE VENC
        add_field(
            3, 0, "Fecha de Venc: ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars["expiration"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly' 
            )
        )

        # OBSERVACIONES
        self.obs_entry = add_field(
                        4, 0, "Observaciones: ", 
                        ctk.CTkEntry(
                            self.info_frame, 
                            textvariable=self.invoice_vars["obs"], 
                            width=120, 
                            height=60, 
                            font=ctk.CTkFont(size=11),
                            state='readonly'
                        )
                    )

        #ESTADO
        add_field(
            5, 0, "Cond. Iva Proveedor: ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars['s_iva_c'], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )

        # CONDICION DE PAGO
        self.pay_cond_wid = add_field(
                            0, 2, "Cond. De Pago: ", 
                            ctk.CTkComboBox(
                                self.info_frame, 
                                values=["CTA CTE", "CONTADO"],
                                variable=self.invoice_vars["pay_cond"], 
                                width=120, 
                                font=ctk.CTkFont(size=11),
                                state='disabled'
                            )
                        )

        # PLAZO EN DIAS PARA EL PAGO
        self.pay_period_wid = add_field(
                            1, 2, "Plazo en dias: ", 
                            ctk.CTkComboBox(
                                self.info_frame, 
                                values=["7", "15", "30", "45", "60", "90"],
                                variable=self.invoice_vars["pay_period"],
                                width=120, 
                                font=ctk.CTkFont(size=11),
                                state='disabled'
        ))

        # SUBTOTAL ORIGINAL
        add_field(
            2, 2, "Subtotal: ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars["orig_subtotal"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
        ))

        # DESCUENTO
        add_field(
            3, 2, "Dto %: ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars["discount"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )

        # MONTO DESCUENTO
        add_field(
            4, 2, "Monto Dto: ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars["discount_amount"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
        ))

        # SUBTOTAL CON DESCUENTO
        add_field(
            5, 2, "Subtotal C/Dto: ", 
            ctk.CTkEntry(
                self.info_frame,
                textvariable=self.invoice_vars["subtotal_w_discount"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly' 
            )
        )     

        # PERCEPCION IIBB
        add_field(
            0, 4, "Percepcion IIBB:  ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars["iibb_per"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )   

        # PERCEPCION IVA
        add_field(
            1, 4, "Percepcion IVA:  ",
            ctk.CTkEntry(
                self.info_frame,
                textvariable=self.invoice_vars["iva_per"],
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )   

        # IVA
        add_field(
            2, 4, "Monto IVA:  ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars["iva"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
            )
        )   
 
        # Total
        add_field(
            3, 4, "Total: ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.invoice_vars["total"], 
                width=120, 
                font=ctk.CTkFont(size=11),
                state='readonly'
        ))


        self.invoice_vars["pay_cond"].trace_add(
            "write", 
            lambda *args: pay_period_control(
                        self.invoice_vars["pay_cond"], 
                        self.invoice_vars["pay_period"],
                        self.pay_period_wid
                    )
        )

        self.invoice_vars["date"].trace_add(
            "write",
            lambda *args: self._loading or calculate_exp_date(
                self.invoice_vars["date"],
                self.invoice_vars["pay_period"],
                self.invoice_vars["expiration"]
            )
        )
        self.invoice_vars["pay_period"].trace_add(
            "write",
            lambda *args: self._loading or calculate_exp_date(
                self.invoice_vars["date"],
                self.invoice_vars["pay_period"],
                self.invoice_vars["expiration"]
            )
        )

        self.customizable_wid = [
            self.num_entry,
            self.date_entry,
            self.obs_entry,
            self.pay_cond_wid,
            self.pay_period_wid
        ]

    ## Carga los campos asociados a la factura
    def load_invoice_data(self, doc_id):
        if doc_id is None:
            return
        invoice_data = self.model.purchase.supplier_invoice.get_invoice_data(doc_id)
        if invoice_data is None:
            return
        iibb_p_amount = self.model.purchase.supplier_invoice.get_iibb_per_amount(doc_id) 
        iva_p_amount = self.model.purchase.supplier_invoice.get_iva_per_amount(doc_id)

        self.invoice_vars['number'].set(invoice_data[2])
        self.invoice_vars['type'].set(invoice_data[3])
        self.invoice_vars['date'].set(iso_to_traditional(invoice_data[4]))
        self.invoice_vars['expiration'].set(iso_to_traditional(invoice_data[5]))
        self.invoice_vars['s_iva_c'].set(invoice_data[6])
        self.invoice_vars['pay_cond'].set(invoice_data[9])
        self.invoice_vars['pay_period'].set(invoice_data[10])
        self.invoice_vars['obs'].set(invoice_data[8])
        self.invoice_vars['orig_subtotal'].set(invoice_data[11])
        self.invoice_vars['discount'].set(invoice_data[12])
        self.invoice_vars['discount_amount'].set(invoice_data[13])
        self.invoice_vars['subtotal_w_discount'].set(invoice_data[14])
        self.invoice_vars['iva'].set(invoice_data[15])
        self.invoice_vars['iibb_per'].set(str(iibb_p_amount))
        self.invoice_vars['iva_per'].set(str(iva_p_amount))
        self.invoice_vars['total'].set(invoice_data[16])

        self._loading = False

    ## -- Obtener datos de la factura -- ##
    def get_invoice_data(self):
        return {
            'invoice_id': self.invoice_vars['number'].get().strip(),
            'date': self.invoice_vars['date'].get().strip(),
            'expiration': self.invoice_vars['expiration'].get().strip(),
            'obs': self.invoice_vars['obs'].get().strip(),
            'pay_cond': self.invoice_vars['pay_cond'].get().strip(),
            'pay_period': self.invoice_vars['pay_period'].get().strip()
        }

    ## -- Carga tabla con informacion -- ##
    def load_data_into_the_sheet(self):
        data = self.model.purchase.get_purchase_items(self.purchase_id)

        self.sheet.set_sheet_data(data)
        self.sheet.set_column_widths([60, 260, 120, 80, 120, 100, 120, 100, 120, 120, 120, 120])

    ## -- Generar purchase detail como pdf -- ##
    def gen_purchase_detail_pdf(self):
        try:
            self.purchase_detail.generate_purchase_detail(self.purchase_id)
            show_success(f'Detalle de compra generado con exito')
        except ValueError as e:
            print(f'Error: {e}')

    ## -- Manejo para eliminar un item de compra-- ##
    def handle_delete_purchase_item(self):
        try: 
            selected_cells = list(self.sheet.get_selected_cells())

            if not selected_cells:
                show_error('Por favor seleccione un item de compra')
                return

            string_error = 'Error. No se pueden eliminar items de una compra ya confirmada'

            state = self.invoice_state.get()
            if state != 'BORRADOR': 
                show_error(f'{string_error}') 
                return

            row_num = selected_cells[0][0]

            row_data = self.sheet.get_row_data(row_num)
            p_id = row_data[0]

            self.controller.delete_purchase_item(self.purchase_id, p_id)

        except ValueError as e:
            print(f'Error: {e}') 

    ## -- Confirmar Compra -- ##
    def confirm_purchase(self, purchase_id):

        # confirmar compra
        if ask_confirmation('Desea confirmar esta Compra', 'Este es el titulo'):
            result = self.controller.confirm_purchase(purchase_id)
            if result:
                self.confirm_btn.configure(state=tk.DISABLED)

        else:
            return

    ## --  Editar campos de los documentos asociados a la compra -- ##
    def edit(self, purchase_id):
        if self.invoice_state.get() != 'BORRADOR':
            show_error('No se puede editar una compra ya confirmada.')
            return

        show_warning('Datos editables')
        self.save_previous_values()
        self.print_info.configure(state='disabled')

        self.edit_btn.configure(
            text='Cancelar Edicion',
            fg_color="#0F4E57",
            hover_color="#082F35",
            width=150,
            command=lambda: self.recover_previous_values_of_invoice(purchase_id)
        )

        self.save_btn.configure(state='normal')
        self.save_btn.configure(fg_color="#4927AC")
        self.save_btn.configure(hover_color="#260980")

        for w in self.customizable_wid:
            w.configure(state='normal')

        self.customizable_wid[0].focus()

    ## -- Guardar datos editados de compra -- ##
    def save(self, purchase_id):
        result = self.controller.update_doc_info(purchase_id, 'FACTURA')

        if result:

            # Recuperar boton de edicion
            self.edit_btn.configure(
                text="Editar",
                fg_color="#2980B9",
                hover_color="#0B5D94",
                width=120,
                command= lambda: self.edit(purchase_id)
            )

            # campos en estado normal
            self.num_entry.configure(state='readonly')
            self.date_entry.configure(state='readonly')
            self.obs_entry.configure(state='readonly')
            self.pay_cond_wid.configure(state='disabled')
            self.pay_period_wid.configure(state='disabled')

            self.save_btn.configure(state='disabled')   
            self.save_btn.configure(fg_color="#3A3251")
            self.save_btn.configure(hover_color="#3A3251")    

            self.print_info.configure(state='normal')

    ## --  Guardar valores anteriores de campos -- ##
    def save_previous_values(self):

        self.custom_wid_values = [
            self.customizable_wid[0].get(), # invoice_id
            self.customizable_wid[1].get(), # date
            self.customizable_wid[2].get(), # obs
            self.customizable_wid[3].get(), # pay_cond
            self.customizable_wid[4].get()  # pay_period
        ]

    ## --  Recuperar valores previos de los campos -- ##
    def recover_previous_values_of_invoice(self, purchase_id):

        self.print_info.configure(state='normal')

        # Recuperar boton de edicion
        self.edit_btn.configure(
            text="Editar",
            fg_color="#2980B9",
            hover_color="#0B5D94",
            width=120,
            command= lambda: self.edit(purchase_id)
        )

        # Recuperar valores
        self.invoice_vars['number'].set(self.custom_wid_values[0])
        self.invoice_vars['date'].set(self.custom_wid_values[1])
        self.invoice_vars['obs'].set(self.custom_wid_values[2])
        self.invoice_vars['pay_cond'].set(self.custom_wid_values[3])
        self.invoice_vars['pay_period'].set(self.custom_wid_values[4])
        
        # campos en estado normal
        self.num_entry.configure(state='readonly')
        self.date_entry.configure(state='readonly')
        self.obs_entry.configure(state='readonly')
        self.pay_cond_wid.configure(state='disabled')
        self.pay_period_wid.configure(state='disabled')