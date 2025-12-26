import customtkinter as ctk
from tkinter import ttk
import tkinter as tk

class ClientSelectorDialog:
    """Diálogo mejorado para selección de clientes con búsqueda"""
    
    def __init__(self, parent, customer_model, current_client=""):
        
        self.customer_model = customer_model
        self.selected_client = None
        self.current_client = current_client
        
        # Crear ventana
        self.dialog = ctk.CTkToplevel(parent)
        # se oculta la ventana
        self.dialog.withdraw() 
        
        self.dialog.title("Seleccionar Cliente")
        #parent.update_idletasks()

        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Centrar ventana
        x = (parent.winfo_screenwidth() // 2) - 300
        y = (parent.winfo_screenheight() // 2) - 250
        self.dialog.geometry(f"600x600+{x}+{y}")
        
        self.create_ui()
        self.load_clients()

        self.dialog.update_idletasks()
        self.dialog.deiconify()
        
    def create_ui(self):
        # Header
        header = ctk.CTkFrame(self.dialog)
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text="👤 Seleccionar Cliente",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        # Búsqueda
        search_frame = ctk.CTkFrame(self.dialog)
        search_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            search_frame,
            text="Buscar:",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(5, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_clients())
        
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Escribe para buscar cliente...",
            height=35
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        search_entry.focus()
        
        clear_btn = ctk.CTkButton(
            search_frame,
            text="✕",
            width=35,
            height=35,
            fg_color="#757575",
            hover_color="#616161",
            command=lambda: self.search_var.set("")
        )
        clear_btn.pack(side="left", padx=5)
        
        # Tabla de clientes
        table_frame = ctk.CTkFrame(self.dialog)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.clients_tree = ttk.Treeview(
            table_frame,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        self.clients_tree["columns"] = ("Nombre", "CUIT/DNI", "Dirección")
        
        widths = [200, 120, 230]
        for col, w in zip(self.clients_tree["columns"], widths):
            self.clients_tree.column(col, width=w, anchor="w" if col == "Nombre" or col == "Dirección" else "center")
            self.clients_tree.heading(col, text=col)
        
        self.clients_tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.clients_tree.yview)
        
        # Doble clic para seleccionar
        self.clients_tree.bind("<Double-Button-1>", lambda e: self.select_client())
        self.clients_tree.bind("<Return>", lambda e: self.select_client())
        
        # Contador
        self.count_label = ctk.CTkLabel(
            self.dialog,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        self.count_label.pack(pady=(0, 5))
        
        # Botones
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(pady=15)
        
        ctk.CTkButton(
            button_frame,
            text="✓ Seleccionar",
            width=140,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=self.select_client
        ).grid(row=0, column=0, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Consumidor Final",
            width=160,
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color="#009688",
            hover_color="#00796B",
            command=self.select_consumidor_final
        ).grid(row=0, column=1, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancelar",
            width=120,
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color="#757575",
            hover_color="#616161",
            command=self.dialog.destroy
        ).grid(row=0, column=2, padx=5)
    
    def load_clients(self):
        """Cargar todos los clientes desde la base de datos"""
        # get_all_customers() retorna: id, nombre, cuit, domicilio, telefono
        all_customers = self.customer_model.get_all_customers()
        
        self.all_clients = []
        for customer in all_customers:
            # customer es una tupla: (id, nombre, cuit, domicilio, telefono)
            self.all_clients.append({
                "id": customer[0],
                "nombre": customer[1] if customer[1] else "",
                "cuit": customer[2] if customer[2] else "",
                "domicilio": customer[3] if customer[3] else "",
                "telefono": customer[4] if len(customer) > 4 and customer[4] else ""
            })
        
        self.filter_clients()
    
    def filter_clients(self):
        """Filtrar clientes según búsqueda"""
        search_text = self.search_var.get().lower()
        
        # Limpiar tabla
        self.clients_tree.delete(*self.clients_tree.get_children())
        
        # Filtrar y agregar
        count = 0
        for client in self.all_clients:
            name = client.get("nombre", "")
            cuit = client.get("cuit", "")
            address = client.get("domicilio", "")
            
            # Filtro
            if (search_text in name.lower() or 
                search_text in cuit.lower() or 
                search_text in address.lower()):
                
                self.clients_tree.insert("", "end", values=(name, cuit, address))
                count += 1
                
                # Seleccionar el cliente actual
                if name == self.current_client:
                    items = self.clients_tree.get_children()
                    if items:
                        self.clients_tree.selection_set(items[-1])
                        self.clients_tree.see(items[-1])
        
        # Actualizar contador
        self.count_label.configure(text=f"Mostrando {count} de {len(self.all_clients)} clientes")
    
    def select_client(self):
        """Seleccionar cliente de la tabla"""
        selection = self.clients_tree.selection()
        if not selection:
            return
        
        item = self.clients_tree.item(selection[0])
        self.selected_client = item["values"][0]  # Nombre del cliente
        self.dialog.destroy()
    
    def select_consumidor_final(self):
        """Seleccionar consumidor final"""
        self.selected_client = "Consumidor Final"
        self.dialog.destroy()
    
    def get_selected(self):
        """Obtener cliente seleccionado"""
        self.dialog.wait_window()
        return self.selected_client
