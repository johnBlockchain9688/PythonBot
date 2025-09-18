# *********************************************************************************
# Date: 24/06/25
# Version: 1.0
# Author: John Blockchain
# mail=john.blockchain9688@gmail.com
# Description: 
# History of change:
# *****************************************************************************
from web3 import Web3
import logging
import time
import os
logger = logging.getLogger(__name__)

class Chain:
    def __init__(self, chain: str):
        self.chain = chain
        self.url = chain.upper() + "_INFURA_URL"
        self.get_url = os.getenv(self.url)
        self.web3 = Web3(Web3.HTTPProvider(self.get_url))
        if not self.web3.is_connected():
            raise Exception("Unable to connect to the Ethereum node")

    def is_connected(self):
        self.web3.is_connected()

    def send_transaction(self, transaction):

        private_key = os.getenv("PRIVATE_KEY")  # Recupero della chiave privata
        signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)  # Firma della transazione
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Invio della transazione
        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        time.sleep(3)
        return self.web3.to_hex(tx_hash)

    def calculate_gas_parameters(self, estimated_gas_limit=21000):
        """
        Calculate optimal gas parameters and check balance sufficiency.

        Args:
            estimated_gas_limit (int): Estimated gas limit for the transaction

        Returns:
            dict: Gas parameters and status, or None if insufficient balance
            {
                'max_fee_per_gas': int,
                'max_priority_fee_per_gas': int,
                'estimated_total_wei': int,

            }
        """

        # Get current gas values
        base_fee = self.web3.eth.get_block("latest")["baseFeePerGas"]
        priority_fee = self.web3.eth.max_priority_fee

        # More efficient multipliers for Base network
        base_multiplier = 1.2  # Reduced from 2
        priority_multiplier = 1.1  # Reduced from 2

        # Calculate new gas prices (in wei) and convert to integers
        new_max_fee_per_gas = int(base_fee * base_multiplier + priority_fee * priority_multiplier)
        new_max_priority_fee = int(priority_fee * priority_multiplier)

        # Set minimum values for Base (in wei)
        min_max_fee = Web3.to_wei(0.003, 'gwei')  # 0.003 gwei minimum
        min_priority_fee = Web3.to_wei(0.001, 'gwei')  # 0.001 gwei minimum

        # Use maximum between calculated and minimum values
        new_max_fee_per_gas = max(new_max_fee_per_gas, min_max_fee)
        new_max_priority_fee = max(new_max_priority_fee, min_priority_fee)

        # Ensure max fee is higher than priority fee
        if new_max_fee_per_gas < new_max_priority_fee:
            new_max_fee_per_gas = new_max_priority_fee * 2

        # Calculate total gas cost
        total_gas_wei = int(estimated_gas_limit * new_max_fee_per_gas)
        total_gas_eth = Web3.from_wei(total_gas_wei, "ether")

        estimated_gas_limit=300000
        return {
            'max_fee_per_gas': int(new_max_fee_per_gas),  # Ensure integer
            'max_priority_fee_per_gas': int(new_max_priority_fee),  # Ensure integer
            'estimated_total_wei': int(estimated_gas_limit),  # Ensure integer

        }
