import binascii
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    def to_dict(self):
        return ({'sender': self.sender, 'recipient': self.recipient, 'amount': self.amount})

    def add_signature(self, signature_):
        self.signature = signature_

    def verify_transaction_signature(self):
        if hasattr(self, 'signature'):
            public_key = RSA.importKey(binascii.unhexlify(self.sender))
            verifier = PKCS1_v1_5.new(public_key)
            h = SHA256.new(str(self.to_dict()).encode('utf8'))
            return verifier.verify(h, binascii.unhexlify(self.signature))
        else:
            return False
