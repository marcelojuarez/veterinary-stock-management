
import re
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from models.customer import CustomerModel
from models.payment_model import PaymentModel
from utils.view_helpers import show_error, show_warning, show_success, center_window

from utils.receipts.pdf_generator import generate_payment_receipt, generate_global_payment_receipt
from utils.receipts.ticket_pos import generate_payment_ticket, generate_global_payment_ticket
from utils.receipts.manager import generate_receipts_for_payment
from utils.receipts.account_statement import generate_account_statement
from utils.receipts.paths import a4_pago_global
from utils.utils import norm_to_2_dec, string_to_2_dec
from decimal import Decimal, InvalidOperation


class CustomerController: 
    def __init__(self):
        self.view = None
        self.model = CustomerModel()
        self.payment_model = PaymentModel()
        self.all_customers = []

    def set_view(self, view):
        self.view = view
        # after set view
        self.load_customers()  

    def load_customers(self):
        """Carga inicial de clientes en memoria"""
        try:
            self.all_customers = self.model.get_all_customers()
            self.view.refresh_customer_table(self.all_customers)
        except Exception as e:
            show_error(f"Error al cargar clientes: {e}")

    def refresh_customer_data(self):
        """Recargar desde DB (solo cuando hay cambios)"""
        try:
            self.all_customers = self.model.get_all_customers()
            self.view.refresh_customer_table(self.all_customers)
        except Exception as e:
            show_error(f"Error al refrescar datos: {e}")

    def search_customer(self, query):
        """Método existente - ahora usa filtrado en memoria"""
        self.filter_customers(query)

    def add_new_customer_window(self, data, window):
        """Guarda un nuevo cliente desde la ventana modal"""
        try:
            # Validaciones básicas
            if not self.__validate_customer_data(data):
                return False
            if not self.__validate_supplier_cuit(data["cuit"]):
                return False
            if not self.__validate_supplier_phone(data["telefono"]):
                return False

            # Guardar cliente
            self.model.add_customer(data)
            self.refresh_customer_data()
            window.destroy()
            return True

        except ValueError as e:
            show_error(f"Error en los datos: {str(e)}")
            return False
        except Exception as e:
            show_error(f"Error al registrar el cliente: {str(e)}")
            return False

    def delete_customer(self, customer_id):
        """Elimina un cliente por su ID"""
        confirm = messagebox.askyesno("Confirmar", "¿Desea eliminar este cliente?")
        if not confirm:
            return False

        try:
            self.model.delete_customer(customer_id)
            self.refresh_customer_data()
            show_success("Cliente eliminado correctamente.")
            return True
        except Exception as e:
            show_error(f"Error al eliminar el cliente: {str(e)}")
            return False


    def filter_customers(self, query: str):
        """Filtra clientes en memoria según la búsqueda"""
        query = query.strip().lower()
        
        if not query:
            # Si no hay búsqueda, mostrar todos
            self.view.refresh_customer_table(self.all_customers)
            return
        
        # Filtrar en memoria
        filtered = []
        for customer in self.all_customers:
            # customer estructura: (id, nombre, cuit, domicilio, telefono, cv, cuig, renspa, establecimiento)
            if (query in str(customer[0]).lower() or        # ID
                query in customer[1].lower() or             # Nombre
                query in customer[2].lower() or             # CUIT
                query in customer[3].lower() or             # Domicilio
                query in customer[4].lower() or             # Teléfono
                query in customer[5].lower() or             # Condicion IVA
                query in customer[6].lower() or             # CV
                query in customer[7].lower() or             # CUIG
                query in customer[8].lower() or             # RENSPA
                query in customer[9].lower()                # Establecimiento
                ):              

                filtered.append(customer)
        
        self.view.refresh_customer_table(filtered)


    def __validate_customer_data(self, data):
        # Validar campos obligatorios 
        required_fields = ['nombre', 'cuit', 'domicilio', 'telefono']
        for field in required_fields:
            if not data[field]:
                show_warning(f'Por favor complete el campo {field}.')
                return False 
        return True

    def __validate_supplier_cuit(self, cuit_field):
        pattern = r'^\d{2}-\d{8}-\d$'
        
        if not re.fullmatch(pattern, cuit_field):
            show_warning("Por favor coloque el CUIT correctamente. Formato: XX-XXXXXXXX-X")
            return False
        
        return True
    
    def __validate_supplier_phone(self, phone_field):
        pattern = r'^\+?\d{7,15}$'
        
        if not re.fullmatch(pattern, phone_field):
            show_warning("Por favor coloque el teléfono correctamente. Debe contener entre 7 y 15 dígitos, puede incluir un '+' al inicio.")
            return False
        
        return True
    
    # --------------------------------------------------------------------
    # 💳 DEUDAS DE CLIENTES
    # --------------------------------------------------------------------

    def show_customer_debts(self, cliente_id, cliente_nombre):
        """Abre ventana con las deudas del cliente"""
        try:
            self.current_client_id = cliente_id

            #changes = self.reconcile_and_detect_changes(cliente_id)

            debts = self.model.get_customer_debts(cliente_id)
            total = self.model.get_total_debt(cliente_id)
            credit = norm_to_2_dec(self.payment_model.get_customer_credit(cliente_id))

            net = norm_to_2_dec(max(Decimal('0.00'), total - credit))
            self.view.open_debt_window(cliente_id, cliente_nombre, debts, total, credit, net)

            # if changes:
            #     self.view.show_warning(
            #     f"⚠️ Se detectaron cambios de precio en {len(changes)} venta(s):\n\n" +
            #     "\n".join(changes)
            #     )
        except Exception as e:
            show_error(f"Error al obtener las deudas: {e}")

    def reconcile_and_detect_changes(self, cliente_id):
        """Reconcilia ventas y detecta cambios de precio"""
        changes = []
        
        # Obtener ventas pendientes/parciales
        rows = self.payment_model.db.fetch_all(
            """
            SELECT s.id, s.estado
            FROM sales s
            WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
            """,
            (cliente_id,)
        )
        
        for sale_id, estado_antes in rows:
            total_antes = self.payment_model.get_sale_total_variable(sale_id)
            paid = self.payment_model.get_sale_paid(sale_id)
            
            # Reconciliar esta venta
            nuevo_estado = self.payment_model.reconcile_sale(sale_id)
            
            # Detectar si cambió a paid
            if estado_antes != 'paid' and nuevo_estado == 'paid':
                total_final = self.payment_model.get_sale_total(sale_id)
                sobrepago = norm_to_2_dec(paid - total_final)
                
                if sobrepago > Decimal('0.01'):
                    changes.append(
                        f"✅ Venta #{sale_id} PAGADA - Saldo a favor: ${sobrepago:.2f}"
                    )
                else:
                    changes.append(f"✅ Venta #{sale_id} quedó PAGADA por cambio de precio")
        
        return changes
    
    def load_sale_items_for_debt(self, sale_id):
        """Carga el detalle de productos de una venta fiada en la vista"""
        try:
            items = self.model.get_sale_items(sale_id)            
            self.view.update_debt_items_table(items)
        except Exception as e:
            show_error(f"Error al obtener los productos de la venta: {e}")

    def customer_has_debts(self, customer_id):
            """Obtengo la cantidad de deudas de un cliente"""
            try: 
                query = """
                    SELECT COUNT(*) 
                    FROM sales 
                    WHERE cliente_id = ? 
                    AND estado IN ('pending', 'partial')
                """
                result = self.model.db.fetch_one(query,(customer_id,))
                return result and result[0] > 0
            except Exception as e:
                show_error(f"Error al obtener las deudas del cliente: {e}")


    def open_global_payment_window(self):
        customer_id = self.view.get_selected_customer_id()
        if not customer_id:
            show_warning("Selecciona un cliente primero.")
            return

        total_debt = self.model.get_total_debt(customer_id)

        if total_debt == Decimal('0.00'):
            self.view.show_warning("El cliente no tiene deudas pendientes")
            return
        
        # Crear ventana modal con estilo
        win = ctk.CTkToplevel(self.view.frame)
        win.title("Pago Global a Cuenta")
        win.transient(self.view.frame)
        win.grab_set()
        center_window(win, 450, 500)

        # Header
        header = ctk.CTkFrame(win, fg_color="#009688", height=60, corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header, 
            text="Registrar Pago Global",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        ).pack(pady=15)

        content = ctk.CTkFrame(win, fg_color="transparent")
        content.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(
            content,
            text="Este pago se distribuirá automáticamente\nentre las deudas más antiguas.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 20))

        # Input
        ctk.CTkLabel(content, text="Monto a entregar:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        amount_var = ctk.StringVar()
        entry_amount = ctk.CTkEntry(
            content,
            textvariable=amount_var,
            width=250,
            height=40,
            placeholder_text="$ 0.00",
            font=ctk.CTkFont(size=14)
        )
        entry_amount.pack()

        # Método de pago
        ctk.CTkLabel(
            content, 
            text="Método de pago:", 
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(20, 5))

        method_var = ctk.StringVar(value="Efectivo")
        method_menu = ctk.CTkComboBox(
            content,
            variable=method_var,
            values=["Efectivo", "Tarjeta", "Transferencia", "Cheque", "Otro"],
            width=250,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        method_menu.pack()

        # Separador visual
        ctk.CTkFrame(content, fg_color="#e0e0e0", height=2).pack(fill="x", pady=(15, 8))

        # Mostrar deuda total destacada
        deuda_frame = ctk.CTkFrame(content, fg_color="#f5f5f5", corner_radius=8)
        deuda_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            deuda_frame,
            text="Deuda total del cliente:",
            font=ctk.CTkFont(size=12),
            text_color="#666666"
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            deuda_frame,
            text=f"${total_debt}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#D32F2F"
        ).pack(pady=(0, 8))
        
        def process():
            try:
                val = entry_amount.get().strip()
                if not val:
                    show_warning("Ingrese un monto.")
                    return
                
                amount = string_to_2_dec(val)

                if amount <= Decimal('0.00'):
                    show_warning("El monto debe ser mayor a 0.")
                    return

            except ValueError:
                show_error("Monto inválido. Ingrese solo números.")
                return

            
            if amount > total_debt:
                show_warning(
                    f"El monto ingresado (${amount}) supera la deuda total del cliente (${total_debt})."
                )
                amount = total_debt
                amount_var.set(f"{total_debt}")
                return

            try:
                method = method_var.get()
                result = self.payment_model.apply_global_payment(customer_id, str(amount), method=method)

                # Construir mensaje de resultado
                msg = ("Pago registrado con éxito.")
                
                show_success(msg) 
                win.destroy()
                
                # 1. Actualizar tabla principal
                self.refresh_customer_data()
                self.current_client_id = customer_id
                self.view.select_customer_in_table(customer_id)
                
                # 2. Actualizar ventana de deudas si está abierta
                # Necesitamos volver a pedir los datos actualizados
                debts = self.model.get_customer_debts(customer_id)
                total = self.model.get_total_debt(customer_id)
                credit = norm_to_2_dec(self.payment_model.get_customer_credit(customer_id))
                net = norm_to_2_dec(max(Decimal('0.00'), total - credit))
                self.view.update_debt_window(debts, total, credit, net)

                # 3. Generar comprobante
                if result['used'] > 0:
                    fmt = self.ask_receipt_format()
                    if not fmt:
                        return

                    client_name = "Cliente"
                    for c in self.all_customers:
                        if c[0] == customer_id:
                            client_name = c[1]
                            break

                    sale_items = {}
                    for sale_id, _ in result['updated_debts']:
                        items = self.model.get_sale_items(sale_id)
                        sale_items[sale_id] = items

                    generate_receipts_for_payment(
                        mode="global",
                        format=fmt,
                        client_name=client_name,
                        method=method,
                        amount=amount,
                        customer_id=customer_id,
                        result_data=result,
                        sale_items=sale_items
                    )


            except Exception as e:
                show_error(f"Error al procesar el pago: {e}")

        # Botones
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=(5,15), fill="x", padx=20)

        ctk.CTkButton(
            btn_frame, 
            text="Confirmar Pago",
            fg_color="#009688",
            hover_color="#00796B",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            command=process
        ).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=150,
            height=40,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=win.destroy
        ).pack(side="right", padx=5, expand=True, fill="x")


    def ask_receipt_format(self):
        want_ticket = messagebox.askyesno("Formato", "¿Desea generar ticket (80mm)?")
        want_a4 = messagebox.askyesno("Formato", "¿Desea generar A4 (extendido)?")

        if want_ticket and want_a4:
            return "both"
        if want_ticket:
            return "ticket"
        if want_a4:
            return "a4"
        return None

    def show_account_history(self, cliente_id, cliente_nombre):
        """Muestra el historial completo de cuenta del cliente"""
        try:
            movements, summary = self.model.get_customer_account_history(cliente_id)
            self.view.open_account_history_window(cliente_id, cliente_nombre, movements, summary)
        except Exception as e:
            self.view.show_error(f"Error al obtener historial: {e}")


    def export_account_history_pdf(self, cliente_id, cliente_nombre):
        """Exporta el historial de cuenta a PDF"""
        try:
            movements, summary = self.model.get_customer_account_history(cliente_id)

            cliente_data = self.model.find_customer_by_id(cliente_id)

            cliente_info = {
                "nombre": cliente_data[1] if cliente_data else "-",
                "cuit": cliente_data[2] if cliente_data else "-",    
                "domicilio": cliente_data[3] if cliente_data else "-",
                "telefono": cliente_data[4] if cliente_data else "-",
            }
            # Generar PDF (podés usar la misma lógica de tus otros PDFs)
            from utils.receipts.account_statement import generate_account_statement
            
            filepath = generate_account_statement(
                cliente_info=cliente_info,
                movements=movements,
                summary=summary
            )
            
            self.view.show_success(f"PDF generado: {filepath}")
            
            # Abrir automáticamente
            import os
            try:
                os.startfile(filepath)
            except:
                pass
                
        except Exception as e:
            self.view.show_error(f"Error al exportar PDF: {e}")

    def apply_credit_to_debts(self, customer_id, customer_name):
        """Aplica el saldo a favor del cliente a sus deudas pendientes"""
        try:
            # Obtener crédito disponible
            credit = norm_to_2_dec(self.payment_model.get_customer_credit(customer_id))

            if credit <= Decimal('0.00'):
                self.view.show_warning("El cliente no tiene saldo a favor.")
                return
            
            # Obtener deuda total
            total_debt = norm_to_2_dec(self.model.get_total_debt(customer_id))

            if total_debt <= Decimal('0.00'):
                self.view.show_warning("El cliente no tiene deudas pendientes.")
                return
            
            # Confirmar acción
            amount_to_apply = min(credit, total_debt)
            
            confirm = messagebox.askyesno(
                "Confirmar",
                f"¿Aplicar ${amount_to_apply} del saldo a favor a las deudas pendientes?\n\n"
                f"Saldo a favor disponible: ${credit}\n"
                f"Deuda total: ${total_debt}"
            )
            
            if not confirm:
                return
            
            # 🔹 PASO 1: Descontar TODO el crédito que vamos a intentar usar
            actual_used = self.payment_model.use_customer_credit(
                client_id=customer_id,
                amount=amount_to_apply,
                reason="Aplicando a deudas pendientes"
            )
            
            if actual_used <= 0:
                self.view.show_error("No se pudo usar el crédito disponible.")
                return
            
            # 🔹 PASO 2: Aplicar pagos manualmente
            query = """
                SELECT s.id,
                    COALESCE(SUM(si.quantity * st.price_with_iva), 0) AS total_variable,
                    COALESCE((SELECT SUM(p.amount) FROM payments p WHERE p.sale_id = s.id), 0) AS paid
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                JOIN stock st ON st.id = si.product_id
                WHERE s.cliente_id = ? AND s.estado IN ('pending', 'partial')
                GROUP BY s.id
                HAVING (total_variable - paid) > 0.01
                ORDER BY s.date DESC
            """
            rows = self.payment_model.db.fetch_all(query, (customer_id,))

            remaining = actual_used
            payments_applied = []

            for row in rows:
                if remaining <= Decimal('0.01'):
                    break

                sale_id, total_variable, paid = row
                balance = norm_to_2_dec(norm_to_2_dec(total_variable) - norm_to_2_dec(paid))
                pay_amount = norm_to_2_dec(min(remaining, balance))
                
                if pay_amount > Decimal('0.009'):
                    # Registrar el pago
                    self.payment_model.create_payment(
                        sale_id=sale_id,
                        client_id=customer_id,
                        amount=pay_amount,
                        method="Saldo a Favor",
                        notes="Aplicación de crédito disponible"
                    )
                    
                    # Actualizar estado de la venta
                    self.payment_model.update_sale_status(sale_id, skip_credit_generation=True)
                    
                    remaining = norm_to_2_dec(remaining - pay_amount)
                    payments_applied.append((sale_id, pay_amount))
            
            # 🔹 PASO 3: Si sobra crédito, devolverlo
            if remaining > Decimal('0.01'):
                self.payment_model.add_customer_credit(
                    client_id=customer_id,
                    amount=remaining,
                    reason="Crédito no utilizado (sin deudas suficientes)",
                    sale_id=None
                )
            
            # Calcular cuánto se usó realmente
            credit_used = actual_used - remaining
            
            # Obtener valores actualizados
            new_credit = norm_to_2_dec(self.payment_model.get_customer_credit(customer_id))
            remaining_debt = norm_to_2_dec(self.model.get_total_debt(customer_id))

            
            # Actualizar la UI
            self.refresh_customer_data()
            self.current_client_id = customer_id
            self.view.select_customer_in_table(customer_id)
            
            # Actualizar ventana de deudas
            debts = self.model.get_customer_debts(customer_id)
            net = norm_to_2_dec(max(Decimal('0.00'), remaining_debt - new_credit))       
            self.view.update_debt_window(debts, remaining_debt, new_credit, net)
            
            self.view.show_success(
                f"✅ Se aplicaron ${credit_used:.2f} del saldo a favor.\n"
                f"Deuda restante: ${remaining_debt:.2f}\n"
                f"Saldo a favor restante: ${new_credit:.2f}"
            )
            
        except Exception as e:
            self.view.show_error(f"Error al aplicar saldo a favor: {e}")
        

    def reset_customer_account(self, cliente_id, cliente_nombre, history_window=None):
        """
        Resetea la cuenta corriente del cliente:
        1. Verifica que no tenga deudas
        2. Genera PDF de respaldo
        3. Elimina todas las ventas y pagos
        4. Deja la cuenta limpia
        """
        try:
            # Verificar que no tenga deudas
            total_debt = self.model.get_total_debt(cliente_id)
            credit = norm_to_2_dec(self.payment_model.get_customer_credit(cliente_id))
            net = norm_to_2_dec(max(Decimal('0.00'), total_debt - credit))

            if net > Decimal('0.01'):
                self.view.show_error(
                    f"No se puede resetear la cuenta.\n\n"
                    f"El cliente tiene una deuda pendiente de ${net:.2f}\n"
                    f"Debe saldar la cuenta antes de resetear."
                )
                return
            
            # Confirmar acción
            confirm = messagebox.askyesno(
                "⚠️ Advertencia",
                f"¿Está seguro que desea RESETEAR la cuenta de {cliente_nombre}?\n\n"
                f"Esta acción:\n"
                f"- Generará un PDF de respaldo automáticamente\n"
                f"- Eliminará TODAS las ventas pagadas\n"
                f"- Eliminará TODOS los pagos registrados\n"
                f"- Eliminará el saldo a favor (si existe)\n"
                f"- Dejará la cuenta en CERO\n\n"
                f"⚠️ Esta operación NO se puede deshacer.\n\n"
                f"¿Continuar?"
            )
            
            if not confirm:
                return
            
            # ================================================================
            # PASO 1: GENERAR PDF DE RESPALDO
            # ================================================================
            try:
                movements, summary = self.model.get_customer_account_history(cliente_id)
                
                # Obtener datos del cliente
                cliente_data = self.model.find_customer_by_id(cliente_id)
                cliente_info = {
                    'nombre': cliente_data[1] if cliente_data else cliente_nombre,
                    'cuit': cliente_data[2] if cliente_data else '',
                    'domicilio': cliente_data[3] if cliente_data else '',
                    'telefono': cliente_data[4] if cliente_data else ''
                }
                
                from utils.receipts.account_statement import generate_account_statement
                from datetime import datetime
                import os
                
                # Generar PDF
                filepath = generate_account_statement(
                    cliente_info=cliente_info,
                    movements=movements,
                    summary=summary
                )
                
                # Renombrar para incluir "CIERRE" y timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dir_path = os.path.dirname(filepath)
                filename = os.path.basename(filepath)
                name, ext = os.path.splitext(filename)
                new_filepath = os.path.join(dir_path, f"{name}_CIERRE_{timestamp}{ext}")
                
                if os.path.exists(filepath):
                    os.rename(filepath, new_filepath)
                
                # Abrir automáticamente
                try:
                    os.startfile(new_filepath)
                except:
                    pass
                    
            except Exception as e:
                error_msg = f"Error al generar PDF de respaldo: {e}\n\n¿Desea continuar con el reset de todos modos?"
                if not messagebox.askyesno("Error en PDF", error_msg):
                    return
            
            # ================================================================
            # PASO 2: ELIMINAR VENTAS PAGADAS Y SUS ITEMS
            # ================================================================
            # Primero obtener IDs de ventas a eliminar
            query_get_sales = """
                SELECT id FROM sales 
                WHERE cliente_id = ? 
                AND estado = 'paid'
            """
            sales_to_delete = self.model.db.fetch_all(query_get_sales, (cliente_id,))
            
            # Eliminar sale_items de esas ventas
            for (sale_id,) in sales_to_delete:
                query_delete_items = "DELETE FROM sale_items WHERE sale_id = ?"
                self.model.db.execute_query(query_delete_items, (sale_id,))
            
            # Eliminar las ventas
            query_delete_sales = """
                DELETE FROM sales 
                WHERE cliente_id = ? 
                AND estado = 'paid'
            """
            self.model.db.execute_query(query_delete_sales, (cliente_id,))
            
            # ================================================================
            # PASO 3: ELIMINAR PAGOS
            # ================================================================
            query_delete_payments = """
                DELETE FROM payments 
                WHERE client_id = ?
            """
            self.payment_model.db.execute_query(query_delete_payments, (cliente_id,))
            
            # ================================================================
            # PASO 4: ELIMINAR CRÉDITOS (si existe la tabla)
            # ================================================================
            try:
                query_delete_credits = """
                    DELETE FROM customer_credit 
                    WHERE client_id = ?
                """
                self.payment_model.db.execute_query(query_delete_credits, (cliente_id,))
            except Exception as e:
                print(f"Tabla customer_credit no existe o error: {e}")
            
            # ================================================================
            # PASO 5: ACTUALIZAR UI
            # ================================================================
            
            # Cerrar ventana de historial
            if history_window and history_window.winfo_exists():
                history_window.destroy()
            
            # Cerrar ventana de deudas si está abierta
            if hasattr(self.view, 'debt_window') and self.view.debt_window.winfo_exists():
                self.view.debt_window.destroy()
            
            # Actualizar tabla principal
            self.refresh_customer_data()
            
            # Mostrar mensaje de éxito
            try:
                self.view.show_success(
                    f"✅ Cuenta reseteada exitosamente\n\n"
                    f"• PDF de respaldo generado\n"
                    f"• Ventas pagadas eliminadas\n"
                    f"• Pagos eliminados\n"
                    f"• Cuenta de {cliente_nombre} limpia\n\n"
                    f"Archivo guardado como:\n{os.path.basename(new_filepath)}"
                )
            except:
                self.view.show_success(
                    f"✅ Cuenta reseteada exitosamente\n\n"
                    f"La cuenta de {cliente_nombre} ahora está limpia."
                )
            
        except Exception as e:
            self.view.show_error(f"Error al resetear cuenta: {e}")
            import traceback
            traceback.print_exc()