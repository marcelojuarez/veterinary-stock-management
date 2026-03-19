# models/supplier/supplier_purchase.py

from datetime import datetime
from .supplier_invoice import SupplierInvoice
from .supplier_receipt import SupplierReceipt
from decimal import Decimal
from utils.utils import norm_to_2_dec, flex_dec, traditional_to_iso

class SupplierPurchase():
    def __init__(self, db, stock_model, stock_movement_model):
        self.db = db
        self.stock_model = stock_model
        self.supplier_invoice = SupplierInvoice(db)
        self.supplier_receipt = SupplierReceipt(db)
        self.movement = stock_movement_model

    ## -- Agregar nueva compra -- ##
    def add_new_purchase(self, data, conn=None, commit=True):
        try:
            query = """
            INSERT INTO purchase (supplier_id, document_type, date, expiration_date, state, observations, pending, total) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = [
                data['supplier_id'],
                data['doc_type'],
                data['date'],
                data['expiration_date'],
                data['state'],
                data['observations'],
                data['pending'],
                data['total']
            ]

            return self.db.execute_query(query, params, conn=conn, commit=commit)
        except ValueError as e:
            print(f'Error al cargar la compra: {e}')

    ## -- Obtener compra por ID -- ##
    def get_purchase_by_id(self, purchase_id):
        try:
            query = """
            SELECT * FROM purchase WHERE id = ?
            """
            
            return self.db.fetch_one(query, (purchase_id, ))

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')
            return None

    ## -- Obtener saldo pendiente de una compra --##
    def get_pending_of_purchase(self, purchase_id):
        try:
            query = """
            SELECT pending FROM purchase WHERE id = ?
            """

            return self.db.fetch_one(query, (purchase_id, ))[0]

        except ValueError as e:
            print(f'Error al obtener saldo pendiente: {e}')
            return None            

    ## Obtener compra por fecha ##
    def get_purchases_by_date(self, date, supplier_id=None):
        try:
            query = """
                SELECT purchase.id, supplier.cuit, supplier.name, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
                purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
                FROM purchase
                JOIN supplier ON purchase.supplier_id = supplier.id
                WHERE purchase.date = ?
                    AND (? IS NULL OR supplier.id = ?) 
                ORDER BY 
                CASE 
                    WHEN purchase.state = 'PENDIENTE' THEN 0 
                    ELSE 1 
                END,
                purchase.expiration_date
            """ 
            params = [
                date,
                supplier_id,
                supplier_id
            ]
            return self.db.fetch_all(query, params)

        except ValueError as e:
            print(f'Error al obtener las compras: {e}')
            return None

    ## -- Devuelve todas las compras asociadas a un CUIT -- ##
    def get_all_purchases(self, supplier_id=None):
        try:
            query = """
                SELECT purchase.id, supplier.cuit, supplier.name, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
                purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
                FROM purchase
                JOIN supplier ON purchase.supplier_id = supplier.id
                WHERE (? IS NULL OR supplier.id = ?) 
                ORDER BY 
                CASE 
                    WHEN purchase.state = 'PENDIENTE' THEN 0 
                    ELSE 1 
                END,
                purchase.expiration_date, purchase.id DESC
            """ 
            params = [
                supplier_id,
                supplier_id
            ]
            return self.db.fetch_all(query, params)
        
        except ValueError as e:
            print(f'Error al obtener las compras: {e}')
            return None
        
    ## -- Devuelve todas las compras confirmadas asociadas a un CUIT -- ##
    def get_all_confirmed_purchases(self, supplier_id=None):
        try:
            query = """
                SELECT purchase.id, supplier.id, supplier.cuit, supplier.name, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
                purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
                FROM purchase
                JOIN supplier ON purchase.supplier_id = supplier.id
                WHERE (? IS NULL OR supplier.id = ?) AND purchase.state != 'BORRADOR'
                ORDER BY 
                CASE 
                    WHEN purchase.state = 'PENDIENTE' THEN 0 
                    ELSE 1 
                END,
                purchase.expiration_date
            """ 
            params = [
                supplier_id,
                supplier_id
            ]
            return self.db.fetch_all(query, params)
        
        except ValueError as e:
            print(f'Error al obtener las compras: {e}')
            return None
    
    ## -- Busca un producto en una determinada compra -- ##
    def get_product_on_purchase(self, purchase_id, product_id):
        try:
            query = """
            SELECT * FROM purchase_item
            WHERE purchase_id = ? AND product_id = ?
            """
            params = [purchase_id, product_id]

            return self.db.fetch_one(query, params)
        
        except ValueError as e:
            print(f'Error al obtener producto: {e}')
            return None

    ## -- Agregar nuevo Producto -- ##
    def add_product(self, product_data):
        date = datetime.now().strftime("%Y-%m-%d")
        """Agregar un nuevo producto"""
        query = """
            INSERT INTO stock 
            (name, pack, list_price, discount, cost_price, profit, price, iva, price_with_iva, quantity, created_at, last_price_update) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            product_data['Name'],
            product_data['Package'],
            product_data['ListPrice'],
            product_data['Discount'],
            product_data['CostPrice'],
            product_data['Profit'],
            product_data['SalePrice'],
            product_data['Iva'],
            product_data['PriceWIva'],
            product_data['Stock'],
            date,
            date
        )
        return self.db.execute_query(query, params)
    
    ##  Transaccion que maneja la adicion de un item y hace sus respectivos calculos
    def handle_add_p_item(self, params, purchase_id, doc_type, doc_id):
        try:
            conn = self.db.get_connection()

            conn.execute("BEGIN")

            self.add_purchase_item(params, conn=conn, commit=False)
            self.recalc_doc_values(purchase_id, doc_type, doc_id, conn=conn, commit=False)

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f'Hubo un errorr {e}')
            return False
        
        finally:
            conn.close() 
    
    def find_product_by_name_and_pack(self, name, pack):
        try:
            query = "SELECT * FROM stock WHERE UPPER(name) = ? AND UPPER(pack) = ? LIMIT 1"
            return self.db.fetch_one(query, (name, pack))
        except Exception as e:
            print(f'Error finding product: {e}')
            return None

    ## -- Agrega un  nuevo Item de compra -- ##
    def add_purchase_item(self, params, conn=None, commit=True):

        query = """
            INSERT INTO purchase_item (purchase_id, product_id, product_name, pack, quantity,
            list_price, discount, cost_price, iva_rate, discount_amount, subtotal, iva_amount, total) 
            VALUES (?, ?, ? ,?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(query, params, conn=conn, commit=commit)
       

    ## -- Obtener tipo de factura para saber si discrimina IVA -- ##
    def get_invoice_type(self, doc_id):
        """Retorna True si la factura discrimina IVA (tipo A o M)"""
        query = """
        SELECT invoice_type FROM supplier_invoice WHERE id = ?
        """
        row = self.db.fetch_one(query, (doc_id,))
        if row:
            return row[0] in ('A', 'M')
        return True  # por defecto asumir que sí discrimina

    ## -- Recalcular los valores del doc asociado a la compra -- ##
    def recalc_doc_values(self, purchase_id, doc_type, doc_id, conn=None, commit=True):

        if doc_type == 'FACTURA':
            ## Factura
            discount = Decimal(self.supplier_invoice.get_invoice_discount(doc_id))
            discrimina_iva = self.get_invoice_type(doc_id)

            ## Monto IVA: solo si la factura discrimina (tipo A o M)
            if discrimina_iva:
                iva_amount = self.get_iva_amount_of_p_items(purchase_id, conn=conn)
                iva_discount = (iva_amount * discount) / Decimal('100')
                iva_amount = norm_to_2_dec(iva_amount - iva_discount)
            else:
                iva_amount = Decimal('0.00')

            ## Subtotal
            orig_subtotal = self.get_subtotal_of_items(purchase_id, conn=conn)
            
            ## Descuento
            discount_amount = norm_to_2_dec(
                (orig_subtotal * discount) / Decimal('100')
            )

            subtotal = norm_to_2_dec(orig_subtotal - discount_amount)

            perceptions_amount = self.supplier_invoice.get_invoice_perceptions_amount(doc_id)
            
            ## Total
            total = subtotal + iva_amount + perceptions_amount
            
            query = """ 
            UPDATE supplier_invoice 
            SET orig_subtotal = ?, discount_amount = ?, subtotal_w_discount = ?, iva = ?, total = ?  
            WHERE id = ? 
            """

            params = [
                str(orig_subtotal), 
                str(discount_amount), 
                str(subtotal), 
                str(iva_amount), 
                str(total), 
                doc_id
            ]

            self.db.execute_query(query, params, conn=conn, commit=commit)

            ## Se actualiza la compra
            query = """ UPDATE purchase SET pending = ? , total = ? WHERE id = ? """

            purchase_params = [str(total), str(total), purchase_id]

            self.db.execute_query(query, purchase_params, conn=conn, commit=commit)

        else:
            ## Remito ## sin iva
            total = self.get_subtotal_of_items(purchase_id, conn=conn)

            print(f'Total: {total}')

            query = """ UPDATE supplier_receipt SET total = ? WHERE id = ? """

            receipt_params = [str(total), doc_id]

            self.db.execute_query(query, receipt_params, conn=conn, commit=commit)

            ## Se actualiza la compra

            query = """ UPDATE purchase SET pending = ? , total = ? WHERE id = ? """

            purchase_params = [str(total), str(total), purchase_id]

            self.db.execute_query(query, purchase_params, conn=conn, commit=commit)

    ## -- Obtener items de compra -- ##
    def get_purchase_items(self, purchase_id):
        query = """
            SELECT product_id, product_name, pack, quantity, list_price, discount, 
            cost_price, iva_rate, discount_amount, subtotal, iva_amount, total
            FROM purchase_item
            WHERE purchase_id = ?
        """

        return self.db.fetch_all(query, (purchase_id, ))

    ##  -- Obtener subtotal de items -- ##
    def get_subtotal_of_items(self, purchase_id, conn=None):
        query = """
        SELECT subtotal
        FROM purchase_item
        WHERE purchase_id = ?
        """
        rows = self.db.fetch_all(query, (purchase_id,), conn=conn)

        subtotal = Decimal('0.00')

        for row in rows:
            subtotal += Decimal(row[0])

        return norm_to_2_dec(subtotal)

    ## -- Obtener suma de iva de items -- ##
    def get_iva_amount_of_p_items(self, purchase_id, conn=None):
        query = """
        SELECT iva_amount
        FROM purchase_item
        WHERE purchase_id = ?
        """
        rows = self.db.fetch_all(query, (purchase_id, ), conn=conn)

        iva_amount = Decimal('0.00')

        for row in rows:
            iva_amount += Decimal(row[0])

        return norm_to_2_dec(iva_amount)

    ## -- Obtener todos los productos de un proveedor a traves de las compras
    def get_all_products_by_supplier_id(self, supplier_id):
        query = """
            SELECT DISTINCT
                s.id            AS product_id,
                s.name          AS product_name,
                s.pack,
                s.cost_price,
                s.price,
                s.quantity,
                p.supplier_id
            FROM purchase p
            JOIN purchase_item pi ON pi.purchase_id = p.id
            JOIN stock s ON s.id = pi.product_id
            WHERE p.supplier_id = ?
            ORDER BY s.name;
        """
        
        return self.db.fetch_all(query, (supplier_id, ))

    ## -- Devuelve todas las compras con deuda pendiente asociadas a un cuit -- ##
    def get_all_purchases_without_paying(self, supplier_id=None):

        query = """
            SELECT purchase.id, supplier.cuit, supplier.name, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
            purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
            FROM purchase
            JOIN supplier ON purchase.supplier_id = supplier.id
            WHERE (? IS NULL OR supplier.id = ?) AND pending > 0 
            ORDER BY 
            CASE 
                WHEN purchase.state = 'PENDIENTE' THEN 0 
                ELSE 1 
            END,
            purchase.expiration_date
        """

        params = [
            supplier_id,
            supplier_id
        ]

        return self.db.fetch_all(query, params)
    
    ## -- setea la compra y el doc asociado como pendiente -- ##
    def set_purchase_as_pending(self, purchase_id, id, doc_type, conn=None, commit=True):

        query = """ UPDATE purchase SET state = 'PENDIENTE' WHERE id = ? """

        self.db.execute_query(query, (purchase_id, ), conn=conn, commit=commit)

        if doc_type == "REMITO":
            query = """
            UPDATE supplier_receipt SET state = 'PENDIENTE' WHERE id = ? 
            """
        else:
            query = """
            UPDATE supplier_invoice SET state = 'PENDIENTE' WHERE id = ? 
            """

        self.db.execute_query(query, (id, ), conn=conn, commit=commit)       

    ## -- Carga los items de la compra en stock y setea la compra como pendiente-- ## 
    def load_products(self, purchase_id, id, doc_type):
        try:
            conn = self.db.get_connection()
            conn.execute("BEGIN")

            self.set_purchase_as_pending(purchase_id, id, doc_type, conn=conn, commit=False)

            items = self.get_purchase_items(purchase_id)

            for i in items:
                i_data = {
                    'id':         i[0],
                    'name':       i[1],
                    'pack':       i[2],
                    'qty':        i[3],
                    'list_price': Decimal(i[4]),
                    'discount':   Decimal(i[5]),
                    'cost_price': Decimal(i[6]),
                    'iva_rate':   Decimal(i[7]),
                }

                # --- Guardar estado ANTERIOR del producto ---
                prev = self.stock_model.get_product_by_id(i_data['id'])
                qty_before   = prev[12] if prev else None  # quantity
                cost_before  = prev[6]  if prev else None  # cost_price
                price_before = prev[7]  if prev else None  # price (sin iva)

                p_data = self.prepare_item_to_add_to_stock(i_data)

                params = [
                    p_data['name'],
                    p_data['pack'],
                    p_data['list_price'],
                    p_data['discount'],
                    p_data['cost_price'],
                    p_data['sale_price'],
                    p_data['iva'],
                    p_data['price_with_iva'],
                    p_data['last_price_upd'],
                    p_data['id']
                ]

                query = """
                UPDATE stock 
                SET name = ?, pack = ?, list_price = ?, discount = ?, cost_price = ?,
                    price = ?, iva = ?, price_with_iva = ?, last_price_update = ?
                WHERE id = ?
                """
                self.db.execute_query(query, params, conn=conn, commit=False)
                self.stock_model.update_quantity(i_data['id'], i_data['qty'], conn=conn, commit=False)

                # --- Registrar movimiento ---
                qty_after   = (qty_before or 0) + i_data['qty']
                cost_after  = p_data['cost_price']
                price_after = p_data['sale_price']

                self.movement.register(
                    product_id   = i_data['id'],
                    product_name = i_data['name'],
                    event_type   = 'COMPRA',
                    detail       = f"Compra ID {purchase_id}",
                    qty_before   = qty_before,
                    qty_after    = qty_after,
                    cost_before  = cost_before,
                    cost_after   = cost_after,
                    price_before = price_before,
                    price_after  = price_after,
                    conn         = conn,
                    commit       = False
                )

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f'Ocurrio un error: {e}')
            return False

        finally:
            conn.close()

    ## -- Prepara cada item de compra para agregarlo a stock -- ##
    def prepare_item_to_add_to_stock(self, item):
            date = datetime.now().strftime("%Y-%m-%d")
            p = self.stock_model.get_product_by_id(item['id']) # recupero producto desde stock

            # recupero los datos y transformo a decimal
            id =  item['id'] # id producto
            name = item['name'] # nombre producto
            pack = item['pack'] # envase producto
            list_price = item['list_price']

            discount = item['discount']
            discount_amount = Decimal((item['list_price'] * discount) / Decimal('100')) # monto descuento

            cost_price = Decimal(item['list_price'] - discount_amount)# se aplica descuento
            iva = item['iva_rate'] # porcentaje de iva
            last_price_upd = date # fecha de ult. act de precio

            profit = Decimal(1 + Decimal(p[3]) / Decimal('100'))

            sale_price = cost_price * profit
            # precio con iva
            if iva == Decimal('21.00'):
                price_with_iva = sale_price * Decimal('1.21')
            elif iva == Decimal('10.50'):
                price_with_iva = sale_price * Decimal('1.105')
            else:
                price_with_iva = sale_price

            cost_price = flex_dec(cost_price)
            sale_price = flex_dec(sale_price)
            price_with_iva = flex_dec(price_with_iva)

            product_data = {
                'id': id, # id producto
                'name': name, # nombre producto
                'pack': pack, # envase producto
                'list_price': str(list_price),
                'discount': str(discount), # descuento
                'cost_price': str(cost_price),
                'iva': str(iva), # porcentaje de iva
                'sale_price': str(sale_price),
                'price_with_iva': str(price_with_iva),
                'last_price_upd': last_price_upd # fecha de ult. act de precio
            }

            return product_data

    ## -- Setear saldo pendiente de la compra-- ##
    def set_new_debt_purchase(self, purchase_id, id, doc_type, new_debt, conn=None, commit=True):

        state = 'PAGADA' if new_debt <= Decimal('0.00') else 'PENDIENTE'

        query = """
        UPDATE purchase
        SET
            pending = ?,
            state = ?
        WHERE id = ?
        """

        params = (str(new_debt), state, purchase_id)

        self.db.execute_query(query, params, conn=conn, commit=commit)

        # Si quedó pagada, actualizar comprobante
        if doc_type == "REMITO":
            query = """
            UPDATE supplier_receipt
            SET state = ?
            WHERE id = ?
            """
        else:
            query = """
            UPDATE supplier_invoice
            SET state = ?
            WHERE id = ?
            """

        params = (state, id)
        self.db.execute_query(query, params, conn=conn, commit=commit)
    
    ## -- Vincular comprobante con compra -- ##
    def set_doc_on_purchase(self, purchase_id, id, doc_type, conn=None, commit=True):
        """Set a doc number on purchase"""

        if doc_type == "REMITO":
            query = """
                UPDATE purchase
                SET receipt_id = ?
                WHERE id = ?
            """
        else:
            query = """
                UPDATE purchase
                SET invoice_id = ?
                WHERE id = ?
            """

        params = [
            id,
            purchase_id
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)
    
    ## -- Debt -- ##
    def get_debt_of_supplier(self, supplier_id):
        query = """
        SELECT pending
        FROM purchase
        WHERE supplier_id = ? AND state != 'BORRADOR'
        """    
        rows = self.db.fetch_all(query, (supplier_id, ))

        pending = Decimal('0.00')

        for row in rows:
            pending += Decimal(row[0])

        return norm_to_2_dec(pending)
    
    ## -- Calcula el pendiente de una compra
    def calculate_pending_of_purchase(self, purchase_id, payment_id):
        # Datos de la compra
        purchase_data = None

        # Datos de pagos asociados a la venta
        payment_data = None

    def update_last_debt_update(self, supplier_id, conn=None, commit=True):
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
        """Actualizar Saldo deuda a un proveedor"""
        query = """
            UPDATE supplier
            SET last_debt_update = ?
            WHERE id = ?
        """
        params = [
            date,
            supplier_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)
        return date

    ## TRANSACCIONES ##

    ## Eliminar un registro de compra junto con su informacion asociada
    def delete_purchase_and_doc(self, purchase_id, doc_id, doc_type):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            query = """
            DELETE FROM purchase WHERE id = ?
            """

            self.db.execute_query(query, (purchase_id, ), conn=conn, commit=False)

            if doc_type == 'REMITO':
                self.supplier_receipt.delete_receipt(doc_id, conn=conn, commit=False)
            else:
                self.supplier_invoice.delete_invoice(doc_id, conn=conn, commit=False)

            conn.commit()
            return True
        
        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close()

    ##  Transaccion que maneja la eliminacion de un item y hace sus respectivos calculos
    def handle_delete_purchase_item(self, purchase_id, product_id, doc_type, doc_id):
        try:
            conn = self.db.get_connection()

            conn.execute("BEGIN")

            self.delete_purchase_item(purchase_id, product_id, conn=conn, commit=False)
            self.recalc_doc_values(purchase_id, doc_type, doc_id, conn=conn, commit=False)

            conn.commit()
            return True
        
        except ValueError as e:
            conn.rollback()
            return False
        
        finally:
            conn.close()

    # Elimina un purchase item
    def delete_purchase_item(self, purchase_id, product_id, conn=None, commit=True):
        query = """
        DELETE FROM purchase_item 
        WHERE purchase_id = ? AND product_id = ?
        """

        self.db.execute_query(query, (purchase_id, product_id), conn=conn, commit=commit)

    ## Transaccion para actualizar informacion de la compra y su doc asociado
    def update_purchase(self, purchase_id, doc_id, data, doc_type):

        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            query = """
            UPDATE purchase
            SET
                date = ?,
                expiration_date = ?,
                observations = ?
            WHERE id = ?
            """
            params = [
                traditional_to_iso(data['date']),
                traditional_to_iso(data['expiration']),
                data['obs'],
                purchase_id
            ]
            
            self.db.execute_query(query, params, conn=conn, commit=False)

            # Si es remito
            if doc_type == 'REMITO':
                self.supplier_receipt.update_receipt_info(doc_id, data, conn=conn, commit=False)

            else:
                self.supplier_invoice.update_invoice_info(doc_id, data, conn=conn, commit=False)

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            import traceback
            traceback.print_exc()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close()

    ## -- Transaccion para agregar venta y recibo -- ##
    def create_receipt_and_purchase(self, receipt_params, purchase_params):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            receipt_id = self.supplier_receipt.add_new_receipt(receipt_params, conn, commit=False)
            purchase_id = self.add_new_purchase(purchase_params, conn, commit=False)

            self.set_doc_on_purchase(purchase_id, receipt_id, "REMITO", conn, commit=False)

            conn.commit()
            return True
        
        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close()

    ## -- Transaccion para agregar venta y factura -- ##
    def create_invoice_and_purchase(self, invoice_params, perception_parameters, purchase_params):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            invoice_id = self.supplier_invoice.add_new_invoice(invoice_params, conn, commit=False)
            for p in perception_parameters:
                self.supplier_invoice.add_invoice_perceptions(invoice_id, p, conn, commit=False)
            purchase_id = self.add_new_purchase(purchase_params, conn, commit=False)

            self.set_doc_on_purchase(purchase_id, invoice_id, "FACTURA", conn, commit=False)

            conn.commit()
            return True 
        
        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close()