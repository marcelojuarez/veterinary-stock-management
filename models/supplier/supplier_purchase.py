# models/supplier/supplier_purchase.py

from datetime import datetime
from models.stock import StockModel
from .supplier_invoice import SupplierInvoice
from .supplier_receipt import SupplierReceipt
from decimal import Decimal, ROUND_HALF_UP
from utils.utils import normalize_decimal, traditional_to_iso

class SupplierPurchase():
    def __init__(self, db):
        self.db = db
        self.stock_model = StockModel()
        self.supplier_invoice = SupplierInvoice(db)
        self.supplier_receipt = SupplierReceipt(db)

    ## -- Agregar nueva compra -- ##
    def add_new_purchase(self, data, conn=None, commit=True):
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            query = """
            INSERT INTO purchase (supplier_id, document_type, date, expiration_date, state, observations, pending, total) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = [
                data['supplier_id'],
                data['doc_type'],
                date,
                data['expiration_date'],
                data['state'],
                data['observations'],
                str(data['pending']),
                str(data['total'])
            ]

            return self.db.execute_query(query, params, conn=conn, commit=commit)
        except ValueError as e:
            print(f'Error al cargar la compra: {e}')

    ## -- Obtener compra por ID -- ##
    def get_purchase_by_id(self, purchase_id):
        try:
            query= """
            SELECT * FROM purchase WHERE id = ?
            """
            
            return self.db.fetch_one(query, (purchase_id, ))

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')
            return None

    ## Obtener compra por fecha ##
    def get_purchases_by_date(self, date, cuit=None):
        try:
            query = """
                SELECT purchase.id, supplier.cuit, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
                purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
                FROM purchase
                JOIN supplier ON purchase.supplier_id = supplier.id
                WHERE purchase.date = ?
                    AND (? IS NULL OR supplier.cuit = ?) 
                ORDER BY 
                CASE 
                    WHEN purchase.state = 'PENDIENTE' THEN 0 
                    ELSE 1 
                END,
                purchase.expiration_date
            """ 
            params = [
                date,
                cuit,
                cuit
            ]
            return self.db.fetch_all(query, params)

        except ValueError as e:
            print(f'Error al obtener las compras: {e}')
            return None

    ## -- Devuelve todas las compras asociadas a un CUIT -- ##
    def get_all_purchases(self, cuit=None):
        try:
            query = """
                SELECT purchase.id, supplier.cuit, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
                purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
                FROM purchase
                JOIN supplier ON purchase.supplier_id = supplier.id
                WHERE (? IS NULL OR supplier.cuit = ?) 
                ORDER BY 
                CASE 
                    WHEN purchase.state = 'PENDIENTE' THEN 0 
                    ELSE 1 
                END,
                purchase.expiration_date
            """ 
            params = [
                cuit,
                cuit
            ]
            return self.db.fetch_all(query, params)
        
        except ValueError as e:
            print(f'Error al obtener las compras: {e}')
            return None
        
    ## -- Devuelve todas las compras confirmadas asociadas a un CUIT -- ##
    def get_all_confirmed_purchases(self, cuit=None):
        try:
            query = """
                SELECT purchase.id, supplier.cuit, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
                purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
                FROM purchase
                JOIN supplier ON purchase.supplier_id = supplier.id
                WHERE (? IS NULL OR supplier.cuit = ?) AND purchase.state != 'BORRADOR'
                ORDER BY 
                CASE 
                    WHEN purchase.state = 'PENDIENTE' THEN 0 
                    ELSE 1 
                END,
                purchase.expiration_date
            """ 
            params = [
                cuit,
                cuit
            ]
            return self.db.fetch_all(query, params)
        
        except ValueError as e:
            print(f'Error al obtener las compras: {e}')
            return None
    
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
            (name, pack, profit, cost_price, price, iva, price_with_iva, quantity, created_at, last_price_update) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            product_data['Name'],
            product_data['Package'],
            str(product_data['Profit']),
            str(product_data['CostPrice']),
            str(product_data['SalePrice']),
            str(product_data['Iva']),
            str(product_data['PriceWIva']),
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
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close() 

    
    ## -- Agregar nuevo Item de compra -- ##
    def add_purchase_item(self, params, conn=None, commit=True):

        query = """
            INSERT INTO purchase_item (purchase_id, product_id, product_name, pack, quantity,
            cost_price, iva_rate,discount, discount_amount, subtotal, iva_amount, total) 
            VALUES (?, ?, ? ,?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(query, params, conn=conn, commit=commit)
       
    ## -- Recalcular los valores del doc asociado a la compra -- ##
    def recalc_doc_values(self, purchase_id, doc_type, doc_id, conn=None, commit=True):

        if doc_type == 'FACTURA':
            ## factura ##

            ## monto_iva
            iva_amount = self.get_iva_amount_of_p_items(purchase_id, conn=conn)[0]
            if iva_amount is None:
                r_iva_amount = normalize_decimal('0.00')
            else:
                r_iva_amount = normalize_decimal(iva_amount)
            print(f'Monto iva: {r_iva_amount}')

            query = """ UPDATE supplier_invoice SET iva = ? WHERE id = ? """

            self.db.execute_query(query, (str(r_iva_amount), doc_id), conn=conn, commit=commit)

            ## subtotal
            subtotal = self.get_subtotal_of_items(purchase_id, conn=conn)[0]
            if subtotal is None:
                r_subtotal = normalize_decimal('0.00')
            else:
                r_subtotal = normalize_decimal(subtotal)

            total = self.get_total_of_items(purchase_id, conn=conn)[0]
            if total is None:
                r_total = normalize_decimal('0.00')
            else:
                r_total = normalize_decimal(total)
            
            query = """ UPDATE supplier_invoice SET subtotal = ?, total = ?  WHERE id = ? """

            self.db.execute_query(query, (str(r_subtotal), str(r_total), doc_id), conn=conn, commit=commit)

        else:
            ## remito
            total = self.get_total_of_items(purchase_id, conn=conn)[0]
            if total is None:
                rounded_total = normalize_decimal('0.00')
            else:
                rounded_total = normalize_decimal(total)

            print(f'Total: {rounded_total}')

            query = """ UPDATE supplier_receipt SET total = ? WHERE id = ? """

            self.db.execute_query(query, (str(rounded_total), doc_id), conn=conn, commit=commit)

    ## -- Obtener items de compra -- ##
    def get_purchase_items(self, purchase_id):
        query = """
            SELECT product_id, product_name, pack, quantity, cost_price, iva_rate,
            discount, discount_amount, subtotal, iva_amount, total
            FROM purchase_item
            WHERE purchase_id = ?
        """

        return self.db.fetch_all(query, (purchase_id, ))

    ##  -- Obtener subtotal de items -- ##
    def get_subtotal_of_items(self, purchase_id, conn=None):
        query = """
        SELECT SUM(subtotal)
        FROM purchase_item
        WHERE purchase_id = ?
        """
        return self.db.fetch_one(query, (purchase_id, ), conn=conn)
    
    ##  -- Obtener total de items -- ##
    def get_total_of_items(self, purchase_id, conn=None):
        query = """
        SELECT SUM(total)
        FROM purchase_item
        WHERE purchase_id = ?
        """ 

        return self.db.fetch_one(query, (purchase_id, ), conn=conn)
    
    ## -- Obtener suma de iva de items -- ##
    def get_iva_amount_of_p_items(self, purchase_id, conn=None):
        query = """
        SELECT SUM(iva_amount)
        FROM purchase_item
        WHERE purchase_id = ?
        """
        return self.db.fetch_one(query, (purchase_id, ), conn=conn)

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
    def get_all_purchases_without_paying(self, cuit=None):

        query = """
            SELECT purchase.id, supplier.cuit, purchase.document_type, purchase.invoice_id, purchase.receipt_id , purchase.date, 
            purchase.expiration_date, purchase.state, purchase.observations, purchase.pending, purchase.total
            FROM purchase
            JOIN supplier ON purchase.supplier_id = supplier.id
            WHERE (? IS NULL OR supplier.cuit = ?) AND pending > 0 
            ORDER BY 
            CASE 
                WHEN purchase.state = 'PENDIENTE' THEN 0 
                ELSE 1 
            END,
            purchase.expiration_date
        """

        params = [
            cuit,
            cuit
        ]

        return self.db.fetch_all(query, params)
    
    def set_initial_debt_purchase(self, purchase_id, id, doc_type, initial_debt, conn=None, commit=True):

        query = """
        UPDATE purchase
        SET
            state = 'PENDIENTE',
            pending = ?,
            total = ?
        WHERE id = ?
        """

        params = (str(initial_debt), str(initial_debt), purchase_id)
        self.db.execute_query(query, params, conn=conn, commit=commit)

        # Si quedó pagada, actualizar comprobante

        if doc_type == "REMITO":
            query = """
            UPDATE supplier_receipt
            SET 
                state = 'PENDIENTE',
                total = ?
            WHERE id = ?
            """
        else:
            query = """
            UPDATE supplier_invoice
            SET 
                state = 'PENDIENTE',
                total = ?
            WHERE id = ?
            """

        params = (str(initial_debt), id)
        self.db.execute_query(query, params, conn=conn, commit=commit)       

    ## -- Carga los items de la compra en stock y setea la nueva deuda del proveedor -- ## 

    def load_products_and_set_initial_debt(self, purchase_id, id, doc_type, debt):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            # Se setea nueva deuda y se carga compra como pendiente
            self.set_initial_debt_purchase(purchase_id, id, doc_type, debt, conn=conn, commit=False)

            items = self.get_purchase_items(purchase_id)

            for i in items:
                
                i_data = {
                    'id': i[0],
                    'name': i[1],
                    'pack': i[2],
                    'qty': i[3],
                    'cost_price': Decimal(i[4]),
                    'iva_rate': Decimal(i[5]),
                    'discount': Decimal(i[6]),
                }

                print(f'Producto desde purchase: \n {i_data}')
                p_data = self.prepare_item_to_add_to_stock(i_data)

                params = [
                    p_data['name'],
                    p_data['pack'],
                    p_data['cost_price'],
                    p_data['sale_price'],
                    p_data['iva'],
                    p_data['price_with_iva'],
                    p_data['last_price_upd'],
                    p_data['id']
                ]

                query = """
                UPDATE stock 
                SET 
                    name = ?,
                    pack = ?,
                    cost_price = ?,
                    price = ?,
                    iva = ?,
                    price_with_iva = ?,
                    last_price_update = ?
                WHERE id = ?
                """

                self.db.execute_query(query, params, conn=conn, commit=False)

                self.stock_model.update_quantity(i_data['id'], i_data['qty'], conn=conn, commit=False)

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
            discount_amount = normalize_decimal((item['cost_price'] * item['discount']) / 100) # monto descuento
            cost_price = normalize_decimal(item['cost_price'] - discount_amount)# se aplica descuento
            iva = item['iva_rate'] # porcentaje de iva
            last_price_upd = date # fecha de ult. act de precio

            profit = Decimal(1 + Decimal(p[3]) / 100)

            sale_price = normalize_decimal(cost_price * profit)

            # precio con iva
            if iva == 21.0:
                price_with_iva = normalize_decimal(sale_price * Decimal(1.21))
            elif iva == 10.5:
                price_with_iva = normalize_decimal(sale_price * Decimal(1.105))
            else:
                price_with_iva = sale_price

            product_data = {
                'id': id, # id producto
                'name': name, # nombre producto
                'pack': pack, # envase producto
                'cost_price': str(cost_price),
                'iva': str(iva), # porcentaje de iva
                'sale_price': str(sale_price),
                'price_with_iva': str(price_with_iva),
                'last_price_upd': last_price_upd # fecha de ult. act de precio
            }

            return product_data

    ## -- Setear saldo pendiente de la compra-- ##
    def set_new_debt_purchase(self, purchase_id, id, doc_type, new_debt, conn=None, commit=True):

        print(f'new_debt: {new_debt}')
        print(f'tipo new_debt: {type(new_debt)}')

        new_debt = normalize_decimal(new_debt)

        state = 'PAGADA' if new_debt <= Decimal(0.00) else 'PENDIENTE'

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
    def get_debt_of_supplier(self, cuit):
        query = """
        SELECT SUM(pending) 
        FROM purchase JOIN supplier ON purchase.supplier_id = supplier.id
        WHERE supplier.cuit = ?
        """

        return self.db.fetch_one(query, (cuit, ))
    
    def update_last_debt_update(self, supplier_id, conn=None, commit=True):
        print('Se ejecuta esta funcion')
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            date = datetime.now().strftime("%Y-%m-%d")

            # Iniciar transacción
            conn.execute("BEGIN")

            query = """
            UPDATE purchase
            SET
                date = ?,
                expiration_date = ?
            WHERE id = ?
            """
            params = [
                date,
                traditional_to_iso(data['expiration']),
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
    def create_invoice_and_purchase(self, invoice_params, purchase_params):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            invoice_id = self.supplier_invoice.add_new_invoice(invoice_params, conn, commit=False)
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
   