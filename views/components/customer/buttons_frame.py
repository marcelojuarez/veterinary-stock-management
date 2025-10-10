import customtkinter as ctk

class ButtonsFrame:
    def __init__(self, parent, on_add_callback, on_update_debt_callback, 
                 on_delete_callback, on_clear_callback):
        self.parent = parent
        self.on_add_callback = on_add_callback
        self.on_update_debt_callback = on_update_debt_callback
        self.on_delete_callback = on_delete_callback
        self.on_clear_callback = on_clear_callback
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal con fondo claro
        self.frame = ctk.CTkFrame(
            self.parent,
            corner_radius=12,
            fg_color="#f8f9fa",
            border_width=1,
            border_color="#e0e0e0"
        )
        self.frame.grid(row=3, column=0, sticky='ew', padx=10, pady=10)

        # Configurar columnas
        for i in range(3):
            self.frame.columnconfigure(i, weight=1)

        # Botones con colores suaves
        button_configs = [
            ("➕ Agregar", self.on_add_callback, "#0d6efd", "#0b5ed7"),         # Azul
            ("💰 Actualizar Deuda", self.on_update_debt_callback, "#0d6efd", "#0d6efd"),  # Verde
            ("🗑️ Borrar", self.on_delete_callback, "#0d6efd", "#0d6efd"),       # Rojo
        ]

        for idx, (text, cmd, fg, hover) in enumerate(button_configs):
            btn = ctk.CTkButton(
                self.frame,
                text=text,
                command=cmd,
                fg_color=fg,
                hover_color=hover,
                text_color="white",
                font=("Segoe UI", 12, "bold"),
                height=40,
                corner_radius=8
            )
            btn.grid(row=0, column=idx, padx=5, pady=5)

    def get_frame(self):
        return self.frame
