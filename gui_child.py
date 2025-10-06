import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QDialog, QDialogButtonBox, QFileDialog,
    QMessageBox, QTextEdit, QInputDialog, QFormLayout, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core_logic import CryptoManager, perform_transfer

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("change password")

        layout = QFormLayout(self)

        self.old_pw_entry = QLineEdit(self)
        self.old_pw_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("current password:", self.old_pw_entry)

        self.new_pw1_entry = QLineEdit(self)
        self.new_pw1_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("new password:", self.new_pw1_entry)

        self.new_pw2_entry = QLineEdit(self)
        self.new_pw2_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("confirm new password:", self.new_pw2_entry)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def get_passwords(self):
        return (
            self.old_pw_entry.text(),
            self.new_pw1_entry.text(),
            self.new_pw2_entry.text()
        )

class ChildApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = CryptoManager()
        self.current_coin_obj = None
        self.current_file_path = None

        self.setWindowTitle("tinycoin")
        self.setFixedSize(550, 410)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.login_view = self._create_login_view()
        self.wallet_view = self._create_wallet_view()

        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.wallet_view)

        self.show_login_view()

    def _create_login_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_label = QLabel("tinycoin")
        welcome_label.setFont(QFont("Arial", 16))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        open_wallet_btn = QPushButton("open your wallet")
        open_wallet_btn.setMinimumHeight(40)
        open_wallet_btn.setMinimumWidth(120)
        open_wallet_btn.clicked.connect(self.login)

        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.addStretch()
        h_layout.addWidget(open_wallet_btn)
        h_layout.addStretch()

        layout.addStretch()
        layout.addWidget(welcome_label)
        layout.addWidget(container)
        layout.addStretch()

        return widget

    def _create_wallet_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.welcome_label = QLabel("")
        self.welcome_label.setFont(QFont("Arial", 14))
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(14)
        layout.addWidget(self.welcome_label)
        layout.addSpacing(14)
        self.balance_label = QLabel("")
        self.balance_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.balance_label)

        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)

        transfer_btn = QPushButton("transfer coins")
        transfer_btn.clicked.connect(self.transfer_coins)
        transfer_btn.setMinimumHeight(30)
        button_layout.addWidget(transfer_btn)

        change_pw_btn = QPushButton("change password")
        change_pw_btn.clicked.connect(self.change_password)
        change_pw_btn.setMinimumHeight(30)
        change_pw_btn.setMinimumWidth(140)
        button_layout.addWidget(change_pw_btn)

        logout_btn = QPushButton("log out")
        logout_btn.clicked.connect(self.logout)
        logout_btn.setMinimumHeight(30)
        button_layout.addWidget(logout_btn)

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

    def show_wallet_view(self):
        self.stacked_widget.setCurrentWidget(self.wallet_view)
        self.update_wallet_display()

    def update_wallet_display(self):
        coin = self.current_coin_obj
        if coin:
            self.welcome_label.setText(f"welcome, {coin.owner_name}!")
            self.balance_label.setText(f"{coin.balance:.2f} coins")
            self.update_logs(coin.transaction_log)
        else:
            self.welcome_label.setText("")
            self.balance_label.setText("")
            self.update_logs([])

    def update_logs(self, log_list):
        self.log_text.clear()
        for entry in reversed(log_list[-30:]):
            self.log_text.append(entry)

    def login(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "select your .coin file", "", "tinycoin files (*.coin)")
        if not file_path:
            return

        coin = self.manager.read_coin_file(file_path)
        if not coin:
            QMessageBox.critical(self, "error", "could not read file. it may be corrupted or not a valid wallet file.")
            return

        while True:
            password, ok = QInputDialog.getText(self, "password", f"enter password for {coin.owner_name}:", QLineEdit.EchoMode.Password)
            if not ok:
                return

            if coin.verify_child_password(password):
                self.current_coin_obj = coin
                self.current_file_path = file_path
                self.show_wallet_view()
                break
            else:
                QMessageBox.critical(self, "login failed", "incorrect password. please try again.")

    def logout(self):
        self.current_coin_obj = None
        self.current_file_path = None
        self.show_login_view()

    def change_password(self):
        dialog = ChangePasswordDialog(self)
        if dialog.exec():
            old_pw, new_pw1, new_pw2 = dialog.get_passwords()

            if not self.current_coin_obj.verify_child_password(old_pw):
                QMessageBox.critical(self, "error", "current password is not correct.")
                return

            if len(new_pw1) < 4:
                QMessageBox.critical(self, "error", "new password must be at least 4 characters long.")
                return

            if new_pw1 != new_pw2:
                QMessageBox.critical(self, "error", "new passwords do not match.")
                return

            self.current_coin_obj.update_password(new_pw1)
            self.manager.write_coin_file(self.current_file_path, self.current_coin_obj)
            self.update_logs(self.current_coin_obj.transaction_log)
            QMessageBox.information(self, "success", "your password has been changed successfully.")

    def transfer_coins(self):
        sender_coin = self.current_coin_obj
        QMessageBox.information(self, "open file to transfer to", "ask the recipient to select THEIR wallet file so you can transfer to them.")

        recipient_path, _ = QFileDialog.getOpenFileName(self, "select recipient's .coin file", "", "tinycoin files (*.coin)")
        if not recipient_path:
            return

        recipient_coin = self.manager.read_coin_file(recipient_path)
        if not recipient_coin:
            QMessageBox.critical(self, "error", "recipient wallet couldn't be opened.")
            return

        if sender_coin.file_id == recipient_coin.file_id:
            QMessageBox.warning(self, "error", "good thinking, but you cannot transfer coins to your own wallet.")
            return

        while True:
            recipient_pass, ok = QInputDialog.getText(self, "recipient's password", f"ask {recipient_coin.owner_name} to enter THEIR password to approve:", QLineEdit.EchoMode.Password)
            if not ok:
                return

            if recipient_coin.verify_child_password(recipient_pass):
                break
            else:
                QMessageBox.critical(self, "error", "incorrect password for recipient. please try again.")
        
        try:
            amount, ok = QInputDialog.getDouble(self, "transfer amount", f"your balance: {sender_coin.balance:.2f}\nenter amount to transfer to {recipient_coin.owner_name}:", 0, 0, 1000000, 2)
            if not ok:
                return
            if amount <= 0:
                QMessageBox.warning(self, "invalid", "transfer amount must be positive")
                return

            success, message = perform_transfer(sender_coin, recipient_coin, amount)
            if success:
                self.manager.write_coin_file(self.current_file_path, sender_coin)
                self.manager.write_coin_file(recipient_path, recipient_coin)
                self.current_coin_obj = sender_coin
                self.update_wallet_display()
                QMessageBox.information(self, "sucesss", message)
            else:
                QMessageBox.critical(self, "transfer failed", message)
        except Exception as e:
            QMessageBox.critical(self, "error", f"an unexpected error occurred: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = ChildApp()
    main_win.show()
    sys.exit(app.exec())