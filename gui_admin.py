import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QDialog, QDialogButtonBox, QFileDialog,
    QMessageBox, QTextEdit, QInputDialog, QFormLayout, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core_logic import Coin, CryptoManager
import admin_password_util

class AdminPasswordDialog(QDialog):
    def __init__(self, parent, is_new):
        super().__init__(parent)
        self.is_new = is_new
        self.setWindowTitle("admin login" if not is_new else "set admin password")
        
        layout = QFormLayout(self)
        if self.is_new:
            self.pw1_entry = QLineEdit(self)
            self.pw1_entry.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("set new admin password:", self.pw1_entry)
            
            self.pw2_entry = QLineEdit(self)
            self.pw2_entry.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("confirm password:", self.pw2_entry)
        else:
            self.pw_entry = QLineEdit(self)
            self.pw_entry.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("enter admin password:", self.pw_entry)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.result = None

    def accept(self):
        if self.is_new:
            pw1 = self.pw1_entry.text()
            pw2 = self.pw2_entry.text()
            if pw1 == pw2 and len(pw1) >= 4:
                self.result = pw1
        else:
            self.result = self.pw_entry.text()
        super().accept()


class AdminChangePasswordDialog(QDialog):
    def __init__(self, parent, owner_name):
        super().__init__(parent)
        self.setWindowTitle(f"reset password for {owner_name}")

        layout = QFormLayout(self)
        self.new_pw1_entry = QLineEdit(self)
        self.new_pw1_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("new password:", self.new_pw1_entry)

        self.new_pw2_entry = QLineEdit(self)
        self.new_pw2_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("confirm new password:", self.new_pw2_entry)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.result = None

    def accept(self):
        self.result = (self.new_pw1_entry.text(), self.new_pw2_entry.text())
        super().accept()


class ModifyBalanceDialog(QDialog):
    def __init__(self, parent, title, current_balance):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        layout = QFormLayout(self)
        layout.addRow(QLabel(f"current balance: {current_balance:.2f}"))

        self.adj_entry = QLineEdit(self)
        layout.addRow("adjustment (+/-):", self.adj_entry)

        self.set_entry = QLineEdit(self)
        layout.addRow("OR set to amount:", self.set_entry)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.result = None

    def accept(self):
        adj_val = self.adj_entry.text()
        set_val = self.set_entry.text()

        try:
            if adj_val and set_val:
                QMessageBox.warning(self, "error", "please use either adjustment OR set, not both.")
                return
            if adj_val:
                amount = float(adj_val)
                self.result = ("adjust", amount)
            elif set_val:
                amount = float(set_val)
                self.result = ("set", amount)
        except ValueError:
            QMessageBox.warning(self, "error", "please enter a valid number.")
            return
        super().accept()


