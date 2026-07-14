import logging
import tkinter as tk
from tksheet import Sheet
import customtkinter as ctk
from services.purchase_detail import PurchaseDetail
from utils.utils import iso_to_traditional, format_currency, format_currency_flex
from utils.view_helpers import center_window, close_win, ask_confirmation, show_success, show_warning, show_error
from utils.printing import send_to_printer
from tkinter.messagebox import askyesno

logger = logging.getLogger(__name__)

class PurchaseInfoReceiptView():
    def __init__(self, model, controller):
        self.model = model
        self.controller = controller
        self.purchase_detail = PurchaseDetail(model)

    def show_purchase_info(self, parent, values):
        try:
            self.receipt_state = tk.StringVar()
            self.receipt_state.set(values[6])

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
                text=f"Detalle de la compra: {self.receipt_state.get()}",
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
            if doc_type == "FACTURA":
                self.show_receipt_fields(doc_id=None)
            else:
                self.show_receipt_fields(doc_id=purchase_data[4])

            # Productos asociados a la compra
            sep = ctk.CTkLabel(
                main_frame,
                text='Productos asociados a la compra',
                font=ctk.CTkFont(size=20, weight="bold")
            )

            sep.pack(anchor="w", padx=20, pady=(5, 5))

            table_frame = ctk.CTkFrame(main_frame, corner_radius=10, height=260)
            table_frame.pack(fill="x", padx=10, pady=5)
            table_frame.pack_propagate(False)

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

            btn_frame = ctk.CTkFrame(main_frame, fg_color="#f5f5f5", corner_radius=10)
            btn_frame.pack(fill='x', padx=10, pady=(5, 10))

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
                text="🗑 Eliminar Item",
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

            width_win = 1100
            height_win = 700

            center_window(purchase_info, width_win, height_win)
            purchase_info.deiconify()

            purchase_info.transient(parent)
            purchase_info.grab_set()

        except ValueError as e:
            logger.error("Error en vista de remito: %s", e)

        except Exception as e:
            logger.error("Error en vista de remito: %s", e)

    ## -- Renderiza los campos de remito y carga sus datos-- ##
    def show_receipt_fields(self, doc_id):

        self.receipt_vars = {
            'number': tk.StringVar(),
            'date': tk.StringVar(),
            'expiration': tk.StringVar(),
            'obs': tk.StringVar(),
            'total': tk.StringVar()
        }
        
        self.load_receipt_data(doc_id)

        if self.receipt_state.get() != "BORRADOR":
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

        # NUMERO DE RECIBO

        num_entry = add_field(
                        0, 0, "Número de Recibo: ", 
                        ctk.CTkEntry(
                            self.info_frame, 
                            textvariable=self.receipt_vars["number"], 
                            width=120,
                            font=ctk.CTkFont(size=11),
                            state='readonly'
                        )
                    )

        # FECHA
        date_entry = add_field(
                        1, 0, "Fecha: ", 
                        ctk.CTkEntry(
                            self.info_frame, 
                            textvariable=self.receipt_vars["date"], 
                            width=120, 
                            font=ctk.CTkFont(size=11),
                            state='readonly'
                        )
                    )

        # FECHA DE VENC
        exp_date_entry = add_field(
                            2, 0, "Fecha de Vencimiento: ", 
                            ctk.CTkEntry(
                                self.info_frame,
                                textvariable=self.receipt_vars["expiration"], 
                                width=120, 
                                font=ctk.CTkFont(size=11),
                                state='readonly'
                            )
                        )

        # OBSERVACIONES
        obs_entry = add_field(
                        0, 2, "Observaciones: ", 
                        ctk.CTkEntry(
                            self.info_frame, 
                            textvariable=self.receipt_vars["obs"], 
                            width=180, 
                            height=60, 
                            font=ctk.CTkFont(size=11),
                            state='readonly'
                        )
                    )

        # Total
        add_field(
            1, 2, "Total: ", 
            ctk.CTkEntry(
                self.info_frame, 
                textvariable=self.receipt_vars["total"], 
                width=120, 
                font=ctk.CTkFont(size=13),
                state='readonly'
            )
        )

        # customizable entries
        self.customizable_wid = (
            num_entry,
            date_entry,
            exp_date_entry,
            obs_entry
        )

    # Carga los campos con informacion
    def load_receipt_data(self, doc_id):
        if doc_id is None:
            return
        receipt_data = self.model.purchase.supplier_receipt.get_receipt_data(doc_id)
        if receipt_data is None:
            return
        self.receipt_vars['number'].set(receipt_data[2]) 
        self.receipt_vars['date'].set(iso_to_traditional(receipt_data[3]))
        self.receipt_vars['expiration'].set(iso_to_traditional(receipt_data[4]))
        self.receipt_vars['obs'].set(receipt_data[5])
        self.receipt_vars['total'].set(format_currency(receipt_data[7]))

    ## --  Obtener datos del recibo -- ##
    def get_receipt_data(self):
        return {
            'receipt_id': self.receipt_vars['number'].get().strip(),
            'date': self.receipt_vars['date'].get().strip(),
            'expiration': self.receipt_vars['expiration'].get().strip(),
            'obs': self.receipt_vars['obs'].get().strip()
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
            logger.error("Error en vista de remito: %s", e)

    ## -- Manejo para eliminar un item de compra-- ##
    def handle_delete_purchase_item(self):
        try: 
            selected_cells = list(self.sheet.get_selected_cells())

            if not selected_cells:
                show_error('Por favor seleccione un item de compra')
                return

            string_error = 'Error. No se pueden eliminar items de una compra ya confirmada'

            state = self.receipt_state.get()
            if state != 'BORRADOR': 
                show_error(f'{string_error}') 
                return

            row_num = selected_cells[0][0]

            row_data = self.sheet.get_row_data(row_num)
            p_id = row_data[0]

            self.controller.delete_purchase_item(self.purchase_id, p_id)

        except ValueError as e:
            logger.error("Error en vista de remito: %s", e) 

    # Botones de accion
    ## -- Confirmar Compra -- ##
    def confirm_purchase(self, purchase_id):

        # confirmar compra
        if ask_confirmation('¿Desea confirmar esta compra?', 'Confirmar compra'):
            result = self.controller.confirm_purchase(purchase_id)
            if result:
                self.confirm_btn.configure(state=tk.DISABLED)
        else:
            return

    ## --  Editar campos de los documentos asociados a la compra -- ##
    def edit(self, purchase_id):
        if self.receipt_state.get() != 'BORRADOR':
            show_error('No se puede editar un remito ya confirmado.')
            return

        show_warning('Datos editables')

        # Guardar valores anteriores
        self.save_previous_values()

        self.print_info.configure(state='disabled')

        # Habilita el boton de cancelar edicion
        self.edit_btn.configure(
            text='Cancelar Edicion',
            fg_color="#0F4E57",
            hover_color="#082F35",
            width=150,
            command=lambda: self.recover_previous_values_of_receipt(purchase_id)
        )

        # Habilita el boton guardar
        self.save_btn.configure(state='normal')
        self.save_btn.configure(fg_color="#4CAF50")
        self.save_btn.configure(hover_color="#388E3C")

        for w in self.customizable_wid:
            w.configure(state='normal')

        self.customizable_wid[0].focus()

    ## -- Guardar datos editados de compra -- ##
    def save(self, purchase_id):
        result = self.controller.update_doc_info(purchase_id, 'REMITO')

        if result:

            # Recuperar boton de edicion
            self.edit_btn.configure(
                text="Editar",
                fg_color="#2980B9",
                hover_color="#0B5D94",
                width=120,
                command= lambda: self.edit(purchase_id)
            )

            for w in self.customizable_wid:
                w.configure(state='readonly')

            self.save_btn.configure(state='disabled')   
            self.save_btn.configure(fg_color="#9E9E9E")
            self.save_btn.configure(hover_color="#757575")    

            self.print_info.configure(state='normal')

    ## --  Guardar valores anteriores de campos -- ##
    def save_previous_values(self):
        
        self.custom_wid_values = [
            self.customizable_wid[0].get(),
            self.customizable_wid[1].get(),
            self.customizable_wid[2].get(),
            self.customizable_wid[3].get(),
        ]

    ## --  Recuperar valores previos de los campos -- ##
    def recover_previous_values_of_receipt(self, purchase_id):

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

        self.receipt_vars['number'].set(self.custom_wid_values[0])
        self.receipt_vars['date'].set(self.custom_wid_values[1])
        self.receipt_vars['expiration'].set(self.custom_wid_values[2])
        self.receipt_vars['obs'].set(self.custom_wid_values[3])
        
        for w in self.customizable_wid:
            w.configure(state='readonly')