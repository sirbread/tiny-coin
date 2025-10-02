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

class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.manager = CryptoManager()
        self.title("tinycoin admin panel")
        self.geometry("350x150")

        tk.Label(self, text="select an action.", pady=10).pack()
        tk.Button(self, text="create new wallet", command=self.create_wallet).pack(pady=5, padx=20, fill=tk.X)
        tk.Button(self, text="modify existing wallet", command=self.modify_wallet).pack(pady=5, padx=20, fill=tk.X)

    def create_wallet(self):
        owner_name = simpledialog.askstring("new wallet", "enter new sibling's name:")
        if not owner_name: return

        child_password = simpledialog.askstring("new wallet", f"enter a password for {owner_name}:", show='*')
        if not child_password: return
        
        try:
            initial_balance = simpledialog.askfloat("new wallet", "enter initial balance (e.g., 10.0):")
            if initial_balance is None: return

            coin = Coin(owner_name, child_password, initial_balance)
            file_path = filedialog.asksaveasfilename(
                defaultextension=".coin", initialfile=f"{owner_name.lower().replace(' ', '_')}.coin",
                filetypes=[("tinycoin files", "*.coin")]
            )
            if not file_path: return

            self.manager.write_coin_file(file_path, coin)
            messagebox.showinfo("done", f"wallet created for {owner_name} at '{file_path}'.")
        except Exception as e:
            messagebox.showerror("error", f"failed to create wallet: {e}")

    def modify_wallet(self):
        file_path =filedialog.askopenfilename(title="select .coin file to modify", filetypes=[("tinycoin files", "*.coin")])
        if not file_path: return


        if not file_path: return

        coin = self.manager.read_coin_file(file_path)
        if not coin:
            messagebox.showerror("error", "could not read file. it may be corrupted.")
            return
        
        dialog = ModifyBalanceDialog(self, f"modify {coin.owner_name}'s wallet", coin.balance)
        if dialog.result is None: return 

        action, amount = dialog.result
        log_entry = ""
        if action == "adjust":
            coin.balance += amount
            log_entry = f"[admin] adjustment of {amount:+.2f}. new balance: {coin.balance:.2f}"
        elif action == "set":
            coin.balance = amount
            log_entry = f"[admin] set balance to {amount:.2f}."
        
        coin.add_transaction(log_entry)
        self.manager.write_coin_file(file_path, coin)
        messagebox.showinfo("success", f"wallet updated successfully.\nnew balance: {coin.balance:.2f}")


if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
