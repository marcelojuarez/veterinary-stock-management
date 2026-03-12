"""
Vista de Caja Diaria
Muestra ingresos, egresos, gastos y permite cierre de caja
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from utils.utils import iso_to_traditional, traditional_to_iso
from utils.view_helpers import center_window


class CashView:
    def __init__(self, parent, cash_model):
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        self.cash_model = cash_model
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Variables
        self.date_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.ingresos_var = tk.StringVar(value="$0.00")
        self.egresos_var = tk.StringVar(value="$0.00")
        self.saldo_var = tk.StringVar(value="$0.00")
        
        self.create_widgets()
        self.load_data()
    
    # ================================================================== #
    # INTERFAZ                                                            #
    # ================================================================== #
    
    def create_widgets(self):
        """Crear interfaz principal"""
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.create_header()
        self.create_summary_cards()
        self.create_movements_table()
        self.create_buttons()
    
    def create_header(self):
        """Header con selector de fecha"""
        header = ctk.CTkFrame(self.frame, fg_color="#3A3251", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="💰 Caja Diaria",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=15)
        
        # Selector de fecha
        date_frame = ctk.CTkFrame(header, fg_color="transparent")
        date_frame.pack(side="right", padx=20, pady=15)
        
        ctk.CTkLabel(
            date_frame,
            text="Fecha:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=(0, 10))
        
        DateEntry(
            date_frame,
            textvariable=self.date_var,
            width=12,
            background="#3A3251",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy"
        ).pack(side="left", padx=5)
        
        # Botones rápidos
        for text, days in [("Hoy", 0), ("Ayer", -1), ("Ant.Ayer", -2)]:
            ctk.CTkButton(
                date_frame,
                text=text,
                width=70,
                height=28,
                fg_color="#4A4251",
                hover_color="#5A5261",
                command=lambda d=days: self.set_quick_date(d)
            ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            date_frame,
            text="🔍 Consultar",
            width=100,
            height=28,
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.load_data
        ).pack(side="left", padx=10)
    
    def create_summary_cards(self):
        """Tarjetas de resumen"""
        cards_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Card INGRESOS
        income_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=15)
        income_card.grid(row=0, column=0, sticky="ew", padx=10)
        
        ctk.CTkLabel(
            income_card,
            text="💰 INGRESOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 5))
        
        self.income_label = ctk.CTkLabel(
            income_card,
            textvariable=self.ingresos_var,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#4CAF50"
        )
        self.income_label.pack(pady=(0, 5))
        
        self.income_detail = ctk.CTkLabel(
            income_card,
            text="Ventas: $0 | Cobros: $0",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.income_detail.pack(pady=(0, 15))
        
        # Card EGRESOS
        expense_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=15)
        expense_card.grid(row=0, column=1, sticky="ew", padx=10)
        
        ctk.CTkLabel(
            expense_card,
            text="💸 EGRESOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F44336"
        ).pack(pady=(15, 5))
        
        self.expense_label = ctk.CTkLabel(
            expense_card,
            textvariable=self.egresos_var,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#F44336"
        )
        self.expense_label.pack(pady=(0, 5))
        
        self.expense_detail = ctk.CTkLabel(
            expense_card,
            text="Compras: $0 | Gastos: $0",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.expense_detail.pack(pady=(0, 15))
        
        # Card SALDO
        balance_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=15)
        balance_card.grid(row=0, column=2, sticky="ew", padx=10)
        
        ctk.CTkLabel(
            balance_card,
            text="📊 SALDO",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2196F3"
        ).pack(pady=(15, 5))
        
        self.balance_label = ctk.CTkLabel(
            balance_card,
            textvariable=self.saldo_var,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#2196F3"
        )
        self.balance_label.pack(pady=(0, 5))
        
        self.balance_status = ctk.CTkLabel(
            balance_card,
            text="—",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.balance_status.pack(pady=(0, 15))
    
    def create_movements_table(self):
        """Tabla de movimientos"""
        table_frame = ctk.CTkFrame(self.frame, fg_color="white", corner_radius=10)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Título
        ctk.CTkLabel(
            table_frame,
            text="📋 Detalle de Movimientos",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="black"
        ).grid(row=0, column=0, pady=(15, 10), sticky="w", padx=20)
        
        # Tabla
        table_container = tk.Frame(table_frame, bg="white")
        table_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        cols = ("Hora", "Tipo", "Concepto", "Monto")
        
        style = ttk.Style()
        style.configure("Cash.Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Cash.Treeview.Heading", font=("Segoe UI", 11, "bold"))
        
        self.movements_tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="headings",
            style="Cash.Treeview"
        )
        
        # Configurar columnas
        col_widths = [100, 120, 400, 120]
        for col, width in zip(cols, col_widths):
            self.movements_tree.column(col, width=width, anchor="w" if col == "Concepto" else "center")
            self.movements_tree.heading(col, text=col)
        
        # Tags de color
        self.movements_tree.tag_configure("ingreso", background="#E8F5E9", foreground="#2E7D32")
        self.movements_tree.tag_configure("egreso", background="#FFEBEE", foreground="#C62828")
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(table_container, orient="vertical", command=self.movements_tree.yview)
        scroll_x = ttk.Scrollbar(table_container, orient="horizontal", command=self.movements_tree.xview)
        self.movements_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.movements_tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
    
    def create_buttons(self):
        """Botones de acción"""
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        btn_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        ctk.CTkButton(
            btn_frame,
            text="💸 Registrar Gasto",
            width=200,
            height=40,
            fg_color="#FF9800",
            hover_color="#F57C00",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_expense_window
        ).grid(row=0, column=0, padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="📊 Ver Período",
            width=200,
            height=40,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_period_window
        ).grid(row=0, column=1, padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="📄 Cerrar Caja",
            width=200,
            height=40,
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.open_close_cash_window
        ).grid(row=0, column=2, padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Actualizar",
            width=200,
            height=40,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.load_data
        ).grid(row=0, column=3, padx=10)
    
    # ================================================================== #
    # LÓGICA                                                              #
    # ================================================================== #
    
    def set_quick_date(self, days_offset):
        """Establecer fecha rápida"""
        target_date = datetime.now() + timedelta(days=days_offset)
        self.date_var.set(target_date.strftime("%d/%m/%Y"))
        self.load_data()
    
    def load_data(self):
        """Cargar datos de caja"""
        try:
            # Convertir fecha
            self.current_date = traditional_to_iso(self.date_var.get())
            
            # Obtener resumen
            summary = self.cash_model.get_cash_summary(self.current_date)
            
            # Actualizar cards
            self.ingresos_var.set(f"${summary['ingresos']['total']:,.2f}")
            self.egresos_var.set(f"${summary['egresos']['total']:,.2f}")
            self.saldo_var.set(f"${summary['saldo']:,.2f}")
            
            # Actualizar detalles
            self.income_detail.configure(
                text=f"Ventas: ${summary['ingresos']['ventas']:,.2f} | Cobros: ${summary['ingresos']['cobros']:,.2f}"
            )
            self.expense_detail.configure(
                text=f"Pagos Prov: ${summary['egresos']['compras']:,.2f} | Gastos: ${summary['egresos']['gastos']:,.2f}"
            )
            
            # Actualizar color del saldo
            if summary['saldo'] >= 0:
                self.balance_label.configure(text_color="#4CAF50")
                self.balance_status.configure(text="✓ Positivo", text_color="#4CAF50")
            else:
                self.balance_label.configure(text_color="#F44336")
                self.balance_status.configure(text="✗ Negativo", text_color="#F44336")
            
            # Cargar movimientos
            self.load_movements()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")
    
    def load_movements(self):
        """Cargar detalle de movimientos"""
        # Limpiar tabla
        for item in self.movements_tree.get_children():
            self.movements_tree.delete(item)
        
        try:
            movements = self.cash_model.get_movements_detail(self.current_date)
            
            for mov in movements:
                fecha_hora, tipo, concepto, monto, icono = mov
                
                # Formatear hora
                try:
                    dt = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
                    hora = dt.strftime("%H:%M")
                except:
                    hora = "—"
                
                # Formatear monto
                monto_str = f"${abs(monto):,.2f}"
                if monto > 0:
                    monto_str = f"+{monto_str}"
                    tag = "ingreso"
                else:
                    monto_str = f"-{monto_str}"
                    tag = "egreso"
                
                self.movements_tree.insert(
                    "",
                    "end",
                    values=(hora, f"{icono} {tipo}", concepto, monto_str),
                    tags=(tag,)
                )
            
            if not movements:
                self.movements_tree.insert(
                    "",
                    "end",
                    values=("—", "—", "No hay movimientos registrados", "—")
                )
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar movimientos: {e}")
    
    # ================================================================== #
    # VENTANAS                                                            #
    # ================================================================== #
    
    def open_expense_window(self):
        """Abrir ventana para registrar gasto"""
        win = ctk.CTkToplevel(self.frame)
        win.title("Registrar Gasto")
        win.configure(fg_color="#e0e0e0")
        win.transient(self.frame)
        win.grab_set()
        win.withdraw()
        
        # Card
        card = ctk.CTkFrame(win, fg_color="white", corner_radius=20)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            card,
            text="💸 Registrar Gasto",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="black"
        ).pack(pady=(20, 10))
        
        # Formulario
        form = ctk.CTkFrame(card, fg_color="#f9f9f9", corner_radius=10)
        form.pack(pady=10, padx=20, fill="x")
        
        # Variables
        date_var = tk.StringVar(value=iso_to_traditional(self.current_date))
        category_var = tk.StringVar(value="Servicios")
        description_var = tk.StringVar()
        amount_var = tk.StringVar()
        method_var = tk.StringVar(value="Efectivo")
        obs_var = tk.StringVar()
        
        def add_field(row, label, widget):
            ctk.CTkLabel(
                form,
                text=label,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="black"
            ).grid(row=row, column=0, sticky="e", padx=(15, 10), pady=8)
            widget.grid(row=row, column=1, sticky="w", padx=(0, 15), pady=8)
            return widget
        
        add_field(0, "Fecha:", ctk.CTkEntry(form, textvariable=date_var, width=300, state="readonly"))
        
        add_field(1, "Categoría:", ctk.CTkComboBox(
            form, width=300, variable=category_var,
            values=self.cash_model.get_expense_categories(),
            state="readonly"
        ))
        
        desc_entry = add_field(2, "Descripción:", ctk.CTkEntry(
            form, width=300, textvariable=description_var,
            placeholder_text="Ej: Factura luz - Febrero"
        ))
        desc_entry.focus()
        
        add_field(3, "Monto:", ctk.CTkEntry(
            form, width=300, textvariable=amount_var,
            placeholder_text="0.00"
        ))
        
        add_field(4, "Forma de Pago:", ctk.CTkComboBox(
            form, width=300, variable=method_var,
            values=self.cash_model.get_payment_methods(),
            state="readonly"
        ))
        
        add_field(5, "Observaciones:", ctk.CTkEntry(
            form, width=300, textvariable=obs_var,
            placeholder_text="Opcional"
        ))
        
        # Botones
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        def save_expense():
            try:
                # Validar
                if not description_var.get().strip():
                    messagebox.showwarning("Advertencia", "Ingrese una descripción")
                    return
                
                if not amount_var.get().strip():
                    messagebox.showwarning("Advertencia", "Ingrese el monto")
                    return
                
                amount = float(amount_var.get())
                if amount <= 0:
                    messagebox.showwarning("Advertencia", "El monto debe ser mayor a 0")
                    return
                
                # Guardar
                self.cash_model.add_expense(
                    date=traditional_to_iso(date_var.get()),
                    category=category_var.get(),
                    description=description_var.get().strip(),
                    amount=amount,
                    payment_method=method_var.get(),
                    observations=obs_var.get().strip()
                )
                
                messagebox.showinfo("Éxito", "Gasto registrado correctamente")
                win.destroy()
                self.load_data()
                
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Guardar",
            width=150,
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save_expense
        ).grid(row=0, column=0, padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=150,
            height=40,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=win.destroy
        ).grid(row=0, column=1, padx=10)
        
        win.bind("<Return>", lambda e: save_expense())
        
        center_window(win, 520, 520)
        win.deiconify()
    
    def open_period_window(self):
        """Ventana de resumen por período"""
        messagebox.showinfo("Próximamente", "Función de período en desarrollo")
    
    def open_close_cash_window(self):
        """Ventana de cierre de caja"""
        try:
            summary = self.cash_model.get_cash_summary(self.current_date)
            
            win = ctk.CTkToplevel(self.frame)
            win.title("Cierre de Caja")
            win.configure(fg_color="#e0e0e0")
            win.transient(self.frame)
            win.grab_set()
            win.withdraw()
            
            # Card
            card = ctk.CTkFrame(win, fg_color="white", corner_radius=20)
            card.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Título
            ctk.CTkLabel(
                card,
                text=f"📄 Cierre de Caja - {self.date_var.get()}",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="black"
            ).pack(pady=(20, 15))
            
            # Resumen
            summary_frame = ctk.CTkFrame(card, fg_color="#f9f9f9", corner_radius=10)
            summary_frame.pack(padx=20, pady=10, fill="x")
            
            # Ingresos
            ctk.CTkLabel(
                summary_frame,
                text="💰 INGRESOS",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#4CAF50"
            ).pack(pady=(15, 5))
            
            ctk.CTkLabel(
                summary_frame,
                text=f"Ventas: ${summary['ingresos']['ventas']:,.2f}",
                font=ctk.CTkFont(size=12)
            ).pack()
            
            ctk.CTkLabel(
                summary_frame,
                text=f"Cobros: ${summary['ingresos']['cobros']:,.2f}",
                font=ctk.CTkFont(size=12)
            ).pack()
            
            ctk.CTkLabel(
                summary_frame,
                text=f"TOTAL: ${summary['ingresos']['total']:,.2f}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#4CAF50"
            ).pack(pady=(5, 15))
            
            # Egresos
            ctk.CTkLabel(
                summary_frame,
                text="💸 EGRESOS",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F44336"
            ).pack(pady=(5, 5))
            
            ctk.CTkLabel(
                summary_frame,
                text=f"Pagos Proveedores: ${summary['egresos']['compras']:,.2f}",
                font=ctk.CTkFont(size=12)
            ).pack()
            
            ctk.CTkLabel(
                summary_frame,
                text=f"Gastos: ${summary['egresos']['gastos']:,.2f}",
                font=ctk.CTkFont(size=12)
            ).pack()
            
            ctk.CTkLabel(
                summary_frame,
                text=f"TOTAL: ${summary['egresos']['total']:,.2f}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#F44336"
            ).pack(pady=(5, 15))
            
            # Saldo
            saldo_color = "#4CAF50" if summary['saldo'] >= 0 else "#F44336"
            
            ctk.CTkLabel(
                summary_frame,
                text=f"📊 Saldo Final: ${summary['saldo']:,.2f}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=saldo_color
            ).pack(pady=(10, 20))
            
            # Botones
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(pady=15)
            
            ctk.CTkButton(
                btn_frame,
                text="Cerrar",
                width=150,
                height=40,
                fg_color="#757575",
                hover_color="#616161",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=win.destroy
            ).pack()
            
            center_window(win, 450, 550)
            win.deiconify()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar cierre: {e}")