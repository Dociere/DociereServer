import os
import binascii

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Using the same fallback key as your Node.js server to maintain consistency
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef").encode('utf-8')

def encrypt(text: str) -> str:
    if not text:
        return text
    if not HAS_CRYPTO:
        return text # Fallback for dev environments without cryptography
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(text.encode('utf-8')) + padder.finalize()

    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return f"{binascii.hexlify(iv).decode('utf-8')}:{binascii.hexlify(encrypted).decode('utf-8')}"

def decrypt(text: str) -> str:
    if not text or ":" not in text:
        return text
    if not HAS_CRYPTO:
        return text # Fallback
    try:
        iv_hex, encrypted_hex = text.split(":", 1)
        iv = binascii.unhexlify(iv_hex)
        encrypted = binascii.unhexlify(encrypted_hex)

        cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(encrypted) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        return data.decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None