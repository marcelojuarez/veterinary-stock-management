import tkinter as tk
from tkinter import messagebox

def close_win( win, parent, callback=None):
    """Cierra la ventana y devuelve el foco al padre"""
    try:
        if callback:
            callback()

        win.destroy()
        parent.after(50, lambda: parent.focus_force())

    except Exception as e:
        print(f"Error al cerrar la ventana: {e}")
        return

def center_window(win, width_win, height_win):
    win.update_idletasks()

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = (screen_width // 2) - (width_win // 2)
    y = (screen_height // 2) - (height_win // 2)

    win.geometry(f"{width_win}x{height_win}+{x}+{y}")

def show_error( message): messagebox.showerror("Error", message)

def show_success( message): messagebox.showinfo("Éxito", message)

def show_warning( message): messagebox.showwarning('Advertencia', message) 

def ask_confirmation( message, title):
    respuesta = messagebox.askokcancel(
        title,
        message
    )

    return respuesta