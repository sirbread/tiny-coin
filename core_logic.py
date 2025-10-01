import os
import pickle
import uuid
from datetime import datetime

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

SALT_SIZE = 16
KEY_SIZE = 32
PBKDF2_ITERATIONS = 100000
MAC_SIZE = 16

MASTER_PASSWORD = "maybe-the-password-was-the-friends-we-made-along-the-way-betterclient"

class Coin:
    def __init__(self, owner_name, child_password, initial_balance=0.0):
        self.file_id = str(uuid.uuid4())
        self.owner_name = owner_name
        self.child_password_salt = get_random_bytes(SALT_SIZE)
        self.child_password_hash = self._hash_password(child_password, self.child_password_salt)
        self.balance = float(initial_balance)
        self.transaction_log = [f"{datetime.utcnow().isoformat()} - Wallet created for {owner_name} with balance {self.balance}"]

    def _hash_password(self, password, salt):
        return SHA256.new(password.encode('utf-8') + salt).digest()

    def verify_child_password(self, password_attempt):
        return self._hash_password(password_attempt, self.child_password_salt) == self.child_password_hash

    def add_transaction(self, entry):
        self.transaction_log.append(f"{datetime.utcnow().isoformat()} - {entry}")

    def __str__(self):
        log_entries = self.transaction_log[-5:]
        log_entries.reverse()
        log_str = "\n  ".join(log_entries)
        return (
            f"owner: {self.owner_name}\n"
            f"balance: {self.balance:.2f} coins\n\n"
            f"recent activity:\n  {log_str}"
        )

class CryptoManager:

    def _derive_key(self, password_bytes, salt):
        return PBKDF2(password_bytes, salt, dkLen=KEY_SIZE, count=PBKDF2_ITERATIONS)

    def write_coin_file(self, file_path, coin_obj):
        salt = get_random_bytes(SALT_SIZE)
        key = self._derive_key(MASTER_PASSWORD.encode('utf-8'), salt)
        
        data_bytes = pickle.dumps(coin_obj)
        cipher = AES.new(key, AES.MODE_GCM)
        encrypted_data, mac = cipher.encrypt_and_digest(data_bytes)

        with open(file_path, 'wb') as f:
            f.write(salt)
            f.write(cipher.nonce)
            f.write(mac)
            f.write(encrypted_data)

    def read_coin_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                salt = f.read(SALT_SIZE)
                nonce = f.read(AES.block_size)
                mac = f.read(MAC_SIZE)
                encrypted_data = f.read()

            key = self._derive_key(MASTER_PASSWORD.encode('utf-8'), salt)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted_data = cipher.decrypt_and_verify(encrypted_data, mac)

            coin_obj = pickle.loads(decrypted_data)
            return coin_obj
        except (FileNotFoundError, ValueError, KeyError):
            return None

def perform_transfer(sender_coin, recipient_coin, amount):
    if sender_coin.balance < amount:
        return False, "too broke. enter something lower"
        
    sender_coin.balance -= amount
    recipient_coin.balance += amount
    
    transaction_note = f"transferred {amount:.2f} to {recipient_coin.owner_name}"
    sender_coin.add_transaction(transaction_note)
    
    receipt_note = f"received {amount:.2f} from {sender_coin.owner_name}"
    recipient_coin.add_transaction(receipt_note)
    
    return True, "transfer successful"
