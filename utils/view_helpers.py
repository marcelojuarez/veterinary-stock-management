import tkinter as tk
import logging
from tkinter import messagebox

logger = logging.getLogger(__name__)

def close_win( win, parent, callback=None):
    """Cierra la ventana y devuelve el foco al padre"""
    try:
        if callback:
            callback()

        win.destroy()
        parent.after(50, lambda: parent.focus_force())

    except Exception as e:
        logger.error("Error al cerrar la ventana: %s", e)
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


def add_treeview_tooltip(tree, col_index: int):
    """
    Muestra un tooltip con el texto completo de la celda indicada al hacer hover.
    col_index: índice de la columna (0-based) sobre la que se activa el tooltip.
    """
    _tip: list = [None]

    def _show(event):
        item = tree.identify_row(event.y)
        col  = tree.identify_column(event.x)
        if not item or not col:
            _hide()
            return
        if int(col.lstrip("#")) - 1 != col_index:
            _hide()
            return
        values = tree.item(item, "values")
        if not values or col_index >= len(values):
            _hide()
            return
        text = str(values[col_index])
        if not text:
            _hide()
            return
        _hide()
        tip = tk.Toplevel(tree)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{event.x_root + 14}+{event.y_root + 14}")
        lbl = tk.Label(
            tip, text=text, justify="left", wraplength=420,
            background="#fffde7", foreground="#333",
            relief="solid", borderwidth=1,
            font=("Segoe UI", 9),
            padx=6, pady=4,
        )
        lbl.pack()
        _tip[0] = tip

    def _hide(*_):
        if _tip[0]:
            try:
                _tip[0].destroy()
            except Exception:
                pass
            _tip[0] = None

    tree.bind("<Motion>", _show)
    tree.bind("<Leave>",  _hide)