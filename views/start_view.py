from PIL import Image
import os

import customtkinter as ctk
import tkinter as tk
from models.company import CompanyModel

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class StartView:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, fg_color="gray58")
        self.frame.pack(fill="both", expand=True)
        self.model = CompanyModel()

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

        def add_field(row, label, widget):
            field_lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="black"
            )

            field_lbl.grid(row=row, column=0, sticky="e", padx=(10,10), pady=7)
            widget.grid(row=row, column=1, sticky="w", padx=(10,10), pady=7)

        add_field(0, "Empresa: ", ctk.CTkEntry(
            form_frame, textvariable=self.businesss_name_var, width=200, state='readonly')
        )
        
        add_field(1, "CUIT: ", ctk.CTkEntry(
            form_frame, textvariable=self.cuit_var, width=200, state='readonly')
        )

        add_field(2, "Condición IVA: ", ctk.CTkEntry(
            form_frame, textvariable=self.iva_condition_var, width=200, state='readonly')
        )

        add_field(3, "Inicio de Act.: ", ctk.CTkEntry(
            form_frame, textvariable=self.start_date_var, width=200, state='readonly')
        )

        add_field(4, "Domicilio: ", ctk.CTkEntry(
            form_frame, textvariable=self.address_var, width=200, state='readonly')
        )

        add_field(5, "Localidad: ", ctk.CTkEntry(
            form_frame, textvariable=self.city_var, width=200, state='readonly')
        )

        add_field(6, "Provincia: ", ctk.CTkEntry(
            form_frame, textvariable=self.province_var, width=200, state='readonly')
        )

        add_field(7, "Código Postal: ", ctk.CTkEntry(
            form_frame, textvariable=self.postal_code_var, width=200, state='readonly')
        )

        add_field(8, "Teléfono: ", ctk.CTkEntry(
            form_frame, textvariable=self.phone1_var, width=200, state='readonly')
        )

        add_field(9, "Teléfono: ", ctk.CTkEntry(
            form_frame, textvariable=self.phone2_var, width=200, state='readonly')
        )

        btn_frame = ctk.CTkFrame(card_frame, fg_color="white")
        btn_frame.pack(pady=20)

        self.btn_save = ctk.CTkButton(
            btn_frame, 
            text="Editar", 
            width=100, 
            font=ctk.CTkFont(size=13, weight='bold')
        )

        self.btn_save.grid(row=0, column=0, padx=15)

        self.btn_cancel = ctk.CTkButton(
            btn_frame, 
            text="Cancelar", 
            width=100,
            state='disabled',
            fg_color="gray", 
            font=ctk.CTkFont(size=13, weight='bold')
        )

        self.btn_cancel.grid(row=0, column=1, padx=15)
        
        # carga de datos
        self.load_company_data()

    def load_company_data(self):
        data = self.model.get_company_data()

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

        