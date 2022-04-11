import binascii

import Crypto
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


class Wallet:
    def __init__(self):
        random = Crypto.Random.new().read
        self._private_key = RSA.generate(1024, random)
        self._public_key = self._private_key.public_key()
        self.amount = 50
        self.tmp_amount = self.amount

    def sign_transaction(self, transaction):
        signer = PKCS1_v1_5.new(self._private_key)
        h = SHA256.new(str(transaction.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    @property
    def identity(self):
        pubkey = binascii.hexlify(self._public_key.exportKey(format='DER'))
        return pubkey.decode('ascii')

    @property
    def private(self):
        prikey = binascii.hexlify(self._private_key.exportKey(format='DER'))
        return prikey.decode('ascii')
