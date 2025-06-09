import hashlib


def hash_password(password, salt):
    """Hash password with salt using SHA256"""
    return hashlib.sha256((password + salt).encode()).hexdigest()
