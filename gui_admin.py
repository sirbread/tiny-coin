import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, scrolledtext
from core_logic import Coin, CryptoManager
import admin_password_util

class AdminPasswordDialog(simpledialog.Dialog):
    def __init__(self, parent, is_new):
        self.is_new = is_new
        super().__init__(parent, "admin login" if not is_new else "set admin password")
    def body(self, master):
        if self.is_new:
            tk.Label(master, text="set new admin password:").pack(pady=5)
            self.pw1_entry = tk.Entry(master, show='*')
            self.pw1_entry.pack(pady=2)
            tk.Label(master, text="confirm password:").pack(pady=5)
            self.pw2_entry = tk.Entry(master, show='*')
            self.pw2_entry.pack(pady=2)
            return self.pw1_entry
        else:
            tk.Label(master, text="enter admin password:").pack(pady=10)
            self.pw_entry = tk.Entry(master, show='*')
            self.pw_entry.pack(pady=5)
            return self.pw_entry
    def apply(self):
        if self.is_new:
            pw1 = self.pw1_entry.get()
            pw2 = self.pw2_entry.get()
            if pw1 != pw2 or len(pw1) < 4:
                self.result = None
            else:
                self.result = pw1
        else:
            self.result = self.pw_entry.get()

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
        self.loaded_coin = None
        self.loaded_file_path = None

        self.title("tinycoin admin panel")
        self.geometry("550x350")
        self._require_password()

        self.login_frame = tk.Frame(self)
        tk.Label(self.login_frame, text="welcome!", font=("Arial", 14)).pack(pady=20)
        tk.Button(self.login_frame, text="open and view a wallet", command=self.open_wallet).pack(pady=10, padx=10, fill=tk.X)
        tk.Button(self.login_frame, text="create new wallet", command=self.create_wallet).pack(pady=10, padx=10, fill=tk.X)

        self.wallet_frame = tk.Frame(self)
        self.balance_label = tk.Label(self.wallet_frame, text="", font=("Arial", 12, "bold"))
        self.balance_label.pack(pady=8)

        tk.Button(self.wallet_frame, text="modify balance", command=self.modify_wallet).pack(pady=4, padx=20, fill=tk.X)
        tk.Button(self.wallet_frame, text="close wallet", command=self.close_wallet).pack(pady=4, padx=20, fill=tk.X)

        self.log_frame = tk.Frame(self.wallet_frame)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        tk.Label(self.log_frame, text="wallet logs:").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=8, state="disabled", font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.show_login_view()

    def _require_password(self):
        pwd_file = admin_password_util.get_pwd_file_path()
        if not admin_password_util.password_file_exists():
            while True:
                dialog = AdminPasswordDialog(self, is_new=True)
                pw = dialog.result
                if not pw:
                    messagebox.showerror("error", "password not set or too short (minimum 4 chars). try again.")
                else:
                    admin_password_util.save_password(pw, pwd_file)
                    messagebox.showinfo("password saved", 
                        "the password has been saved to a hidden file in the same directory as this executable.\n"
                        "moving this executable resets the password. deleting the file allows a new password to be set. careful!")
                    break
        while True:
            dialog = AdminPasswordDialog(self, is_new=False)
            pw = dialog.result
            if pw and admin_password_util.check_password(pw, pwd_file):
                break
            messagebox.showerror("access denied", "invalid password. please try again.")

    def show_login_view(self):
        self.wallet_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.loaded_coin = None
        self.loaded_file_path = None

    def show_wallet_view(self):
        self.login_frame.pack_forget()
        self.wallet_frame.pack(fill="both", expand=True)
        self.display_wallet(self.loaded_coin)


    def display_wallet(self, coin):
        if not coin:
            self.balance_label.config(text="")
            self.update_logs([])
        else:
            self.balance_label.config(text=f"{coin.owner_name}: {coin.balance:.2f} coins")
            self.update_logs(coin.transaction_log)

    def update_logs(self, log_list):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        for entry in reversed(log_list[-30:]):
            self.log_text.insert(tk.END, entry + "\n")
        self.log_text.config(state="disabled")


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
            self.loaded_coin = coin
            self.loaded_file_path = file_path
            self.show_wallet_view()
        except Exception as e:
            messagebox.showerror("error", f"failed to create wallet: {e}")

    def open_wallet(self):
        file_path = filedialog.askopenfilename(title="select .coin file to open", filetypes=[("tinycoin files", "*.coin")])
        if not file_path:
            return
        coin = self.manager.read_coin_file(file_path)
        if not coin:
            messagebox.showerror("error", "could not read file. it may be corrupted.")
            return
        self.loaded_coin = coin
        self.loaded_file_path = file_path
        self.show_wallet_view()

    def modify_wallet(self):
        if not self.loaded_coin or not self.loaded_file_path:
            messagebox.showerror("error", "no wallet loaded.")
            return
        coin = self.loaded_coin

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
        self.manager.write_coin_file(self.loaded_file_path, coin)
        messagebox.showinfo("success", f"wallet updated successfully.\nnew balance: {coin.balance:.2f}")

        self.display_wallet(coin)

    def close_wallet(self):
        self.show_login_view()

if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
