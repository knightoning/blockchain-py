# -*- coding: utf-8 -*
import hashlib
import json
from time import time
from urlparse import urlparse
import requests


class BlockChain(object):

    def __init__(self):
        """
        初始化一个创世快
        """
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

        self.nodes = set()

    def new_block(self,proof,previous_hash=None):
        # Creates a new Block and adds it to the chain
        """
        生产新块
        :param proof:<int> The proof given by the Proof of Work algorithm
        :param previous_hash:(Optional)<str> Hash of previous Block
        :return:<dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self,sender,recipient,amount):
        # Adds a new transaction to the list of transactions
        """
        生成新交易信息，将信息加入到下一个待挖的区块中
        :param sender:<str> Address of the Sender
        :param recipient:<str> Address of the Recipient
        :param amount:<int> The index of the Block that will hold this transaction
        :return:
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        # Hashes a Block
        """
        生产块的 SHA-256 hash值
        :param block: <dict> Block
        :return: <str>
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        简单的工作量证明：
         - 查找 p' 使得 hash(pp') 以4个0开头
         - p 是上一个块的证明，p'是当前的证明
         规则是：寻找一个数 p，使得它与前一个区块的 proof 拼接成的字符串的 Hash 值以 4 个零开头。
         衡量算法复杂度的办法是修改零开头的个数。使用4个来用于演示，你会发现多一个零都会大大增加计算出结果所需的时间。
        :param last_proof: <int>
        :return:
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证证明：是否hash(last_proof,proof)以4个0开头？
        :param proof:<int> Current Proof
        :param last_proof:<int> Previous Proof
        :return: <bool> True if correct,False if not.
        """
        guess = '{last_proof}{proof}'.format(last_proof=last_proof,proof=proof).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def register_node(self,address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg.'http://192.168.0.5:8030'
        :return: Node
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self,chain):
        """
        实现共识算法
        前面提到，冲突是指不同的节点拥有不同的链，为了解决这个问题，规定最长的、有效的链才是最终的链，换句话说，网络中有效最长链才是实际的链
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid,False if not

        """
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(last_block)
            print(block)
            print("\n---------------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'],block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        共识算法解决冲突
        使用网络中最长的链
        第一个方法 valid_chain() 用来检查是否是有效链，遍历每个块验证hash和proof。
        第二个方法 resolve_conflicts() 用来解决冲突，遍历所有的邻居节点，并用上一个方法检查链的有效性，
        如果发现有效更长链，就替换掉自己的链。

        :return: <bool> True 如果链被取代，否则为False
        """
        neighbours = self.nodes
        new_chain = None
        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get('http://{node}/chain'.format(node=node))
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain =chain
        # Replace our chain if we discovered a new,valid chain longer than our
        if new_chain:
            self.chain = new_chain
            return True
        return False
