import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, scrolledtext
from core_logic import Coin, CryptoManager
import admin_password_util
import time

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

class AdminChangePasswordDialog(simpledialog.Dialog):
    def __init__(self, parent, owner_name):
        self.owner_name = owner_name
        super().__init__(parent, f"reset password for {owner_name}")

    def body(self, master):
        tk.Label(master, text="new password:").grid(row=0, sticky="w")
        self.new_pw1_entry = tk.Entry(master, show='*')
        self.new_pw1_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(master, text="confirm new password:").grid(row=1, sticky="w")
        self.new_pw2_entry = tk.Entry(master, show='*')
        self.new_pw2_entry.grid(row=1, column=1, padx=5, pady=2)

        return self.new_pw1_entry

    def apply(self):
        self.result = (
            self.new_pw1_entry.get(),
            self.new_pw2_entry.get()
        )


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
        self.failed_attempts = 0
        self.lockout_duration = 15 * 60 #15 mins adjust if needed
        self.max_failed_attempts = 5
        self.is_destroyed_by_logic = False

        self.title("tinycoin admin panel")
        self.geometry("550x350")

        self.withdraw()

        if not self._require_password():
            self.is_destroyed_by_logic = True
            self.destroy()
            return

        self.deiconify()

        self.login_frame = tk.Frame(self)
        tk.Label(self.login_frame, text="welcome!", font=("Arial", 14)).pack(pady=20)
        tk.Button(self.login_frame, text="open and view a wallet", command=self.open_wallet).pack(pady=10, padx=10, fill=tk.X)
        tk.Button(self.login_frame, text="create new wallet", command=self.create_wallet).pack(pady=10, padx=10, fill=tk.X)

        self.wallet_frame = tk.Frame(self)
        self.balance_label = tk.Label(self.wallet_frame, text="", font=("Arial", 12, "bold"))
        self.balance_label.pack(pady=8)

        tk.Button(self.wallet_frame, text="modify balance", command=self.modify_wallet).pack(pady=4, padx=20, fill=tk.X)
        tk.Button(self.wallet_frame, text="change wallet password", command=self.admin_change_password).pack(pady=4, padx=20, fill=tk.X)
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
        
        lockout_time = admin_password_util.get_lockout_time()
        if lockout_time:
            remaining_time = int(self.lockout_duration - (time.time() - lockout_time))
            if remaining_time > 0:
                minutes, seconds = divmod(remaining_time, 60)
                messagebox.showerror("locked out", f"too many failed attempts. please wait {minutes}m {seconds}s.")
                return False
            else:
                admin_password_util.clear_lockout()

        while True:
            dialog = AdminPasswordDialog(self, is_new=False)
            pw = dialog.result
            if pw and admin_password_util.check_password(pw, pwd_file):
                self.failed_attempts = 0
                admin_password_util.clear_lockout()
                return True

            self.failed_attempts += 1
            remaining_attempts = self.max_failed_attempts - self.failed_attempts

            if self.failed_attempts >= self.max_failed_attempts:
                admin_password_util.set_lockout()
                messagebox.showerror("access denied", "too many failed attempts. the application will now close. please wait 15 minutes.")
                return False
            elif pw is None:
                return False
            else:
                 messagebox.showerror("access denied", f"invalid password. {remaining_attempts} attempts remaining.")

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

    def admin_change_password(self):
        if not self.loaded_coin: return

        dialog = AdminChangePasswordDialog(self, self.loaded_coin.owner_name)
        if not dialog.result: return

        new_pw1, new_pw2 = dialog.result

        if len(new_pw1) < 4:
            messagebox.showerror("error", "new password must be at least 4 characters long.", parent=self)
            return

        if new_pw1 != new_pw2:
            messagebox.showerror("error", "new passwords do not match.", parent=self)
            return

        self.loaded_coin.update_password(new_pw1)
        self.loaded_coin.add_transaction("[admin] password was reset by admin.")
        self.manager.write_coin_file(self.loaded_file_path, self.loaded_coin)
        self.update_logs(self.loaded_coin.transaction_log)
        messagebox.showinfo("success", f"password for {self.loaded_coin.owner_name} has been reset.")


    def close_wallet(self):
        self.show_login_view()

if __name__ == "__main__":
    app = AdminApp()
    if not app.is_destroyed_by_logic:
        app.mainloop()
