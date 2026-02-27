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

        # Configurar grid principal
        self.frame.grid_rowconfigure(3, weight=1)
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

        ctk.CTkLabel(
            header,
            text="📊 Reportes Fiscales",
            font=ctk.CTkFont(size=17, weight="bold"),
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

        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_actual = datetime.now().month
        self.mes_var.set(meses[mes_actual - 1])

        ctk.CTkComboBox(
            period_frame,
            variable=self.mes_var,
            values=meses,
            width=150,
            height=35,
            state="readonly"
        ).pack(side="left", padx=5, pady=10)

        anio_actual = datetime.now().year
        anios = [str(y) for y in range(anio_actual - 5, anio_actual + 2)]
        self.anio_var.set(str(anio_actual))

        ctk.CTkComboBox(
            period_frame,
            variable=self.anio_var,
            values=anios,
            width=100,
            height=35,
            state="readonly"
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
            text="📅 Mes Actual",
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
    # TARJETAS DE RESUMEN - DOS FILAS
    # ================================================================

    def create_summary_cards(self):
        summary_outer = ctk.CTkFrame(self.frame, fg_color="transparent")
        summary_outer.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
        summary_outer.grid_columnconfigure(0, weight=1)

        # --- Fila 1: IVA ---
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

        self.card_iva_ventas = self._make_card(
            iva_row, 0,
            "💰 IVA VENTAS", "$0.00", "Débito Fiscal",
            "#E3F2FD", "#1565C0"
        )
        self.card_iva_compras = self._make_card(
            iva_row, 1,
            "🛒 IVA COMPRAS", "$0.00", "Crédito Fiscal",
            "#E8F5E9", "#2E7D32"
        )
        self.card_iva_saldo = self._make_card(
            iva_row, 2,
            "📊 SALDO IVA", "$0.00", "A Pagar / A Favor",
            "#FFF3E0", "#E65100"
        )

        # Separador
        sep = ctk.CTkFrame(summary_outer, fg_color="#e0e0e0", height=1)
        sep.grid(row=2, column=0, sticky="ew", pady=(8, 2))

        # --- Fila 2: Percepciones y Retenciones ---
        otros_label = ctk.CTkLabel(
            summary_outer,
            text="PERCEPCIONES Y RETENCIONES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#757575"
        )
        otros_label.grid(row=3, column=0, sticky="w", padx=5, pady=(2, 2))

        otros_row = ctk.CTkFrame(summary_outer, fg_color="transparent")
        otros_row.grid(row=4, column=0, sticky="ew", pady=(0, 5))
        otros_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_per_sufridas = self._make_card(
            otros_row, 0,
            "📋 PERC. SUFRIDAS", "$0.00", "En compras",
            "#F3E5F5", "#6A1B9A"
        )
        self.card_per_efectuadas = self._make_card(
            otros_row, 1,
            "📋 PERC. EFECTUADAS", "$0.00", "En ventas",
            "#EDE7F6", "#4527A0"
        )
        self.card_ret_sufridas = self._make_card(
            otros_row, 2,
            "🏦 RET. SUFRIDAS", "$0.00", "IVA + IIBB",
            "#FCE4EC", "#880E4F"
        )
        self.card_ret_efectuadas = self._make_card(
            otros_row, 3,
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

        self._create_resumen_tab()
        self._create_ventas_tab()
        self._create_compras_tab()
        self._create_percepciones_tab()
        self._create_retenciones_tab()

    # ---- Tab: Resumen IVA ----

    def _create_resumen_tab(self):
        tab = self.tabview.tab("📈 Resumen IVA")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Alícuota", "Ventas Neto", "Ventas IVA", "Compras Neto", "Compras IVA", "Saldo Bruto", "Saldo Neto")
        self.resumen_table = self._make_treeview(frame, cols, [90, 120, 110, 120, 110, 105, 105], height=12)

    # ---- Tab: Detalle Ventas ----

    def _create_ventas_tab(self):
        tab = self.tabview.tab("💰 Detalle Ventas")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Fecha", "Venta #", "Cliente", "CUIT", "Alícuota", "Neto", "IVA", "Total")
        anchors = {"Cliente": "w"}
        self.ventas_table = self._make_treeview(frame, cols, [100, 70, 200, 130, 80, 110, 110, 110], height=15, custom_anchors=anchors)

    # ---- Tab: Detalle Compras ----

    def _create_compras_tab(self):
        tab = self.tabview.tab("🛒 Detalle Compras")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Fecha", "Compra #", "Proveedor", "CUIT", "Alícuota", "Neto", "IVA", "Total")
        anchors = {"Proveedor": "w"}
        self.compras_table = self._make_treeview(frame, cols, [100, 70, 200, 130, 80, 110, 110, 110], height=15, custom_anchors=anchors)

    # ---- Tab: Percepciones ----

    def _create_percepciones_tab(self):
        tab = self.tabview.tab("📋 Percepciones")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sub-tabs
        self.perc_subtabs = ctk.CTkTabview(frame, height=330)
        self.perc_subtabs.pack(fill="both", expand=True)
        self.perc_subtabs.add("📥 Sufridas (Compras)")
        self.perc_subtabs.add("📤 Efectuadas (Ventas)")

        # Sufridas: percepciones que me cobran en facturas de proveedor
        sub_sufridas = self.perc_subtabs.tab("📥 Sufridas (Compras)")
        f1 = ctk.CTkFrame(sub_sufridas, fg_color="transparent")
        f1.pack(fill="both", expand=True)
        cols_s = ("Fecha", "Factura #", "Proveedor", "CUIT", "Tipo", "Monto")
        anchors_s = {"Proveedor": "w"}
        self.perc_sufridas_table = self._make_treeview(
            f1, cols_s, [110, 100, 220, 140, 120, 120], height=12, custom_anchors=anchors_s
        )

        # Efectuadas: percepciones que cobramos nosotros en ventas
        sub_efectuadas = self.perc_subtabs.tab("📤 Efectuadas (Ventas)")
        f2 = ctk.CTkFrame(sub_efectuadas, fg_color="transparent")
        f2.pack(fill="both", expand=True)
        cols_e = ("Fecha", "Venta #", "Cliente", "CUIT", "Tipo", "Monto")
        anchors_e = {"Cliente": "w"}
        self.perc_efectuadas_table = self._make_treeview(
            f2, cols_e, [110, 100, 220, 140, 120, 120], height=12, custom_anchors=anchors_e
        )

    # ---- Tab: Retenciones ----

    def _create_retenciones_tab(self):
        tab = self.tabview.tab("🏦 Retenciones")
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sub-tabs
        self.ret_subtabs = ctk.CTkTabview(frame, height=330)
        self.ret_subtabs.pack(fill="both", expand=True)
        self.ret_subtabs.add("📥 Sufridas (Ventas)")
        self.ret_subtabs.add("📤 Efectuadas (Compras)")

        # Sufridas: retenciones que el cliente nos hace en ventas
        sub_sufridas = self.ret_subtabs.tab("📥 Sufridas (Ventas)")
        f1 = ctk.CTkFrame(sub_sufridas, fg_color="transparent")
        f1.pack(fill="both", expand=True)
        cols_s = ("Fecha", "Venta #", "Cliente", "CUIT", "Tipo", "Certificado", "Monto")
        anchors_s = {"Cliente": "w"}
        self.ret_sufridas_table = self._make_treeview(
            f1, cols_s, [110, 80, 200, 130, 80, 120, 110], height=12, custom_anchors=anchors_s
        )

        # Efectuadas: retenciones que nosotros hacemos al proveedor en compras
        sub_efectuadas = self.ret_subtabs.tab("📤 Efectuadas (Compras)")
        f2 = ctk.CTkFrame(sub_efectuadas, fg_color="transparent")
        f2.pack(fill="both", expand=True)
        cols_e = ("Fecha", "Compra #", "Proveedor", "CUIT", "Tipo", "Certificado", "Monto")
        anchors_e = {"Proveedor": "w"}
        self.ret_efectuadas_table = self._make_treeview(
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
    # ACTUALIZAR CARDS
    # ================================================================

    def update_summary(self, posicion):
        """
        Actualiza las cards de IVA.
        posicion = resultado de IVAModel.get_posicion_iva()
        """
        self.card_iva_ventas.configure(text=format_money(posicion.get('iva_ventas', 0)))
        self.card_iva_compras.configure(text=format_money(posicion.get('iva_compras', 0)))

        try:
            saldo = float(posicion.get('saldo', 0) or 0)
        except (TypeError, ValueError):
            saldo = 0.0

        saldo_text = format_money(abs(saldo))
        if saldo > 0:
            self.card_iva_saldo.configure(text=saldo_text, text_color="#F44336")
        elif saldo < 0:
            self.card_iva_saldo.configure(text=saldo_text, text_color="#4CAF50")
        else:
            self.card_iva_saldo.configure(text="$0.00", text_color="#666666")

    def update_otros_summary(self, totales):
        """
        Actualiza cards de percepciones y retenciones.
        totales = {
            'per_sufridas': float,
            'per_efectuadas': float,
            'ret_sufridas': float,
            'ret_efectuadas': float
        }
        """
        self.card_per_sufridas.configure(text=format_money(totales.get('per_sufridas', 0)))
        self.card_per_efectuadas.configure(text=format_money(totales.get('per_efectuadas', 0)))
        self.card_ret_sufridas.configure(text=format_money(totales.get('ret_sufridas', 0)))
        self.card_ret_efectuadas.configure(text=format_money(totales.get('ret_efectuadas', 0)))

    # ================================================================
    # ACTUALIZAR TABLAS IVA
    # ================================================================

    def update_resumen_table(self, detalle_posicion):
        for item in self.resumen_table.get_children():
            self.resumen_table.delete(item)

        for item in detalle_posicion['detalle']:
            self.resumen_table.insert("", "end", values=(
                item['alicuota'],
                format_money(item.get('ventas_neto', 0)),
                format_money(item.get('iva_ventas', 0)),
                format_money(item.get('compras_neto', 0)),
                format_money(item.get('iva_compras', 0)),
                format_money(item.get('saldo', 0)),   # bruto
                "—"                                   # neto solo en TOTAL
            ))

        # Fila subtotales brutos
        self.resumen_table.insert("", "end", values=(
            "Subtotal", "—",
            format_money(detalle_posicion.get('total_iva_ventas', 0)),
            "—",
            format_money(detalle_posicion.get('total_iva_compras', 0)),
            format_money(detalle_posicion.get('saldo_bruto', 0)),
            "—"
        ), tags=("subtotal",))

        # Filas de ajustes si existen
        ret_iva = detalle_posicion.get('ret_iva', 0)
        per_iva = detalle_posicion.get('per_iva', 0)
        if ret_iva:
            self.resumen_table.insert("", "end", values=(
                "Ret. IVA sufridas", "—", f"-{format_money(ret_iva)}",
                "—", "—", "—", "—"
            ), tags=("ajuste",))
        if per_iva:
            self.resumen_table.insert("", "end", values=(
                "Perc. IVA sufridas", "—", "—",
                "—", f"+{format_money(per_iva)}", "—", "—"
            ), tags=("ajuste",))

        # Fila TOTAL NETO
        self.resumen_table.insert("", "end", values=(
            "TOTAL",
            "—",
            format_money(detalle_posicion.get('debito_fiscal', detalle_posicion.get('total_iva_ventas', 0))),
            "—",
            format_money(detalle_posicion.get('credito_fiscal', detalle_posicion.get('total_iva_compras', 0))),
            format_money(detalle_posicion.get('saldo_bruto', 0)),
            format_money(detalle_posicion.get('saldo_total', 0))
        ), tags=("total",))

        self.resumen_table.tag_configure("total",    background="#E0E0E0", font=("Segoe UI", 10, "bold"))
        self.resumen_table.tag_configure("subtotal", background="#F5F5F5", font=("Segoe UI", 9, "bold"))
        self.resumen_table.tag_configure("ajuste",   background="#FFF9C4", font=("Segoe UI", 9, "italic"))

    def update_ventas_table(self, ventas):
        for item in self.ventas_table.get_children():
            self.ventas_table.delete(item)

        for v in ventas:
            fecha = v[1][:10] if v[1] and len(v[1]) > 10 else v[1]
            self.ventas_table.insert("", "end", values=(
                fecha, v[0], v[2], v[3],
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
                fecha, c[0], c[2], c[3],
                format_percent(c[4]),
                format_money(c[5]),
                format_money(c[6]),
                format_money(c[7])
            ))

    # ================================================================
    # ACTUALIZAR TABLAS PERCEPCIONES
    # ================================================================

    def update_perc_sufridas_table(self, percepciones):
        """
        percepciones: lista de tuplas desde DB
        Columnas esperadas:
          (fecha, invoice_id, proveedor, cuit, tax_type, amount)
        """
        for item in self.perc_sufridas_table.get_children():
            self.perc_sufridas_table.delete(item)

        total = 0.0
        for p in percepciones:
            fecha = p[0][:10] if p[0] and len(p[0]) > 10 else p[0]
            monto = float(p[5] or 0)
            total += monto
            self.perc_sufridas_table.insert("", "end", values=(
                fecha, p[1], p[2], p[3], p[4], format_money(monto)
            ))

        if percepciones:
            self.perc_sufridas_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", format_money(total)
            ), tags=("total",))
            self.perc_sufridas_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    def update_perc_efectuadas_table(self, percepciones):
        """
        percepciones: lista de tuplas
        Columnas esperadas:
          (fecha, sale_id, cliente, cuit, tax_type, amount)
        """
        for item in self.perc_efectuadas_table.get_children():
            self.perc_efectuadas_table.delete(item)

        total = 0.0
        for p in percepciones:
            fecha = p[0][:10] if p[0] and len(p[0]) > 10 else p[0]
            monto = float(p[5] or 0)
            total += monto
            self.perc_efectuadas_table.insert("", "end", values=(
                fecha, p[1], p[2], p[3], p[4], format_money(monto)
            ))

        if percepciones:
            self.perc_efectuadas_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", format_money(total)
            ), tags=("total",))
            self.perc_efectuadas_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    # ================================================================
    # ACTUALIZAR TABLAS RETENCIONES
    # ================================================================

    def update_ret_sufridas_table(self, retenciones):
        """
        retenciones: lista de tuplas desde DB (sale_retentions)
        Columnas esperadas:
          (fecha, sale_id, cliente, cuit, tax_type, certificate_number, amount)
        """
        for item in self.ret_sufridas_table.get_children():
            self.ret_sufridas_table.delete(item)

        total = 0.0
        for r in retenciones:
            fecha = r[0][:10] if r[0] and len(r[0]) > 10 else r[0]
            monto = float(r[6] or 0)
            total += monto
            self.ret_sufridas_table.insert("", "end", values=(
                fecha, r[1], r[2], r[3], r[4], r[5] or "-", format_money(monto)
            ))

        if retenciones:
            self.ret_sufridas_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", "", format_money(total)
            ), tags=("total",))
            self.ret_sufridas_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    def update_ret_efectuadas_table(self, retenciones):
        """
        retenciones: lista de tuplas (retenciones que le hacemos al proveedor)
        Columnas esperadas:
          (fecha, purchase_id, proveedor, cuit, tax_type, certificate_number, amount)
        """
        for item in self.ret_efectuadas_table.get_children():
            self.ret_efectuadas_table.delete(item)

        total = 0.0
        for r in retenciones:
            fecha = r[0][:10] if r[0] and len(r[0]) > 10 else r[0]
            monto = float(r[6] or 0)
            total += monto
            self.ret_efectuadas_table.insert("", "end", values=(
                fecha, r[1], r[2], r[3], r[4], r[5] or "-", format_money(monto)
            ))

        if retenciones:
            self.ret_efectuadas_table.insert("", "end", values=(
                "", "TOTAL", "", "", "", "", format_money(total)
            ), tags=("total",))
            self.ret_efectuadas_table.tag_configure("total", background="#E0E0E0", font=("Segoe UI", 10, "bold"))

    # ================================================================
    # COMANDOS
    # ================================================================

    def load_reports(self):
        if self.controller:
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            mes = meses.index(self.mes_var.get()) + 1
            anio = int(self.anio_var.get())
            self.controller.load_period_reports(mes, anio)

    def load_current_month(self):
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.mes_var.set(meses[datetime.now().month - 1])
        self.anio_var.set(str(datetime.now().year))
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
    # UTILIDADES
    # ================================================================

    def show_error(self, msg):
        messagebox.showerror("Error", msg)

    def show_success(self, msg):
        messagebox.showinfo("Éxito", msg)

    def show_warning(self, msg):
        messagebox.showwarning("Advertencia", msg)