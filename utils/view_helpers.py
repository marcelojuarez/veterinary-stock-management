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

def center_window(window, width, height):
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()

    # que no sea más grande que la pantalla
    width  = min(width,  screen_w - 50)
    height = min(height, screen_h - 50)

    x = (screen_w - width)  // 2
    y = (screen_h - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def show_error( message): messagebox.showerror("Error", message)

def show_success( message): messagebox.showinfo("Éxito", message)

def show_warning( message): messagebox.showwarning('Advertencia', message) 

def ask_confirmation( message, title):
    respuesta = messagebox.askokcancel(
        title,
        message
    )

    return respuesta