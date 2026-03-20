import re

# Validators for user


def validate_password_strength(password: str) -> str:
    """Validation method for password validation."""
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.") # noqa
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lower letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[@$!%*?&#]", password):
        raise ValueError(
            "Password must contain at least one special "
            "character: @, $, !, %, *, ?, #, &."
        )
    return password


def validate_login(login: str) -> str:
    """Validation method for login validation."""
    if not (6 <= len(login) <= 30):
        raise ValueError("Login must be between 6 and 30 characters.")
    if re.search(r"[^a-zA-Z0-9]", login):
        raise ValueError(
            "Login must contain only letters and numbers "
            "(no symbols or spaces)"
        )
    if len(re.findall(r"[a-zA-Z]", login)) < 5:
        raise ValueError("Login must contain at least 5 letters")

    return login
