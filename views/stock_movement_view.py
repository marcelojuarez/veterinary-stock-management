import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from utils.utils import traditional_to_iso, iso_to_traditional
from utils.view_helpers import center_window


EVENT_LABELS = {
    'COMPRA':       '🛒 Compra',
    'VENTA':        '🧾 Venta',
    'PRECIO':       '✏️ Precio',
    'PRECIO_MASIVO':'📈 Precio masivo',
    'AJUSTE':       '🔧 Ajuste',  # ← NUEVO
}

EVENT_COLORS = {
    'COMPRA':       '#E3F2FD',
    'VENTA':        '#E8F5E9',
    'PRECIO':       '#FFF3E0',
    'PRECIO_MASIVO':'#F3E5F5',
    'AJUSTE':       '#FFF9C4',  # ← NUEVO (amarillo claro)
}


class StockMovementView:
    def __init__(self, movement_model, stock_model=None, controller=None):
        self.movement = movement_model
        self.stock_model = stock_model  # ← NUEVO: necesario para ajustes
        self.controller = controller

    # ================================================================== #
    # VENTANA PRINCIPAL                                                  #
    # ================================================================== #

    def open(self, parent, product_id=None, product_name=None):
        """
        Si se pasa product_id abre el historial filtrado por ese producto.
        Si no, abre el historial global.
        """
        win = ctk.CTkToplevel(parent)
        win.title("Historial de Movimientos de Stock")
        win.transient(parent)
        win.grab_set()
        win.withdraw()

        title_text = (
            f"Historial: {product_name}" if product_name
            else "Historial global de movimientos"
        )

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(win, fg_color="#3A3251", height=55, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"📋  {title_text}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=12)

        # ── Filtros ──────────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(win, fg_color="#f5f5f5", corner_radius=8)
        filter_frame.pack(fill="x", padx=15, pady=10)

        # Fechas
        hoy = datetime.now()
        hace_30 = hoy - timedelta(days=30)

        fecha_desde_var = tk.StringVar(value=hace_30.strftime("%d/%m/%Y"))
        fecha_hasta_var = tk.StringVar(value=hoy.strftime("%d/%m/%Y"))

        ctk.CTkLabel(filter_frame, text="Desde:", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=0, padx=(15, 5), pady=10)

        DateEntry(
            filter_frame,
            textvariable=fecha_desde_var,
            width=11,
            background="#3A3251",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy"
        ).grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(filter_frame, text="Hasta:", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=2, padx=(15, 5), pady=10)

        DateEntry(
            filter_frame,
            textvariable=fecha_hasta_var,
            width=11,
            background="#3A3251",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy"
        ).grid(row=0, column=3, padx=5, pady=10)

        # Tipo de evento
        ctk.CTkLabel(filter_frame, text="Tipo:", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=4, padx=(15, 5), pady=10)

        event_var = tk.StringVar(value="Todos")
        ctk.CTkComboBox(
            filter_frame,
            variable=event_var,
            values=["Todos", "Compra", "Venta", "Precio", "Precio masivo", "Ajuste"],  # ← AGREGADO "Ajuste"
            width=130,
            state="readonly"
        ).grid(row=0, column=5, padx=5, pady=10)

        # Botones rápidos
        quick_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        quick_frame.grid(row=0, column=6, padx=15, pady=10)

        def set_today():
            fecha_desde_var.set(hoy.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            load()

        def set_week():
            inicio = hoy - timedelta(days=hoy.weekday())
            fecha_desde_var.set(inicio.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            load()

        def set_month():
            inicio = hoy.replace(day=1)
            fecha_desde_var.set(inicio.strftime("%d/%m/%Y"))
            fecha_hasta_var.set(hoy.strftime("%d/%m/%Y"))
            load()

        for txt, cmd in [("Hoy", set_today), ("Semana", set_week), ("Mes", set_month)]:
            ctk.CTkButton(
                quick_frame, text=txt, width=65, height=28, font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#3A3251", hover_color="#1e1a2e",
                command=cmd
            ).pack(side="left", padx=2)

        ctk.CTkButton(
            filter_frame, text="🔍 Filtrar", width=100, height=32,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: load()
        ).grid(row=0, column=7, padx=15, pady=10)

        # ── Resumen ──────────────────────────────────────────────────────
        summary_var = tk.StringVar(value="")
        ctk.CTkLabel(
            win,
            textvariable=summary_var,
            font=ctk.CTkFont(size=12),
            text_color="#555555"
        ).pack(anchor="w", padx=20)

        # ── Tabla ────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(win)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        cols = ("Fecha", "Producto", "Tipo", "Detalle",
                "Stock Ant.", "Stock Act.",
                "Costo Ant.", "Costo Act.",
                "Precio Ant.", "Precio Act.")

        style = ttk.Style()
        style.configure("Mov.Treeview", rowheight=18, font=("Segoe UI", 7))
        style.configure("Mov.Treeview.Heading", font=("Segoe UI", 8, "bold"))

        tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=18,
            style="Mov.Treeview"
        )

        col_widths = [115, 180, 90, 180, 65, 65, 80, 80, 80, 80]
        for col, w in zip(cols, col_widths):
            tree.column(col, width=w, anchor="center" if col != "Producto" and col != "Detalle" else "w")
            tree.heading(col, text=col)

        # Tags de color por tipo
        for key, color in EVENT_COLORS.items():
            tree.tag_configure(key, background=color)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # ── Botones ──────────────────────────────────────────────────────
        # ✨ NUEVO: Frame para botones
        button_frame = ctk.CTkFrame(win, fg_color="transparent")
        button_frame.pack(pady=10)

        # ✨ NUEVO: Botón Ajustar Stock (solo visible si es un producto específico)
        if product_id and self.stock_model:
            ctk.CTkButton(
                button_frame,
                text="🔧 Ajustar Stock",
                width=140,
                height=35,
                fg_color="#FF9800",
                hover_color="#F57C00",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda: self.open_adjust_stock_window(win, product_id, product_name, load)
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Cerrar",
            width=120,
            height=35,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=win.destroy
        ).pack(side="left", padx=5)

        # ── Función de carga ─────────────────────────────────────────────
        def load():
            for row in tree.get_children():
                tree.delete(row)

            d_from = traditional_to_iso(fecha_desde_var.get())
            d_to   = traditional_to_iso(fecha_hasta_var.get())

            rows = self.movement.get_by_date_range(
                d_from, d_to,
                product_id=product_id  # None = global
            )

            # Filtro por tipo de evento
            event_map = {
                "Compra":       "COMPRA",
                "Venta":        "VENTA",
                "Precio":       "PRECIO",
                "Precio masivo":"PRECIO_MASIVO",
                "Ajuste":       "AJUSTE",  # ← AGREGADO
            }
            selected = event_var.get()
            if selected != "Todos":
                rows = [r for r in rows if r[4] == event_map.get(selected)]

            for r in rows:
                # r = (id, product_id, product_name, date, event_type,
                #      detail, qty_before, qty_after,
                #      cost_before, cost_after, price_before, price_after)
                _, _, p_name, date, ev_type, detail, \
                    qty_b, qty_a, cost_b, cost_a, price_b, price_a = r

                # Formatear fecha
                try:
                    date_fmt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_fmt = date

                def fmt(v):
                    return f"${v}" if v not in (None, "") else "—"

                def fmt_qty(v):
                    return str(v) if v is not None else "—"

                tree.insert("", "end", values=(
                    date_fmt,
                    p_name,
                    EVENT_LABELS.get(ev_type, ev_type),
                    detail or "—",
                    fmt_qty(qty_b),
                    fmt_qty(qty_a),
                    fmt(cost_b),
                    fmt(cost_a),
                    fmt(price_b),
                    fmt(price_a),
                ), tags=(ev_type,))

            summary_var.set(f"  {len(rows)} movimientos encontrados")

        # Carga inicial
        load()

        center_window(win, 1300, 750)
        win.deiconify()

    # ================================================================== #
    # VENTANA AJUSTAR STOCK (NUEVA FUNCIONALIDAD)                        #
    # ================================================================== #

    def open_adjust_stock_window(self, parent, product_id, product_name, callback_refresh):
        """
        Ventana para ajustar stock manualmente con justificación
        """
        if not self.stock_model:
            messagebox.showerror("Error", "No hay modelo de stock disponible")
            return

        # Obtener datos actuales del producto
        try:
            product = self.stock_model.get_product_by_id(product_id)
            if not product:
                messagebox.showerror("Error", "Producto no encontrado")
                return
            print(product)
            current_stock = int(product[12])  # quantity está en índice 9
            current_cost = product[6]  # cost_price
            current_price = product[7]  # price
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener datos del producto: {e}")
            return

        # Crear ventana modal
        adjust_win = ctk.CTkToplevel(parent)
        adjust_win.title("Ajustar Stock")
        adjust_win.configure(fg_color="#e0e0e0")
        adjust_win.transient(parent)
        adjust_win.grab_set()
        adjust_win.withdraw()

        # Card principal
        card = ctk.CTkFrame(adjust_win, fg_color="white", corner_radius=20)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        ctk.CTkLabel(
            card,
            text="🔧 Ajustar Stock",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="black"
        ).pack(pady=(20, 10))

        # Formulario
        form = ctk.CTkFrame(card, fg_color="#f9f9f9", corner_radius=10)
        form.pack(pady=10, padx=20, fill="x")

        # Variables
        new_stock_var = tk.StringVar()
        reason_var = tk.StringVar(value="Vencimiento")
        observations_var = tk.StringVar()

        def add_field(row, label, widget, readonly=False):
            ctk.CTkLabel(
                form,
                text=label,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="black"
            ).grid(row=row, column=0, sticky="e", padx=(15, 10), pady=8)
            
            if readonly:
                widget.configure(state="readonly")
            
            widget.grid(row=row, column=1, sticky="w", padx=(0, 15), pady=8)
            return widget

        # Producto (readonly)
        add_field(
            0, "Producto:",
            ctk.CTkEntry(form, width=300, textvariable=tk.StringVar(value=product_name)),
            readonly=True
        )

        # Stock actual (readonly)
        add_field(
            1, "Stock Actual:",
            ctk.CTkEntry(form, width=300, textvariable=tk.StringVar(value=str(current_stock))),
            readonly=True
        )

        # Nuevo stock (editable)
        new_stock_entry = add_field(
            2, "Nuevo Stock:",
            ctk.CTkEntry(form, width=300, textvariable=new_stock_var, placeholder_text="Ingrese el nuevo stock")
        )
        new_stock_entry.focus()

        # Diferencia (calculada)
        diff_var = tk.StringVar(value="—")
        diff_label = add_field(
            3, "Diferencia:",
            ctk.CTkEntry(form, width=300, textvariable=diff_var),
            readonly=True
        )

        # Calcular diferencia automáticamente
        def update_diff(*args):
            try:
                new = int(new_stock_var.get())
                diff = new - current_stock
                sign = "+" if diff > 0 else ""
                diff_var.set(f"{sign}{diff}")
                
                # Cambiar color según sea aumento o disminución
                if diff > 0:
                    diff_label.configure(text_color="#4CAF50")  # Verde
                elif diff < 0:
                    diff_label.configure(text_color="#F44336")  # Rojo
                else:
                    diff_label.configure(text_color="#757575")  # Gris
            except ValueError:
                diff_var.set("—")
                diff_label.configure(text_color="#757575")

        new_stock_var.trace_add("write", update_diff)

        # Motivo (dropdown)
        add_field(
            4, "Motivo:",
            ctk.CTkComboBox(
                form,
                width=300,
                variable=reason_var,
                values=[
                    "Vencimiento",
                    "Rotura/Daño",
                    "Inventario (corrección)",
                    "Devolución",
                    "Pérdida",
                    "Otro"
                ],
                state="readonly"
            )
        )

        # Observaciones
        add_field(
            5, "Observaciones:",
            ctk.CTkEntry(
                form,
                width=300,
                textvariable=observations_var,
                placeholder_text="Detalles adicionales (opcional)"
            )
        )

        # Frame de confirmación (destacado)
        confirm_frame = ctk.CTkFrame(card, fg_color="#FFF9C4", corner_radius=10)
        confirm_frame.pack(pady=15, padx=20, fill="x", ipady=10)

        ctk.CTkLabel(
            confirm_frame,
            text="⚠️ Este ajuste modificará el stock del producto",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F57C00"
        ).pack()

        # Botones
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=15)

        def confirm_adjust():
            """Confirmar y guardar ajuste"""
            try:
                # Validaciones
                new_stock_str = new_stock_var.get().strip()
                if not new_stock_str:
                    messagebox.showwarning("Advertencia", "Ingrese el nuevo stock")
                    return

                new_stock = int(new_stock_str)
                if new_stock < 0:
                    messagebox.showwarning("Advertencia", "El stock no puede ser negativo")
                    return

                if new_stock == current_stock:
                    messagebox.showinfo("Información", "El stock no ha cambiado")
                    return

                # Construir detalle del ajuste
                reason = reason_var.get()
                obs = observations_var.get().strip()
                detail_parts = [f"Motivo: {reason}"]
                if obs:
                    detail_parts.append(f"Obs: {obs}")
                detail = " | ".join(detail_parts)

                # Confirmación final
                diff = new_stock - current_stock
                msg = (
                    f"¿Confirmar ajuste de stock?\n\n"
                    f"Producto: {product_name}\n"
                    f"Stock actual: {current_stock}\n"
                    f"Stock nuevo: {new_stock}\n"
                    f"Diferencia: {diff:+d}\n\n"
                    f"{detail}"
                )

                if not messagebox.askyesno("Confirmar Ajuste", msg):
                    return

                # 1. Actualizar stock en la tabla stock
                self.stock_model.update_product_quantity(product_id, new_stock)

                # 2. Registrar movimiento
                self.movement.register(
                    product_id=product_id,
                    product_name=product_name,
                    event_type="AJUSTE",
                    detail=detail,
                    qty_before=current_stock,
                    qty_after=new_stock,
                    cost_before=current_cost,
                    cost_after=current_cost,  # No cambia
                    price_before=current_price,
                    price_after=current_price  # No cambia
                )

                messagebox.showinfo("Éxito", "Stock ajustado correctamente")
                
                # Refrescar tabla de movimientos
                if callback_refresh:
                    callback_refresh()
                    self.controller.refresh_stock_table()
                
                adjust_win.destroy()

            except ValueError:
                messagebox.showerror("Error", "El stock debe ser un número entero")
            except Exception as e:
                messagebox.showerror("Error", f"Error al ajustar stock: {e}")

        ctk.CTkButton(
            btn_frame,
            text="✓ Confirmar Ajuste",
            width=160,
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=confirm_adjust
        ).grid(row=0, column=0, padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=160,
            height=40,
            fg_color="#757575",
            hover_color="#616161",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=adjust_win.destroy
        ).grid(row=0, column=1, padx=10)

        # Enter para confirmar
        adjust_win.bind("<Return>", lambda e: confirm_adjust())

        # Centrar y mostrar
        center_window(adjust_win, 550, 580)
        adjust_win.deiconify()