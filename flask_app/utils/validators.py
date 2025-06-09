# Utility functions
import re


def validate_email(email):
    """Validate email format"""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password meets minimum requirements"""
    if not password or len(password.strip()) == 0:
        return False, "Password cannot be empty"
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, None