class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = CryptoManager()
        self.loaded_coin = None
        self.loaded_file_path = None
        self.failed_attempts = 0
        self.lockout_duration = 15 * 60
        self.max_failed_attempts = 5
        self.is_destroyed_by_logic = False

        self.setWindowTitle("tinycoin admin panel")
        self.setFixedSize(550, 410)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.login_view = self._create_login_view()
        self.wallet_view = self._create_wallet_view()

        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.wallet_view)

        self.show_login_view()

    def run_password_check(self):
        self.hide() 
        if not self._require_password():
            self.is_destroyed_by_logic = True
            self.close()
            return False
        self.show()
        return True

    def _require_password(self):
        pwd_file = admin_password_util.get_pwd_file_path()
        if not admin_password_util.password_file_exists():
            while True:
                dialog = AdminPasswordDialog(self, is_new=True)
                if not dialog.exec(): return False
                pw = dialog.result
                if not pw:
                    QMessageBox.critical(self, "error", "password not set or too short (minimum 4 chars). try again.")
                else:
                    admin_password_util.save_password(pw, pwd_file)
                    QMessageBox.information(self, "password saved", 
                        "the password has been saved to a hidden file in the same directory as this executable.\n"
                        "moving this executable resets the password. deleting the file allows a new password to be set. careful!")
                    break
        
        lockout_time = admin_password_util.get_lockout_time()
        if lockout_time and (time.time() - lockout_time) < self.lockout_duration:
            remaining_time = int(self.lockout_duration - (time.time() - lockout_time))
            minutes, seconds = divmod(remaining_time, 60)
            QMessageBox.critical(self, "locked out", f"too many failed attempts. please wait {minutes}m {seconds}s.")
            return False
        admin_password_util.clear_lockout()

        while True:
            dialog = AdminPasswordDialog(self, is_new=False)
            if not dialog.exec(): return False
            pw = dialog.result
            if pw and admin_password_util.check_password(pw, pwd_file):
                admin_password_util.clear_lockout()
                return True

            self.failed_attempts += 1
            if self.failed_attempts >= self.max_failed_attempts:
                admin_password_util.set_lockout()
                QMessageBox.critical(self, "access denied", "too many failed attempts. the application will now close. please wait 15 minutes.")
                return False
            else:
                remaining_attempts = self.max_failed_attempts - self.failed_attempts
                QMessageBox.critical(self, "access denied", f"invalid password. {remaining_attempts} attempts remaining.")

    def _create_login_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_label = QLabel("tinycoin admin")
        welcome_label.setFont(QFont("Arial", 16))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_container = QWidget()
        v_layout = QVBoxLayout(button_container)
        
        open_wallet_btn = QPushButton("open and view a wallet")
        open_wallet_btn.setMinimumHeight(40)
        open_wallet_btn.setMinimumWidth(180)
        open_wallet_btn.clicked.connect(self.open_wallet)
        v_layout.addWidget(open_wallet_btn)

        create_wallet_btn = QPushButton("create new wallet")
        create_wallet_btn.setMinimumHeight(40)
        create_wallet_btn.setMinimumWidth(180)
        create_wallet_btn.clicked.connect(self.create_wallet)
        v_layout.addWidget(create_wallet_btn)

        h_wrapper_layout = QHBoxLayout()
        h_wrapper_layout.addStretch()
        h_wrapper_layout.addWidget(button_container)
        h_wrapper_layout.addStretch()

        layout.addStretch()
        layout.addWidget(welcome_label)
        layout.addLayout(h_wrapper_layout)
        layout.addStretch()

        return widget

    def _create_wallet_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.owner_label = QLabel("")
        self.owner_label.setFont(QFont("Arial", 14))
        self.owner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(13)

        layout.addWidget(self.owner_label)
        layout.addSpacing(13)


        self.balance_label = QLabel("")
        self.balance_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_label)

        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)

        modify_btn = QPushButton("modify balance")
        modify_btn.setMinimumHeight(30)
        modify_btn.setMinimumWidth(120)

        modify_btn.clicked.connect(self.modify_wallet)
        button_layout.addWidget(modify_btn)

        change_pw_btn = QPushButton("change password")
        change_pw_btn.setMinimumHeight(30)
        change_pw_btn.clicked.connect(self.admin_change_password)
        button_layout.addWidget(change_pw_btn)

        close_btn = QPushButton("close wallet")
        close_btn.setMinimumHeight(30)
        close_btn.clicked.connect(self.close_wallet)
        button_layout.addWidget(close_btn)

        h_button_layout = QHBoxLayout()
        h_button_layout.addStretch()
        h_button_layout.addWidget(button_container)
        h_button_layout.addStretch()
        layout.addLayout(h_button_layout)

        log_label = QLabel("wallet logs:")
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.log_text)

        return widget

    def show_login_view(self):
        self.stacked_widget.setCurrentWidget(self.login_view)
        self.loaded_coin = None
        self.loaded_file_path = None

    def show_wallet_view(self):
        self.stacked_widget.setCurrentWidget(self.wallet_view)
        self.display_wallet(self.loaded_coin)

    def display_wallet(self, coin):
        if not coin:
            self.owner_label.setText("")
            self.balance_label.setText("")
            self.update_logs([])
        else:
            self.owner_label.setText(f"modifying {coin.owner_name}'s wallet")
            self.balance_label.setText(f"{coin.balance:.2f} coins")
            self.update_logs(coin.transaction_log)

    def update_logs(self, log_list):
        self.log_text.clear()
        for entry in reversed(log_list[-30:]):
            self.log_text.append(entry)

    def create_wallet(self):
        owner_name, ok = QInputDialog.getText(self, "new wallet", "enter new sibling's name:")
        if not ok or not owner_name: return

        child_password, ok = QInputDialog.getText(self, "new wallet", f"enter a password for {owner_name}:", QLineEdit.EchoMode.Password)
        if not ok or not child_password: return

        initial_balance, ok = QInputDialog.getDouble(self, "new wallet", "enter initial balance (e.g., 10.0):", 0, 0, 1000000, 2)
        if not ok: return

        try:
            coin = Coin(owner_name, child_password, initial_balance)
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Wallet File", f"{owner_name.lower().replace(' ', '_')}.coin", "tinycoin files (*.coin)")
            if not file_path: return

            self.manager.write_coin_file(file_path, coin)
            QMessageBox.information(self, "done", f"wallet created for {owner_name} at '{file_path}'.")
            self.loaded_coin = coin
            self.loaded_file_path = file_path
            self.show_wallet_view()
        except Exception as e:
            QMessageBox.critical(self, "error", f"failed to create wallet: {e}")

    def open_wallet(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "select .coin file to open", "", "tinycoin files (*.coin)")
        if not file_path: return
        
        coin = self.manager.read_coin_file(file_path)
        if not coin:
            QMessageBox.critical(self, "error", "could not read file. it may be corrupted.")
            return
        self.loaded_coin = coin
        self.loaded_file_path = file_path
        self.show_wallet_view()

    def modify_wallet(self):
        if not self.loaded_coin: return
        dialog = ModifyBalanceDialog(self, f"modify {self.loaded_coin.owner_name}'s wallet", self.loaded_coin.balance)
        if not dialog.exec() or not dialog.result: return

        action, amount = dialog.result
        log_entry = ""
        if action == "adjust":
            self.loaded_coin.balance += amount
            log_entry = f"[admin] adjustment of {amount:+.2f}. new balance: {self.loaded_coin.balance:.2f}"
        elif action == "set":
            self.loaded_coin.balance = amount
            log_entry = f"[admin] set balance to {amount:.2f}."
        
        self.loaded_coin.add_transaction(log_entry)
        self.manager.write_coin_file(self.loaded_file_path, self.loaded_coin)
        QMessageBox.information(self, "success", f"wallet updated successfully.\nnew balance: {self.loaded_coin.balance:.2f}")
        self.display_wallet(self.loaded_coin)

    def admin_change_password(self):
        if not self.loaded_coin: return
        dialog = AdminChangePasswordDialog(self, self.loaded_coin.owner_name)
        if not dialog.exec() or not dialog.result: return
        new_pw1, new_pw2 = dialog.result

        if len(new_pw1) < 4:
            QMessageBox.critical(self, "error", "new password must be at least 4 characters long.")
            return
        if new_pw1 != new_pw2:
            QMessageBox.critical(self, "error", "new passwords do not match.")
            return

        self.loaded_coin.update_password(new_pw1)
        self.loaded_coin.add_transaction("[admin] password was reset by admin.")
        self.manager.write_coin_file(self.loaded_file_path, self.loaded_coin)
        self.update_logs(self.loaded_coin.transaction_log)
        QMessageBox.information(self, "success", f"password for {self.loaded_coin.owner_name} has been reset.")

    def close_wallet(self):
        self.show_login_view()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = AdminApp()
    if main_win.run_password_check():
        sys.exit(app.exec())