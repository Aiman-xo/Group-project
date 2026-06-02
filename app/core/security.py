# THIS IS WHERE WE WRITE THE ACCESS TOKEN CREATION AND REFRESH TOKEN CREATION AND PASSWORD HASHING CODE.

from passlib.context import CryptContext

# bcrypt hashing algorithm
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    """
    Convert plain password to hashed password
    """

    return pwd_context.hash(password)