from models.invoice import InvoiceModel
from models.customer import CustomerModel
from services.invoice_pdf import InvoicePDFService

class InvoiceController:
    def __init__(self):
        self.invoice_model = InvoiceModel()
        self.customer_model = CustomerModel()

    def generate_invoice(self, customer_id, items):
        """Crear la factura + PDF"""

        subtotal = sum(q * p for (_, q, p) in items)
        iva = round(subtotal * 0.21, 2)
        total = round(subtotal + iva, 2)

        # Crear factura
        invoice_id, number = self.invoice_model.create_invoice(
            customer_id, subtotal, iva, total
        )

        # Crear ítems
        for product_id, quantity, price in items:
            sub = round(quantity * price, 2)
            self.invoice_model.add_invoice_item(
                invoice_id, product_id, quantity, price, sub
            )

        # Obtener datos de cliente
        customer = self.customer_model.find_customer_by_id(customer_id)

        # Generar PDF
        pdf_path = InvoicePDFService().generate_pdf(
            number=number,
            customer=customer,
            items=items,
            subtotal=subtotal,
            iva=iva,
            total=total
        )

        return invoice_id, pdf_path
