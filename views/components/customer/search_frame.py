import customtkinter as ctk

class SearchFrame:
    def __init__(self, parent, on_search_callback, on_show_all_callback):
        self.parent = parent
        self.on_search_callback = on_search_callback
        self.on_show_all_callback = on_show_all_callback
        self.find_var = ctk.StringVar()
        self.create_widgets()
    
    def create_widgets(self):
        self.frame = ctk.CTkFrame(
            self.parent,
            corner_radius=12,
            fg_color="#f8f9fa",
            border_width=1,
            border_color="#e9ecef"
        )
        self.frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.frame.grid_columnconfigure(1, weight=1)

        search_icon = ctk.CTkLabel(
            self.frame,
            text="🔍",
            font=("Segoe UI", 14),
            text_color="#6c757d"
        )
        search_icon.grid(row=0, column=0, padx=(15, 5), pady=12)

        self.find_entry = ctk.CTkEntry(
            self.frame,
            textvariable=self.find_var,
            placeholder_text="Buscar por nombre, CUIT o domicilio...",
            placeholder_text_color="#adb5bd",
            fg_color="#ffffff",
            text_color="#2c3e50",
            border_width=1,
            border_color="#ced4da",
            corner_radius=8,
            height=38,
            font=("Segoe UI", 12)
        )
        self.find_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        find_btn = ctk.CTkButton(
            self.frame,
            text="Buscar",
            command=self.search_customer,
            width=90,
            fg_color="#3498db",
            hover_color="#2980b9",
            text_color="white",
            font=("Segoe UI", 12, "bold"),
            height=38,
            corner_radius=8
        )
        find_btn.grid(row=0, column=2, padx=5, pady=8)

        show_all_btn = ctk.CTkButton(
            self.frame,
            text="Ver Todos",
            command=self.show_all_customers,
            width=100,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            text_color="white",
            font=("Segoe UI", 12),
            height=38,
            corner_radius=8
        )
        show_all_btn.grid(row=0, column=3, padx=(5, 15), pady=8)
    
    def search_customer(self):
        self.on_search_callback(self.find_var.get())
    
    def show_all_customers(self):
        self.find_var.set("")
        self.on_show_all_callback()
    
    def get_search_term(self):
        return self.find_var.get()