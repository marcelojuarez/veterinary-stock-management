import customtkinter as ctk
from tkinter import messagebox
from models.customer import CustomerModel
from .components.customer.search_frame import SearchFrame
from .components.customer.customer_table import CustomerTable
from .components.customer.buttons_frame import ButtonsFrame
from .components.customer.add_customer_window import AddCustomerWindow
from .components.customer.update_debt_window import UpdateDebtWindow
# CONFIGURACIÓN GLOBAL MEJORADA
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class CustomersView:
    def __init__(self, parent, controller=None):
        self.controller = controller
        self.model = CustomerModel()

        self.frame = ctk.CTkFrame(parent, corner_radius=16, fg_color="#ffffff", border_width=1, border_color="#e0e0e0")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.setup_variables()
        self.create_widgets()

    def setup_variables(self):
        self.name_var = ctk.StringVar()
        self.cuit_var = ctk.StringVar()
        self.home_var = ctk.StringVar()
        self.phone_var = ctk.StringVar()
        self.find_var = ctk.StringVar()

    def create_widgets(self):
        # Header moderno con icono y estadísticas
        self.create_header()
        
        # Componente de búsqueda 
        self.search_component = SearchFrame(
            self.frame,
            on_search_callback=self.search_customer,
            on_show_all_callback=self.show_all_customers
        )

        # Componente de tabla 
        self.table_component = CustomerTable(
            self.frame,
            on_double_click_callback=self.on_double_click
        )

        # Botones 
        self.buttons_component = ButtonsFrame(
            self.frame,
            on_add_callback=self.open_add_window,
            on_update_debt_callback=self.update_debt,
            on_delete_callback=self.delete_customer,
            on_clear_callback=self.clear_form
        )

    def create_header(self):
        """Header moderno con icono y estadísticas"""
        header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        # Título con icono
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(fill="x", expand=True)
        
        title_label = ctk.CTkLabel(
            title_container,
            text="👥 Gestión de Clientes",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color="#2c3e50"
        )
        title_label.pack(anchor="center")
    
    def search_customer(self, search_term=None):
        if self.controller:
            if search_term is None:
                search_term = self.search_component.get_search_term()
            self.controller.search_customer(search_term)

    def show_all_customers(self):
        if self.controller:
            self.search_component.find_var.set("")
            self.controller.search_customer("")

    def refresh_customer_table(self, customers):
        self.table_component.refresh_data(customers)

    def on_double_click(self, event):
        tree = self.table_component.get_tree()
        row_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        if col != "#6":
            return

        x, y, width, height = tree.bbox(row_id, col)
        value = tree.set(row_id, column=col)

        # Entry temporal para edición 
        self.edit_box = ctk.CTkEntry(
            tree, 
            font=("Segoe UI", 12),
            width=width,
            height=height,
            fg_color="#ffffff",
            text_color="#2c3e50",
            border_width=1,
            border_color="#3498db",
            corner_radius=4
        )
        self.edit_box.place(x=x, y=y)
        self.edit_box.insert(0, value)
        self.edit_box.focus()
        self.edit_box.select_range(0, "end")

        self.edit_box.bind("<Return>", lambda e: self.save_edit(row_id, col))
        self.edit_box.bind("<Escape>", lambda e: self.edit_box.destroy())

    def open_add_window(self):
        AddCustomerWindow(
            self.frame.winfo_toplevel(),
            vars_dict={
                "nombre": self.name_var,
                "cuit": self.cuit_var,
                "domicilio": self.home_var,
                "telefono": self.phone_var,
            },
            on_add_callback=self.handle_add_customer,
        )

    def get_customer_data(self):
        return {
            "nombre": self.name_var.get().strip(),
            "cuit": self.cuit_var.get().strip(),
            "domicilio": self.home_var.get().strip(),
            "telefono": self.phone_var.get().strip(),
        }

    def update_debt(self):
        selected = self.table_component.get_selection()
        if not selected:
            self.show_error("Seleccioná un cliente")
            return

        row_id = selected[0]
        col = "#6"
        tree = self.table_component.get_tree()
        x, y, width, height = tree.bbox(row_id, col)
        value = tree.set(row_id, column=col)

        self.edit_box = ctk.CTkEntry(
            tree, 
            font=("Segoe UI", 12),
            width=width,
            height=height,
            fg_color="#ffffff",
            text_color="#2c3e50",
            border_width=1,
            border_color="#3498db",
            corner_radius=4
        )
        self.edit_box.place(x=x, y=y)
        self.edit_box.insert(0, value)
        self.edit_box.focus()
        self.edit_box.select_range(0, "end")
        self.edit_box.bind("<Return>", lambda e: self.save_edit(row_id, col))
        self.edit_box.bind("<Escape>", lambda e: self.edit_box.destroy())

    def delete_customer(self):
        if self.controller:
            selected = self.table_component.get_selection()
            if not selected:
                self.show_error("Seleccioná un cliente")
                return

            customer_data = self.table_component.get_item_values(selected[0])
            customer_id = customer_data[0]
            customer_name = customer_data[1]

            confirm = messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Estás seguro de eliminar al cliente: {customer_name}?",
                icon="warning",
            )

            if confirm:
                self.controller.delete_customer(customer_id)

    def handle_add_customer(self, window):
        try:
            success = self.controller.add_new_customer(window)
            return success
        except Exception as e:
            self.show_error(f"Error al agregar cliente: {str(e)}")
            return False

    def clear_form(self):
        self.name_var.set("")
        self.cuit_var.set("")
        self.home_var.set("")
        self.phone_var.set("")

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def show_success(self, message):
        messagebox.showinfo("Éxito", message)

    def show_warning(self, message):
        messagebox.showwarning("Advertencia", message)

    def save_edit(self, row_id, col):
        new_value = self.edit_box.get()
        self.table_component.set_item_value(row_id, col, new_value)
        self.edit_box.destroy()
        customer_id = self.table_component.get_item_values(row_id)[0]
        self.controller.update_customer_debt(customer_id, float(new_value))

    def set_controller(self, controller):
        self.controller = controller

    def update_debt(self):
        selected = self.table_component.get_selection()
        if not selected:
            self.show_error("Seleccioná un cliente")
            return

        row_id = selected[0]
        customer_data = self.table_component.get_item_values(row_id)
        cliente_id = customer_data[0]
        cliente_nombre = customer_data[1]

        # Abrir la ventana de pagos
        UpdateDebtWindow(self.frame.winfo_toplevel(), cliente_id, cliente_nombre)