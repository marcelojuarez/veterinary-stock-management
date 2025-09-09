import tkinter as tk
from tkinter import ttk
from config.settings import settings
from views.stock_view import StockView
from views.sales_view import SalesView
from views.supplier_view import SupplierView
from views.customers_view import CustomersView
from controllers.stock_controller import StockController

class App():
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_notebook()
        self.load_initial_data()

    def setup_window(self):
        view_config = settings['VIEW_CONFIG']
        self.root.title(view_config['window-title'])
        self.root.geometry(view_config['window-size'])

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        self.stock_view = StockView(self.notebook)
        self.stock_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.stock_view.frame, text='Inventario')

        sales_view = SalesView(self.notebook)
        sales_view.frame.pack(fill='both', expand=True)
        self.notebook.add(sales_view.frame, text='Venta')


        supplier_controller = SupplierController(self.notebook)
        supplier_view = SupplierView(self.notebook, supplier_controller)

        supplier_view.frame.pack(fill='both', expand=True)
        self.notebook.add(supplier_view.frame, text='Proveedores')

        customers_view = CustomersView(self.notebook)
        customers_view.frame.pack(fill='both', expand=True)
        self.notebook.add(customers_view.frame, text='Clientes')

        self.stock_controller = StockController(self.stock_view)
        self.stock_view.controller = self.stock_controller

    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            self.stock_controller.refresh_stock_table()
        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")

    def run(self):
        self.root.mainloop()