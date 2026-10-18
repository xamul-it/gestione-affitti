"""
Cifratura credenziali IMAP/SMTP con Fernet.

La chiave è derivata da SECRET_KEY della piattaforma tramite PBKDF2-HMAC-SHA256.
MAI loggare o serializzare credenziali decifrate.
"""
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from app.core.config import settings

_SALT = b"modstack_pec_credentials_v1"
_ITERATIONS = 100_000


def _get_fernet() -> Fernet:
    """Costruisce un'istanza Fernet con chiave derivata da SECRET_KEY."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return Fernet(key)


def encrypt_credential(plaintext: str) -> str:
    """Cifra una credenziale in chiaro e restituisce il token Fernet come stringa."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_credential(ciphertext: str) -> str:
    """Decifra un token Fernet e restituisce la credenziale in chiaro.

    MAI loggare il valore restituito.
    """
    return _get_fernet().decrypt(ciphertext.encode()).decode()
