from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

class InvoicePDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()

    def generate_pdf(self, number, customer, items, subtotal, iva, total):
        os.makedirs("facturas", exist_ok=True)
        filename = f"facturas/{number}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []

        title = Paragraph(f"<b>Factura Interna Nº {number}</b>", self.styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 20))

        cust_text = f"""
            <b>{customer[1]}</b><br/>
            CUIT: {customer[2]}<br/>
            Domicilio: {customer[3]}<br/>
            Teléfono: {customer[4]}
        """
        elements.append(Paragraph(cust_text, self.styles["Normal"]))
        elements.append(Spacer(1, 15))

        # Tabla de ítems
        table_data = [["Código", "Cantidad", "Precio", "Subtotal"]]
        for pid, q, price in items:
            table_data.append([pid, q, f"${price:.2f}", f"${q*price:.2f}"])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 20))

        totals = f"""
            Subtotal: ${subtotal:.2f}<br/>
            IVA 21%: ${iva:.2f}<br/>
            <b>Total: ${total:.2f}</b>
        """
        elements.append(Paragraph(totals, self.styles["Normal"]))

        doc.build(elements)
        return filename
