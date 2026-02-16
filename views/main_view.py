import tkinter as tk
import customtkinter as ctk
from tkinter import ttk

from config.settings import settings
from events import EventBus

from views.start_view import StartView
from views.stock_view import StockView
from views.sales_view import SalesView
from views.supplier_view import SupplierView
from views.customers_view import CustomersView

from controllers.auth_controller import validate_data
from controllers.stock_controller import StockController
from controllers.sales_controller import SalesController
from controllers.supplier_controller import SupplierController
from controllers.customer_controller import CustomerController
from controllers.purchase_controller import PurchaseController
from controllers.payment_controller import PaymentController
from controllers.supplier_invoice_controller import SupplierInvoiceController
from controllers.supplier_receipt_controller import SupplierReceiptController

class App():
    def __init__(self):
        self.root = ctk.CTk()
        self.setup_window()
        self.setup_variables()
        self.login_window()

    def setup_window(self):
        view_config = settings['VIEW_CONFIG']
        self.root.title(view_config['window-title'])
        self.root.geometry(view_config['window-size'])
        self.root.resizable(False, False)
        self.root.withdraw()
        self.root.update_idletasks()
        
    def setup_variables(self):
        self.user_var = tk.StringVar()
        self.user_var.set('admin')
        
        self.pwd_var = tk.StringVar()
        self.pwd_var.set('admin')

    def login_window(self):
        self.login_win = ctk.CTkToplevel(self.root)
        self.login_win.title("Inicio de sesion")
        
        # Asociar la cruz al cierre de la app
        self.login_win.protocol("WM_DELETE_WINDOW", self.root.destroy)

        # Permitir usar Enter como boton
        self.login_win.bind("<Return>", lambda event: entry_btn.invoke())


        width_win = 300
        height_win = 160
        self.center_window(self.login_win, width_win, height_win)

        self.login_win.columnconfigure(0, weight=1)
        self.login_win.columnconfigure(1, weight=1)
        self.login_win.rowconfigure(0, weight=1)
        self.login_win.rowconfigure(1, weight=1)
        self.login_win.rowconfigure(2, weight=1)

        # usuario
        user_lbl = ctk.CTkLabel(self.login_win, text="USUARIO: ", font=ctk.CTkFont(size=15, weight="bold"))
        user_lbl.grid(row=0, column=0, pady=(15,1))

        user_entry = ctk.CTkEntry(self.login_win, textvariable=self.user_var)
        user_entry.grid(row=0, column=1, pady=(15,1))

        # password
        pwd_lbl = ctk.CTkLabel(self.login_win, text='CONTRASEÑA:', font=ctk.CTkFont(size=15, weight="bold"))
        pwd_lbl.grid(row=1, column=0)

        pwd_entry = ctk.CTkEntry(self.login_win, show='*', textvariable=self.pwd_var)
        pwd_entry.grid(row=1, column=1)

        entry_btn = ctk.CTkButton(self.login_win, text='Entrar', command=lambda: self.load_system(), font=ctk.CTkFont(size=15, weight="bold"))
        entry_btn.grid(row=2, column=0)

        cancel_btn = ctk.CTkButton(self.login_win, text="Cancelar", command=self.root.destroy, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#4CAF50", hover_color="#45a049")
        cancel_btn.grid(row=2, column=1)

    def load_system(self):
        if (validate_data(self.user_var.get(), self.pwd_var.get())):
                
            self.create_views_and_controllers()
            self.root.after(100, self.load_initial_data) 

            self.root.deiconify()
            self.root.update_idletasks()

            self.login_win.destroy() 

    def create_views_and_controllers(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # Event bus 
        event_bus = EventBus()
        
        # --- CONTROLLERS ---
        self.stock_controller = StockController(event_bus)
        self.sales_controller = SalesController()
        self.supplier_controller = SupplierController()
        self.customer_controller = CustomerController()

        self.purchase_controller = PurchaseController(event_bus)

        self.payment_controller = PaymentController()
        self.invoice_controller = SupplierInvoiceController()
        self.receipt_controller = SupplierReceiptController()

        ## -- VIEWS -- ##
        # --- START ---  
        self.start_view = StartView(self.notebook)
        self.notebook.add(self.start_view.frame, text='Inicio')

        # --- STOCK ---
        self.stock_view = StockView(self.notebook, controller=self.stock_controller)
        self.stock_controller.set_view(self.stock_view)

        self.stock_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.stock_view.frame, text='Inventario')

        # --- SALES ---
        self.sales_view = SalesView(self.notebook, controller=self.sales_controller)
        self.sales_controller.set_view(self.sales_view)

        self.sales_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.sales_view.frame, text='Venta')

        # --- SUPPLIERS ---
        self.supplier_view = SupplierView(self.notebook,self.supplier_controller, self.purchase_controller, 
            self.payment_controller, self.invoice_controller, self.receipt_controller)
        
        self.supplier_controller.set_view(self.supplier_view)
        self.supplier_controller.set_model(self.supplier_view.model)

        self.supplier_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.supplier_view.frame, text='Proveedores')

        # --- CUSTOMERS ---
        self.customers_view = CustomersView(self.notebook, controller=self.customer_controller)  
        self.customer_controller.set_view(self.customers_view)

        self.customers_view.attach_controller(self.customer_controller)
        self.customers_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.customers_view.frame, text='Clientes')

        # --- BACKUPS ---
        from views.backup_manager import BackupManagerView
        self.backup_view = BackupManagerView(self.notebook, controller=self.stock_controller)
        self.backup_view.frame.pack(fill='both', expand=True)
        self.notebook.add(self.backup_view.frame, text='Backups')

    def load_initial_data(self):
        try:
            self.stock_controller.load_products()
            self.supplier_controller.refresh_supplier_table()
            self.customer_controller.refresh_customer_data()
        except Exception as e:
            print(f"Error cargando datos iniciales: {e}")

    def center_window(self, win, width_win, height_win):
        win.update_idletasks()

        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        x = (screen_width // 2) - (width_win // 2)
        y = (screen_height // 2) - (height_win // 2)

        win.geometry(f"{width_win}x{height_win}+{x}+{y}")

    def run(self):
        self.root.mainloop()