from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

from class_blockchain import *
from class_wallet import *

app = FastAPI()


class User:

    # TO DO: MAC or Windows
    # For MAC: "0.0.0.0"
    # For Windows: "127.0.0.1"
    # For Android (Not Needed): "10.0.2.2"

    def __init__(self):
        self.blockchain = Blockchain()
        self.myWallet = Wallet()
        self.tmp_amount = 0

        # Windows localhost:
        self.host = "127.0.0.1"

    def update_balance(self):
        block_info = {
            'chain': self.blockchain.chain,
            'length': len(self.blockchain.chain),
        }
        add = 0
        minus = 0
        for i in range(block_info["length"]):
            curr_tx = block_info["chain"][i]["transaction"]
            for j in range(len(curr_tx)):
                tx = curr_tx[j]
                if tx["sender"] == self.myWallet.identity:
                    minus += float(tx["amount"])
                if tx["recipient"] == self.myWallet.identity:
                    add += float(tx["amount"])
        self.myWallet.amount = 50 + add - minus


@app.get('/mine')
def mine(self):
    # mine reward
    self.blockchain.current_transactions.append(
        {'sender': 'reward',
         'recipient': self.myWallet.identity,
         'amount': '1'}
    )
    self.myWallet.amount += 1
    # add new block to the chain
    block = self.blockchain.new_block()

    new_block = {
        'message': 'New Block Mined',
        'index': block['index'],
        'transaction': block['transaction'],
        'hash': block['hash'],
        'prev_hash': block['prev_hash'],
    }
    self.update_balance()
    return jsonable_encoder(new_block)


@app.post('/new_transaction')
def new_transaction(self, sender: str, recipient: str, amount: str):
    # create a new transaction
    tmp_amount = self.myWallet.tmp_amount
    if tmp_amount <= float(amount) + 0.5:
        response = {'message': 'Wallet Balance is not enough for transaction'}
        return jsonable_encoder(response)
    else:
        self.myWallet.tmp_amount = tmp_amount - float(amount)
    index = self.blockchain.new_transaction(sender, recipient, amount)
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonable_encoder(response)


@app.get('/full_chain')
def full_chain(self):
    response = {
        'chain': self.blockchain.chain,
        'length': len(self.blockchain.chain),
    }
    return jsonable_encoder(response)


@app.get('/get_pub_key')
def get_pub_key(self):
    return jsonable_encoder({'public_key': self.myWallet.identity})


@app.get('/get_balance')
def get_balance(self):
    return jsonable_encoder({'Balance': "{:.2f}".format(self.myWallet.amount)})


@app.get('/get_node')
def get_node(self):
    response = {
        'total_nodes': list(self.blockchain.nodes),
    }
    return jsonable_encoder(response)


@app.post('/register')
def register(self, node: str):
    self.blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(self.blockchain.nodes),
    }
    return jsonable_encoder(response)


@app.get('/consensus')
def consensus(self):
    replaced = self.blockchain.consensus()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': self.blockchain.chain
        }
        self.update_balance()
    else:
        response = {
            'message': 'Our chain is authoritative',
            'new_chain': self.blockchain.chain
        }
    return jsonable_encoder(response)
