import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from core_logic import CryptoManager, perform_transfer

class ChildApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.manager = CryptoManager()
        self.current_coin_obj = None
        self.current_file_path = None
        #hyphen or not
        self.title("tinycoin")
        self.geometry("350x200")
        self.login_frame = tk.Frame(self)
        self.wallet_frame = tk.Frame(self)
        self._create_login_widgets()
        self._create_wallet_widgets()
        self.show_login_view() 

    def _create_login_widgets(self):
        tk.Label(self.login_frame, text="welcome!", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.login_frame, text="open your wallet", command=self.login).pack(pady=10, padx=40, ipady=10, fill=tk.X)

    def _create_wallet_widgets(self):
        self.welcome_label = tk.Label(self.wallet_frame, text="", font=("Arial", 14))
        self.welcome_label.pack(pady=10)
        self.balance_label = tk.Label(self.wallet_frame, text="", font=("Arial", 18, "bold"))
        self.balance_label.pack(pady=5)
        tk.Button(self.wallet_frame, text="transfer coins", command=self.transfer_coins).pack(pady=10, padx=40, fill=tk.X)
        tk.Button(self.wallet_frame, text="log out", command=self.logout).pack(pady=5, padx=40, fill=tk.X)

    def show_login_view(self):
        self.wallet_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_wallet_view(self):
        self.login_frame.pack_forget()
        self.wallet_frame.pack(fill="both", expand=True)
        self.update_wallet_display()

    def update_wallet_display(self):
        if self.current_coin_obj:
            self.welcome_label.config(text=f"welcome, {self.current_coin_obj.owner_name}!")
            self.balance_label.config(text=f"{self.current_coin_obj.balance:.2f} coins")

    def login(self):
        file_path = filedialog.askopenfilename(title="select your .coin file", filetypes=[("tinycoin files", "*.coin")])
        if not file_path: return
        password = simpledialog.askstring("password", "enter your password:", show='*')
        if not password: return
        coin = self.manager.read_coin_file(file_path)
        if coin and coin.verify_child_password(password):
            self.current_coin_obj = coin
            self.current_file_path = file_path
            self.show_wallet_view()
        else:
            messagebox.showerror("login failed", "wallet coundn't be opened, check your password.")

    def logout(self):
        self.current_coin_obj = None
        self.current_file_path = None
        self.show_login_view()

#child
    def transfer_coins(self):
        sender_coin = self.current_coin_obj
        messagebox.showinfo("to recipient", "ask the person you're transferring TO to select THEIR wallet file.")
        recipient_path = filedialog.askopenfilename(title="select RECIPIENT's .coin file", filetypes=[("tinycoin files", "*.coin")])
        if not recipient_path: return
        recipient_pass = simpledialog.askstring("recipient's password", "ask the person you're transferring TO to enter THEIR password:", show='*')
        if not recipient_pass: return

        recipient_coin = self.manager.read_coin_file(recipient_path)
        if not (recipient_coin and recipient_coin.verify_child_password(recipient_pass)):
            messagebox.showerror("error", "recipient wallet couldn't be opened, check password.")
            return

        if sender_coin.file_id == recipient_coin.file_id:
            messagebox.showwarning("error", "good thinking, but you cannot transfer coins to your own wallet.")
            return

        try:
            amount = simpledialog.askfloat("transfer amount", f"your balance: {sender_coin.balance:.2f}\nenter amount to transfer to {recipient_coin.owner_name}:")
            if amount is None or amount <= 0:
                messagebox.showwarning("invalid", "transfer amount must be positive")
                return

            success, message = perform_transfer(sender_coin, recipient_coin, amount)
            if success:
                self.manager.write_coin_file(self.current_file_path, sender_coin)
                self.manager.write_coin_file(recipient_path, recipient_coin)
                self.update_wallet_display()
                messagebox.showinfo("sucesss", message)
            else:
                messagebox.showerror("transfer failed", message)
        except Exception as e:
            messagebox.showerror("error", f"an unexpected error occurred: {e}")



if __name__ == "__main__":
    app = ChildApp()
    app.mainloop()