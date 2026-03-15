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
        header = ctk.CTkFrame(self.frame)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="💰 Caja Diaria",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

        # Selector de fecha
        date_frame = ctk.CTkFrame(header, fg_color="transparent")
        date_frame.grid(row=0, column=2, padx=15, pady=8)

        ctk.CTkLabel(
            date_frame,
            text="Fecha:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 6))

        DateEntry(
            date_frame,
            textvariable=self.date_var,
            width=12,
            background="#3A3251",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy"
        ).pack(side="left", padx=5)

        for text, days in [("Hoy", 0), ("Ayer", -1), ("Ant.Ayer", -2)]:
            ctk.CTkButton(
                date_frame, text=text, width=70, height=28,
                fg_color="#4A4251", hover_color="#5A5261",
                command=lambda d=days: self.set_quick_date(d)
            ).pack(side="left", padx=2)

        ctk.CTkButton(
            date_frame, text="🔍 Consultar", width=100, height=28,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.load_data
        ).pack(side="left", padx=10)

    def create_summary_cards(self):
        cards_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)  # ← 4 columnas
        
        # Agregar variables
        self.saldo_inicial_var = tk.StringVar(value="$0.00")
        self.saldo_final_var = tk.StringVar(value="$0.00")
        
        specs = [
            ("opening", "🏦 SALDO INICIAL", "#607D8B", "#ECEFF1", self.saldo_inicial_var, "—"),
            ("income",  "💰 INGRESOS", "#2E7D32", "#E8F5E9", self.ingresos_var, "Ventas: $0 | Cobros: $0"),
            ("expense", "💸 EGRESOS",  "#C62828", "#FFEBEE", self.egresos_var,  "Compras: $0 | Gastos: $0"),
            ("balance", "📊 SALDO FINAL",    "#1565C0", "#E3F2FD", self.saldo_final_var,    "—"),
        ]

        for col, (key, label, fg, bg, var, detail_text) in enumerate(specs):
            card = ctk.CTkFrame(cards_frame, fg_color=bg, corner_radius=10)
            card.grid(row=0, column=col, padx=6, sticky="ew")

            ctk.CTkLabel(card, text=label,
                        font=ctk.CTkFont(size=11), text_color="#555").pack(pady=(8, 2))

            val_lbl = ctk.CTkLabel(card, textvariable=var,
                                font=ctk.CTkFont(size=16, weight="bold"),
                                text_color=fg)
            val_lbl.pack()

            detail_lbl = ctk.CTkLabel(card, text=detail_text,
                                    font=ctk.CTkFont(size=11), text_color="#666")
            detail_lbl.pack(pady=(2, 8))

            if key == "opening":
                self.opening_label = val_lbl
                self.opening_detail = detail_lbl
            elif key == "income":
                self.income_label  = val_lbl
                self.income_detail = detail_lbl
            elif key == "expense":
                self.expense_label  = val_lbl
                self.expense_detail = detail_lbl
            elif key == "balance":
                self.balance_label  = val_lbl
                self.balance_status = detail_lbl
    
    def create_movements_table(self):
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(table_frame, text="📋 Detalle de Movimientos",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Cash.Treeview",
                        background="#f9f9f9", fieldbackground="#f9f9f9",
                        rowheight=22, font=("Segoe UI", 8))
        style.configure("Cash.Treeview.Heading",
                        background="#e6e6e6", foreground="#000",
                        font=("Segoe UI", 9, "bold"))
        style.map("Cash.Treeview.Heading", background=[("active", "#dcdcdc")])

        cols = ("Hora", "Tipo", "Concepto", "Monto")
        self.movements_tree = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            height=14, style="Cash.Treeview"
        )
        col_widths = {"Hora": 100, "Tipo": 120, "Concepto": 400, "Monto": 120}
        for col in cols:
            self.movements_tree.column(col, width=col_widths[col],
                                    anchor="w" if col == "Concepto" else "center")
            self.movements_tree.heading(col, text=col, anchor="center")

        self.movements_tree.tag_configure("ingreso", background="#E8F5E9")
        self.movements_tree.tag_configure("egreso",  background="#FFEBEE")
        self.movements_tree.tag_configure("fiada",   background="#F5F5F5", foreground="#9E9E9E")

        sy = ttk.Scrollbar(table_frame, orient="vertical",   command=self.movements_tree.yview)
        sx = ttk.Scrollbar(table_frame, orient="horizontal", command=self.movements_tree.xview)
        self.movements_tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sx.pack(side="bottom", fill="x")
        sy.pack(side="right",  fill="y")
        self.movements_tree.pack(fill="both", expand=True, padx=(10, 0))
    
    def create_buttons(self):
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=12)
        btn_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)  # ← 4 columnas
    
        buttons = [
            ("🏦 Abrir caja",      self.open_cash_opening_window, "#4CAF50", "#45a049"),
            ("💸 Registrar gasto", self.open_expense_window,       "#FF9800", "#F57C00"),
            ("📄 Cerrar caja",     self.open_close_cash_window,    "#F44336", "#D32F2F"),
            ("🔄 Actualizar",      self.load_data,                 "#009688", "#00796B"),
        ]
        
        for col, (text, cmd, fg, hover) in enumerate(buttons):
            ctk.CTkButton(
                btn_frame, text=text, width=180, height=38,
                fg_color=fg, hover_color=hover,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=cmd
            ).grid(row=0, column=col, padx=4)
    
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
            self.saldo_inicial_var.set(f"${summary['saldo_inicial']:,.2f}")
            self.ingresos_var.set(f"${summary['ingresos']['total']:,.2f}")
            self.egresos_var.set(f"${summary['egresos']['total']:,.2f}")
            self.saldo_final_var.set(f"${summary['saldo_final']:,.2f}")

            if summary['caja_cerrada']:
                self.opening_detail.configure(text="Caja cerrada", text_color="#F44336")
            elif summary['caja_abierta']:
                self.opening_detail.configure(text="Caja abierta", text_color="#4CAF50")
            else:
                self.opening_detail.configure(text="Sin abrir", text_color="#FF9800")
            
            # Actualizar detalles
            self.income_detail.configure(
                text=f"Ventas: ${summary['ingresos']['ventas']:,.2f} | Cobros: ${summary['ingresos']['cobros']:,.2f}"
            )
            self.expense_detail.configure(
                text=f"Pagos Prov: ${summary['egresos']['compras']:,.2f} | Gastos: ${summary['egresos']['gastos']:,.2f}"
            )
            
            # Actualizar color y texto del saldo final
            saldo_final = summary['saldo_final']
            if saldo_final >= 0:
                self.balance_label.configure(text_color="#4CAF50")
                self.balance_status.configure(
                    text=f"Movimientos: ${summary['saldo_movimientos']:,.2f}",
                    text_color="#4CAF50"
                )
            else:
                self.balance_label.configure(text_color="#F44336")
                self.balance_status.configure(
                    text=f"Movimientos: ${summary['saldo_movimientos']:,.2f}",
                    text_color="#F44336"
                )
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
                fecha_hora, tipo, concepto, monto = mov
                
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
                    values=(hora, f"{tipo}", concepto, monto_str),
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

    def open_cash_opening_window(self):
        """Ventana para abrir caja"""
        # Verificar si ya está abierta
        if self.cash_model.is_cash_open(self.current_date):
            messagebox.showwarning(
                "Advertencia",
                f"La caja para {self.date_var.get()} ya está abierta"
            )
            return
        
        if self.cash_model.is_cash_closed(self.current_date):
            messagebox.showwarning(
                "Advertencia",
                f"La caja para {self.date_var.get()} ya está cerrada"
            )
            return
        
        win = ctk.CTkToplevel(self.frame)
        win.title("Abrir Caja")
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
            text=f"🏦 Abrir Caja - {self.date_var.get()}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="black"
        ).pack(pady=(20, 10))
        
        # Info
        ctk.CTkLabel(
            card,
            text="Ingrese el saldo inicial en efectivo",
            font=ctk.CTkFont(size=12),
            text_color="#666"
        ).pack(pady=(0, 20))
        
        # Form
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=30, pady=10, fill="x")
        
        # Variables
        amount_var = tk.StringVar()
        notes_var = tk.StringVar()
        
        def add_field(row, label_text, widget):
            ctk.CTkLabel(
                form, text=label_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w", text_color="black"
            ).grid(row=row, column=0, sticky="w", pady=8)
            widget.grid(row=row, column=1, sticky="ew", pady=8)
            return widget
        
        amount_entry = add_field(0, "Saldo Inicial:", ctk.CTkEntry(
            form, width=300, textvariable=amount_var,
            placeholder_text="0.00", font=ctk.CTkFont(size=14)
        ))
        amount_entry.focus()
        
        add_field(1, "Observaciones:", ctk.CTkEntry(
            form, width=300, textvariable=notes_var,
            placeholder_text="Opcional"
        ))
        
        form.grid_columnconfigure(1, weight=1)
        
        # Botones
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_opening():
            try:
                if not amount_var.get().strip():
                    messagebox.showwarning("Advertencia", "Ingrese el saldo inicial")
                    return
                
                amount = float(amount_var.get())
                if amount < 0:
                    messagebox.showwarning("Advertencia", "El saldo no puede ser negativo")
                    return
                
                # Abrir caja
                self.cash_model.open_cash(
                    date=self.current_date,
                    opening_amount=amount,
                    notes=notes_var.get().strip()
                )
                
                messagebox.showinfo("Éxito", "Caja abierta correctamente")
                win.destroy()
                self.load_data()
                
            except ValueError:
                messagebox.showerror("Error", "El monto debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", f"Error al abrir caja: {e}")
        
        ctk.CTkButton(
            btn_frame,
            text="🏦 Abrir Caja",
            width=150,
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save_opening
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
        
        win.bind("<Return>", lambda e: save_opening())
        
        from utils.view_helpers import center_window
        center_window(win, 500, 350)
        win.deiconify()
    
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
    

    def open_close_cash_window(self):
        """Ventana de cierre de caja con arqueo"""
        try:
            # Verificar que esté abierta
            if not self.cash_model.is_cash_open(self.current_date):
                if self.cash_model.is_cash_closed(self.current_date):
                    messagebox.showwarning(
                        "Advertencia",
                        "La caja ya está cerrada para esta fecha"
                    )
                else:
                    messagebox.showwarning(
                        "Advertencia",
                        "Debe abrir la caja antes de cerrarla"
                    )
                return
            
            summary = self.cash_model.get_cash_summary(self.current_date)
            opening = self.cash_model.get_cash_opening(self.current_date)
            
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
            
            # SALDO INICIAL
            ctk.CTkLabel(
                summary_frame,
                text="🏦 SALDO INICIAL",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#607D8B"
            ).pack(pady=(15, 5))
            
            ctk.CTkLabel(
                summary_frame,
                text=f"${summary['saldo_inicial']:,.2f}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#607D8B"
            ).pack(pady=(0, 10))
            
            # INGRESOS
            ctk.CTkLabel(
                summary_frame,
                text="💰 INGRESOS DEL DÍA",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#4CAF50"
            ).pack(pady=(5, 5))
            
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
            ).pack(pady=(5, 10))
            
            # EGRESOS
            ctk.CTkLabel(
                summary_frame,
                text="💸 EGRESOS DEL DÍA",
                font=ctk.CTkFont(size=13, weight="bold"),
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
            ).pack(pady=(5, 10))
            
            # SALDO ESPERADO
            expected = summary['saldo_final']
            
            ctk.CTkLabel(
                summary_frame,
                text=f"📊 SALDO ESPERADO",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#1565C0"
            ).pack(pady=(10, 5))
            
            expected_label = ctk.CTkLabel(
                summary_frame,
                text=f"${expected:,.2f}",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#1565C0"
            )
            expected_label.pack(pady=(0, 15))
            
            # ARQUEO - Input saldo real
            ctk.CTkLabel(
                card,
                text="💵 Arqueo de Caja",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="black"
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                card,
                text="Ingrese el efectivo real contado:",
                font=ctk.CTkFont(size=12),
                text_color="#666"
            ).pack()
            
            actual_var = tk.StringVar()
            notes_var = tk.StringVar()
            difference_var = tk.StringVar(value="$0.00")
            
            entry_frame = ctk.CTkFrame(card, fg_color="transparent")
            entry_frame.pack(pady=10)
            
            actual_entry = ctk.CTkEntry(
                entry_frame,
                width=200,
                height=40,
                textvariable=actual_var,
                placeholder_text="0.00",
                font=ctk.CTkFont(size=16),
                justify="center"
            )
            actual_entry.pack()
            actual_entry.focus()
            
            # Diferencia
            diff_frame = ctk.CTkFrame(card, fg_color="#FFF9C4", corner_radius=10)
            diff_frame.pack(padx=20, pady=10, fill="x")
            
            ctk.CTkLabel(
                diff_frame,
                text="📊 Diferencia:",
                font=ctk.CTkFont(size=13),
                text_color="#666"
            ).pack(pady=(10, 0))
            
            diff_label = ctk.CTkLabel(
                diff_frame,
                textvariable=difference_var,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#F57C00"
            )
            diff_label.pack(pady=(0, 10))
            
            # Calcular diferencia automáticamente
            def calculate_difference(*args):
                try:
                    if actual_var.get().strip():
                        actual = float(actual_var.get())
                        diff = actual - float(expected)
                        difference_var.set(f"${diff:,.2f}")
                        
                        if diff == 0:
                            diff_label.configure(text_color="#4CAF50")
                            diff_frame.configure(fg_color="#E8F5E9")
                        elif diff > 0:
                            diff_label.configure(text_color="#2196F3")
                            diff_frame.configure(fg_color="#E3F2FD")
                        else:
                            diff_label.configure(text_color="#F44336")
                            diff_frame.configure(fg_color="#FFEBEE")
                    else:
                        difference_var.set("$0.00")
                        diff_label.configure(text_color="#F57C00")
                        diff_frame.configure(fg_color="#FFF9C4")
                except ValueError:
                    difference_var.set("Inválido")
                    diff_label.configure(text_color="#F44336")
            
            actual_var.trace('w', calculate_difference)
            
            # Observaciones
            ctk.CTkLabel(
                card,
                text="Observaciones:",
                font=ctk.CTkFont(size=12),
                text_color="#666"
            ).pack(pady=(10, 5))
            
            ctk.CTkEntry(
                card,
                width=400,
                textvariable=notes_var,
                placeholder_text="Opcional: Explique diferencias si las hay"
            ).pack(pady=(0, 10))
            
            # Botones
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(pady=15)
            
            def close_cash():
                try:
                    if not actual_var.get().strip():
                        messagebox.showwarning("Advertencia", "Ingrese el saldo real")
                        return
                    
                    actual = float(actual_var.get())
                    if actual < 0:
                        messagebox.showwarning("Advertencia", "El saldo no puede ser negativo")
                        return
                    
                    # Confirmar si hay diferencia
                    diff = actual - float(expected)
                    if abs(diff) > 0.01:
                        msg = f"Hay una diferencia de ${diff:,.2f}\n\n¿Desea continuar con el cierre?"
                        if not messagebox.askyesno("Confirmar", msg):
                            return
                    
                    # Cerrar caja
                    result = self.cash_model.close_cash(
                        date=self.current_date,
                        closing_amount=actual,
                        notes=notes_var.get().strip()
                    )
                    
                    messagebox.showinfo(
                        "Éxito",
                        f"Caja cerrada correctamente\n\n"
                        f"Esperado: ${result['expected_closing']:,.2f}\n"
                        f"Real: ${result['actual_closing']:,.2f}\n"
                        f"Diferencia: ${result['difference']:,.2f}"
                    )
                    
                    win.destroy()
                    self.load_data()
                    
                except ValueError:
                    messagebox.showerror("Error", "El monto debe ser un número válido")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cerrar caja: {e}")
            
            ctk.CTkButton(
                btn_frame,
                text="✅ Cerrar Caja",
                width=150,
                height=40,
                fg_color="#4CAF50",
                hover_color="#45a049",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=close_cash
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
            
            win.bind("<Return>", lambda e: close_cash())
            
            from utils.view_helpers import center_window
            center_window(win, 500, 950)
            win.deiconify()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar cierre: {e}")