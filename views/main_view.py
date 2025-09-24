import tkinter as tk
from tkinter import ttk, messagebox
from controllers.auth_controller import validate_data
from config.settings import settings
from views.stock_view import StockView
from views.sales_view import SalesView
from views.supplier_view import SupplierView
from views.customers_view import CustomersView
from controllers.stock_controller import StockController
from controllers.supplier_controller import SupplierController
from controllers.customer_controller import CustomerController
class App():
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.login_window()

    def setup_window(self):
        view_config = settings['VIEW_CONFIG']
        self.root.title(view_config['window-title'])
        self.root.geometry(view_config['window-size'])
        self.root.withdraw()
        self.root.update_idletasks()
        
    def setup_variables(self):
        self.user_var = tk.StringVar()
        self.pwd_var = tk.StringVar()

    def login_window(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Inicio de sesion")
        
        # Asociar la cruz al cierre de la app
        self.login_win.protocol("WM_DELETE_WINDOW", self.root.destroy)

        # posicion y tamaño de root
        x_root = self.root.winfo_x() 
        y_root = self.root.winfo_y()
        width_root = self.root.winfo_width()
        height_root = self.root.winfo_height()

        width_win = 320
        height_win = 160

        # calculo del centro
        x = x_root + (width_root // 2) - (width_win // 2)
        y = y_root + (height_root // 2) - (height_win // 2)

        print(x)
        print(y)
      
        self.login_win.geometry(f"{width_win}x{height_win}+{x}+{y}")

        self.login_win.columnconfigure(0, weight=1)
        self.login_win.columnconfigure(1, weight=1)
        self.login_win.rowconfigure(0, weight=1)
        self.login_win.rowconfigure(1, weight=1)
        self.login_win.rowconfigure(2, weight=1)

        # usuario
        user_lbl = ttk.Label(self.login_win, text="USUARIO: ")
        user_lbl.grid(row=0, column=0)

        user_entry = ttk.Entry(self.login_win, textvariable=self.user_var)
        user_entry.grid(row=0, column=1)

        # password
        pwd_lbl = ttk.Label(self.login_win, text='CONTRASEÑA')
        pwd_lbl.grid(row=1, column=0, padx=2)

        pwd_entry = ttk.Entry(self.login_win, show='*', textvariable=self.pwd_var)
        pwd_entry.grid(row=1, column=1)

        entry_btn = ttk.Button(self.login_win, text='Entrar', command=lambda: self.load_system())
        entry_btn.grid(row=2, column=1, padx=1, pady=5)


    def load_system(self):
        if (validate_data(self.user_var.get(), self.pwd_var.get())):
            self.root.deiconify()
            self.create_notebook()
            self.load_initial_data()
            self.login_win.destroy()  

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        self.stock_view = StockView(self.notebook)
        self.stock_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.stock_view.frame, text='Inventario')

        sales_view = SalesView(self.notebook)
        sales_view.frame.pack(fill='both', expand=True)
        self.notebook.add(sales_view.frame, text='Venta')

        self.supplier_view = SupplierView(self.notebook)
        self.supplier_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.supplier_view.frame, text='Proveedores')

        self.customers_view = CustomersView(self.notebook)
        self.customers_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.customers_view.frame, text='Clientes')

        self.stock_controller = StockController(self.stock_view)
        self.stock_view.controller = self.stock_controller

        self.supplier_controller = SupplierController(self.supplier_view)
        self.supplier_view.controller = self.supplier_controller

        self.customer_controller = CustomerController(self.customers_view)
        self.customers_view.controller = self.customer_controller

    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            self.stock_controller.refresh_stock_table()
            self.supplier_controller.refresh_supplier_table()
        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")


    def run(self):
        self.root.mainloop()