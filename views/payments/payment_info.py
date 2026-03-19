from tksheet import Sheet
import customtkinter as ctk
from utils.view_helpers import center_window, close_win
from utils.utils import iso_to_traditional, format_currency

class PaymentInfo():
    def __init__(self, model):
        self.model = model

    def show_payment_info(self, parent, values):
        payment_info = ctk.CTkToplevel(parent)
        payment_info.title("Información del Pago")
        payment_info.resizable(False, False)
        center_window(payment_info, 650, 450)

        payment_info.protocol(
            "WM_DELETE_WINDOW",
            lambda: close_win(payment_info, parent)
        )
        payment_info.transient(parent)
        payment_info.grab_set()

        main_frame = ctk.CTkFrame(payment_info, corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(
            main_frame,
            text=f"Detalle del Pago: (ID: {values[0]})",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=(10, 20))

        info_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        info_frame.pack(fill="x", padx=10, pady=(0, 20))

        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=2)

        method = values[3]
        payment_id = values[0]

        if method == "TRANSFERENCIA":
            data = self.model.payment.get_transfer_data(payment_id)
            fields = [
                ("Método", "Transferencia"),
                ("Número de operación", data[0]),
                ("CBU/Alias (Cuenta Emisora)", data[1]),
                ("CBU/Alias (Cuenta Receptora)", data[2]),
            ]

        elif method == "CHEQUE":
            data = self.model.payment.get_check_data(payment_id)
            fields = [
                ("Método", "Cheque"),
                ("Número de cheque", data[0]),
                ("Banco", data[1]),
            ]
        else:
            fields = [
                ("Método", "Efectivo")
            ]

        for row, (label, value) in enumerate(fields):
            lbl = ctk.CTkLabel(
                info_frame,
                text=label + ":",
                font=ctk.CTkFont(size=13, weight="bold")
            )
            lbl.grid(row=row, column=0, sticky="w", padx=15, pady=6)

            val = ctk.CTkLabel(
                info_frame,
                text=value,
                font=ctk.CTkFont(size=13)
            )
            val.grid(row=row, column=1, sticky="w", padx=15, pady=6)

        sep = ctk.CTkLabel(
            main_frame,
            text="Compras afectadas por este pago",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        sep.pack(anchor="w", padx=20, pady=(5, 5))

        table_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        data = [
            [
                purchase_id,
                format_currency(amount_applied),
                iso_to_traditional(applied_at)
            ]
            for purchase_id, amount_applied, applied_at
            in self.model.payment.get_purchase_payment_relation(payment_id)
        ]

        headers = ["ID Compra", "Monto aplicado", "Fecha"]

        sheet = Sheet(
            table_frame,
            data=data,
            headers=headers,
            show_x_scrollbar=False,
            show_y_scrollbar=True
        )
        sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_width_resize",
            "double_click_column_resize",
        ))
        sheet.set_column_widths([100, 150, 200])
        sheet.pack(fill="both", expand=True, padx=5, pady=5)

        btn_close = ctk.CTkButton(
            main_frame,
            text="Cerrar",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=120,
            command=lambda: close_win(payment_info, parent)
        )
        btn_close.pack(pady=(5,10))

