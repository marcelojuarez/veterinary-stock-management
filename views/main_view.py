import tkinter as tk
from tkinter import ttk
from config.settings import settings
from views.stock_view import StockView
from views.sales_view import SalesView
from views.suppliers_view import SuppliersView
from views.customers_view import CustomersView

class App():
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_notebook()

    def setup_window(self):
        view_config = settings['VIEW_CONFIG']
        self.root.title(view_config['window-title'])
        self.root.geometry(view_config['window-size'])

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        stock_view = StockView(self.notebook)
        stock_view.frame.pack(fill='both', expand=True)
        self.notebook.add(stock_view.frame, text='Inventario')

        sales_view = SalesView(self.notebook)
        sales_view.frame.pack(fill='both', expand=True)
        self.notebook.add(sales_view.frame, text='Venta')

        suppliers_view = SuppliersView(self.notebook)
        suppliers_view.frame.pack(fill='both', expand=True)
        self.notebook.add(suppliers_view.frame, text='Proveedores')

        customers_view = CustomersView(self.notebook)
        customers_view.frame.pack(fill='both', expand=True)
        self.notebook.add(customers_view.frame, text='Clientes')

    def run(self):
        self.root.mainloop()