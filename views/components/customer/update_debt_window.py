import customtkinter as ctk
from tksheet import Sheet
from db.database import Database
from tkinter import messagebox
import datetime
import threading

class UpdateDebtWindow:
    def __init__(self, parent, cliente_id, cliente_nombre):
        self.db = Database()
        self.cliente_id = cliente_id
        self.cliente_nombre = cliente_nombre

        self.product_data = self._fetch_products_with_prices()
        self.product_names = ["Seleccionar producto..."] + list(self.product_data.keys())

        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Pagos de {cliente_nombre}")
        self.window.geometry("1200x700")
        self.window.resizable(True, True)
        self.window.configure(fg_color="white")
    
        self.center_window(parent)
        self.window.focus_set()

        self.create_widgets()
        self.load_data()

        def center_window(self, parent):
            """Centra la ventana inicialmente"""
            self.window.update_idletasks()
            width = 1300
            height = 750
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
            self.window.geometry(f"{width}x{height}+{x}+{y}")

    def center_window(self, parent):
        self.window.update_idletasks()
        width, height = 1200, 700
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.window, corner_radius=12, fg_color="#f8f9fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=4)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        sheet_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10)
        sheet_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=10)

        self.sheet = Sheet(
            sheet_frame,
            headers=["ID", "Fecha", "Concepto", "Monto", "Pagado"],
            height=450,
            width=750,
            show_row_index=False,
            show_top_left=False,
            editable=True,
        )

        # Habilitar bindings básicos
        self.sheet.enable_bindings((
            "single_select",
            "row_select",
            "column_width_resize",
            "arrowkeys",
            "rc_delete_row",
            "copy",
            "cut",
            "paste",
            "edit_cell"
        ))

        self.sheet.readonly_columns([0, 1, 4])

        self.sheet.hide_columns([0])
        self.sheet.pack(fill="both", expand=True, padx=10, pady=10)

       # PANEL DE CONTROLES DERECHO - COMPACTO Y CON TODOS LOS BOTONES
        controls_frame = ctk.CTkFrame(main_frame, fg_color="#f8fafc", corner_radius=12)
        controls_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        
        # Hacer que el frame de controles use todo el espacio vertical
        controls_frame.grid_rowconfigure(8, weight=1)

        # Header del cliente
        header_controls = ctk.CTkFrame(controls_frame, fg_color="#3498db", corner_radius=8, height=45)
        header_controls.pack(fill="x", padx=10, pady=(10, 15))
        header_controls.pack_propagate(False)
        
        ctk.CTkLabel(
            header_controls,
            text=f"👤 {self.cliente_nombre}",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color="white"
        ).pack(expand=True)

        # SECCIÓN 1: PRODUCTOS RÁPIDOS
        product_title = ctk.CTkLabel(
            controls_frame,
            text="🛒 AGREGAR PRODUCTO",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color="#2c3e50"
        )
        product_title.pack(anchor="w", padx=15, pady=(5, 8))

        self.selected_product_var = ctk.StringVar(value=self.product_names[0])
        product_menu = ctk.CTkOptionMenu(
            controls_frame, 
            variable=self.selected_product_var, 
            values=self.product_names, 
            width=180,
            height=32,
            fg_color="white",
            button_color="#3498db",
            button_hover_color="#2980b9",
            text_color="#2c3e50",
            dropdown_fg_color="white",
            dropdown_text_color="#2c3e50"
        )
        product_menu.pack(fill="x", padx=15, pady=(0, 8))

        add_product_btn = ctk.CTkButton(
            controls_frame,
            text="➕ Agregar al Concepto",
            command=self.add_product_to_concept,
            fg_color="#27ae60",
            hover_color="#219652",
            text_color="white",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 11)
        )
        add_product_btn.pack(fill="x", padx=15, pady=(0, 15))

        # Separador
        ctk.CTkFrame(controls_frame, fg_color="#e0e6ed", height=1).pack(fill="x", padx=15, pady=8)

        # SECCIÓN 2: ESTADO DE PAGO
        payment_title = ctk.CTkLabel(
            controls_frame,
            text="💰 ESTADO DE PAGO",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color="#2c3e50"
        )
        payment_title.pack(anchor="w", padx=15, pady=(5, 8))

        paid_btn = ctk.CTkButton(
            controls_frame,
            text="✅ Pagado",
            command=self.mark_as_paid,
            fg_color="#27ae60",
            hover_color="#219652",
            text_color="white",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 11)
        )
        paid_btn.pack(fill="x", padx=15, pady=(0, 6))

        unpaid_btn = ctk.CTkButton(
            controls_frame,
            text="❌ No Pagado",
            command=self.mark_as_unpaid,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            text_color="white",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 11)
        )
        unpaid_btn.pack(fill="x", padx=15, pady=(0, 15))

        # Separador
        ctk.CTkFrame(controls_frame, fg_color="#e0e6ed", height=1).pack(fill="x", padx=15, pady=8)

        # SECCIÓN 3: GESTIÓN DE REGISTROS
        management_title = ctk.CTkLabel(
            controls_frame,
            text="📋 GESTIÓN",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color="#2c3e50"
        )
        management_title.pack(anchor="w", padx=15, pady=(5, 8))

        new_sale_btn = ctk.CTkButton(
            controls_frame,
            text="📄 Nueva Venta",
            command=self.add_new_row,
            fg_color="#3498db",
            hover_color="#2980b9",
            text_color="white",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 11)
        )
        new_sale_btn.pack(fill="x", padx=15, pady=(0, 6))

        save_btn = ctk.CTkButton(
            controls_frame,
            text="💾 Guardar Todo",
            command=self.save_changes,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            text_color="white",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 11, "bold")
        )
        save_btn.pack(fill="x", padx=15, pady=(0, 6))

        delete_btn = ctk.CTkButton(
            controls_frame,
            text="🗑️ Eliminar Fila",
            command=self.delete_selected_row,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            text_color="white",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont("Segoe UI", 11)
        )
        delete_btn.pack(fill="x", padx=15, pady=(0, 15))

        # Separador final
        ctk.CTkFrame(controls_frame, fg_color="#e0e6ed", height=1).pack(fill="x", padx=15, pady=8)

        # SECCIÓN 4: INFORMACIÓN
        info_title = ctk.CTkLabel(
            controls_frame,
            text="💡 AYUDA",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color="#2c3e50"
        )
        info_title.pack(anchor="w", padx=15, pady=(5, 8))

        info_text = ctk.CTkLabel(
            controls_frame,
            text="• Selecciona una fila para gestionarla\n• Usa los botones para cambiar estados\n• Guarda los cambios al finalizar",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#7f8c8d",
            justify="left",
            wraplength=180
        )
        info_text.pack(anchor="w", padx=15, pady=(0, 15))

        # Espacio flexible para empujar todo hacia arriba
        ctk.CTkFrame(controls_frame, fg_color="transparent", height=10).pack(fill="x")

    def mark_as_paid(self):
        """Marca la fila seleccionada como pagada"""
        selected = self.sheet.get_currently_selected()
        if selected:
            row = selected[0]
            self.sheet.set_cell_data(row, 4, "Sí")
        else:
            messagebox.showwarning("Advertencia", "Selecciona una fila primero")

    def mark_as_unpaid(self):
        """Marca la fila seleccionada como no pagada"""
        selected = self.sheet.get_currently_selected()
        if selected:
            row = selected[0]
            self.sheet.set_cell_data(row, 4, "No")
        else:
            messagebox.showwarning("Advertencia", "Selecciona una fila primero")

    def add_new_row(self):
        data = self.sheet.get_sheet_data() or []
        new_row = ["", datetime.date.today().isoformat(), "", 0.0, "No"]
        data.append(new_row)
        self.sheet.set_sheet_data(data, redraw=True)

    def delete_selected_row(self):
        data = self.sheet.get_sheet_data()
        selected_cell = self.sheet.get_currently_selected()
        if selected_cell:
            row_idx = selected_cell[0]
            if row_idx < len(data):
                if messagebox.askyesno("Confirmar", "¿Eliminar esta fila?"):
                    row_data = data[row_idx]
                    if row_data[0]:
                        try:
                            self.delete_from_database(int(row_data[0]))
                        except:
                            pass
                    data.pop(row_idx)
                    self.sheet.set_sheet_data(data, redraw=True)

    def load_data(self):
        rows = self.db.fetch_all(
            "SELECT id, fecha, concepto, monto, pagado FROM pagos_clientes WHERE cliente_id = ? ORDER BY fecha",
            (self.cliente_id,)
        )

        data_to_load = []
        for row in rows:
            id_pago, fecha, concepto, monto, pagado = row
            if not concepto or str(concepto).strip() in ("", "...") or not monto or float(monto) <= 0.0:
                continue
            fecha_display = str(fecha) if fecha else datetime.date.today().isoformat()
            pagado_display = "Sí" if int(pagado) == 1 else "No"
            data_to_load.append([str(id_pago), fecha_display, str(concepto), float(monto), pagado_display])

        if not data_to_load:
            data_to_load = [["", datetime.date.today().isoformat(), "", 0.0, "No"]]

        self.sheet.set_sheet_data(data_to_load, redraw=True)


    def _fetch_products_with_prices(self):
        """Consulta la tabla 'stock' y devuelve un diccionario {'nombre': precio}."""
        print("--- USANDO DATOS DE PRUEBA PARA PRODUCTOS ---") # Un aviso para que no te olvides
        return {
            "Alimento Gati 3kg": 8500.0,
            "Shampoo Antipulgas": 4200.50,
            "Pipeta Power": 3100.0,
            "Inyección Simple": 2500.0,
            "Consulta Veterinaria": 7000.0
        }
        
        # try:
        #     products_tuples = self.db.fetch_all("SELECT name, price FROM stock ORDER BY name ASC")
        #     return {name: price for name, price in products_tuples}
        # except Exception as e:
        #     self.window.after(0, lambda: messagebox.showerror("Error de BD", f"No se pudieron cargar los productos: {e}"))
        #     return {}
        
    def add_product_to_concept(self):
        """Agrega el producto seleccionado del menú al concepto y monto de la fila actual."""
        selected_row_info = self.sheet.get_currently_selected()
        if not selected_row_info:
            messagebox.showwarning("Atención", "Por favor, selecciona una fila en la tabla para agregar el producto.")
            return
        selected_row_index = selected_row_info.row

        product_name = self.selected_product_var.get()
        if "Seleccionar" in product_name:
            return

        product_price = self.product_data.get(product_name, 0.0)
        current_concept = str(self.sheet.get_cell_data(selected_row_index, 2) or "")

        # Añade el producto al texto del concepto
        new_concept = f"{current_concept}, {product_name}" if current_concept else product_name
        self.sheet.set_cell_data(selected_row_index, 2, new_concept)

        # Suma el precio del producto al monto actual
        current_amount = float(self.sheet.get_cell_data(selected_row_index, 3) or 0.0)
        new_amount = current_amount + product_price
        self.sheet.set_cell_data(selected_row_index, 3, round(new_amount, 2))

        self.sheet.redraw() 
        
    
    def clean_database_empty_records(self):
        rows = self.db.fetch_all(
            "SELECT id, concepto, monto FROM pagos_clientes WHERE cliente_id = ?",
            (self.cliente_id,)
        )

        empty_records = [r[0] for r in rows if not r[1] or str(r[1]).strip() in ("", "...") or not r[2] or float(r[2]) == 0.0]
        if not empty_records:
            messagebox.showinfo("Info", "No hay registros vacíos para limpiar")
            return

        if messagebox.askyesno("Confirmar Limpieza", f"Se eliminarán {len(empty_records)} registros vacíos. ¿Continuar?"):
            def cleanup_worker():
                conn = self.db.get_connection()
                cursor = conn.cursor()
                try:
                    for record_id in empty_records:
                        cursor.execute("DELETE FROM pagos_clientes WHERE id = ?", (record_id,))
                    conn.commit()
                    cursor.close()
                    self.window.after(0, lambda: messagebox.showinfo("Éxito", f"Se eliminaron {len(empty_records)} registros vacíos"))
                    self.window.after(100, self.load_data)
                except Exception as e:
                    self.window.after(0, lambda: messagebox.showerror("Error", f"Error limpiando BD: {str(e)}"))
            threading.Thread(target=cleanup_worker, daemon=True).start()

    def delete_from_database(self, pago_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM pagos_clientes WHERE id = ?", (pago_id,))
            conn.commit()
        except Exception as e:
            print(f"Error deleting: {e}")
        finally:
            cursor.close()

    def save_changes(self):
        data = self.sheet.get_sheet_data()
        valid_data = [row for row in data if len(row) >= 5 and row[2] and float(row[3]) > 0.0]
        if not valid_data:
            messagebox.showwarning("Advertencia", "No hay datos válidos para guardar")
            return

        def worker():
            conn = self.db.get_connection()
            cursor = conn.cursor()
            try:
                for row in valid_data:
                    id_pago_str, fecha, concepto, monto, pagado = row
                    id_pago = int(id_pago_str) if id_pago_str and id_pago_str.strip() else None
                    fecha = fecha if fecha else datetime.date.today().isoformat()
                    monto = float(monto)
                    
                    # Validación robusta del campo pagado
                    pagado_str = str(pagado).strip().lower()
                    if pagado_str in ['sí', 'si', 's', '1', 'true', 'verdadero']:
                        pagado_val = 1
                    else:
                        pagado_val = 0

                    if id_pago:
                        cursor.execute("SELECT id FROM pagos_clientes WHERE id = ?", (id_pago,))
                        if cursor.fetchone():
                            cursor.execute(
                                "UPDATE pagos_clientes SET fecha=?, concepto=?, monto=?, pagado=? WHERE id=?",
                                (fecha, concepto, monto, pagado_val, id_pago)
                            )
                    else:
                        cursor.execute(
                            "INSERT INTO pagos_clientes (cliente_id, fecha, concepto, monto, pagado) VALUES (?, ?, ?, ?, ?)",
                            (self.cliente_id, fecha, concepto, monto, pagado_val)
                        )
                conn.commit()
                self.window.after(0, lambda: messagebox.showinfo("Éxito", "Datos guardados correctamente!"))
                self.window.after(100, self.load_data)
            except Exception as e:
                conn.rollback()
                self.window.after(0, lambda: messagebox.showerror("Error", f"Error guardando: {str(e)}"))
            finally:
                cursor.close()

        threading.Thread(target=worker, daemon=True).start()