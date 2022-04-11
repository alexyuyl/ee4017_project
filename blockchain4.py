import hashlib
import json
import datetime
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 
from Crypto.Hash import SHA256
import binascii
import requests
import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from urllib.parse import urlparse

class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
    
    def to_dict(self):
        return ({'sender':self.sender,'recipient':self.recipient, 'amount':self.amount})

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

class Blockchain(object):

    difficulty = 2

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # create genesis block
        self.new_block(prev_hash='0')

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            # for case http://0.0.0.0:1000
            self.nodes.add(parsed_url.netloc)
            response = requests.get(f'{address}/get_node').json()
            node_list = response['total_nodes']
            if f'0.0.0.0:{port}' in node_list:
                node_list.remove(f'0.0.0.0:{port}')
            for res in node_list:
                self.nodes.add(res)
        else:
            raise ValueError('Invalid URL')
    
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        # check proof of work of genesis block
        if not last_block['hash'].startswith('0' * Blockchain.difficulty):
            return False

        while current_index < len(chain):
            block = chain[current_index]
            # check the current hash and prev hash
            if block['prev_hash'] != last_block['hash']:
                return False
            # check proof of work
            if not block['hash'].startswith('0' * Blockchain.difficulty):
                return False

            last_block = block
            current_index += 1
        
        return True

    def consensus(self):
        # return True if our chain is replace, False if not
        neighbours = self.nodes
        new_chain = None
        
        # replace of the chain is longer than ours
        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/full_chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # check length and is the chain valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # replace the chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

    def new_block(self, prev_hash = None):
        # Create a new block and adds it to the chain
        block = {
            'index': len(self.chain)+1,
            'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'transaction': self.current_transactions,
            'hash': None,
            'prev_hash': prev_hash or self.last_block['hash'],
            'nonce': 0
        }

        # reset current list of transactions
        block['hash'] = self.proof_of_work(block)
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        # Add a new transaction to the list of transactions
        transaction = Transaction(sender, recipient, amount)
        transaction.add_signature(myWallet.sign_transaction(transaction))
        transaction_result = transaction.verify_transaction_signature()
        if transaction_result:
            self.current_transactions.append(transaction.to_dict())
            self.current_transactions.append(self.transaction_fee())
        # return index of block that the transaction will be added
            return self.last_block['index'] + 1     

    def transaction_fee(self):
        response = {'sender': myWallet.identity,
                    'recipient': 'transaction fee',
                    'amount': '0.5'}
        return response

    def proof_of_work(self, block):
        block['nonce'] = 0
        computed_hash = self.hash(block)
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block['nonce'] += 1
            computed_hash = self.hash(block)
        return computed_hash

    @staticmethod
    def hash(block):
        # Hashes a block
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # return last block in chain
        return self.chain[-1]

app = FastAPI()
blockchain = Blockchain()
myWallet = Wallet()
tmp_amount = 0

def update_balance():
    block_info = {
    'chain': blockchain.chain,
    'length': len(blockchain.chain),
    }
    add = 0
    minus = 0
    for i in range(block_info["length"]):
        curr_tx = block_info["chain"][i]["transaction"]
        for j in range(len(curr_tx)):
            tx = curr_tx[j]
            if tx["sender"] == myWallet.identity:
                minus += float(tx["amount"])
            if tx["recipient"] == myWallet.identity:
                add += float(tx["amount"])
    myWallet.amount = 50 + add - minus

@app.get('/mine')
def mine():
    # mine reward
    blockchain.current_transactions.append(
        {'sender':'reward',
        'recipient':myWallet.identity,
        'amount' :'1'}
    )
    myWallet.amount += 1
    # add new block to the chain
    block = blockchain.new_block()

    new_block = {
        'message': 'New Block Mined',
        'index': block['index'],
        'transaction': block['transaction'],
        'hash':block['hash'],
        'prev_hash': block['prev_hash'],
    }
    update_balance()
    return jsonable_encoder(new_block)


@app.post('/new_transaction')
def new_transaction(sender:str , recipient:str, amount:str):
    # create a new transaction
    tmp_amount = myWallet.tmp_amount
    if tmp_amount <= float(amount) + 0.5:
        response = {'message': 'Wallet Balance is not enough for transaction'}
        return jsonable_encoder(response)
    else:
        myWallet.tmp_amount = tmp_amount - float(amount)
    index = blockchain.new_transaction(sender, recipient, amount)
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonable_encoder(response)

@app.get('/full_chain')
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonable_encoder(response)

@app.get('/get_pub_key')
def get_pub_key():
    return jsonable_encoder({'public_key': myWallet.identity})

@app.get('/get_balance')
def get_balance():
    return jsonable_encoder({'Balance': "{:.2f}".format(myWallet.amount)})

@app.get('/get_node')
def get_node():
    response = {
        'total_nodes': list(blockchain.nodes),
    }
    return jsonable_encoder(response)

@app.post('/register')
def register(node: str):
    blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonable_encoder(response)

@app.get('/consensus')
def consensus():
    replaced = blockchain.consensus()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
        update_balance()
    else:
        response = {
            'message': 'Our chain is authoritative',
            'new_chain': blockchain.chain
        }
    return jsonable_encoder(response)

if __name__ == "__main__":
    port = 4000
    uvicorn.run("__main__:app", host="0.0.0.0", port=port)