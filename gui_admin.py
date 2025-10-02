import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from core_logic import Coin, CryptoManager

class ModifyBalanceDialog(simpledialog.Dialog):
    def __init__(self, parent, title, current_balance):
        self.current_balance = current_balance
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text=f"current balance: {self.current_balance:.2f}").grid(row=0, columnspan=2)

        tk.Label(master, text="adjustment (+/-):").grid(row=1, sticky="w")
        self.adj_entry = tk.Entry(master)
        self.adj_entry.grid(row=1, column=1)

        tk.Label(master, text="OR set to amount:").grid(row=2, sticky="w")
        self.set_entry = tk.Entry(master)
        self.set_entry.grid(row=2, column=1)
        
        return self.adj_entry
    def apply(self):
        adj_val = self.adj_entry.get()
        set_val = self.set_entry.get()

        try:
            if adj_val and set_val:
                messagebox.showwarning("error", "please use either adjustment OR set, not both.", parent=self)
                return
            if adj_val:
                amount = float(adj_val)
                self.result = ("adjust", amount)
            elif set_val:
                amount = float(set_val)
                self.result = ("set", amount)
        except ValueError:
            messagebox.showwarning("error", "please enter a valid number.", parent=self)


if __name__ == "__main__":
    #app = AdminApp()
    #app.mainloop()
