from PIL import Image
import os
import sys
import customtkinter as ctk
import tkinter as tk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class StartView:
    def __init__(self, parent, company_model):
        self.frame = ctk.CTkFrame(parent, fg_color="gray58")
        self.frame.pack(fill="both", expand=True)
        self.company_model = company_model
        self.editing = False
        self._backup = {}
        self.entries = {}

        self.create_background_logo()
        self.create_main_widget()

    def create_vars(self):

        self.businesss_name_var = tk.StringVar()
        self.cuit_var = tk.StringVar()
        self.iva_condition_var = tk.StringVar()
        self.start_date_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.province_var = tk.StringVar()
        self.postal_code_var = tk.StringVar()
        self.phone1_var = tk.StringVar()
        self.phone2_var = tk.StringVar()

    def create_background_logo(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))
        
        logo_path = os.path.join(base_path, "assets", "logo.png")

        image = Image.open(logo_path).convert("RGBA")
        image = image.resize((200, 200))

        alpha = 50  
        image.putalpha(alpha)

        self.logo_image = ctk.CTkImage(light_image=image, size=(400, 400))

        self.logo_label = ctk.CTkLabel(
            self.frame,
            image=self.logo_image,
            text=""
        )
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")
        
    def create_main_widget(self):

        self.create_vars()

        left_frame = ctk.CTkFrame(
            self.frame,
            width=500,
            fg_color='#fafaf0',
            corner_radius=12
        )
        left_frame.pack(side="left", padx=30, pady=30, anchor="n")

        card_frame = ctk.CTkFrame(
            left_frame,
            fg_color="white",
        )
        card_frame.pack(fill="both", expand=True)

        title_label = ctk.CTkLabel(
            card_frame,
            text="Datos Veterinaria",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="black"
        )
        title_label.pack(pady=20)

        # contenedor del formulario
        form_frame = ctk.CTkFrame(card_frame, fg_color="white")
        form_frame.pack(pady=5, padx=10, fill="x")

        row = 0

        def add_field(row, label, var_name, var):
            ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="black"
            ).grid(row=row, column=0, sticky="e", padx=(10,10), pady=7)

            entry = ctk.CTkEntry(form_frame, textvariable=var, width=200, state='readonly')
            entry.grid(row=row, column=1, sticky="w", padx=(10,10), pady=7)
            self.entries[var_name] = entry

        add_field(0, "Empresa: ",       "business_name",  self.businesss_name_var)
        add_field(1, "CUIT: ",          "cuit",           self.cuit_var)
        add_field(2, "Condición IVA: ", "iva_condition",  self.iva_condition_var)
        add_field(3, "Inicio de Act.: ","start_date",     self.start_date_var)
        add_field(4, "Domicilio: ",     "address",        self.address_var)
        add_field(5, "Localidad: ",     "city",           self.city_var)
        add_field(6, "Provincia: ",     "province",       self.province_var)
        add_field(7, "Código Postal: ", "postal_code",    self.postal_code_var)
        add_field(8, "Teléfono 1: ",    "phone1",         self.phone1_var)
        add_field(9, "Teléfono 2: ",    "phone2",         self.phone2_var)

        btn_frame = ctk.CTkFrame(card_frame, fg_color="white")
        btn_frame.pack(pady=20)

        self.btn_save = ctk.CTkButton(
            btn_frame, 
            text="Editar", 
            width=100, 
            font=ctk.CTkFont(size=13, weight='bold'),
            command=self.toggle_edit
        )

        self.btn_save.grid(row=0, column=0, padx=15)

        self.btn_cancel = ctk.CTkButton(
            btn_frame, 
            text="Cancelar", 
            width=100,
            state='disabled',
            fg_color="gray", 
            font=ctk.CTkFont(size=13, weight='bold'),
            command=self.cancel_edit
        )

        self.btn_cancel.grid(row=0, column=1, padx=15)
        
        # carga de datos
        self.load_company_data()

    def _save_changes(self):
        data = {
            'business_name': self.businesss_name_var.get(),
            'cuit': self.cuit_var.get(),
            'iva_condition': self.iva_condition_var.get(),
            'start_date': self.start_date_var.get(),
            'address': self.address_var.get(),
            'city': self.city_var.get(),
            'province': self.province_var.get(),
            'postal_code': self.postal_code_var.get(),
            'phone1': self.phone1_var.get(),
            'phone2': self.phone2_var.get(),
        }

        try:
            self.company_model.edit_company_data(data)
            self._finish_edit()
        except Exception as e:
            tk.messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def toggle_edit(self):
        if not self.editing:
            self.editing = True
            self._backup = {
                'business_name': self.businesss_name_var.get(),
                'cuit': self.cuit_var.get(),
                'iva_condition': self.iva_condition_var.get(),
                'start_date': self.start_date_var.get(),
                'address': self.address_var.get(),
                'city': self.city_var.get(),
                'province': self.province_var.get(),
                'postal_code': self.postal_code_var.get(),
                'phone1': self.phone1_var.get(),
                'phone2': self.phone2_var.get(),
            }
            self._set_fields_state('normal')
            self.btn_save.configure(text="Guardar", fg_color="#4CAF50", hover_color="#45a049")
            self.btn_cancel.configure(state="normal", fg_color="#757575")
        else:
            self._save_changes()
    
    def cancel_edit(self):
        self.businesss_name_var.set(self._backup['business_name'])
        self.cuit_var.set(self._backup['cuit'])
        self.iva_condition_var.set(self._backup['iva_condition'])
        self.start_date_var.set(self._backup['start_date'])
        self.address_var.set(self._backup['address'])
        self.city_var.set(self._backup['city'])
        self.province_var.set(self._backup['province'])
        self.postal_code_var.set(self._backup['postal_code'])
        self.phone1_var.set(self._backup['phone1'])
        self.phone2_var.set(self._backup['phone2'])
        self._finish_edit()

    def load_company_data(self):
        data = self.company_model.get_company_data()

        self.businesss_name_var.set(data[1])
        self.cuit_var.set(data[2])
        self.iva_condition_var.set(data[3])
        self.start_date_var.set(data[4])
        self.address_var.set(data[5])
        self.city_var.set(data[6])
        self.province_var.set(data[7])
        self.postal_code_var.set(data[8])
        self.phone1_var.set(data[9])
        self.phone2_var.set(data[10])

    def _finish_edit(self):
        self.editing = False
        self._set_fields_state('readonly')
        self.btn_save.configure(text="Editar", fg_color="#3B8ED0", hover_color="#36719F")
        self.btn_cancel.configure(state="disabled", fg_color="gray")

    def _set_fields_state(self, state: str):
        for entry in self.entries.values():
            entry.configure(state=state)
        