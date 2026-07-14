import logging
import tkinter as tk
from tksheet import Sheet
import customtkinter as ctk
from services.purchase_detail import PurchaseDetail
from utils.utils import iso_to_traditional, format_currency, format_currency_flex
from utils.invoice_utils import pay_period_control, calculate_exp_date
from utils.view_helpers import center_window, close_win, ask_confirmation, show_success, show_warning, show_error
from utils.printing import send_to_printer
from tkinter.messagebox import askyesno

logger = logging.getLogger(__name__)

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
            purchase_info.configure(fg_color="#e0e0e0")
            purchase_info.withdraw()

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
                text=f"Detalle de la compra: {self.invoice_state.get()}",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            header.pack(side='left', anchor='w', padx=5)

            self.confirm_btn = ctk.CTkButton(
                header_frame,
                text='Confirmar compra',
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
                self.show_invoice_fields(doc_id=purchase_data[3])

            btn_frame = ctk.CTkFrame(main_frame, fg_color="#f5f5f5", corner_radius=10)
            btn_frame.pack(fill='x', padx=10, pady=(5, 10), side='bottom')

            # Productos asociados a la compra
            sep = ctk.CTkLabel(
                main_frame,
                text='Productos asociados a la compra',
                font=ctk.CTkFont(size=20, weight="bold")
            )

            sep.pack(anchor="w", padx=20, pady=(5, 5))

            table_frame = ctk.CTkFrame(main_frame, corner_radius=10)
            table_frame.pack(fill="both", expand=True, padx=10)

            headers = ["Id", "Nombre", "Envase", "Cantidad", "Bonif.", "Dto % x Bonif.", "Precio Lista", "Dto %", 
                       'Precio Costo', "Iva %", "Monto Descuento", "Subtotal", "Monto Total Iva", "Total"]

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

            # columnas: spacer | btn | btn | btn | btn | btn | spacer
            for i in (0, 6):
                btn_frame.grid_columnconfigure(i, weight=1)
            for i in (1, 2, 3, 4, 5):
                btn_frame.grid_columnconfigure(i, weight=1)

            self.save_btn = ctk.CTkButton(
                btn_frame,
                text="💾 Guardar",
                fg_color="#9E9E9E",
                hover_color="#757575",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=130,
                height=36,
                state='disabled',
                command=lambda: self.save(values[0])
            )
            self.save_btn.grid(row=0, column=1, padx=6, pady=10)

            self.edit_btn = ctk.CTkButton(
                btn_frame,
                text="✏️ Editar",
                fg_color="#2980B9",
                hover_color="#0B5D94",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=130,
                height=36,
                command=lambda: self.edit(values[0])
            )
            self.edit_btn.grid(row=0, column=2, padx=6, pady=10)

            self.del_item_btn = ctk.CTkButton(
                btn_frame,
                text="🗑 Eliminar item",
                fg_color="#E74C3C",
                hover_color="#C0392B",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=130,
                height=36,
                command=self.handle_delete_purchase_item
            )
            self.del_item_btn.grid(row=0, column=3, padx=6, pady=10)

            self.print_info = ctk.CTkButton(
                btn_frame,
                text="🖨 Imprimir",
                fg_color="#0B9E97",
                hover_color="#087E78",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=130,
                height=36,
                command=lambda: self.gen_purchase_detail_pdf()
            )
            self.print_info.grid(row=0, column=4, padx=6, pady=10)

            close_btn = ctk.CTkButton(
                btn_frame,
                text="✖ Cerrar",
                fg_color="#757575",
                hover_color="#616161",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=130,
                height=36,
                command=lambda: close_win(purchase_info, parent, parent.focus_force)
            )
            close_btn.grid(row=0, column=5, padx=6, pady=10)

            width_win = 950
            height_win = 700

            center_window(purchase_info, width_win, height_win)

            purchase_info.deiconify()

            purchase_info.transient(parent)
            purchase_info.grab_set()

        except ValueError as e:
            logger.error("Error en vista de factura: %s", e)

        except Exception as e:
            logger.error("Error en vista de factura: %s", e)

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
        self.invoice_vars['orig_subtotal'].set(format_currency(invoice_data[11]))
        self.invoice_vars['discount'].set(invoice_data[12])
        self.invoice_vars['discount_amount'].set(format_currency(invoice_data[13]))
        self.invoice_vars['subtotal_w_discount'].set(format_currency(invoice_data[14]))
        self.invoice_vars['iva'].set(format_currency(invoice_data[15]))
        self.invoice_vars['iibb_per'].set(format_currency(iibb_p_amount))
        self.invoice_vars['iva_per'].set(format_currency(iva_p_amount))
        self.invoice_vars['total'].set(format_currency(invoice_data[16]))

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
        data_raw = self.model.purchase.get_purchase_items(self.purchase_id)

        data = [
            [           
                id, # id
                name, # name
                pack, # pack
                qty, # quantity
                f"+{bonus_qty}" if bonus_qty and int(bonus_qty) > 0 else "—",
                bonus_discount, # bonus discount
                format_currency_flex(l_price), # list_price
                discount, # discount
                format_currency_flex(c_price), # cost_price
                iva_rate, # iva 
                format_currency(discount_amt), # discount_amount
                format_currency(subtotal), # subtotal
                format_currency(iva_amt), # iva_amount
                format_currency(total) # total
            ]

            for id, name, pack, qty, l_price, discount, c_price, iva_rate, discount_amt, 
            bonus_qty, bonus_discount, subtotal, iva_amt, total in data_raw

        ]

        self.sheet.set_sheet_data(data)
        self.sheet.set_column_widths([60, 260, 120, 80, 70, 90, 120, 100, 120, 100, 120, 120, 120, 120])

    ## -- Generar purchase detail como pdf -- ##
    def gen_purchase_detail_pdf(self):
        try:
            path = self.purchase_detail.generate_purchase_detail(self.purchase_id)
            show_success(f'Detalle de compra generado con exito: {path}')

            if askyesno("Imprimir Detalle de Compra", f"¿Desea imprimir el Detalle de Compra?"):
                success = send_to_printer(path)
                if not success:
                    show_error("No se pudo realizar la impresion")
            
        except ValueError as e:
            logger.error("Error en vista de factura: %s", e)

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
            logger.error("Error en vista de factura: %s", e) 

    ## -- Confirmar Compra -- ##
    def confirm_purchase(self, purchase_id):
        if not ask_confirmation('¿Desea confirmar esta compra?', 'Confirmar compra'):
            return
        self.confirm_btn.configure(state="disabled", text="Procesando...")
        result = self.controller.confirm_purchase(purchase_id)
        if not result:
            self.confirm_btn.configure(state="normal", text="Confirmar compra")

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
        self.save_btn.configure(fg_color="#4CAF50")
        self.save_btn.configure(hover_color="#388E3C")

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
            self.save_btn.configure(fg_color="#9E9E9E")
            self.save_btn.configure(hover_color="#757575")    

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