import os
import hashlib
import secrets
import sys
import time

def get_pwd_file_path():
    fname = ".admin_pwd"
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), fname)

def get_failed_log_path():
    fname = ".admin_failed_log"
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

def set_lockout():
    path = get_failed_log_path()
    salt = secrets.token_bytes(16)
    timestamp = str(time.time()).encode('utf-8')
    h = hashlib.sha256(timestamp + salt).digest()
    with open(path, "wb") as f:
        f.write(salt + timestamp + h)
    set_hidden(path)

def get_lockout_time():
    path = get_failed_log_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        salt = data[:16]
        hash_start_index = 16 + len(str(time.time())) - 5

        # salt (16) + timestamp (?) + hash (32)
        stored_hash = data[-32:]
        timestamp_bytes = data[16:-32]

        h = hashlib.sha256(timestamp_bytes + salt).digest()

        if h != stored_hash:
            # if skids tamper
            # skreeeeeeeee
            return None

        return float(timestamp_bytes)
    except Exception:
        return None

def clear_lockout():
    path = get_failed_log_path()
    if os.path.exists(path):
        os.remove(path)
