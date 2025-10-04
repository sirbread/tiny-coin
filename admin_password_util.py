import os
import hashlib
import secrets
import sys

def get_pwd_file_path():
    fname = ".admin_pwd"
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), fname)

def set_hidden(filepath):
    if os.name == "nt":
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(filepath), FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            os.system(f'attrib +h "{filepath}"')

def hash_password(pw, salt):
    return hashlib.sha256(pw.encode('utf-8') + salt).digest()

def save_password(pw, path):
    salt = secrets.token_bytes(16)
    h = hash_password(pw, salt)
    with open(path, "wb") as f:
        f.write(salt + h)
    set_hidden(path)

def check_password(pw, path):
    with open(path, "rb") as f:
        data = f.read()
    salt, stored_hash = data[:16], data[16:]
    return hash_password(pw, salt) == stored_hash

def password_file_exists():
    return os.path.exists(get_pwd_file_path())

