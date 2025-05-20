from ecc_keygen import ecc_keygen as ecc_keygen
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
class ecc_signing_and_verify:
    def __init__(self):
        self.ecc_keygen = ecc_keygen("ez12345678")
        self.keys = self.ecc_keygen.load_key("ez12345678")
        self.private_key = self.keys[0]
        self.public_key = self.keys[1]
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
            self.public_key.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception as e:
            print(f"[-] Signature verification failed: {e}")
            return False