import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime
from utils.utils import format_money, format_percent
from calendar import monthrange

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ReportsView:
    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")
        
        # Variables
        self.mes_var = tk.StringVar()
        self.anio_var = tk.StringVar()
        
        # Configurar grid
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Crear layout
        self.create_header()
        self.create_period_selector()
        self.create_summary_cards()
        self.create_tabs()
        
    # ================================================================
    # HEADER
    # ================================================================
    
    def create_header(self):
        header = ctk.CTkFrame(self.frame, fg_color="#e0e0e0", corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 5))
        
        title = ctk.CTkLabel(
            header,
            text="📊 Reportes de IVA",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#212121"
        )
        title.pack(side="left", padx=15, pady=8)
        
        # Botón de ayuda
        help_btn = ctk.CTkButton(
            header,
            text="❓ Ayuda",
            width=100,
            height=35,
            fg_color="#2196F3",
            hover_color="#1976D2",
            command=self.show_help
        )
        help_btn.pack(side="right", padx=15, pady=5)
    
    # ================================================================
    # SELECTOR DE PERIODO
    # ================================================================
    
    def create_period_selector(self):
        period_frame = ctk.CTkFrame(self.frame, fg_color="#ffffff", corner_radius=10)
        period_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(
            period_frame,
            text="Periodo:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(15, 10), pady=10)
        
        # Mes
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        
        mes_actual = datetime.now().month
        self.mes_var.set(meses[mes_actual - 1])
        
        mes_combo = ctk.CTkComboBox(
            period_frame,
            variable=self.mes_var,
            values=meses,
            width=150,
            height=35,
            state="readonly"
        )
        mes_combo.pack(side="left", padx=5, pady=10)
        
        # Año
        anio_actual = datetime.now().year
        anios = [str(y) for y in range(anio_actual - 5, anio_actual + 2)]
        self.anio_var.set(str(anio_actual))
        
        anio_combo = ctk.CTkComboBox(
            period_frame,
            variable=self.anio_var,
            values=anios,
            width=100,
            height=35,
            state="readonly"
        )
        anio_combo.pack(side="left", padx=5, pady=10)
        
        # Botón consultar
        ctk.CTkButton(
            period_frame,
            text="🔍 Consultar",
            width=130,
            height=35,
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.load_reports
        ).pack(side="left", padx=10, pady=10)
        
        # Botón mes actual
        ctk.CTkButton(
            period_frame,
            text="📅 Mes Actual",
            width=130,
            height=35,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.load_current_month
        ).pack(side="left", padx=5, pady=10)
        
        # Botón exportar
        ctk.CTkButton(
            period_frame,
            text="📄 Exportar PDF",
            width=130,
            height=35,
            fg_color="#FF9800",
            hover_color="#F57C00",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.export_pdf
        ).pack(side="right", padx=15, pady=10)
    
    # ================================================================
    # TARJETAS DE RESUMEN
    # ================================================================
    
    def create_summary_cards(self):
        summary_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        summary_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        summary_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Card IVA Ventas
        self.card_ventas = self.create_card(
            summary_frame, 0,
            "💰 IVA VENTAS",
            "$0.00",
            "Débito Fiscal",
            "#E3F2FD", "#2196F3"
        )
        
        # Card IVA Compras
        self.card_compras = self.create_card(
            summary_frame, 1,
            "🛒 IVA COMPRAS",
            "$0.00",
            "Crédito Fiscal",
            "#E8F5E9", "#4CAF50"
        )
        
        # Card Saldo
        self.card_saldo = self.create_card(
            summary_frame, 2,
            "📊 SALDO",
            "$0.00",
            "A Pagar / A Favor",
            "#FFF3E0", "#FF9800"
        )
    
    def create_card(self, parent, col, title, value, subtitle, bg_color, title_color):
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=12)
        card.grid(row=0, column=col, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=title_color
        ).pack(pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#212121"
        )
        value_label.pack(pady=5)
        
        ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        ).pack(pady=(5, 15))
        
        return value_label
    
    # ================================================================
    # TABS CON TABLAS
    # ================================================================
    
    def create_tabs(self):
        tabs_frame = ctk.CTkFrame(self.frame)
        tabs_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        tabs_frame.grid_rowconfigure(0, weight=1)
        tabs_frame.grid_columnconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(tabs_frame, height=400)
        self.tabview.pack(fill="both", expand=True)
        
        # Tabs
        self.tabview.add("📈 Resumen por Alícuota")
        self.tabview.add("💰 Detalle Ventas")
        self.tabview.add("🛒 Detalle Compras")
        
        # Contenido de cada tab
        self.create_resumen_tab()
        self.create_ventas_tab()
        self.create_compras_tab()
    
    def create_resumen_tab(self):
        tab = self.tabview.tab("📈 Resumen por Alícuota")
        
        # Frame para resumen
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tabla de resumen
        cols = ("Alícuota", "Ventas Neto", "Ventas IVA", "Compras Neto", "Compras IVA", "Saldo IVA")
        self.resumen_table = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        
        col_widths = [100, 120, 120, 120, 120, 120]
        for col, w in zip(cols, col_widths):
            self.resumen_table.column(col, width=w, anchor="center")
            self.resumen_table.heading(col, text=col, anchor="center")
        
        # Scrollbar
        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.resumen_table.yview)
        self.resumen_table.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.resumen_table.pack(fill="both", expand=True)
    
    def create_ventas_tab(self):
        tab = self.tabview.tab("💰 Detalle Ventas")
        
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("Fecha", "Venta #", "Cliente", "CUIT", "Alícuota", "Neto", "IVA", "Total")
        self.ventas_table = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        
        col_widths = [100, 70, 200, 120, 80, 100, 100, 100]
        for col, w in zip(cols, col_widths):
            self.ventas_table.column(col, width=w, anchor="center" if col != "Cliente" else "w")
            self.ventas_table.heading(col, text=col, anchor="center")
        
        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.ventas_table.yview)
        self.ventas_table.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.ventas_table.pack(fill="both", expand=True)
    
    def create_compras_tab(self):
        tab = self.tabview.tab("🛒 Detalle Compras")
        
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        cols = ("Fecha", "Compra #", "Proveedor", "CUIT", "Alícuota", "Neto", "IVA", "Total")
        self.compras_table = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        
        col_widths = [100, 70, 200, 120, 80, 100, 100, 100]
        for col, w in zip(cols, col_widths):
            self.compras_table.column(col, width=w, anchor="center" if col != "Proveedor" else "w")
            self.compras_table.heading(col, text=col, anchor="center")
        
        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=self.compras_table.yview)
        self.compras_table.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.compras_table.pack(fill="both", expand=True)
    
    # ================================================================
    # MÉTODOS DE ACTUALIZACIÓN
    # ================================================================
    
    def update_summary(self, posicion):
        """Actualizar tarjetas de resumen"""
        self.card_ventas.configure(
            text=format_money(posicion.get('iva_ventas'))
        )
        self.card_compras.configure(
            text=format_money(posicion.get('iva_compras'))
        )

        try:
            saldo = float(posicion.get('saldo', 0) or 0)
        except (TypeError, ValueError):
            saldo = 0.0

        saldo_text = format_money(abs(saldo))

        if saldo > 0:
            self.card_saldo.configure(text=saldo_text, text_color="#F44336")
        elif saldo < 0:
            self.card_saldo.configure(text=saldo_text, text_color="#4CAF50")
        else:
            self.card_saldo.configure(text="$0.00", text_color="#666666")

    def update_resumen_table(self, detalle_posicion):
        for item in self.resumen_table.get_children():
            self.resumen_table.delete(item)

        for item in detalle_posicion['detalle']:
            self.resumen_table.insert("", "end", values=(
                item['alicuota'],
                format_money(item.get('ventas_neto')) if 'ventas_neto' in item else "-",
                format_money(item.get('iva_ventas')),
                format_money(item.get('compras_neto')) if 'compras_neto' in item else "-",
                format_money(item.get('iva_compras')),
                format_money(item.get('saldo'))
            ))

        self.resumen_table.insert("", "end", values=(
            "TOTAL",
            "-",
            format_money(detalle_posicion.get('total_iva_ventas')),
            "-",
            format_money(detalle_posicion.get('total_iva_compras')),
            format_money(detalle_posicion.get('saldo_total'))
        ), tags=("total",))

        self.resumen_table.tag_configure(
            "total", background="#E0E0E0", font=("Segoe UI", 10, "bold")
        )

    
    def update_ventas_table(self, ventas):
        
        for item in self.ventas_table.get_children():
            self.ventas_table.delete(item)
        print(ventas)
        for v in ventas:
            print("NETO:", v[6], type(v[6]))
            print("IVA:", v[7], type(v[7]))
            print("TOTAL:", v[8], type(v[8]))

            print(v)
            fecha = v[1][:10] if v[1] and len(v[1]) > 10 else v[1]

            self.ventas_table.insert("", "end", values=(
                fecha,
                v[0],
                v[2],
                v[3],
                format_percent(v[5]),
                format_money(v[6]),
                format_money(v[7]),
                format_money(v[8])
            ))

    def update_compras_table(self, compras):
        for item in self.compras_table.get_children():
            self.compras_table.delete(item)

        for c in compras:
            fecha = c[1][:10] if c[1] and len(c[1]) > 10 else c[1]

            self.compras_table.insert("", "end", values=(
                fecha,
                c[0],
                c[2],
                c[3],
                format_percent(c[4]),
                format_money(c[5]),
                format_money(c[6]),
                format_money(c[7])
            ))

    
    # ================================================================
    # COMANDOS
    # ================================================================
    
    def load_reports(self):
        """Cargar reportes del periodo seleccionado"""
        if self.controller:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes_nombre = self.mes_var.get()
            mes = meses.index(mes_nombre) + 1
            anio = int(self.anio_var.get())
            
            self.controller.load_period_reports(mes, anio)
    
    def load_current_month(self):
        """Cargar reportes del mes actual"""
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        
        self.mes_var.set(meses[mes_actual - 1])
        self.anio_var.set(str(anio_actual))
        
        self.load_reports()
    
    def export_pdf(self):
        """Exportar reporte a PDF"""
        if self.controller:
            self.controller.export_to_pdf()
    
    def show_help(self):
        """Mostrar ventana de ayuda"""
        help_text = """
        📊 REPORTES DE IVA - AYUDA
        
        Este módulo te permite:
        
        1. Ver el IVA cobrado en ventas (Débito Fiscal)
        2. Ver el IVA pagado en compras (Crédito Fiscal)
        3. Calcular el saldo de IVA a pagar o a favor
        
        CÓMO USAR:
        
        • Selecciona el mes y año que quieres consultar
        • Presiona "Consultar" para ver los reportes
        • Usa "Mes Actual" para ver el periodo en curso
        
        TABS:
        
        • Resumen: Muestra totales por alícuota de IVA
        • Detalle Ventas: Lista todas las ventas del periodo
        • Detalle Compras: Lista todas las compras del periodo
        
        IMPORTANTE:
        
        El sistema calcula automáticamente:
        - IVA Ventas = Lo que cobraste a tus clientes
        - IVA Compras = Lo que pagaste a tus proveedores
        - Saldo = IVA Ventas - IVA Compras
        
        Si el saldo es POSITIVO: Debes pagar a AFIP
        Si el saldo es NEGATIVO: Tienes saldo a favor
        """
        
        messagebox.showinfo("Ayuda - Reportes de IVA", help_text)
    
    # ================================================================
    # ATTACH CONTROLLER
    # ================================================================
    
    def attach_controller(self, controller):
        self.controller = controller
    
    # ================================================================
    # UTILIDADES
    # ================================================================
    
    def show_error(self, msg):
        messagebox.showerror("Error", msg)
    
    def show_success(self, msg):
        messagebox.showinfo("Éxito", msg)
    
    def show_warning(self, msg):
        messagebox.showwarning("Advertencia", msg)