from tkinter import ttk

def setup_styles():
    style = ttk.Style()

    # Colores y fuente global
    style.configure(".", font=("Segoe UI", 10))

    # LabelFrame
    style.configure("Modern.TLabelframe", background="#F0F0F0", foreground="#2C3E50")
    style.configure("Modern.TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#2C3E50")

    # Label
    style.configure("Modern.TLabel", background="#F0F0F0", foreground="#2C3E50")

    # Entry
    style.configure("Modern.TEntry", padding=5, relief="flat")

    # Button
    style.configure("Modern.TButton",
                    padding=(10, 5),
                    relief="flat",
                    background="#3498DB",
                    foreground="white")
    style.map("Modern.TButton",
              background=[("active", "#2980B9")])

    # Treeview
    style.configure("Custom.Treeview",
                    font=("Segoe UI", 10),
                    rowheight=28,
                    borderwidth=0,
                    relief="flat")
    style.configure("Custom.Treeview.Heading",
                    font=("Segoe UI", 10, "bold"),
                    padding=8)
    style.map("Custom.Treeview.Heading",
              background=[("active", "#3498DB")],
              foreground=[("active", "white")])

    # Scrollbar
    style.configure("Vertical.TScrollbar",
                    gripcount=0,
                    background="#BDC3C7",
                    troughcolor="#ECF0F1",
                    bordercolor="#BDC3C7",
                    arrowcolor="#2C3E50")
