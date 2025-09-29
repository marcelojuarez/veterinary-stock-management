from tkinter import messagebox
import customtkinter as ctk

class AddCustomerWindow:
    def __init__(self, parent, vars_dict, on_add_callback):
        self.vars = vars_dict
        self.on_add_callback = on_add_callback

        self.window = ctk.CTkToplevel(parent)
        self.window.title("Agregar Nuevo Cliente")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        self.window.configure(fg_color="white")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.focus_set()
        self.center_window(parent)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        parent.attributes('-disabled', True)

        self.create_widgets()

    def center_window(self, parent):
        self.window.update_idletasks()
        width, height = 500, 400
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def on_close(self):
        self.window.master.attributes('-disabled', False)
        self.window.destroy()

    def create_widgets(self):
        title_label = ctk.CTkLabel(
            self.window,
            text="Nuevo Cliente",
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color="#2c3e50"
        )
        title_label.pack(pady=20)

        form_frame = ctk.CTkFrame(self.window, corner_radius=12, fg_color="#f8f9fa")
        form_frame.pack(fill="both", expand=True, padx=30, pady=10)
        form_frame.columnconfigure(1, weight=1)

        labels = {
            "nombre": "Nombre:",
            "cuit": "CUIT:",
            "domicilio": "Domicilio:",
            "telefono": "Teléfono:"
        }

        self.entries = {}
        for idx, (key, label_text) in enumerate(labels.items()):
            label = ctk.CTkLabel(
                form_frame,
                text=label_text,
                font=("Segoe UI", 12, "bold"),
                text_color="#2c3e50",
                anchor="e"
            )
            label.grid(row=idx, column=0, padx=15, pady=12, sticky='e')

            entry = ctk.CTkEntry(
                form_frame,
                textvariable=self.vars[key],
                width=250,
                font=("Segoe UI", 12),
                fg_color="white",
                text_color="#2c3e50",
            )
            entry.grid(row=idx, column=1, padx=15, pady=12, sticky='ew')
            self.entries[key] = entry

        button_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=20)

        agregar_btn = ctk.CTkButton(
            button_frame,
            text="➕ Agregar Cliente",
            command=self.on_add_button_click,
            font=("Segoe UI", 14, "bold"),
            fg_color="#0d6efd",
            hover_color="#0b5ed7",
            text_color="white",
            height=40,
            corner_radius=8
        )
        agregar_btn.pack(side="left", expand=True, padx=10)

        cancelar_btn = ctk.CTkButton(
            button_frame,
            text="✖ Cancelar",
            command=self.on_close,
            font=("Segoe UI", 14),
            fg_color="#6c757d",
            hover_color="#5a6268",
            text_color="white",
            height=40,
            corner_radius=8
        )
        cancelar_btn.pack(side="left", expand=True, padx=10)

    def on_add_button_click(self):
        try:
            success = self.on_add_callback(self.window)
            if success:
                pass
        except Exception as e:
            messagebox.showerror("Error", str(e))

