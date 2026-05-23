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
            if product and product[8]:  # columna 'iva' en stock
                iva_pct = Decimal(str(product[8]))
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
            # Formato unificado: qty en [3], price en [4], siempre
            # len 5: normal       (pid, name, pack, qty, price)
            # len 6: honorarios   (pid, name, pack, qty, price, obs)
            # len 7: fraccionado  (pid, name, pack, qty, price, unit_label, True)
            product_id = item[0]
            name       = item[1]
            pack       = item[2]

            if len(item) == 6:
                observations = item[5]   # honorarios
            elif len(item) == 7 and item[6] is True:
                observations = item[5]   # fraccionado: "FRAC. 5 KG"
            else:
                observations = None

            price = flex_dec(item[4])  # precio con IVA incluido

            if len(item) == 7 and item[6] is True:
                # Fraccionado: mostrar 1 unidad con precio total (qty_real × precio_unit)
                # Ej: 5 KG × $10/KG → display qty=1, display price=$50
                actual_qty  = flex_dec(item[3])
                quantity    = Decimal('1')
                price       = norm_to_2_dec(actual_qty * price)
            else:
                quantity = flex_dec(item[3])

            divisor, rate = self._get_iva_rate(product_id)

            net_unit_exact = price / divisor
            net_unit       = norm_to_2_dec(net_unit_exact)

            line_net = norm_to_2_dec(net_unit_exact * quantity)
            line_iva = norm_to_2_dec(net_unit_exact * quantity * rate)

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
            product_id = item[0]
            price      = flex_dec(item[4])
            if len(item) == 7 and item[6] is True:
                quantity   = Decimal('1')
                price      = norm_to_2_dec(flex_dec(item[3]) * price)
            else:
                quantity   = flex_dec(item[3])
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