import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox, scrolledtext
from core_logic import CryptoManager, perform_transfer

class ChildApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.manager = CryptoManager()
        self.current_coin_obj = None
        self.current_file_path = None
        self.title("tinycoin")
        self.geometry("550x410")
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

        self.log_frame = tk.Frame(self.wallet_frame)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        tk.Label(self.log_frame, text="wallet logs:").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=8, state="disabled", font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)


    def show_login_view(self):
        self.wallet_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_wallet_view(self):
        self.login_frame.pack_forget()
        self.wallet_frame.pack(fill="both", expand=True)
        self.update_wallet_display()

    def update_wallet_display(self):
        coin = self.current_coin_obj
        if coin:
            self.welcome_label.config(text=f"welcome, {coin.owner_name}!")
            self.balance_label.config(text=f"{coin.balance:.2f} coins")
            self.update_logs(coin.transaction_log)
        else:
            self.welcome_label.config(text="")
            self.balance_label.config(text="")
            self.update_logs([])

    def update_logs(self, log_list):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        for entry in reversed(log_list[-30:]):
            self.log_text.insert(tk.END, entry + "\n")
        self.log_text.config(state="disabled")


    def login(self):
        file_path = filedialog.askopenfilename(title="select your .coin file", filetypes=[("tinycoin files", "*.coin")])
        if not file_path: return

        coin = self.manager.read_coin_file(file_path)
        if not coin:
            messagebox.showerror("error", "could not read file. it may be corrupted or not a valid wallet file.")
            return

        while True:
            password = simpledialog.askstring("password", f"enter password for {coin.owner_name}:", show='*')
            if not password:
                return

            if coin.verify_child_password(password):
                self.current_coin_obj = coin
                self.current_file_path = file_path
                self.show_wallet_view()
                break
            else:
                messagebox.showerror("login failed", "incorrect password. please try again.")

    def logout(self):
        self.current_coin_obj = None
        self.current_file_path = None
        self.show_login_view()

    def transfer_coins(self):
        sender_coin = self.current_coin_obj
        messagebox.showinfo("recipient's turn", "now, ask the recipient to select THEIR wallet file.")
        
        recipient_path = filedialog.askopenfilename(title="select recipient's .coin file", filetypes=[("tinycoin files", "*.coin")])
        if not recipient_path: return

        recipient_coin = self.manager.read_coin_file(recipient_path)
        if not (recipient_coin):
            messagebox.showerror("error", "recipient wallet couldn't be opened.")
            return

        if sender_coin.file_id == recipient_coin.file_id:
            messagebox.showwarning("error", "good thinking, but you cannot transfer coins to your own wallet.")
            return

        while True:
            recipient_pass = simpledialog.askstring("recipient's password", f"ask {recipient_coin.owner_name} to enter THEIR password to approve:", show='*')
            if not recipient_pass:
                return

            if recipient_coin.verify_child_password(recipient_pass):
                break
            else:
                messagebox.showerror("error", "incorrect password for recipient. please try again.")
        try:
            amount = simpledialog.askfloat("transfer amount", f"your balance: {sender_coin.balance:.2f}\nenter amount to transfer to {recipient_coin.owner_name}:")
            if amount is None or amount <= 0:
                messagebox.showwarning("invalid", "transfer amount must be positive")
                return

            success, message = perform_transfer(sender_coin, recipient_coin, amount)
            if success:
                self.manager.write_coin_file(self.current_file_path, sender_coin)
                self.manager.write_coin_file(recipient_path, recipient_coin)
                self.current_coin_obj = sender_coin
                self.update_wallet_display()
                messagebox.showinfo("sucesss", message)
            else:
                messagebox.showerror("transfer failed", message)
        except Exception as e:
            messagebox.showerror("error", f"an unexpected error occurred: {e}")



if __name__ == "__main__":
    app = ChildApp()
    app.mainloop()