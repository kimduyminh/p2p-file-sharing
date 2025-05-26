from ecc_keygen import ecc_keygen as ecc_keygen
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
class ecc_signing_and_verify:
    def __init__(self,private_key, public_key, public_key_sender):
        self.private_key = private_key
        self.public_key = public_key
        self.public_key_sender = public_key_sender
        pass

    def sign(self,path):
        data = open(path, "rb").read()
        signature = self.private_key.sign(
            data,
            ec.ECDSA(hashes.SHA256())
        )
        return signature

    def verify(self,path,signature):
        try:
            data = open(path, "rb").read()
            self.public_key_sender.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception as e:
            print(f"[-] Signature verification failed: {e}")
            return False