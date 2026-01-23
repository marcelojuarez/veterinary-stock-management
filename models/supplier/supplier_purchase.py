# models/supplier/supplier_purchase.py

from datetime import datetime
from models.stock import StockModel
from decimal import Decimal, ROUND_HALF_UP

class SupplierPurchase():
    def __init__(self, db):
        self.db = db
        self.stock_model = StockModel()

    ## Nueva compra
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

    ## Obtener compra por id
    def get_purchase_by_id(self, purchase_id):
        try:
            query= """
            SELECT * FROM purchase WHERE id = ?
            """
            
            return self.db.fetch_one(query, (purchase_id, ))

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')
            return None

    ## Obtener compra por fecha 
    def get_purchase_by_date(self, date):
        try:
            query= """
            SELECT * FROM purchase WHERE date = ?
            """
            return self.db.fetch_all(query, (date, ))

        except ValueError as e:
            print(f'Error al obtener la compra: {e}')
            return None

    ## Devuelve todas las compras asociadas a un cuit 
    def get_all_purchases(self, cuit=None):

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
    
    ## Nuevo Producto
    def add_product(self, product_data):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
    ## Nuevo Item de compra
    def add_purchase_item(self, params):
        query = """
            INSERT INTO purchase_item (purchase_id, product_id, product_name, pack, quantity, cost_price, iva_rate, 
            discount, discount_amount, subtotal, iva_amount, total) 
            VALUES (?, ?, ? ,?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(query, params)
    
    ## -- Obtener items de compra -- ##
    def get_purchase_items(self, purchase_id):
        query = """
            SELECT product_id, product_name, pack, quantity, cost_price, iva_rate,
            discount, discount_amount, subtotal, iva_amount, total
            FROM purchase_item
            WHERE purchase_id = ?
        """

        return self.db.fetch_all(query, (purchase_id, ))

    ##  -- Obtener suma de los items para generar deuda -- ##
    def get_sum_of_items(self, purchase_id):
        query = """
        SELECT SUM(total)
        FROM purchase_item
        WHERE purchase_id = ?
        """ 

        return self.db.fetch_one(query, (purchase_id, ))
    
    def get_iva_amount_of_p_items(self, purchase_id):
        query = """
        SELECT SUM(iva_amount)
        FROM purchase_item
        WHERE purchase_id = ?
        """
        return self.db.fetch_one(query, (purchase_id, ))

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
        initial_debt = round(initial_debt, 2)

        query = """
        UPDATE purchase
        SET
            state = 'PENDIENTE',
            pending = ?,
            total = ?
        WHERE id = ?
        """

        params = (initial_debt, initial_debt, purchase_id)

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

        params = (initial_debt, id)
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

            if doc_type == 'FACTURA':
                
                iva_amount = self.get_iva_amount_of_p_items(purchase_id)[0]
                print(f'Monto iva: {iva_amount}')

                query = """
                UPDATE supplier_invoice
                SET iva = ?
                WHERE id = ?
                """
                params = [
                    iva_amount,
                    id
                ]
                self.db.execute_query(query, (params), conn=conn, commit=False)

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f'Ocurrio un error: {e}')
            return False

        finally:
            conn.close()

    def prepare_item_to_add_to_stock(self, item):
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            p = self.stock_model.get_product_by_id(item['id']) # recupero producto desde stock

            print(f'Producto desde stock \n {p}')

            # recupero los datos y transformo a decimal
            id =  item['id'] # id producto
            name = item['name'] # nombre producto
            pack = item['pack'] # envase producto
            discount_amount = Decimal((item['cost_price'] * item['discount']) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) # monto descuento
            cost_price = Decimal(item['cost_price'] - discount_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) # se aplica descuento
            iva = item['iva_rate'] # porcentaje de iva
            last_price_upd = date # fecha de ult. act de precio

            profit = Decimal(1 + Decimal(p[3]) / 100)

            sale_price = Decimal(cost_price * profit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # precio con iva
            if iva == 21.0:
                price_with_iva = Decimal(sale_price * Decimal(1.21)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            elif iva == 10.5:
                price_with_iva = Decimal(sale_price * Decimal(1.105)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
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

            print(f'Precio de producto stock act \n :{product_data}')

            return product_data
    
    def delete_purchase(self, purchase_id, conn=None, commit=True):
        query = """
        DELETE FROM purchase WHERE id = ?
        """

        self.db.execute_query(query, (purchase_id, ), conn=conn, commit=commit)

    ## -- Setear saldo pendiente de la compra-- ##
    def set_new_debt_purchase(self, purchase_id, id, doc_type, new_debt, conn=None, commit=True):

        print(f'new_debt: {new_debt}')
        print(f'tipo new_debt: {type(new_debt)}')

        if new_debt <= Decimal("0.00"):
            new_debt = Decimal("0.00")

        query = """
        UPDATE purchase
        SET
            pending = ?,
            state = CASE
                WHEN ? <= 0 THEN 'PAGADA'
                ELSE 'PENDIENTE'
            END
        WHERE id = ?
        """

        params = (str(new_debt), new_debt, purchase_id)

        self.db.execute_query(query, params, conn=conn, commit=commit)

        # Si quedó pagada, actualizar comprobante
        if doc_type == "REMITO":
            query = """
            UPDATE supplier_receipt
            SET 
                state = CASE 
                    WHEN ? <= 0 THEN 'PAGADA'
                    ELSE 'PENDIENTE'
                END
            WHERE id = ?
            """
        else:
            query = """
            UPDATE supplier_invoice
                SET state = CASE
                    WHEN ? <= 0 THEN 'PAGADA'
                    ELSE 'PENDIENTE'
                END
            WHERE id = ?
            """

        params = (new_debt, id)
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

    ## -- Invoice -- ##
    def add_new_invoice(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d")
        query = """
        INSERT INTO supplier_invoice(supplier_id, invoice_id, invoice_type, date, expiration_date, 
        total, subtotal, iva, discount, state, observations)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params =[
            data['supplier_id'],
            data['invoice_id'],
            data['invoice_type'],
            date,
            data['expiration_date'],
            str(data['total']),
            str(data['subtotal']),
            str(data['iva']),
            str(data['discount']),
            data['state'],
            data['observations'],
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)

    def get_invoice_data(self, invoice_id):
        query = """
        SELECT * FROM supplier_invoice
        WHERE id = ? 
        """

        return self.db.fetch_one(query, (invoice_id, ))
        
    def update_invoice_info(self, invoice_id, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        UPDATE supplier_invoice
        SET 
            invoice_id = ?,
            invoice_type = ?,
            observations = ?,
            date = ?,
            expiration_date = ?
        WHERE id = ?
        """

        params = [
            data['invoice_id'],
            data['invoice_type'], 
            data['obs'],
            date,
            data['expiration'],
            invoice_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=commit)

    def delete_invoice(self, invoice_id, conn=None, commit=True):
        query = """
        DELETE FROM supplier_invoice WHERE id = ?
        """

        self.db.execute_query(query, (invoice_id, ), conn=conn, commit=commit)

    ## -- RECEIPT -- ##
    def add_new_receipt(self, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d")
        query = """
        INSERT INTO supplier_receipt(supplier_id, receipt_id, date, expiration_date, observations,
        state, total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            data['supplier_id'],
            data['receipt_id'],
            date,
            data['expiration_date'],
            data['observations'],
            data['state'],
            str(data['total']), 
        ]

        return self.db.execute_query(query, params, conn=conn, commit=commit)
    
    def get_receipt_data(self, receipt_id):
        query = """
        SELECT * FROM supplier_receipt
        WHERE id = ? 
        """

        return self.db.fetch_one(query, (receipt_id, ))
    
    def update_receipt_info(self, receipt_id, data, conn=None, commit=True):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        UPDATE supplier_receipt
        SET 
            receipt_id = ?,
            date = ?,
            expiration_date = ?,
            observations = ?
        WHERE id = ?
        """

        params = [
            data['receipt_id'],            
            date,
            data['expiration'],
            data['obs'],
            receipt_id
        ]

        self.db.execute_query(query, params, conn=conn, commit=False)

    def delete_receipt(self, receipt_id, conn=None, commit=True):
        query = """
        DELETE FROM supplier_receipt WHERE id = ?
        """

        self.db.execute_query(query, (receipt_id, ), conn=conn, commit=commit)

    ## TRANSACCIONES ##

    ## Eliminar un registro de compra junto con su informacion asociada
    def delete_purchase_and_doc(self, purchase_id, doc_id, doc_type):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            self.delete_purchase(purchase_id, conn=conn, commit=False)

            if doc_type == 'REMITO':
                self.delete_receipt(doc_id, conn=conn, commit=False)
            else:
                self.delete_invoice(doc_id, conn=conn, commit=False)

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        finally:
            conn.close()
    ## Transaccion para 

    ## Transaccion para actualizar informacion de la compra y su doc asociado
    def update_purchase(self, purchase_id, doc_id, data, doc_type):

        try:
            conn = self.db.get_connection()
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
                data['expiration'],
                purchase_id
            ]
            
            self.db.execute_query(query, params, conn=conn, commit=False)

            # Si es remito
            if doc_type == 'REMITO':
                self.update_receipt_info(doc_id, data, conn=conn, commit=False)

            else:
                self.update_invoice_info(doc_id, data, conn=conn, commit=False)

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

            receipt_id = self.add_new_receipt(receipt_params, conn, commit=False)
            purchase_id = self.add_new_purchase(purchase_params, conn, commit=False)

            print(f"receipt_id: {receipt_id}")
            print(f"purchase_id: {purchase_id}")

            self.set_doc_on_purchase(purchase_id, receipt_id, "REMITO", conn, commit=False)

            self.update_last_debt_update(purchase_params['supplier_id'], conn, commit=False)

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close()
            return True

    ## -- Transaccion para agregar venta y factura -- ##
    def create_invoice_and_purchase(self, invoice_params, purchase_params):
        try:
            conn = self.db.get_connection()

            # Iniciar transacción
            conn.execute("BEGIN")

            invoice_id = self.add_new_invoice(invoice_params, conn, commit=False)
            purchase_id = self.add_new_purchase(purchase_params, conn, commit=False)

            self.set_doc_on_purchase(purchase_id, invoice_id, "FACTURA", conn, commit=False)

            self.update_last_debt_update(purchase_params['supplier_id'], conn, commit=False)

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f'Hubo un error {e}')
            return False
        
        finally:
            conn.close() 
            return True    