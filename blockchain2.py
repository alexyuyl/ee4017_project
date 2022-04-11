import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

from class_blockchain import Blockchain
from class_wallet import Wallet

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
        {'sender': 'reward',
         'recipient': myWallet.identity,
         'amount': '1'}
    )
    myWallet.amount += 1
    # add new block to the chain
    block = blockchain.new_block()

    new_block = {
        'message': 'New Block Mined',
        'index': block['index'],
        'transaction': block['transaction'],
        'hash': block['hash'],
        'prev_hash': block['prev_hash'],
    }
    update_balance()
    return jsonable_encoder(new_block)


@app.post('/new_transaction')
def new_transaction(sender: str, recipient: str, amount: str):
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
    port = 2000
    uvicorn.run("__main__:app", host="0.0.0.0", port=port)
