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
            headers=["ID", "Fecha", "Concepto", "Monto", "Pagado"],
            height=400,
            width=550,
            show_row_index=False,
            show_top_left=False,
            editable=False,
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
        ))

        self.sheet.readonly_columns([0, 4])

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

        # Botones para marcar/desmarcar pagado rápidamente
        button_frame = ctk.CTkFrame(info_frame, fg_color="white")
        button_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="✅ Marcar como Pagado",
            command=self.mark_as_paid,
            fg_color="#3498db",
            hover_color="#3498db",
            text_color="white",
            height=35
        ).pack(fill="x", pady=(0, 5))

        ctk.CTkButton(
            button_frame,
            text="❌ Marcar como No Pagado",
            command=self.mark_as_unpaid,
            fg_color="#3498db",
            hover_color="#3498db",
            text_color="white",
            height=35
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            info_frame,
            text="💾 Guardar cambios",
            command=self.save_changes,
            fg_color="#3498db",
            hover_color="#3498db",
            text_color="white",
            corner_radius=8,
            height=40
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            info_frame,
            text="➕ Agregar nueva venta",
            command=self.add_new_row,
            fg_color="#3498db",
            hover_color="#3498db",
            text_color="white",
            corner_radius=8,
            height=40
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            info_frame,
            text="🗑️ Eliminar fila seleccionada",
            command=self.delete_selected_row,
            fg_color="#3498db",
            hover_color="#3498db",
            text_color="white",
            corner_radius=8,
            height=40
        ).pack(fill="x", padx=20, pady=(0, 10))


        ctk.CTkLabel(
            info_frame,
            text="💡 Usa los botones ✅/❌ para marcar pagos\n💡",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#6c757d",
            justify="left"
        ).pack(fill="x", padx=20, pady=(20, 0))

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