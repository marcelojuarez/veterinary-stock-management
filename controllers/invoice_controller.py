from services.invoice_internal_pdf import InvoiceInternalPDFService
from decimal import Decimal
from utils.utils import norm_to_2_dec, flex_dec

class InvoiceController:
    def __init__(self, invoice_model, customer_model, stock_model):
        self.invoice_model = invoice_model
        self.customer_model = customer_model
        self.stock_model = stock_model

    def _get_iva_rate(self, product_id):
        """
        Obtiene la alícuota de IVA real del producto desde stock.
        Retorna el divisor (ej: 1.21) y la tasa (ej: 0.21).
        Si no encuentra el producto o la alícuota es 0, retorna (1, 0).
        """
        try:
            product = self.stock_model.get_product_by_id(product_id)
            if product and product[9]:  # columna 'iva' en stock
                iva_pct = Decimal(str(product[9]))
                rate = iva_pct / Decimal("100")
                divisor = Decimal("1") + rate
                return divisor, rate
        except Exception:
            pass
        # fallback: sin IVA (honorarios u otros sin alícuota)
        return Decimal("1"), Decimal("0")

    def generate_invoice(self, customer_id, items):
        """Crear la factura + PDF usando la alícuota real de cada producto"""

        total_subtotal = Decimal("0.00")
        total_iva     = Decimal("0.00")

        # iva_breakdown: { "21.00": Decimal, "10.50": Decimal, ... }
        iva_breakdown = {}

        # Enriquecer cada ítem con su neto y alícuota para el PDF
        enriched_items = []

        for item in items:
            if len(item) == 6:
                product_id, name, pack, quantity, price, observations = item
            else:
                product_id, name, pack, quantity, price = item
                observations = None

            price    = flex_dec(price)  # precio con IVA incluido

            divisor, rate = self._get_iva_rate(product_id)

            net_unit_exact = price / divisor
            net_unit       = norm_to_2_dec(net_unit_exact)

            line_net  = norm_to_2_dec(net_unit_exact * quantity)

            line_iva  = norm_to_2_dec(net_unit_exact * quantity * rate)

            total_subtotal += line_net
            total_iva      += line_iva

            # Acumular por alícuota (ej: "21.00", "10.50", "0.00")
            pct_key = f"{norm_to_2_dec(rate * Decimal('100'))}"
            if pct_key not in iva_breakdown:
                iva_breakdown[pct_key] = Decimal("0.00")
            iva_breakdown[pct_key] += line_iva

            if observations is not None:
                enriched_items.append((product_id, name, pack, quantity, net_unit, observations, rate))
            else:
                enriched_items.append((product_id, name, pack, quantity, net_unit, rate))

        total_subtotal = norm_to_2_dec(total_subtotal)
        total_iva      = norm_to_2_dec(total_iva)
        total          = norm_to_2_dec(total_subtotal + total_iva)

        # Redondear breakdown
        iva_breakdown = {k: norm_to_2_dec(v) for k, v in iva_breakdown.items()}

        # Crear factura en DB (con ítems originales — precios con IVA)
        invoice_id, number = self.invoice_model.create_invoice(
            customer_id, total_subtotal, total_iva, total
        )

        for item in items:
            if len(item) == 6:
                product_id, _, _, quantity, price, _ = item
            else:
                product_id, _, _, quantity, price = item

            quantity   = flex_dec(quantity)
            price      = flex_dec(price)
            line_total = norm_to_2_dec(quantity * price)

            self.invoice_model.add_invoice_item(
                invoice_id, product_id, quantity, price, line_total
            )

        # Obtener datos de cliente
        customer = self.customer_model.find_customer_by_id(customer_id)

        # Generar PDF con datos enriquecidos
        pdf_path = InvoiceInternalPDFService().generate_pdf(
            invoice_id=invoice_id,
            number=number,
            customer=customer,
            items=enriched_items,
            subtotal=total_subtotal,
            iva_breakdown=iva_breakdown,
            total=total
        )

        return pdf_path