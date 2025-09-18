

from web3 import Web3

import logging

from CryptoUtil.Chain import Chain

logger = logging.getLogger(__name__)
class SmartContract:
    def __init__(self, chain: str, abi: str, address: str):
        self.chain_name=chain
        self.blockChain=Chain(chain)
        self.abi = abi
        self.address = self.blockChain.web3.to_checksum_address(address)
        self.contract = self.blockChain.web3.eth.contract(address=self.address, abi=self.abi)

    def call_function(self, function_name: str, *args):
        """Chiama una funzione di sola lettura (view) dello smart contract"""
        try:
            function = getattr(self.contract.functions, function_name)
            return function(*args).call()
        except Exception as e:
            print(f"Errore nella call: {e}")
            return None
