import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime
from utils.utils import format_currency, format_money, format_percent
from calendar import monthrange

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ReportsView:
    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ctk.CTkFrame(parent, fg_color="#f0f0f0")

        # Variables
        self.month_var = tk.StringVar()
        self.year_var  = tk.StringVar()

        # Configure main grid
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Build layout
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

        ctk.CTkLabel(
            header,
            text="📊 Reportes Fiscales",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#212121"
        ).pack(side="left", padx=15, pady=8)

        ctk.CTkButton(
            header,
            text="❓ Ayuda",
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=100,
            height=35,
            fg_color="#2196F3",
            hover_color="#1976D2",
            command=self.show_help
        ).pack(side="right", padx=15, pady=5)

    # ================================================================
    # PERIOD SELECTOR
    # ================================================================

    def create_period_selector(self):
        period_frame = ctk.CTkFrame(self.frame, fg_color="#ffffff", corner_radius=10)
        period_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(
            period_frame,
            text="Periodo:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(15, 10), pady=10)

        months = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
        ]
        
        current_month = datetime.now().month
        self.month_var.set(months[current_month - 1])

        ctk.CTkComboBox(
            period_frame,
            variable=self.month_var,
            values=months,
            width=150,
            height=35,
            state="readonly"
        ).pack(side="left", padx=5, pady=10)

        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 5, current_year + 2)]
        self.year_var.set(str(current_year))

        ctk.CTkComboBox(
            period_frame,
            variable=self.month_var,
            values=months,
            width=150,
            height=35,
            state="readonly",
            button_color="#009688",
            button_hover_color="#00796B",
            border_color="#cccccc",
            fg_color="white",
            text_color="#212121"
        ).pack(side="left", padx=5, pady=10)

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

        ctk.CTkButton(
            period_frame,
            text="📅 Mes actual",
            width=130,
            height=35,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.load_current_month
        ).pack(side="left", padx=5, pady=10)

        ctk.CTkButton(
            period_frame,
            text="📄 Exportar PDF",
            text_color="#ffffff",
            width=130,
            height=35,
            fg_color="#FF9800",
            hover_color="#F57C00",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.export_pdf
        ).pack(side="right", padx=15, pady=10)

    # ================================================================
    # SUMMARY CARDS - TWO ROWS
    # ================================================================

    def create_summary_cards(self):
        summary_outer = ctk.CTkFrame(self.frame, fg_color="transparent")
        summary_outer.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
        summary_outer.grid_columnconfigure(0, weight=1)

        # --- Row 1: IVA ---
        iva_label = ctk.CTkLabel(
            summary_outer,
            text="IVA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#757575"
        )
        iva_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 2))

        iva_row = ctk.CTkFrame(summary_outer, fg_color="transparent")
        iva_row.grid(row=1, column=0, sticky="ew")
        iva_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_iva_sales = self._make_card(
            iva_row, 0,
            "💰 IVA VENTAS", "$0.00", "Débito Fiscal",
            "#E3F2FD", "#1565C0"
        )
        self.card_purchases_iva = self._make_card(
            iva_row, 1,
            "🛒 IVA COMPRAS", "$0.00", "Crédito Fiscal",
            "#E8F5E9", "#2E7D32"
        )
        self.card_iva_balance = self._make_card(
            iva_row, 2,
            "📊 SALDO IVA", "$0.00", "A Pagar / A Favor",
            "#FFF3E0", "#E65100"
        )

        # Separator
        sep = ctk.CTkFrame(summary_outer, fg_color="#e0e0e0", height=1)
        sep.grid(row=2, column=0, sticky="ew", pady=(8, 2))

        # --- Row 2: Perceptions and Retentions ---
        others_label = ctk.CTkLabel(
            summary_outer,
            text="PERCEPCIONES Y RETENCIONES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#757575"
        )
        others_label.grid(row=3, column=0, sticky="w", padx=5, pady=(2, 2))

        others_row = ctk.CTkFrame(summary_outer, fg_color="transparent")
        others_row.grid(row=4, column=0, sticky="ew", pady=(0, 5))
        others_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_per_suffered = self._make_card(
            others_row, 0,
            "📋 PERC. SUFRIDAS", "$0.00", "En compras",
            "#F3E5F5", "#6A1B9A"
        )
        self.card_per_made = self._make_card(
            others_row, 1,
            "📋 PERC. EFECTUADAS", "$0.00", "En ventas",
            "#EDE7F6", "#4527A0"
        )
        self.card_ret_suffered = self._make_card(
            others_row, 2,
            "🏦 RET. SUFRIDAS", "$0.00", "IVA + IIBB",
            "#FCE4EC", "#880E4F"
        )
        self.card_ret_made = self._make_card(
            others_row, 3,
            "🏦 RET. EFECTUADAS", "$0.00", "En compras",
            "#FFF8E1", "#F57F17"
        )

    def _make_card(self, parent, col, title, value, subtitle, bg_color, title_color):
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=12)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=title_color
        ).pack(pady=(12, 3))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#212121"
        )
        value_label.pack(pady=3)

        ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(size=10),
            text_color="#757575"
        ).pack(pady=(3, 12))

        return value_label

    # ================================================================
    # TABS
    # ================================================================

    def create_tabs(self):
        tabs_frame = ctk.CTkFrame(self.frame)
        tabs_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(5, 10))
        tabs_frame.grid_rowconfigure(0, weight=1)
        tabs_frame.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(tabs_frame, height=380)
        self.tabview.pack(fill="both", expand=True)

        self.tabview.add("📈 Resumen IVA")
        self.tabview.add("💰 Detalle Ventas")
        self.tabview.add("🛒 Detalle Compras")
        self.tabview.add("📋 Percepciones")
        self.tabview.add("🏦 Retenciones")

        self._create_summary_tab()
        self._create_sales_tab()
        self._create_purchases_tab()
        self._create_perceptions_tab()
        self._create_retentions_tab()

    # ---- Tab: IVA Summary ----

    def _create_summary_tab(self):
        tab = self.tabview.tab("📈 Resumen IVA")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Alícuota", "Ventas Neto", "Ventas IVA", "Compras Neto", "Compras IVA", "Saldo Bruto", "Saldo Neto")
        self.summary_table = self._make_treeview(frame, cols, [90, 120, 110, 120, 110, 105, 105], height=12)

    # ---- Tab: Sales Detail ----

    def _create_sales_tab(self):
        tab = self.tabview.tab("💰 Detalle Ventas")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Fecha", "Venta #", "Cliente", "CUIT", "Alícuota", "Neto", "IVA", "Total")
        anchors = {"Cliente": "w"}
        self.sales_table = self._make_treeview(frame, cols, [100, 70, 200, 130, 80, 110, 110, 110], height=15, custom_anchors=anchors)

    # ---- Tab: Purchases Detail ----

    def _create_purchases_tab(self):
        tab = self.tabview.tab("🛒 Detalle Compras")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Fecha", "Compra #", "Proveedor", "CUIT", "Alícuota", "Neto", "IVA", "Total")
        anchors = {"Proveedor": "w"}
        self.purchases_table = self._make_treeview(frame, cols, [100, 70, 200, 130, 80, 110, 110, 110], height=15, custom_anchors=anchors)

    # ---- Tab: Perceptions ----

    def _create_perceptions_tab(self):
        tab = self.tabview.tab("📋 Percepciones")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sub-tabs
        self.perc_subtabs = ctk.CTkTabview(frame, height=330)
        self.perc_subtabs.pack(fill="both", expand=True)
        self.perc_subtabs.add("📥 Sufridas (Compras)")
        self.perc_subtabs.add("📤 Efectuadas (Ventas)")

        # Sufridas: percepciones que me cobran en facturas de proveedor
        sub_suffered = self.perc_subtabs.tab("📥 Sufridas (Compras)")
        f1 = ctk.CTkFrame(sub_suffered, fg_color="transparent")
        f1.pack(fill="both", expand=True)
        cols_s = ("Fecha", "Factura #", "Proveedor", "CUIT", "Tipo", "Monto")
        anchors_s = {"Proveedor": "w"}
        self.perc_suffered_table = self._make_treeview(
            f1, cols_s, [110, 100, 220, 140, 120, 120], height=12, custom_anchors=anchors_s
        )

        # Efectuadas: percepciones que cobramos nosotros en ventas
        sub_made = self.perc_subtabs.tab("📤 Efectuadas (Ventas)")
        f2 = ctk.CTkFrame(sub_made, fg_color="transparent")
        f2.pack(fill="both", expand=True)
        cols_e = ("Fecha", "Venta #", "Cliente", "CUIT", "Tipo", "Monto")
        anchors_e = {"Cliente": "w"}
        self.perc_made_table = self._make_treeview(
            f2, cols_e, [110, 100, 220, 140, 120, 120], height=12, custom_anchors=anchors_e
        )

    # ---- Tab: Retentions ----

    def _create_retentions_tab(self):
        tab = self.tabview.tab("🏦 Retenciones")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sub-tabs
        self.ret_subtabs = ctk.CTkTabview(frame, height=330)
        self.ret_subtabs.pack(fill="both", expand=True)
        self.ret_subtabs.add("📥 Sufridas (Ventas)")
        self.ret_subtabs.add("📤 Efectuadas (Compras)")

        # Sufridas: retenciones que el cliente nos hace en ventas
        sub_suffered = self.ret_subtabs.tab("📥 Sufridas (Ventas)")
        f1 = ctk.CTkFrame(sub_suffered, fg_color="transparent")
        f1.pack(fill="both", expand=True)
        cols_s = ("Fecha", "Venta #", "Cliente", "CUIT", "Tipo", "Certificado", "Monto")
        anchors_s = {"Cliente": "w"}
        self.ret_suffered_table = self._make_treeview(
            f1, cols_s, [110, 80, 200, 130, 80, 120, 110], height=12, custom_anchors=anchors_s
        )

        # Efectuadas: retenciones que nosotros hacemos al proveedor en compras
        sub_made = self.ret_subtabs.tab("📤 Efectuadas (Compras)")
        f2 = ctk.CTkFrame(sub_made, fg_color="transparent")
        f2.pack(fill="both", expand=True)
        cols_e = ("Fecha", "Compra #", "Proveedor", "CUIT", "Tipo", "Certificado", "Monto")
        anchors_e = {"Proveedor": "w"}
        self.ret_made_table = self._make_treeview(
            f2, cols_e, [110, 80, 200, 130, 80, 120, 110], height=12, custom_anchors=anchors_e
        )

    # ---- Helper Treeview ----

    def _make_treeview(self, parent, cols, widths, height=12, custom_anchors=None):
        container = tk.Frame(parent, bg="#f0f0f0")
        container.pack(fill="both", expand=True)

        tree = ttk.Treeview(container, columns=cols, show="headings", height=height)
        custom_anchors = custom_anchors or {}

        for col, w in zip(cols, widths):
            anchor = custom_anchors.get(col, "center")
            tree.column(col, width=w, anchor=anchor)
            tree.heading(col, text=col, anchor="center")

        scroll_y = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        return tree

    # ================================================================
    # UPDATE CARDS
    # ================================================================

    def update_summary(self, position):
        """
        Updates the IVA summary cards.
        position = result of IVAModel.get_iva_position()
        """
        self.card_iva_sales.configure(text=format_currency(position.get('iva_sales', 0)))
        self.card_purchases_iva.configure(text=format_currency(position.get('purchases_iva', 0)))

        try:
            balance = float(position.get('balance', 0) or 0)  # FIX: was 'balance' (key now consistent with model)
        except (TypeError, ValueError):
            balance = 0.0

        balance_text = format_currency(abs(balance))
        if balance > 0:
            self.card_iva_balance.configure(text=balance_text, text_color="#F44336")
        elif balance < 0:
            self.card_iva_balance.configure(text=balance_text, text_color="#4CAF50")
        else:
            self.card_iva_balance.configure(text="$0.00", text_color="#666666")

    def update_other_summary(self, totals):
        """
        Updates the perceptions and retentions cards.
        totals = {
            'per_suffered': float,
            'per_made':     float,
            'ret_suffered': float,
            'ret_made':     float
        }
        """
        self.card_per_suffered.configure(text=format_currency(totals.get('per_suffered', 0)))
        self.card_per_made.configure(text=format_currency(totals.get('per_made', 0)))
        self.card_ret_suffered.configure(text=format_currency(totals.get('ret_suffered', 0)))
        self.card_ret_made.configure(text=format_currency(totals.get('ret_made', 0)))

    # ================================================================
    # UPDATE IVA TABLES
    # ================================================================

    def update_summary_table(self, position_detail):
        for item in self.summary_table.get_children():
            self.summary_table.delete(item)

        for item in position_detail['rows']:
            self.summary_table.insert("", "end", values=(
                item['aliquot'],
                format_currency(item.get('sales_net', 0)),
                format_currency(item.get('iva_sales', 0)),
                format_currency(item.get('purchases_net', 0)),
                format_currency(item.get('purchases_iva', 0)),
                format_currency(item.get('balance', 0)),   # gross balance per aliquot
                "—"                                     # net only shown in TOTAL row
            ))

        # Gross subtotal row
        self.summary_table.insert("", "end", values=(
            "Subtotal", "—",
            format_currency(position_detail.get('total_iva_sales', 0)),
            "—",
            format_currency(position_detail.get('total_purchases_iva', 0)),
            format_currency(position_detail.get('balance_gross', 0)),  # FIX: was 'balance_bruto'
            "—"
        ), tags=("subtotal",))

        # Adjustment rows if applicable
        ret_iva = position_detail.get('ret_iva', 0)
        per_iva = position_detail.get('per_iva', 0)
        if ret_iva:
            self.summary_table.insert("", "end", values=(
                "Ret. IVA sufridas", "—", f"-{format_currency(ret_iva)}",
                "—", "—", "—", "—"
            ), tags=("adjustment",))
        if per_iva:
            self.summary_table.insert("", "end", values=(
                "Perc. IVA sufridas", "—", "—",
                "—", f"+{format_currency(per_iva)}", "—", "—"
            ), tags=("adjustment",))

        # TOTAL NET row
        self.summary_table.insert("", "end", values=(
            "TOTAL",
            "—",
            format_currency(position_detail.get('fiscal_debt', position_detail.get('total_iva_sales', 0))),
            "—",
            format_currency(position_detail.get('fiscal_credit', position_detail.get('total_purchases_iva', 0))),
            format_currency(position_detail.get('balance_gross', 0)),   # FIX: was 'balance_bruto'
            format_currency(position_detail.get('balance_total', 0))    # FIX: was 'balance_total' (now consistent)
        ), tags=("total",))

        self.summary_table.tag_configure("total",      background="#E0E0E0", font=("Segoe UI", 10, "bold"))
        self.summary_table.tag_configure("subtotal",   background="#F5F5F5", font=("Segoe UI", 9, "bold"))
        self.summary_table.tag_configure("adjustment", background="#FFF9C4", font=("Segoe UI", 9, "italic"))

    def update_sales_table(self, sales):
        for item in self.sales_table.get_children():
            self.sales_table.delete(item)

        for v in sales:
            date = v[1][:10] if v[1] and len(v[1]) > 10 else v[1]
            self.sales_table.insert("", "end", values=(
                date, v[0], v[2], v[3],
                format_percent(v[5]),
                format_currency(v[6]),
                format_currency(v[7]),
                format_currency(v[8])
            ))

    def update_purchases_table(self, purchases):
        for item in self.purchases_table.get_children():
            self.purchases_table.delete(item)

        for c in purchases:
            date = c[1][:10] if c[1] and len(c[1]) > 10 else c[1]
            self.purchases_table.insert("", "end", values=(
                date, c[0], c[2], c[3],
                format_percent(c[4]),
                format_currency(c[5]),
                format_currency(c[6]),
                format_currency(c[7])
            ))

    # ================================================================
    # UPDATE PERCEPTIONS TABLES
    # ================================================================

    def update_suffered_percep_table(self, perceptions):
        """
        perceptions: list of tuples from DB
        Expected columns:
          (date, invoice_id, supplier, cuit, tax_type, amount)
        """
        for item in self.perc_suffered_table.get_children():
            self.perc_suffered_table.delete(item)

        total = 0.0
        for p in perceptions:
            date   = p[0][:10] if p[0] and len(p[0]) > 10 else p[0]
            amount = float(p[5] or 0)
            total += amount
            self.perc_suffered_table.insert("", "end", values=(
                date, p[1], p[2], p[3], p[4], format_currency(amount)
            ))

        if perceptions:
            self.perc_suffered_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", format_currency(total)
            ), tags=("total",))
            self.perc_suffered_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    def update_made_percep_table(self, perceptions):
        """
        perceptions: list of tuples
        Expected columns:
          (date, sale_id, customer, cuit, tax_type, amount)
        """
        for item in self.perc_made_table.get_children():
            self.perc_made_table.delete(item)

        total = 0.0
        for p in perceptions:
            date   = p[0][:10] if p[0] and len(p[0]) > 10 else p[0]
            amount = float(p[5] or 0)
            total += amount
            self.perc_made_table.insert("", "end", values=(
                date, p[1], p[2], p[3], p[4], format_currency(amount)
            ))

        if perceptions:
            self.perc_made_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", format_currency(total)
            ), tags=("total",))
            self.perc_made_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    # ================================================================
    # UPDATE RETENTIONS TABLES
    # ================================================================

    def update_suffered_ret_table(self, retentions):
        """
        retentions: list of tuples from DB (sale_retentions)
        Expected columns:
          (date, sale_id, customer, cuit, tax_type, certificate_number, amount)
        """
        for item in self.ret_suffered_table.get_children():
            self.ret_suffered_table.delete(item)

        total = 0.0
        for r in retentions:
            date   = r[0][:10] if r[0] and len(r[0]) > 10 else r[0]
            amount = float(r[6] or 0)
            total += amount
            self.ret_suffered_table.insert("", "end", values=(
                date, r[1], r[2], r[3], r[4], r[5] or "-", format_currency(amount)
            ))

        if retentions:
            self.ret_suffered_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", "", format_currency(total)
            ), tags=("total",))
            self.ret_suffered_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    def update_made_ret_table(self, retentions):
        """
        retentions: list of tuples (retentions we apply to the supplier)
        Expected columns:
          (date, purchase_id, supplier, cuit, tax_type, certificate_number, amount)
        """
        for item in self.ret_made_table.get_children():
            self.ret_made_table.delete(item)

        total = 0.0
        for r in retentions:
            date   = r[0][:10] if r[0] and len(r[0]) > 10 else r[0]
            amount = float(r[6] or 0)
            total += amount
            self.ret_made_table.insert("", "end", values=(
                date, r[1], r[2], r[3], r[4], r[5] or "-", format_currency(amount)
            ))

        if retentions:
            self.ret_made_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", "", format_currency(total)
            ), tags=("total",))
            self.ret_made_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    # ================================================================
    # COMMANDS
    # ================================================================

    def load_reports(self):
        if self.controller:
            months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            month = months.index(self.month_var.get()) + 1
            year  = int(self.year_var.get())
            self.controller.load_period_reports(month, year)

    def load_current_month(self):
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_var.set(months[datetime.now().month - 1])
        self.year_var.set(str(datetime.now().year))
        self.load_reports()

    def export_pdf(self):
        if self.controller:
            self.controller.export_to_pdf()

    def show_help(self):
        help_text = """
📊 REPORTES FISCALES - AYUDA

═══ IVA ═══
• IVA Ventas: Débito Fiscal (lo que cobraste a clientes)
• IVA Compras: Crédito Fiscal (lo que pagaste a proveedores)
• Saldo IVA: Débito - Crédito
  → Rojo = A pagar a AFIP
  → Verde = Saldo a favor

═══ PERCEPCIONES ═══
• Sufridas: Percepciones que te cobraron tus proveedores
  en facturas de compra (IVA_PER, IIBB_PER)
• Efectuadas: Percepciones que vos cobraste a clientes

═══ RETENCIONES ═══
• Sufridas: Retenciones que tus clientes te hicieron
  al pagarte (IVA, IIBB)
• Efectuadas: Retenciones que vos le hiciste al proveedor

═══ USO ═══
1. Seleccioná mes y año
2. Presioná "Consultar"
3. Usá los tabs para navegar entre IVA, Percepciones y Retenciones
        """
        messagebox.showinfo("Ayuda - Reportes Fiscales", help_text)

    # ================================================================
    # ATTACH CONTROLLER
    # ================================================================

    def attach_controller(self, controller):
        self.controller = controller

    # ================================================================
    # UTILITIES
    # ================================================================

    def show_error(self, msg):
        messagebox.showerror("Error", msg)

    def show_success(self, msg):
        messagebox.showinfo("Éxito", msg)

    def show_warning(self, msg):
        messagebox.showwarning("Advertencia", msg)