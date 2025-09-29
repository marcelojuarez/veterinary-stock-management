import customtkinter as ctk
from tkinter import ttk

class CustomerTable:
    def __init__(self, parent, on_double_click_callback=None):
        self.parent = parent
        self.on_double_click_callback = on_double_click_callback
        self.create_widgets()

    def create_widgets(self):
        tree_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color="#f8f9fa")
        tree_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(2, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        tree_container = ctk.CTkFrame(tree_frame, corner_radius=8, fg_color="white")
        tree_container.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Custom.Treeview",
                        font=("Segoe UI", 11))       
        style.configure("Custom.Treeview.Heading",
                        font=("Segoe UI", 13, "bold"))

        self.tree = ttk.Treeview(
            tree_container,
            show='headings',
            height=18,
            style="Custom.Treeview"   
        )

        scrl_bar = ctk.CTkScrollbar(tree_container, orientation='vertical', command=self.tree.yview)
        scrl_bar.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrl_bar.set)

        self.tree['columns'] = ("Id", "Nombre", "Cuit", "Domicilio", "Telefono")

        column_configs = [
            ("Id", 60, False),
            ("Nombre", 200, True),
            ("Cuit", 120, False),
            ("Domicilio", 200, True),
            ("Telefono", 120, False)
        ]

        for col, width, stretch in column_configs:
            self.tree.column(col, anchor='w', width=width, stretch=stretch)
            self.tree.heading(col, text=col + " ↕")

        self.tree.grid(row=0, column=0, sticky='nsew')

        if self.on_double_click_callback:
            self.tree.bind("<Double-1>", self.on_double_click_callback)

    def refresh_data(self, customers):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, customer in enumerate(customers):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert('', 'end', iid=customer[0], values=customer, tags=(tag,))
        self.tree.tag_configure('evenrow', background='#ffffff')
        self.tree.tag_configure('oddrow', background='#f8f9fa')

    def get_selection(self):
        return self.tree.selection()

    def get_item_values(self, item_id):
        return self.tree.item(item_id)['values']

    def set_item_value(self, item_id, column, value):
        self.tree.set(item_id, column=column, value=value)

    def get_tree(self):
        return self.tree
