from ctypes import wintypes
import platform
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from events import EventBus
from datetime import datetime
from config.settings import settings
from services.cloud_backup_service import CloudBackupService

from views.start_view import StartView
from views.stock_view import StockView
from views.sales_view import SalesView
from views.supplier_view import SupplierView
from views.supplier_info_view import SupplierInfoView
from views.customers_view import CustomersView
from views.reports_view import ReportsView
from views.checks_view import ChecksView
from views.cash_view import CashView

from models.company import CompanyModel
from models.customer import CustomerModel
from models.invoice import InvoiceModel
from models.iva import IVAModel
from models.payment_model import PaymentModel
from models.remito import RemitoModel
from models.sale import SalesModel
from models.supplier import SupplierModel
from models.stock import StockModel
from models.checks_model import ChecksModel
from models.cash_model import CashModel
#from models.user import User
from tkinter import messagebox
from controllers.auth_controller import validate_data
from controllers.invoice_controller import InvoiceController
from controllers.stock_controller import StockController
from controllers.sales_controller import SalesController
from controllers.supplier_controller import SupplierController
from controllers.customer_controller import CustomerController
from controllers.purchase_controller import PurchaseController
from controllers.payment_controller import PaymentController
from controllers.supplier_invoice_controller import SupplierInvoiceController
from controllers.supplier_receipt_controller import SupplierReceiptController
from controllers.iva_reports_controller import ReportsController
from controllers.checks_controller import ChecksController
from views.backup_manager import BackupManagerView
import sys, os
import ctypes 
from ctypes import wintypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class App():
    def __init__(self):
        self.root = ctk.CTk()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        if screen_width <= 1366 or screen_height <= 768:
            ctk.set_widget_scaling(0.85)
            ctk.set_window_scaling(0.85)

        self.setup_window()
        self.setup_variables()
        self.login_window()

    def setup_window(self):
        view_config = settings['VIEW_CONFIG']
        self.root.title(view_config['window-title'])

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.root.state('zoomed')  

        self.root.minsize(1000, 600)
        self.root.resizable(True, True)

        self.root.withdraw()

        # icono
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.join(base_path, '..')
        
        icon_path = os.path.join(base_path, 'assets', 'logo.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
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

        self.login_win.lift()
        self.login_win.focus_force()
        
    def load_system(self):
        if (validate_data(self.user_var.get(), self.pwd_var.get())):
                
            self.create_componentes()
            self.root.after(100, self.load_initial_data) 
            
            self.root.deiconify() 
            self.root.update_idletasks()

            self.login_win.destroy() 
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_componentes(self):
        self.notebook = ttk.Notebook(self.root)
        self.root.update_idletasks()
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.notebook.pack(fill='both', expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self.root.update() 

        # Event bus 
        event_bus = EventBus()

        ## -- MODELS -- ##
        invoice_model = InvoiceModel()
        iva_model = IVAModel()
        company_model = CompanyModel()
        sales_model = SalesModel()
        payment_model = PaymentModel(sales_model)
        customer_model = CustomerModel(payment_model)
        payment_model.customer_model = customer_model
        remito_model = RemitoModel()
        stock_model = StockModel(sales_model, payment_model, event_bus)
        supplier_model = SupplierModel(stock_model)
        checks_model = ChecksModel()   # ← crea tabla checks + migra check_id en payments
        cash_model = CashModel()

        ## --- CONTROLLERS --- ##
        self.stock_controller = StockController(
            stock_model, supplier_model, payment_model, event_bus
        )
        self.supplier_controller = SupplierController(supplier_model, event_bus)
        self.customer_controller = CustomerController(
            customer_model, payment_model, event_bus, checks_model=checks_model
        )
        self.checks_controller = ChecksController(checks_model, checks_model.db, event_bus=event_bus)
        self.iva_reports_controller = ReportsController(iva_model)

        self.purchase_controller = PurchaseController(supplier_model, stock_model, event_bus)
        self.payment_controller = PaymentController(supplier_model, event_bus, checks_model=checks_model)
        self.supplier_invoice_controller = SupplierInvoiceController(supplier_model)
        self.receipt_controller = SupplierReceiptController(supplier_model)
        self.invoice_controller = InvoiceController(invoice_model, customer_model, stock_model)
        self.sales_controller = SalesController(
            customer_model, remito_model, sales_model, stock_model, self.invoice_controller, event_bus
        )

        ## --- VIEWS --- ##
        # --- START ---  
        self.start_view = StartView(self.notebook, company_model)
        self.notebook.add(self.start_view.frame, text='Inicio')

        # --- STOCK ---
        self.stock_view = StockView(self.notebook, self.stock_controller, stock_model)
        self.stock_controller.set_view(self.stock_view)

        self.notebook.add(self.stock_view.frame, text='Inventario')

        # --- SALES ---
        self.sales_view = SalesView(
            self.notebook, self.sales_controller, stock_model, customer_model
        )
        self.sales_controller.set_view(self.sales_view)

        self.notebook.add(self.sales_view.frame, text='Venta')

        # --- SUPPLIERS ---
        self.supplier_view = SupplierView(
            self.notebook, self.supplier_controller, self.purchase_controller, 
            self.payment_controller, self.supplier_invoice_controller, self.receipt_controller,
            supplier_model, stock_model
        )
        
        self.supplier_info_view = SupplierInfoView(self.notebook, self.supplier_controller, supplier_model)

        self.supplier_controller.set_view(self.supplier_view)
        self.supplier_controller.set_info_view(self.supplier_info_view)

        self.notebook.add(self.supplier_view.frame, text='Proveedores')

        # --- CUSTOMERS ---
        self.customers_view = CustomersView(self.notebook, controller=self.customer_controller)  
        self.customer_controller.set_view(self.customers_view)
        self.customers_view.attach_controller(self.customer_controller)
        self.notebook.add(self.customers_view.frame, text='Clientes')

        # --- CHEQUES ---
        self.checks_view = ChecksView(self.notebook, self.checks_controller)
        self.checks_controller.set_view(self.checks_view)
        self.notebook.add(self.checks_view.frame, text='Cheques')

        self.cash_view = CashView(self.notebook, cash_model)
        self.notebook.add(self.cash_view.frame, text='Caja')

        # --- REPORTES ---
        self.reports_view = ReportsView(self.notebook, controller=self.iva_reports_controller)
        self.iva_reports_controller.set_view(self.reports_view)
        self.notebook.add(self.reports_view.frame, text='Reportes')

        # --- BACKUPS ---
        self.backup_view = BackupManagerView(self.notebook, controller=self.stock_controller)
        self.notebook.add(self.backup_view.frame, text='Backups')

        # Cargar mes actual automáticamente
        self.iva_reports_controller.load_period_reports(
            datetime.now().month,
            datetime.now().year
        )

    def on_tab_change(self, event):
        selected_tab = event.widget.tab(event.widget.select(), "text")

        if selected_tab == "Reportes":
            self.reports_view.load_reports()

        if selected_tab == "Venta":
            self.sales_view.load_available_products()


    def load_initial_data(self):
        try:
            self.stock_controller.load_products()
            self.supplier_controller.refresh_supplier_table()
            self.customer_controller.refresh_customer_data()
        except Exception as e:
            import traceback
            traceback.print_exc()
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

    
    def on_close(self):
        if messagebox.askyesno("Salir", "¿Desea cerrar el sistema?"):
            try:
                CloudBackupService().run()
            except Exception as e:
                print(f'Error en backup: {e}')
            finally:
                self.root.destroy()