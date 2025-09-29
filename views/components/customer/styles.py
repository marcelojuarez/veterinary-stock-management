import tkinter as tk
from tkinter import ttk

class StyleManager:
    @staticmethod
    def setup_styles():
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("MainDark.TFrame", background="#1E1E1E")
        
        style.configure("Modern.TLabel", 
                       background="#1E1E1E", 
                       font=("Segoe UI", 10),
                       foreground="#E0E0E0")
        
        style.configure("Modern.TButton",
                        font=("Segoe UI", 10, "bold"),
                        padding=(12, 6),
                        relief="flat",
                        background="#2D2D2D",
                        foreground="#FFFFFF")
        style.map("Modern.TButton",
                  background=[("active", "#007ACC"), ("pressed", "#005A9E")],
                  foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")])
        
        style.configure("Modern.TLabelframe",
                       background="#1E1E1E",
                       borderwidth=1,
                       relief="solid")
        style.configure("Modern.TLabelframe.Label",
                       background="#F0F0F0",
                       font=("Segoe UI", 9, "bold"),
                       foreground="#00BFFF")
        
        style.configure("Modern.Treeview",
                        background="#2D2D2D",
                        foreground="#E0E0E0",
                        rowheight=30,
                        fieldbackground="#2D2D2D",
                        borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Modern.Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background="#007ACC",
                        foreground="white",
                        relief="flat",
                        padding=(8, 6))
        style.map("Modern.Treeview",
                    background=[("selected", "#005A9E")],
                    foreground=[("selected", "#FFFFFF")])
        
        style.configure("Modern.TEntry",
                       fieldbackground="#2D2D2D",
                       foreground="#FFFFFF",
                       borderwidth=1,
                       relief="solid",
                       padding=(6, 4),
                       insertcolor="#FFFFFF")