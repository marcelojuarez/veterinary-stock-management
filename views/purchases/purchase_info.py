from views.view_helpers import close_win, show_error
import customtkinter as ctk
from tksheet import Sheet

class PurchaseInfo():
    def __init__(self, model):
        self.model = model

    def show_purchase_info(self, parent, values):
        purchase_info = ctk.CTkToplevel(parent)
        purchase_info.withdraw() # oculta

        purchase_info.title("Informacion de la Compra")
        purchase_info.protocol(
            "WM_DELETE_WINDOW",
            lambda: close_win(purchase_info, parent)
        )
        purchase_info.resizable(False, False)
        
        purchase_info.transient(parent)
        purchase_info.grab_set()

        width_win = 650
        height_win = 650

        x_root = parent.winfo_x()
        y_root = parent.winfo_y()
        width_root = parent.winfo_width()
        height_root = parent.winfo_height()

        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        purchase_info.geometry(f"{width_win}x{height_win}+{x}+{y}")
        purchase_info.configure(fg_color="#e0e0e0")

        main_frame = ctk.CTkFrame(purchase_info, corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(
            main_frame,
            text=f"Detalle de la compra: (ID: {values[0]})",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(10, 20))

        info_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        info_frame.pack(fill="x", padx=10, pady=(0, 20))

        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=2)

        purchase_id = values[0]
        purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
        print(f'Purchase data: {purchase_data}')
        
        doc_type = purchase_data[2]

        if doc_type == "REMITO":
            receipt_data = self.model.purchase.get_receipt_data(purchase_data[4])
            print(f'receipt_data: {receipt_data}')

            fields = [
                ('Número de Recibo', receipt_data[2]),
                ('Fecha', receipt_data[3]),
                ('Fecha de Vencimiento', receipt_data[4]),
                ('Observaciones', receipt_data[5]),
                ('Estado', receipt_data[6]),
                ('Total', receipt_data[7])
            ]
        elif doc_type == "FACTURA":
            invoice_data = self.model.purchase.get_invoice_data(purchase_data[3])
            print(f'invoice_data: {invoice_data}')

            fields=[
                ('Número de Factura', invoice_data[2]),
                ('Tipo de Factura', invoice_data[3]),
                ('Punto de venta', invoice_data[4]),
                ('Fecha', invoice_data[5]),
                ('Fecha de Vencimiento', invoice_data[6]),
                ('IVA', invoice_data[9]),
                ('Descuento', invoice_data[10]),
                ('SubTotal', invoice_data[8]),
                ('Total', invoice_data[7])
            ]

            purchase_info.geometry("650x750")
        else:
            show_error('Tipo de documento desconocido')
            return
        
        # Se ubican los datos de los documentos
        for row, (label, value) in enumerate(fields):
            lbl = ctk.CTkLabel(
                info_frame,
                text=label + ": ",
                font=ctk.CTkFont(size=13, weight="bold")
            )
            lbl.grid(row=row, column=0, sticky="w", padx=15, pady=6)

            val = ctk.CTkLabel(
                info_frame,
                text=value,
                font=ctk.CTkFont(size=13)
            )
            val.grid(row=row, column=1, sticky="w", padx=15, pady=6)

        # Productos asociados a la compra

        sep = ctk.CTkLabel(
            main_frame,
            text='Productos asociados a la compra',
            font=ctk.CTkFont(size=15, weight="bold")
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

        btn_close = ctk.CTkButton(
            main_frame,
            text="Cerrar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            command=lambda: close_win(purchase_info, parent)
        )
        btn_close.pack(pady=(5,10))

        purchase_info.deiconify() # se muestra