from models.customer import CustomerModel
from models.payment_model import PaymentModel
from tkinter import messagebox
import re
import customtkinter as ctk
from datetime import datetime
import os

from utils.receipts.pdf_generator import generate_payment_receipt, generate_global_payment_receipt
from utils.receipts.ticket_pos import generate_payment_ticket, generate_global_payment_ticket
from utils.receipts.manager import generate_receipts_for_payment
from utils.receipts.account_statement import generate_account_statement
from utils.receipts.paths import a4_pago_global


class CustomerController: 
    def __init__(self, view):
        self.view = view
        self.model = CustomerModel()
        self.payment_model = PaymentModel()
        self.all_customers = []  
        self.load_customers()  

    def load_customers(self):
        """Carga inicial de clientes en memoria"""
        try:
            self.all_customers = self.model.get_all_customers()
            self.view.refresh_customer_table(self.all_customers)
        except Exception as e:
            self.view.show_error(f"Error al cargar clientes: {e}")

    def refresh_customer_data(self):
        """Recargar desde DB (solo cuando hay cambios)"""
        try:
            self.all_customers = self.model.get_all_customers()
            self.view.refresh_customer_table(self.all_customers)
        except Exception as e:
            self.view.show_error(f"Error al refrescar datos: {e}")


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
            self.view.show_error(f"Error en los datos: {str(e)}")
            return False
        except Exception as e:
            self.view.show_error(f"Error al registrar el cliente: {str(e)}")
            return False

    def delete_customer(self, customer_id):
        """Elimina un cliente por su ID"""
        confirm = messagebox.askyesno("Confirmar", "¿Desea eliminar este cliente?")
        if not confirm:
            return False

        try:
            self.model.delete_customer(customer_id)
            self.refresh_customer_data()
            self.view.show_success("Cliente eliminado correctamente.")
            return True
        except Exception as e:
            self.view.show_error(f"Error al eliminar el cliente: {str(e)}")
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
            # customer estructura: (id, nombre, cuit, domicilio, telefono)
            if (query in str(customer[0]).lower() or        # ID
                query in customer[1].lower() or             # Nombre
                query in customer[2].lower() or             # CUIT
                query in customer[3].lower() or             # Domicilio
                query in customer[4].lower()):              # Teléfono
                filtered.append(customer)
        
        self.view.refresh_customer_table(filtered)

    
    def clear_form(self):
        """Limpiar formulario de la vista"""
        self.view.name_var.set("")
        self.view.cuit_var.set("")
        self.view.home_var.set("")
        self.view.phone_var.set("")

    def __validate_customer_data(self, data):
        # Validar campos obligatorios 
        required_fields = ['nombre', 'cuit', 'domicilio', 'telefono']
        for field in required_fields:
            if not data[field]:
                self.view.show_warning(f'Por favor complete el campo {field}.')
                return False 
        return True

    def __validate_supplier_cuit(self, cuit_field):
        pattern = r'^\d{2}-\d{8}-\d$'
        
        if not re.fullmatch(pattern, cuit_field):
            self.view.show_warning("Por favor coloque el CUIT correctamente. Formato: XX-XXXXXXXX-X")
            return False
        
        return True
    
    def __validate_supplier_phone(self, phone_field):
        pattern = r'^\+?\d{7,15}$'
        
        if not re.fullmatch(pattern, phone_field):
            self.view.show_warning("Por favor coloque el teléfono correctamente. Debe contener entre 7 y 15 dígitos, puede incluir un '+' al inicio.")
            return False
        
        return True
    
    # --------------------------------------------------------------------
    # 💳 DEUDAS DE CLIENTES
    # --------------------------------------------------------------------

    def show_customer_debts(self, cliente_id, cliente_nombre):
        """Abre ventana con las deudas del cliente"""
        try:
            self.current_client_id = cliente_id

            changes = self.reconcile_and_detect_changes(cliente_id)

            debts = self.model.get_customer_debts(cliente_id)
            total = self.model.get_total_debt(cliente_id)
            credit = round(self.payment_model.get_customer_credit(cliente_id), 2)

            net = round(max(0.0, total - credit), 2)
            self.view.open_debt_window(cliente_id, cliente_nombre, debts, total, credit, net)

            if changes:
                self.view.show_warning(
                f"⚠️ Se detectaron cambios de precio en {len(changes)} venta(s):\n\n" +
                "\n".join(changes)
                )
        except Exception as e:
            self.view.show_error(f"Error al obtener las deudas: {e}")

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
                sobrepago = round(paid - total_final, 2)
                
                if sobrepago > 0.01:
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
            self.view.show_error(f"Error al obtener los productos de la venta: {e}")

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
                self.view.show_error(f"Error al obtener las deudas del cliente: {e}")

    def register_payment(self, sale_id, client_id, amount, method, window):
        try:
            # 1) Estado ANTES (para saldo previo)
            before = self.payment_model.get_sale_balance(sale_id)

            # 2) Registrar pago
            self.payment_model.create_payment(
                sale_id=sale_id,
                client_id=client_id,
                amount=amount,
                method=method,
                notes="Payment through UI"
            )

            # 3) Actualizar estado y congelar si queda paid
            status = self.payment_model.update_sale_status(sale_id,skip_credit_generation=True)

            self.payment_model.reconcile_sale(sale_id)

            # 4) Estado DESPUÉS (para saldo restante / total)
            after = self.payment_model.get_sale_balance(sale_id)

            # 5) Actualizar UI de deudas
            debts = self.model.get_customer_debts(client_id)
            total = self.model.get_total_debt(client_id)
            credit = round(self.payment_model.get_customer_credit(client_id), 2)
            net = round(max(0.0, total - credit), 2)
            self.view.update_debt_window(debts, total, credit, net)

            window.destroy()
            self.view.show_success("Pago registrado con éxito.")

            # 6) Comprobante (siempre que el usuario quiera)
            fmt = self.ask_receipt_format()
            if not fmt:
                return

            client_name = self.model.find_customer_by_id(client_id)[1]
            sale_items = self.model.get_sale_items(sale_id)

            generate_receipts_for_payment(
                mode="sale",
                format=fmt,
                client_name=client_name,
                method=method,
                amount=amount,
                sale_id=int(sale_id),
                sale_info=after,
                payments=self.payment_model.get_payments_for_sale(sale_id),
                sale_items=sale_items
            )

        except Exception as e:
            self.view.show_error(f"Error: {e}")


    def open_global_payment_window(self):
        customer_id = self.view.get_selected_customer_id()
        if not customer_id:
            self.view.show_warning("Selecciona un cliente primero.")
            return

        total_debt = round(float(self.model.get_total_debt(customer_id)), 2)

        if total_debt == 0:
            self.view.show_warning("El cliente no tiene deudas pendientes")
            return
        
        # Crear ventana modal con estilo
        win = ctk.CTkToplevel(self.view.frame)
        win.title("Pago Global a Cuenta")
        win.geometry("450x400")
        win.transient(self.view.frame)
        win.grab_set()

        # Centrar
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f'{width}x{height}+{x}+{y}')

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

        def process():
            try:
                val = entry_amount.get().strip()
                if not val:
                    self.view.show_warning("Ingrese un monto.")
                    return
                
                amount = round(float(val), 2)

                if amount <= 0:
                    self.view.show_warning("El monto debe ser mayor a 0.")
                    return

            except ValueError:
                self.view.show_error("Monto inválido. Ingrese solo números.")
                return

            
            if amount > total_debt:
                self.view.show_warning(
                    f"El monto ingresado (${amount:.2f}) supera la deuda total del cliente (${total_debt:.2f})."
                )
                amount = total_debt
                amount_var.set(f"{total_debt:.2f}")
                return

            try:
                result = self.payment_model.apply_global_payment(customer_id, amount)

                # Construir mensaje de resultado
                msg = ("Pago registrado con éxito.")
                
                self.view.show_success(msg) 
                win.destroy()
                
                # 1. Actualizar tabla principal
                self.refresh_customer_data()
                self.current_client_id = customer_id
                self.view.select_customer_in_table(customer_id)
                
                # 2. Actualizar ventana de deudas si está abierta
                # Necesitamos volver a pedir los datos actualizados
                debts = self.model.get_customer_debts(customer_id)
                total = self.model.get_total_debt(customer_id)
                credit = round(self.payment_model.get_customer_credit(customer_id), 2)
                net = round(max(0.0, total - credit), 2)
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
                        method="Global",
                        amount=amount,
                        customer_id=customer_id,
                        result_data=result,
                        sale_items=sale_items
                    )


            except Exception as e:
                self.view.show_error(f"Error al procesar el pago: {e}")

        # Botones
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)

        ctk.CTkButton(
            btn_frame, 
            text="Confirmar Pago",
            fg_color="#009688",
            hover_color="#00796B",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            command=process
        ).pack(side="right", padx=5, expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=150,
            height=40,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=win.destroy
        ).pack(side="left", padx=5, expand=True, fill="x")


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
            movements = self.model.get_customer_account_history(cliente_id)
            summary = self.model.get_customer_account_summary(cliente_id)
            self.view.open_account_history_window(cliente_id, cliente_nombre, movements, summary)
        except Exception as e:
            self.view.show_error(f"Error al obtener historial: {e}")


    def export_account_history_pdf(self, cliente_id, cliente_nombre):
        """Exporta el historial de cuenta a PDF"""
        try:
            movements = self.model.get_customer_account_history(cliente_id)
            summary = self.model.get_customer_account_summary(cliente_id)
            
            # Generar PDF (podés usar la misma lógica de tus otros PDFs)
            from utils.receipts.account_statement import generate_account_statement
            
            filepath = generate_account_statement(
                cliente_nombre=cliente_nombre,
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
            credit = round(self.payment_model.get_customer_credit(customer_id), 2)
            
            if credit <= 0:
                self.view.show_warning("El cliente no tiene saldo a favor.")
                return
            
            # Obtener deuda total
            total_debt = round(float(self.model.get_total_debt(customer_id)), 2)
            
            if total_debt <= 0:
                self.view.show_warning("El cliente no tiene deudas pendientes.")
                return
            
            # Confirmar acción
            amount_to_apply = min(credit, total_debt)
            
            confirm = messagebox.askyesno(
                "Confirmar",
                f"¿Aplicar ${amount_to_apply:.2f} del saldo a favor a las deudas pendientes?\n\n"
                f"Saldo a favor disponible: ${credit:.2f}\n"
                f"Deuda total: ${total_debt:.2f}"
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
                if remaining <= 0.01:
                    break

                sale_id, total_variable, paid = row
                balance = round(float(total_variable) - float(paid), 2)
                pay_amount = round(min(remaining, balance), 2)
                
                if pay_amount > 0.01:
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
                    
                    remaining = round(remaining - pay_amount, 2)
                    payments_applied.append((sale_id, pay_amount))
            
            # 🔹 PASO 3: Si sobra crédito, devolverlo
            if remaining > 0.01:
                self.payment_model.add_customer_credit(
                    client_id=customer_id,
                    amount=remaining,
                    reason="Crédito no utilizado (sin deudas suficientes)",
                    sale_id=None
                )
            
            # Calcular cuánto se usó realmente
            credit_used = actual_used - remaining
            
            # Obtener valores actualizados
            new_credit = round(self.payment_model.get_customer_credit(customer_id), 2)
            remaining_debt = round(float(self.model.get_total_debt(customer_id)), 2)

            
            # Actualizar la UI
            self.refresh_customer_data()
            self.current_client_id = customer_id
            self.view.select_customer_in_table(customer_id)
            
            # Actualizar ventana de deudas
            debts = self.model.get_customer_debts(customer_id)
            net = round(max(0.0, remaining_debt - new_credit), 2)
            self.view.update_debt_window(debts, remaining_debt, new_credit, net)
            
            self.view.show_success(
                f"✅ Se aplicaron ${credit_used:.2f} del saldo a favor.\n"
                f"Deuda restante: ${remaining_debt:.2f}\n"
                f"Saldo a favor restante: ${new_credit:.2f}"
            )
            
        except Exception as e:
            self.view.show_error(f"Error al aplicar saldo a favor: {e}")