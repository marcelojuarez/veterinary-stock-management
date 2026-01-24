import os

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime

class PurchaseDetail():
    def __init__(self, model):
        self.model = model

    def load_data(self, purchase_id):
        purchase_data = self.model.purchase.get_purchase_by_id(purchase_id)
        name = None

        # Datos de compra
        self.purchase = {
            'id': purchase_data[0],
            'supplier_name': name,
            'document_type': purchase_data[2],
            'date': purchase_data[5],
            'expiration_date': purchase_data[6],
            'state': purchase_data[7],
            'observations': purchase_data[8],
            'pending': purchase_data[9],
            'total': self.model.purchase.get_sum_of_items(purchase_id)[0]
        }

        # Datos de items de compra
        self.items = self.model.purchase.get_purchase_items(purchase_id)

        # 
        if self.purchase['document_type'] == 'REMITO':
            doc_id = purchase_data[4]
            receipt_data = self.model.purchase.get_receipt_data(doc_id)

            self.doc_data = {
               'id': receipt_data[2],
            }

        else:
            doc_id = purchase_data[3]
            invoice_data = self.model.purchase.get_invoice_data(doc_id)

            # self.doc_data = {
            #    'id': invoice_data[2],
            #    'type': invoice_data[3],
            #    'discount': ,
            #    'iva':,
            #    'subtotal':,
            #    'total':
            # }

    def generate_purchase_detail(self, purchase_id):
        self.load_data(purchase_id)
        
        date = self.purchase['date']

        os.makedirs("comprobantes/purchase_detail", exist_ok=True)
        filename = f"comprobantes/purchase_detail/{date}_compra_nro_{purchase_id}.pdf"

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        elements = []

        # Titulo
        elements.append(
            Paragraph(f"Detalle de Compra Nº {self.purchase["id"]}", styles["Title"])
        )
        elements.append(Spacer(1, 12))

        # Datos generales
        date_ui = datetime.strptime(
            self.purchase["date"], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

        expiration_date_ui = datetime.strptime(
            self.purchase["expiration_date"], "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

        info = f"""
        <b>Proveedor:</b> {self.purchase['supplier_name']}<br/>
        <b>Tipo documento:</b> {self.purchase['document_type']}<br/>
        <b>Fecha:</b> {date_ui}<br/>
        <b>Fecha De Vencimiento:</b> {expiration_date_ui}<br/>
        <b>Estado: {self.purchase['state']}</b>
        """

        elements.append(Paragraph(info, styles["Normal"]))
        elements.append(Spacer(1, 16))

        # Tabla de ítems
        table_data = [
            [
                "Producto", "Envase", "Cant.",
                "Precio", "IVA %", "Subtotal", "IVA", "Total"
            ]
        ]

        for item in self.items:
            table_data.append([
                item[1], # product_name
                item[2], # pack
                item[3], # quantity
                f"${item[4]}", # cost_price
                f"{item[5]}%", # iva_rate
                f"${item[8]}", # sub_total
                f"${item[9]}", # iva_amount
                f"${item[10]}", # total
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("ALIGN", (2,1), (-1,-1), "RIGHT"),
            ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 16))

        # Totales
        totals = f"""
        <b>Total:</b> ${self.purchase['total']}<br/>
        """

        elements.append(Paragraph(totals, styles["Normal"]))

        # Observaciones
        if self.purchase["observations"]:
            elements.append(Spacer(1, 12))
            elements.append(
                Paragraph(
                    f"<b>Observaciones:</b><br/>{self.purchase['observations']}",
                    styles["Normal"]
                )
            )

        doc.build(elements)
