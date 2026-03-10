# -*- coding: utf-8 -*-
"""
Vista de gestión de backups
Permite crear, restaurar y configurar backups desde la interfaz
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from services.backup_service import get_backup_service
import shutil
import logging
from pathlib import Path
from views.stock_view import StockView
from utils.view_helpers import center_window
from services.cloud_backup_service import CloudBackupService

class BackupManagerView(ctk.CTkFrame):
    """Vista para gestionar backups de la base de datos"""

    def __init__(self, parent, controller):
        self.frame = ctk.CTkFrame(parent)
        self.backup_service = get_backup_service()
        self.cloud_service = CloudBackupService()
        super().__init__(parent)
        self.controller = controller

        self.create_widgets()
        self.refresh_data()
        self.auto_refresh()

    # ======================================================
    # UI
    # ======================================================

    def create_widgets(self):
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.create_status_panel()
        self.create_backups_table()
        self.create_actions_panel()

    def create_header(self):
        header = ctk.CTkFrame(self.frame)
        header.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        title = ctk.CTkLabel(
            header,
            text="🧾 Gestión de Backups",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        title.grid(row=0, column=0, padx=(15, 10), pady=8, sticky="w")

        refresh_btn = ctk.CTkButton(
            header,
            text="Actualizar",
            width=120,
            height=35,
            fg_color="#009688",
            hover_color="#00796B",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.refresh_data
        )
        refresh_btn.grid(row=0, column=1, padx=10)

    def create_status_panel(self):
        status_frame = ctk.CTkFrame(self.frame)
        status_frame.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.status_vars = {
            'auto_backup': tk.StringVar(value="Estado: -"),
            'total_backups': tk.StringVar(value="Total: -"),
            'last_backup': tk.StringVar(value="Último: -"),
            'db_size': tk.StringVar(value="BD: -")
        }

        labels = [
            ("Backup automático:", self.status_vars['auto_backup']),
            ("Total backups:", self.status_vars['total_backups']),
            ("Último backup:", self.status_vars['last_backup']),
            ("Tamaño BD:", self.status_vars['db_size'])
        ]

        for i, (text, var) in enumerate(labels):
            ctk.CTkLabel(
                status_frame,
                text=text,
                font=ctk.CTkFont(size=13, weight="bold")
            ).grid(row=0, column=i * 2, padx=8, pady=10, sticky="w")

            ctk.CTkLabel(
                status_frame,
                textvariable=var,
                font=ctk.CTkFont(size=13)
            ).grid(row=0, column=i * 2 + 1, padx=5, pady=10, sticky="w")

    def create_backups_table(self):
        table_frame = ctk.CTkFrame(self.frame)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            table_frame,
            text="Backups disponibles",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, pady=(10, 5))

        container = tk.Frame(table_frame, bg="white")
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=20, font=("Segoe UI", 8))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        self.backups_tree = ttk.Treeview(
            container,
            show="headings",
            columns=("Nombre", "Fecha", "Tamaño", "Tipo"),
        )

        for col, w in {
            "Nombre": 320,
            "Fecha": 200,
            "Tamaño": 100,
            "Tipo": 100
        }.items():
            self.backups_tree.column(col, width=w, anchor=tk.CENTER)
            self.backups_tree.heading(col, text=col, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.backups_tree.yview
        )
        self.backups_tree.configure(yscrollcommand=scrollbar.set)

        self.backups_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.backups_tree.bind("<Double-Button-1>", lambda e: self.show_backup_details())

    def create_actions_panel(self):
        actions = ctk.CTkFrame(self.frame)
        actions.grid(row=3, column=0, sticky="ew", padx=10, pady=15)

        for i in range(13):
            actions.grid_columnconfigure(i, weight=1 if i % 2 == 0 else 0)

        buttons = [
            ("Crear backup",    self.create_manual_backup),
            ("☁️ Subir a drive", self.upload_to_drive),      # <- nuevo
            ("Restaurar",       self.restore_selected_backup),
            ("Eliminar",        self.delete_selected_backup),
            ("Exportar",        self.export_backup),
            ("Configuración",   self.open_config_window)
        ]

        for i, (text, cmd) in enumerate(buttons):
            ctk.CTkButton(
                actions,
                text=text,
                width=200,
                height=40,
                fg_color="#009688",
                hover_color="#00796B",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=cmd
            ).grid(row=0, column=i * 2 + 1, padx=8, pady=10)


    # ======================================================
    # LOGIC
    # ======================================================

    def refresh_data(self):
        try:
            status = self.backup_service.get_status()

            auto = "Activo ✓" if status.get("is_running") else "Inactivo ✗"
            self.status_vars["auto_backup"].set(auto)
            self.status_vars["total_backups"].set(status.get("total_backups", 0))

            last = status.get("last_backup")
            self.status_vars["last_backup"].set(last["date"] if last else "Nunca")

            self.status_vars["db_size"].set(f"{status.get('db_size_mb', 0):.2f} MB")

            self.refresh_backups_table()

        except Exception as e:
            messagebox.showerror("Error", f"Error actualizando datos:\n{e}")

    def refresh_backups_table(self):
        self.backups_tree.delete(*self.backups_tree.get_children())

        backups = self.backup_service.list_backups()
        for b in backups:
            name = b["name"]
            date = b["date"]
            size = f"{b['size_mb']:.2f} MB"

            if "manual" in name:
                tipo = "Manual"
            elif "auto" in name:
                tipo = "Auto"
            elif "daily" in name:
                tipo = "Diario"
            elif "weekly" in name:
                tipo = "Semanal"
            else:
                tipo = "Otro"

            self.backups_tree.insert("", "end", values=(name, date, size, tipo))

    def create_manual_backup(self):
        if not messagebox.askyesno(
            "Crear Backup",
            "¿Desea crear un backup manual?\n\nEsto puede tardar unos segundos."
        ):
            return

        backup = self.backup_service.create_backup("manual")
        if backup:
            messagebox.showinfo("Éxito", f"Backup creado:\n{backup.name}")
            self.refresh_data()
        else:
            messagebox.showerror("Error", "No se pudo crear el backup")

    def restore_selected_backup(self):
        selected = self.backups_tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un backup")
            return

        name = self.backups_tree.item(selected[0])["values"][0]
        path = self.backup_service.backup_dir / name

        if not messagebox.askyesno(
            "ADVERTENCIA",
            f"Restaurar backup:\n\n{name}\n\nEsto reemplazará la base actual."
        ):
            return

        if self.backup_service.restore_backup(path):
            messagebox.showinfo("Éxito", "Base restaurada correctamente")
            self.refresh_data()
            self.controller.refresh_stock_table()
        else:
            messagebox.showerror("Error", "No se pudo restaurar el backup")

    def delete_selected_backup(self):
        selected = self.backups_tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un backup")
            return

        name = self.backups_tree.item(selected[0])["values"][0]
        path = self.backup_service.backup_dir / name

        if messagebox.askyesno("Eliminar", f"¿Eliminar backup?\n\n{name}"):
            path.unlink()
            self.refresh_data()

    def export_backup(self):
        selected = self.backups_tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un backup")
            return

        name = self.backups_tree.item(selected[0])["values"][0]
        src = self.backup_service.backup_dir / name

        dest = filedialog.asksaveasfilename(
            title="Exportar Backup",
            initialfile=name,
            defaultextension=src.suffix
        )

        if dest:
            shutil.copy2(src, dest)
            messagebox.showinfo("Éxito", "Backup exportado correctamente")

    def show_backup_details(self):
        selected = self.backups_tree.selection()
        if not selected:
            return

        name, date, size, tipo = self.backups_tree.item(selected[0])["values"]
        path = self.backup_service.backup_dir / name

        valid = self.backup_service.verify_database_integrity(path)

        messagebox.showinfo(
            "Detalles del Backup",
            f"Nombre: {name}\nFecha: {date}\nTamaño: {size}\nTipo: {tipo}\n"
            f"Ruta: {path}\nIntegridad: {'OK' if valid else 'Corrupto'}"
        )

    def open_config_window(self):
        win = ctk.CTkToplevel(self.frame)
        win.title("Configuración de Backups")
        win.configure(fg_color="#e0e0e0")
        win.grab_set()
        center_window(win, 520, 420)

        config = self.backup_service.config

        auto_var = tk.BooleanVar(value=config.get("auto_backup_enabled", True))
        interval_var = tk.StringVar(value=str(config.get("backup_interval_minutes", 30)))
        max_var = tk.StringVar(value=str(config.get("max_backups", 50)))
        retention_var = tk.StringVar(value=str(config.get("retention_days", 30)))
        compress_var = tk.BooleanVar(value=config.get("compress_backups", True))

        # Card blanca igual que agregar clientes
        card_frame = ctk.CTkFrame(win, fg_color="white", corner_radius=20)
        card_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card_frame,
            text="Configuración de Backups",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))

        # Form frame igual que agregar clientes
        form_frame = ctk.CTkFrame(card_frame, fg_color="#f9f9f9", corner_radius=10)
        form_frame.pack(pady=10, padx=20, fill="x")

        def add_field(row, label, widget):
            ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="black"
            ).grid(row=row, column=0, sticky="e", padx=(10, 10), pady=7)
            widget.grid(row=row, column=1, sticky="w", padx=(10, 10), pady=7)

        add_field(0, "Intervalo (min):", ctk.CTkEntry(form_frame, textvariable=interval_var, width=200))
        add_field(1, "Máx backups:",     ctk.CTkEntry(form_frame, textvariable=max_var, width=200))
        add_field(2, "Días retención:",  ctk.CTkEntry(form_frame, textvariable=retention_var, width=200))
        add_field(3, "Backup automático:", ctk.CTkCheckBox(form_frame, text="", variable=auto_var))
        add_field(4, "Comprimir backups:", ctk.CTkCheckBox(form_frame, text="", variable=compress_var))

        # Botones igual que agregar clientes
        btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        def save():
            try:
                self.backup_service.save_config({
                    "auto_backup_enabled": auto_var.get(),
                    "backup_interval_minutes": int(interval_var.get()),
                    "max_backups": int(max_var.get()),
                    "retention_days": int(retention_var.get()),
                    "compress_backups": compress_var.get()
                })
                messagebox.showinfo("Éxito", "Configuración guardada")
                win.destroy()
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(
            btn_frame, text="Guardar", width=150, height=40,
            fg_color="#009688", hover_color="#00796B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=save
        ).grid(row=0, column=0, padx=15)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=150, height=40,
            fg_color="#E74C3C", hover_color="#C0392B",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=win.destroy
        ).grid(row=0, column=1, padx=15)

    def auto_refresh(self):
        self.refresh_data()
        self.frame.after(30000, self.auto_refresh)

    def upload_to_drive(self):
        if not messagebox.askyesno(
            "Subir a Drive",
            "¿Subir un backup a Google Drive?\n\n"
            "La primera vez abrirá el navegador para autorizar el acceso."
        ):
            return
        try:
            name = self.cloud_service.run()
            messagebox.showinfo("Éxito", f"Backup subido a Google Drive:\n{name}")
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo subir el backup:\n{e}")
