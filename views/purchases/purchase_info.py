import customtkinter as ctk
import tkinter as tk 
from tksheet import Sheet

from views.view_helpers import close_win, show_error, ask_confirmation, show_warning

class PurchaseInfo():
    def __init__(self, model, controller=None):
        self.model = model
        self.controller = controller
    
    def set_controller(self, controller):
        self.controller = controller

    def show_purchase_info(self, parent, values):
        try:
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
                text=f"Detalle de la compra: (ID: {values[0]})",
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
                command= lambda: self.confirm_purchase(purchase_info, parent, values[0])
            )
            self.confirm_btn.pack(side='right', anchor='w', padx=5)

            info_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="white")
            info_frame.pack(fill="x", padx=10, pady=(0, 20))

            info_frame.columnconfigure(0, weight=1)
            info_frame.columnconfigure(1, weight=2)

            purchase_id = values[0]
            purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
            
            doc_type = purchase_data[2]

            if doc_type == "REMITO":
                width_win = 650
                height_win = 750

                # Widgets para informacion del remito
                receipt_data = self.model.purchase.get_receipt_data(purchase_data[4])

                self.receipt_vars = {
                    'number': tk.StringVar(value=receipt_data[2]),
                    'date': tk.StringVar(value=receipt_data[3]),
                    'expiration': tk.StringVar(value=receipt_data[4]),
                    'obs': tk.StringVar(value=receipt_data[5]),
                    'state': tk.StringVar(value=receipt_data[6]),
                    'total': tk.StringVar(value=receipt_data[7])
                }
                
                if self.receipt_vars['state'].get() != "BORRADOR":
                    self.confirm_btn.configure(state=tk.DISABLED)

                # NUMERO DE RECIBO
                ctk.CTkLabel(info_frame, text="Número de Recibo: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=0, column=0, sticky="w", padx=15, pady=6)

                num_entry = ctk.CTkEntry(
                    info_frame, textvariable=self.receipt_vars["number"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                )
                num_entry.grid(row=0, column=1, sticky="w", padx=15, pady=6)

                # FECHA
                ctk.CTkLabel(info_frame, text="Fecha: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=1, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.receipt_vars["date"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=1, column=1, sticky="w", padx=15, pady=6)

                # FECHA DE VENC
                ctk.CTkLabel(info_frame, text="Fecha de Vencimiento: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=2, column=0, sticky="w", padx=15, pady=6)

                exp_date_entry = ctk.CTkEntry(
                    info_frame, textvariable=self.receipt_vars["expiration"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                )
                exp_date_entry.grid(row=2, column=1, sticky="w", padx=15, pady=6)

                # Observaciones
                ctk.CTkLabel(info_frame, text="Observaciones: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=3, column=0, sticky="w", padx=15, pady=6)

                obs_entry = ctk.CTkEntry(
                    info_frame, textvariable=self.receipt_vars["obs"], width=200, height=60, state='readonly', font=ctk.CTkFont(size=13)
                )
                obs_entry.grid(row=3, column=1, sticky="w", padx=15, pady=6)

                # Estado
                ctk.CTkLabel(info_frame, text="Estado: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=4, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.receipt_vars["state"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=4, column=1, sticky="w", padx=15, pady=6)

                # Total
                ctk.CTkLabel(info_frame, text="Total: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=5, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.receipt_vars["total"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=5, column=1, sticky="w", padx=15, pady=6)

                # customizable entries
                self.customizable_wid = (
                    num_entry,
                    exp_date_entry,
                    obs_entry
                )

            elif doc_type == "FACTURA":
                width_win = 650
                height_win = 900

                # Widgets para informacion de la factura
                invoice_data = self.model.purchase.get_invoice_data(purchase_data[3])

                self.invoice_vars = {
                        'number': tk.StringVar(value=invoice_data[2]),
                        'type': tk.StringVar(value=invoice_data[3]),
                        'obs': tk.StringVar(value=invoice_data[11]),
                        'date': tk.StringVar(value=invoice_data[4]),
                        'expiration': tk.StringVar(value=invoice_data[5]),
                        'iva': tk.StringVar(value=str(invoice_data[8])),
                        'state': tk.StringVar(value=invoice_data[10]),
                        'discount': tk.StringVar(value=str(invoice_data[9])),
                        'subtotal': tk.StringVar(value=str(invoice_data[7])),
                        'total': tk.StringVar(value=str(invoice_data[6]))
                    }

                if self.invoice_vars['state'].get() != "BORRADOR":
                    self.confirm_btn.configure(state=tk.DISABLED)

                # NUMERO DE FACTURA
                ctk.CTkLabel(info_frame, text="Número de Factura: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=0, column=0, sticky="w", padx=15, pady=6)

                num_entry = ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["number"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                )
                num_entry.grid(row=0, column=1, sticky="w", padx=15, pady=6)

                # TIPO DE FACTURA
                ctk.CTkLabel(info_frame, text="Tipo de Factura: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=1, column=0, sticky="w", padx=15, pady=6)

                type_box = ctk.CTkComboBox(
                    info_frame, values=['A', 'B', 'C', '-'], variable=self.invoice_vars["type"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                )
                type_box.grid(row=1, column=1, sticky="w", padx=15, pady=6)
                type_box.set('A')

                # OBSERVACIONES
                ctk.CTkLabel(info_frame, text="Observaciones: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=2, column=0, sticky="w", padx=15, pady=6)

                obs_entry = ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["obs"], width=250, height=60, state='readonly', font=ctk.CTkFont(size=13)
                )
                obs_entry.grid(row=2, column=1, sticky="w", padx=15, pady=6)

                # FECHA
                ctk.CTkLabel(info_frame, text="Fecha: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=3, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["date"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=3, column=1, sticky="w", padx=15, pady=6)

                # FECHA DE VENC
                ctk.CTkLabel(info_frame, text="Fecha de Vencimiento: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=4, column=0, sticky="w", padx=15, pady=6)

                exp_date_entry = ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["expiration"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                )
                exp_date_entry.grid(row=4, column=1, sticky="w", padx=15, pady=6)

                # IVA
                ctk.CTkLabel(info_frame, text="IVA: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=5, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["iva"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=5, column=1, sticky="w", padx=15, pady=6)

                # DESCUENTO
                ctk.CTkLabel(info_frame, text="Descuento: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=6, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["discount"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=6, column=1, sticky="w", padx=15, pady=6)            

                # SUBTOTAL
                ctk.CTkLabel(info_frame, text="Subtotal: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=7, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["subtotal"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=7, column=1, sticky="w", padx=15, pady=6)            

                # Total
                ctk.CTkLabel(info_frame, text="Total: ", font=ctk.CTkFont(size=13, weight="bold")
                ).grid(row=8, column=0, sticky="w", padx=15, pady=6)

                ctk.CTkEntry(
                    info_frame, textvariable=self.invoice_vars["total"], width=200, state='readonly', font=ctk.CTkFont(size=13)
                ).grid(row=8, column=1, sticky="w", padx=15, pady=6)

                self.customizable_wid = [
                    num_entry,
                    type_box,
                    obs_entry,
                    exp_date_entry,
                ]

            else:
                show_error('Tipo de documento desconocido')
                return

            # Productos asociados a la compra
            sep = ctk.CTkLabel(
                main_frame,
                text='Productos asociados a la compra',
                font=ctk.CTkFont(size=20, weight="bold")
            )

            sep.pack(anchor="w", padx=20, pady=(5, 5))

            table_frame = ctk.CTkFrame(main_frame, corner_radius=10)
            table_frame.pack(fill="both", expand=True, padx=10, pady=5)

            sheet = Sheet(
                table_frame,
                # data=data,
                # headers=headers,
                show_x_scrollbar=False,
                show_y_scrollbar=True
            )
            # sheet.enable_bindings((
            #     "single_select",
            #     "row_select",
            #     "column_width_resize",
            #     "double_click_column_resize",
            # ))
            # sheet.set_column_widths([100, 150, 200])
            sheet.pack(fill="both", expand=True, padx=5, pady=5)

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
                command= lambda: self.save(values[0], values[2])
            )
            self.save_btn.grid(row=0, column=0, padx=10)

            self.edit_btn = ctk.CTkButton(
                btn_frame,
                text="Editar",
                fg_color="#2980B9",
                hover_color="#0B5D94",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=120,
                command= lambda: self.edit(values[0], values[2])
            )
            self.edit_btn.grid(row=0, column=1, padx=10)

            close_btn = ctk.CTkButton(
                btn_frame,
                text="Cerrar",
                fg_color="#E74C3C",
                hover_color="#C0392B",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=120,
                command=lambda: close_win(purchase_info, parent, parent.focus_force)
            )
            close_btn.grid(row=0, column=2, padx=10)

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

    # Confirmar Compra
    def confirm_purchase(self, win, parent, purchase_id):

        # confirmar compra
        if ask_confirmation('Desea confirmar esta Compra', 'Este es el titulo'):

            # Control si tiene compras asociadas
            self.controller.confirm_purchase(purchase_id)
        
            close_win(win, parent)
        else:
            print('no aca')
            return

    # Editar campos de los documentos asociados a la compra
    def edit(self, purchase_id, doc_type):
        show_warning('Datos editables')

        # Guardar valores anteriores
        self.save_previous_values(doc_type)

        # Habilita el boton de cancelar edicion
        self.edit_btn.configure(
            text='Cancelar Edicion',
            fg_color="#0F4E57",
            hover_color="#082F35",
            width=150,
            command=lambda: self.recover_previous_values(purchase_id, doc_type)
        )

        # Habilita el boton guardar
        self.save_btn.configure(state='normal')
        self.save_btn.configure(fg_color="#4927AC")
        self.save_btn.configure(hover_color="#260980")

        for w in self.customizable_wid:
            w.configure(state='normal')

        self.customizable_wid[0].focus()

    # Guardar compra
    def save(self, purchase_id, doc_type):
        result = self.controller.update_doc_info(purchase_id, doc_type)

        if result:

            # Recuperar boton de edicion
            self.edit_btn.configure(
                text="Editar",
                fg_color="#2980B9",
                hover_color="#0B5D94",
                width=120,
                command= lambda: self.edit(purchase_id, doc_type)
            )

            for w in self.customizable_wid:
                w.configure(state='readonly')

            self.save_btn.configure(state='disabled')   
            self.save_btn.configure(fg_color="#3A3251")
            self.save_btn.configure(hover_color="#3A3251")    

    # Guardar valores anteriores de campos
    def save_previous_values(self, doc_type):

        if doc_type == 'REMITO':
            self.custom_wid_values = [
                self.customizable_wid[0].get(),
                self.customizable_wid[1].get(),
                self.customizable_wid[2].get(),
            ]

        else:
            self.custom_wid_values = [
                self.customizable_wid[0].get(),
                self.customizable_wid[1].get(),
                self.customizable_wid[2].get(),
                self.customizable_wid[3].get(),
            ] 

        for value in self.custom_wid_values:
            print(value)

    # Recuperar valores previos de los campos
    def recover_previous_values(self, purchase_id, doc_type):

        # Recuperar boton de edicion
        self.edit_btn.configure(
            text="Editar",
            fg_color="#2980B9",
            hover_color="#0B5D94",
            width=120,
            command= lambda: self.edit(purchase_id, doc_type)
        )

        # Recuperar valores
        if doc_type == 'REMITO':

            self.receipt_vars['number'].set(self.custom_wid_values[0])
            self.receipt_vars['expiration'].set(self.custom_wid_values[1])
            self.receipt_vars['obs'].set(self.custom_wid_values[2])
                
        else:
            self.invoice_vars['number'].set(self.custom_wid_values[0])
            self.invoice_vars['type'].set(self.custom_wid_values[1])
            self.invoice_vars['point_sale'].set(self.custom_wid_values[2])
            self.invoice_vars['expiration'].set(self.custom_wid_values[3])
        
        for w in self.customizable_wid:
            w.configure(state='readonly')


    # Obtener datos del recibo
    def get_receipt_data(self):
        return {
            'receipt_id': self.receipt_vars['number'].get().strip(),
            'expiration': self.receipt_vars['expiration'].get().strip(),
            'obs': self.receipt_vars['obs'].get().strip()
        }

    # Obtener datos de la factura
    def get_invoice_data(self):
        return {
            'invoice_id': self.invoice_vars['number'].get().strip(),
            'invoice_type': self.invoice_vars['type'].get().strip(),
            'obs': self.invoice_vars['obs'].get().strip(),
            'expiration': self.invoice_vars['expiration'].get().strip()
        }


