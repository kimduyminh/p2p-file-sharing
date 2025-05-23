import os

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
class ecc_keygen:
    def __init__(self,passw):
        password = passw.encode()
        if not os.path.exists("private_key.pem") or not os.path.exists("public_key.pem"):
            self.private_key = ec.generate_private_key(ec.SECP256R1())
            with open("private_key.pem", "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.BestAvailableEncryption(password)
                ))
            public_key = self.private_key.public_key()
            with open("public_key.pem", "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
    def load_key(self,passw):
        password = passw.encode()
        with open("private_key.pem", "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=password
            )
        with open("public_key.pem", "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        return [private_key, public_key]