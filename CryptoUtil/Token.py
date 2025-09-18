from web3 import Web3
import logging
import json
import requests
import os
from CryptoUtil.SmartContract import SmartContract

logger = logging.getLogger(__name__)

# ✅ generic ERC20 Token ABI (Stored as JSON String)
ERC20_ABI= json.loads("""
    [{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_l2Bridge\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"_l1Token\",\"type\":\"address\"},{\"internalType\":\"string\",\"name\":\"_name\",\"type\":\"string\"},{\"internalType\":\"string\",\"name\":\"_symbol\",\"type\":\"string\"}],\"stateMutability\":\"nonpayable\",\"type\":\"constructor\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"address\",\"name\":\"owner\",\"type\":\"address\"},{\"indexed\":true,\"internalType\":\"address\",\"name\":\"spender\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"uint256\",\"name\":\"value\",\"type\":\"uint256\"}],\"name\":\"Approval\",\"type\":\"event\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"address\",\"name\":\"_account\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"uint256\",\"name\":\"_amount\",\"type\":\"uint256\"}],\"name\":\"Burn\",\"type\":\"event\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"address\",\"name\":\"_account\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"uint256\",\"name\":\"_amount\",\"type\":\"uint256\"}],\"name\":\"Mint\",\"type\":\"event\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"address\",\"name\":\"from\",\"type\":\"address\"},{\"indexed\":true,\"internalType\":\"address\",\"name\":\"to\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"uint256\",\"name\":\"value\",\"type\":\"uint256\"}],\"name\":\"Transfer\",\"type\":\"event\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"owner\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"spender\",\"type\":\"address\"}],\"name\":\"allowance\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"spender\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"amount\",\"type\":\"uint256\"}],\"name\":\"approve\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"account\",\"type\":\"address\"}],\"name\":\"balanceOf\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_from\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"_amount\",\"type\":\"uint256\"}],\"name\":\"burn\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"decimals\",\"outputs\":[{\"internalType\":\"uint8\",\"name\":\"\",\"type\":\"uint8\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"spender\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"subtractedValue\",\"type\":\"uint256\"}],\"name\":\"decreaseAllowance\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"spender\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"addedValue\",\"type\":\"uint256\"}],\"name\":\"increaseAllowance\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"l1Token\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"l2Bridge\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_to\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"_amount\",\"type\":\"uint256\"}],\"name\":\"mint\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"name\",\"outputs\":[{\"internalType\":\"string\",\"name\":\"\",\"type\":\"string\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"bytes4\",\"name\":\"_interfaceId\",\"type\":\"bytes4\"}],\"name\":\"supportsInterface\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"pure\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"symbol\",\"outputs\":[{\"internalType\":\"string\",\"name\":\"\",\"type\":\"string\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"totalSupply\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"recipient\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"amount\",\"type\":\"uint256\"}],\"name\":\"transfer\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"sender\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"recipient\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"amount\",\"type\":\"uint256\"}],\"name\":\"transferFrom\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"nonpayable\",\"type\":\"function\"}]
  """)




class Token(SmartContract):
    def __init__(self, chain_name: str, name: str):
        self.name=name
        token_address=self.get_token_address(name,chain_name)
        if token_address is None:
             raise Exception(f"No address found for token {name}. Check .env or coingeko name")
        super().__init__(chain_name, ERC20_ABI, token_address)
        self.decimals=self.contract.functions.decimals().call()

    def transferToken(self, amount, from_address, to_address):
        """
        Trasferisce un certo quantitativo di token ERC-20.

        Args:
            amount (float): Quantità di token da trasferire.
            from_address (str): Indirizzo del mittente.
            to_address (str): Indirizzo del destinatario.
            token (str): Nome del token (ad es. "USDT").
            web3 (Web3): Istanza Web3.

        Returns:
            str: Hash della transazione.
        """
        amount_wei = self.get_wei_amount(amount)


        # Ottenere il nonce del mittente (numero di transazioni inviate)
        nonce = self.blockChain.web3.eth.get_transaction_count(from_address)

        # Creazione della transazione
        transaction = self.contract.functions.transfer(to_address, amount_wei).build_transaction({
            "from": from_address,
            "nonce": nonce,
            "gas": 100000,  # Gas limit stimato
            "gasPrice": self.blockChain.web3.eth.gas_price,
        })

        # Invio della transazione
        tx_hash = self.blockChain.send_transaction(transaction)
        return tx_hash

    def get_token_price(self):
        """
        Restituisce il valore in USD della criptovaluta specificata per ID.

        :param crypto_id: ID della criptovaluta su CoinGecko (es. 'bitcoin', 'ethereum')
        :return: Prezzo in USD come float, oppure None in caso di errore
        """
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': self.name,
            'vs_currencies': 'usd'
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # genera eccezione se risposta non 2xx
        data = response.json()
        return data[self.name]['usd']


    def get_wei_amount(self,amount: float):
        amount_float=float(amount)
        amount_wei = int(amount_float * (10 ** self.decimals))
        return amount_wei


    def total_supply(self) -> int:
        return self.call_function("totalSupply")

    def balance_of(self, address: str) -> int:

        return self.call_function("balanceOf", self.blockChain.web3.to_checksum_address(address))

    def get_token_coingecko(self, token, blockchain):
        response = requests.get("https://api.coingecko.com/api/v3/coins/list?include_platform=true")
        response.raise_for_status()
        coins = response.json()
        for coin in coins:
            if coin["id"] == token:
                platforms = coin.get("platforms", {})
                address = platforms.get(blockchain)
                return address

        raise ValueError(f"❌ Unsupported token: {token}")


    def approve(self, spender, wallet_address, amount):
        token_contract = load_token_contract(token, web3)

        nonce = self.blockChain.web3.eth.get_transaction_count(wallet_address)
        tx = self.contract.functions.approve(spender, amount).build_transaction({
            'from': wallet_address,
            'nonce': nonce
        })
        tx_hash = self.blockChain.send_transaction(tx)
        allow_token = self.contract.functions.allowance(wallet_address, spender).call()

        return tx_hash

    def get_token_address(self, token_name, chain_name:str):
        """
        Get token address in a certain  blockchain

        Args:
        token= coin_id according  to https://api.coingecko.com/
        blockchain: according  to https://api.coingecko.com/

        Returns:
        adddress of token
        """

        token_label = chain_name.upper() + "_" + token_name.upper() + "_ADDRESS"
        token_address = os.getenv(token_label)

        if not token_address:
            token_address = self.get_token_coingecko(token_name)

        return token_address
