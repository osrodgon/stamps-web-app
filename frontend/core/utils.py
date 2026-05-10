import re

def is_valid_email(email):
    # Regex for: text + @ + text + . + text
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email.strip()) is not None

def is_strong_password(password):
    # Regex for: 1 upper, 1 lower, 1 digit, 1 special, min 8 chars
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[_!@#$%^&*(),.?\":{}|<>]).{8,}$"
    return re.match(pattern, password) is not None