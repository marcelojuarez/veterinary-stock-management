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

        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Pagos de {cliente_nombre}")
        self.window.geometry("800x500")
        self.window.resizable(True, True)
        self.window.configure(fg_color="white")
        self.window.transient(parent)
        self.center_window(parent)

        try:
            self.window.grab_set()
        except:
            pass
        self.window.focus_set()

        self.create_widgets()
        self.load_data()

    def center_window(self, parent):
        self.window.update_idletasks()
        width, height = 800, 500
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.window, corner_radius=12, fg_color="#f8f9fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        sheet_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=8)
        sheet_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)

        self.sheet = Sheet(
            sheet_frame,
            headers=["ID", "Fecha", "Concepto", "Monto", "Pagado (Sí/No)"],
            height=400,
            width=550,
            show_row_index=False,
            show_top_left=False,
            editable=True
        )

        self.sheet.enable_bindings((
            "single_select",          
            "row_select",            
            "column_width_resize",     
            "arrowkeys",               
            "edit_cell",               
            "rc_delete_row",           
            "copy",                   
            "cut",                     
            "paste",               
        ))

        self.sheet.set_options(
            auto_resize_default_row_index=False,
            drag_selection=False,     
            row_drag_and_drop=False,   
            enable_rc_menu=True,       
            selection_mode="Cell",
            select_mode="Cell",        
            expand_sheet_if_paste_too_big=True,
            paste_insert_column_limit=10,
            paste_insert_row_limit=100,
            edit_cell_auto_select=True,
        )

        self.sheet.hide_columns([0])
        self.sheet.pack(fill="both", expand=True)

        # Info cliente y botones
        info_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=8)
        info_frame.grid(row=0, column=1, sticky="nsew", pady=10)

        ctk.CTkLabel(
            info_frame,
            text=f"Cliente:\n{self.cliente_nombre}",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color="#2c3e50"
        ).pack(pady=20)

        ctk.CTkButton(
            info_frame,
            text="💾 Guardar cambios",
            command=self.save_changes,
            fg_color="#198754",
            hover_color="#157347",
            text_color="white",
            corner_radius=8,
            height=40
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            info_frame,
            text="➕ Agregar nueva venta",
            command=self.add_new_row,
            fg_color="#0d6efd",
            hover_color="#0b5ed7",
            text_color="white",
            corner_radius=8,
            height=40
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            info_frame,
            text="🗑️ Eliminar fila seleccionada",
            command=self.delete_selected_row,
            fg_color="#dc3545",
            hover_color="#c82333",
            text_color="white",
            corner_radius=8,
            height=40
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            info_frame,
            text="🧹 Limpiar BD vacíos",
            command=self.clean_database_empty_records,
            fg_color="#ffc107",
            hover_color="#e0a800",
            text_color="black",
            corner_radius=8,
            height=35
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text="💡 Click en número de fila para seleccionar\n💡 Click derecho para eliminar\n💡 Edita directamente en celdas",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#6c757d",
            justify="left"
        ).pack(fill="x", padx=20, pady=(20, 0))

    def add_new_row(self):
        try:
            data = self.sheet.get_sheet_data() or []
            new_row = ["", datetime.date.today().isoformat(), "", 0.0, "No"]  # Siempre "No" por defecto
            data.append(new_row)
            self.sheet.set_sheet_data(data, redraw=True)
            messagebox.showinfo("Éxito", "Nueva fila agregada")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

    def delete_selected_row(self):
        try:
            # Método manual: buscar la primera fila con datos seleccionados
            data = self.sheet.get_sheet_data()
            selected_cell = self.sheet.get_currently_selected()
            
            if selected_cell:
                row_idx = selected_cell[0]
                if row_idx is not None and row_idx < len(data):
                    if messagebox.askyesno("Confirmar", "¿Eliminar esta fila?"):
                        # Eliminar de BD si tiene ID
                        row_data = data[row_idx]
                        if row_data[0] and str(row_data[0]).strip():
                            try:
                                pago_id = int(row_data[0])
                                self.delete_from_database(pago_id)
                            except ValueError:
                                pass
                        
                        # Eliminar de la lista y actualizar
                        data.pop(row_idx)
                        self.sheet.set_sheet_data(data, redraw=True)
                        messagebox.showinfo("Éxito", "Fila eliminada")
                else:
                    messagebox.showinfo("Info", "Selecciona una fila")
            else:
                messagebox.showinfo("Info", "Selecciona una fila haciendo click en ella")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

    def load_data(self):
        """Cargar datos desde la base de datos, filtrando registros vacíos"""
        try:
            rows = self.db.fetch_all(
                "SELECT id, fecha, concepto, monto, pagado FROM pagos_clientes WHERE cliente_id = ? ORDER BY fecha",
                (self.cliente_id,)
            )
            
            valid_rows = []
            for row in rows:
                id_pago, fecha, concepto, monto, pagado = row
                
                
                is_valid = (
                    concepto and str(concepto).strip() != "" and 
                    str(concepto).strip() != "..." and  
                    monto and float(monto) > 0.0        
                )
                
                if is_valid:
                    valid_rows.append(row)
                    print(f"✅ Registro válido: ID {id_pago} - '{concepto}' - ${monto} - Pagado: {pagado}")

           
            self.sheet.set_sheet_data([], redraw=False)
            
            data_to_load = []
            
            if valid_rows:
                
                for row in valid_rows:
                    id_pago, fecha, concepto, monto, pagado = row
                    
                    if pagado == 1:
                        pagado_display = "Sí" 
                    else:
                        pagado_display = "No" 
                    
                    data_to_load.append([
                        str(id_pago),
                        str(fecha) if fecha else datetime.date.today().isoformat(),
                        str(concepto),
                        float(monto),
                        pagado_display
                    ])
            
            
            if data_to_load:
                self.sheet.set_sheet_data(data_to_load, redraw=True)
                print(f"✅ Cargados {len(data_to_load)} registros válidos")
            else:
                self.sheet.set_sheet_data([["", datetime.date.today().isoformat(), "", 0.0, "No"]], redraw=True)
                print("✅ No hay registros válidos, mostrando fila vacía")
                
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.sheet.set_sheet_data([["", datetime.date.today().isoformat(), "", 0.0, "No"]])

    def clean_database_empty_records(self):
        """Limpiar registros vacíos de la base de datos"""
        try:
            rows = self.db.fetch_all(
                "SELECT id, concepto, monto FROM pagos_clientes WHERE cliente_id = ?",
                (self.cliente_id,)
            )
            
            empty_records = []
            for row in rows:
                id_pago, concepto, monto = row
                is_empty = (
                    not concepto or 
                    str(concepto).strip() == "" or 
                    str(concepto).strip() == "..." or
                    not monto or 
                    float(monto) == 0.0
                )
                
                if is_empty:
                    empty_records.append(id_pago)
                    print(f"🗑️ Registro vacío encontrado: ID {id_pago}")
            
            if not empty_records:
                messagebox.showinfo("Info", "No hay registros vacíos para limpiar")
                return
            
            confirm = messagebox.askyesno(
                "Confirmar Limpieza", 
                f"Se eliminarán {len(empty_records)} registros vacíos. ¿Continuar?"
            )
            
            if confirm:
                def cleanup_worker():
                    conn = self.db.get_connection()
                    cursor = conn.cursor()
                    try:
                        for record_id in empty_records:
                            cursor.execute("DELETE FROM pagos_clientes WHERE id = ?", (record_id,))
                        
                        conn.commit()
                        cursor.close()
                        
                        self.window.after(0, lambda: messagebox.showinfo(
                            "Éxito", 
                            f"Se eliminaron {len(empty_records)} registros vacíos"
                        ))
                
                        self.window.after(100, self.load_data)
                        
                    except Exception as e:
                        self.window.after(0, lambda: messagebox.showerror(
                            "Error", 
                            f"Error limpiando BD: {str(e)}"
                        ))
                
                threading.Thread(target=cleanup_worker, daemon=True).start()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error analizando BD: {str(e)}")

    

    def delete_from_database(self, pago_id):
        """Eliminar registro de la base de datos"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pagos_clientes WHERE id = ?", (pago_id,))
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Error deleting from database: {e}")

    def save_changes(self):
        """Guardar solo datos válidos"""
        try:
            data = self.sheet.get_sheet_data()
            if not data:
                messagebox.showwarning("Advertencia", "No hay datos para guardar")
                return

            valid_data = []
            for row in data:
                if len(row) >= 5:
                    id_pago_str, fecha, concepto, monto, pagado = row
                    is_valid = (
                        concepto and str(concepto).strip() != "" and
                        monto and float(monto) > 0.0
                    )
                    if is_valid:
                        valid_data.append(row)

            if not valid_data:
                messagebox.showwarning("Advertencia", "No hay datos válidos para guardar (concepto y monto requeridos)")
                return

            def worker():
                conn = self.db.get_connection()
                cursor = conn.cursor()
                try:
                    for row in valid_data:
                        id_pago_str, fecha, concepto, monto, pagado = row
                        id_pago = int(id_pago_str) if id_pago_str and id_pago_str.strip() else None

                        if not fecha or not fecha.strip():
                            fecha = datetime.date.today().isoformat()
                        
                        monto = float(monto) if monto else 0.0
                        
                        pagado_texto = str(pagado).strip().lower()
                        
                        variaciones_si = ["si", "sí", "sí", "si", "1", "true", "verdadero", "yes", "y"]
                        
                        
                        if pagado_texto in variaciones_si:
                            pagado_val = 1
                            print(f"✅ Convertido '{pagado}' → 1 (Sí)")
                        else:
                            
                            pagado_val = 0
                            print(f"✅ Convertido '{pagado}' → 0 (No)")

                        if id_pago:
                            cursor.execute("SELECT id FROM pagos_clientes WHERE id = ?", (id_pago,))
                            if cursor.fetchone():
                                cursor.execute(
                                    "UPDATE pagos_clientes SET fecha=?, concepto=?, monto=?, pagado=? WHERE id=?",
                                    (fecha, concepto, monto, pagado_val, id_pago)  # ✅ Guardar como 0/1
                                )
                                print(f"📝 Actualizado ID {id_pago} - Pagado: {pagado_val}")
                        else:
                            cursor.execute(
                                "INSERT INTO pagos_clientes (cliente_id, fecha, concepto, monto, pagado) VALUES (?, ?, ?, ?, ?)",
                                (self.cliente_id, fecha, concepto, monto, pagado_val)  # ✅ Guardar como 0/1
                            )
                            nuevo_id = cursor.lastrowid
                            print(f"✅ Nuevo registro ID {nuevo_id} - Pagado: {pagado_val}")
                    
                    conn.commit()
                    self.window.after(0, lambda: messagebox.showinfo("Éxito", "Datos guardados correctamente!"))
                    self.window.after(100, self.load_data)  # Recargar para normalizar textos
                    
                except Exception as e:
                    conn.rollback()
                    self.window.after(0, lambda: messagebox.showerror("Error", f"Error guardando: {str(e)}"))
                finally:
                    cursor.close()

            threading.Thread(target=worker, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando datos: {str(e)}")