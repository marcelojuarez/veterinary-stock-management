import tkinter as tk
from tkinter import messagebox

def close_win( win, parent):
    """Cierra la ventana y devuelve el foco al padre"""
    try:
        win.destroy()
        parent.after(50, lambda: parent.focus_force())

    except Exception as e:
        print(f"Error al cerrar la ventana: {e}")
        return

def show_error( message): messagebox.showerror("Error", message)

def show_success( message): messagebox.showinfo("Éxito", message)

def show_warning( message): messagebox.showwarning('Advertencia', message) 

def ask_confirmation( message, title):
    respuesta = messagebox.askokcancel(
        title,
        message
    )

    return respuesta