import hashlib
import json
import datetime
from urllib.parse import urlparse

from fastapi import requests

from class_transaction import *
from class_wallet import *


class Blockchain(object):
    difficulty = 2

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # create genesis block
        self.new_block(prev_hash='0')

    def register_node(self, address, port):
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

    def new_block(self, prev_hash=None):
        # Create a new block and adds it to the chain
        block = {
            'index': len(self.chain) + 1,
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
        transaction.add_signature(Wallet.sign_transaction(transaction))
        transaction_result = transaction.verify_transaction_signature()
        if transaction_result:
            self.current_transactions.append(transaction.to_dict())
            self.current_transactions.append(self.transaction_fee())
            # return index of block that the transaction will be added
            return self.last_block['index'] + 1

    def transaction_fee(self):
        response = {'sender': Wallet.identity,
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