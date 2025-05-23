import json
import requests
import time
from web3 import Web3
import os
from dotenv import load_dotenv
from datetime import datetime
#########################################################################################
# Obiettivo di questo script è fornire delle funzioni di base per interagire con smart contract ERC20
#
#
##########################################################################################
def  AAVE_withdraw_ETH(amount, to_address,web3):
    
    amount_wei=get_wei_amount("ETH",amount,web3)
    lending_eth_contract= get_AAVE_eth_pool(web3)
     # Ottenere il nonce del mittente (numero di transazioni inviate)
    nonce = web3.eth.get_transaction_count(to_address)
    transaction = lending_eth_contract.functions. withdrawETH(to_address, amount_wei,to_address).build_transaction({
    'from': to_address,
    'gas': 300000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
    })
    
    
    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
    return tx_hash




def  AAVE_deposit_ETH(amount, from_address,web3):
    
    amount_wei=get_wei_amount("ETH",amount,web3)
    lending_eth_contract= get_AAVE_eth_pool(web3)
     # Ottenere il nonce del mittente (numero di transazioni inviate)
    nonce = web3.eth.get_transaction_count(from_address)
    transaction = lending_eth_contract.functions.depositETH(from_address, from_address, 0).build_transaction({
    'from': from_address,
    'gas': 300000,
    'gasPrice': web3.eth.gas_price,
    'value': amount_wei,
    'nonce': nonce,
    })
    
    
    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
    return tx_hash
def get_AAVE_eth_pool(web3):
    """
    Carica prima il contratto che ha tuttti gli indirizzi da cui ricavo l'indirizzo del lending pool e poi carico quello.
    

    Args:
       
        web3 (Web3): Istanza di Web3 per l'interazione con la blockchain.

    Returns:
    l
     """
    lending_pool_address =os.getenv('OPT_AAVE_ETH_ADDRESS') 
    lending_pool_abi_file=os.getenv("AAVE_ETH_ABI_FILE")
    lending_pool = load_contract(lending_pool_address, lending_pool_abi_file, web3)
    return lending_pool







def get_AAVE_lending_pool(web3):
    """
    Carica prima il contratto che ha tuttti gli indirizzi da cui ricavo l'indirizzo del lending pool e poi carico quello.
    

    Args:
       
        web3 (Web3): Istanza di Web3 per l'interazione con la blockchain.

    Returns:
    l
     """
    lending_pool_address =os.getenv('OPT_AAVE_POOL_ADDRESS') 
    lending_pool_abi_file=os.getenv("AAVE_POOL_ABI_FILE")
    lending_pool = load_contract(lending_pool_address, lending_pool_abi_file, web3)
    return lending_pool



def  get_wei_amount(token,amount,web3):
    if token == "USDC":
          amount_wei = amount*1000000
    elif token == "USDT":
          amount_wei=web3.to_wei(amount, 'mwei') 
    else:
          amount_wei=web3.to_wei(amount, 'ether')  
    return amount_wei
        

def approve(token, spender, wallet_address, max_amount, web3):
   token_contract= load_token_contract(token, web3)
   nonce = web3.eth.get_transaction_count(wallet_address)
   tx = token_contract.functions.approve(spender, max_amount).build_transaction({
      'from': wallet_address, 
      'nonce': nonce
      })
   tx_hash=send_transaction(tx, web3)
   allow_token= token_contract.functions.allowance(wallet_address, spender).call()
 
   return tx_hash


def  AAVE_withdraw_Token(amount, from_address,token, web3):
    
    amount_wei=get_wei_amount(token,amount,web3)
    
    lending_pool_address =os.getenv( 'OPT_AAVE_POOL_ADDRESS')  
    lending_poolcontract= get_AAVE_lending_pool(web3)
    approve(token, lending_pool_address, from_address, amount_wei,web3)
    token_contract= load_token_contract(token, web3)
    token_address=get_token_address(token)
    # Ottenere il nonce del mittente (numero di transazioni inviate)
    nonce = web3.eth.get_transaction_count(from_address)
    transaction = lending_poolcontract.functions.withdraw(token_address, amount_wei,from_address).build_transaction({
    'from': from_address,
    'gas': 300000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
    })
    
    
    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
  
    return tx_hash




def  AAVE_deposit_Token(amount, from_address,token, web3):
    
    amount_wei=get_wei_amount(token,amount,web3)
    
    lending_pool_address =os.getenv( 'OPT_AAVE_POOL_ADDRESS')  
    lending_poolcontract= get_AAVE_lending_pool(web3)
    approve(token, lending_pool_address, from_address, amount_wei,web3)
    token_contract= load_token_contract(token, web3)
    token_address=get_token_address(token)
    # Ottenere il nonce del mittente (numero di transazioni inviate)
    nonce = web3.eth.get_transaction_count(from_address)

    
    transaction = lending_poolcontract.functions.supply(token_address, amount_wei,from_address,0).build_transaction({
    'from': from_address,
    'gas': 300000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
    })
    
    
    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)

    return tx_hash

def get_token_address(token):
    if token == "USDC":
          token_address=os.getenv("OPT_USDC_ADDRESS")
    elif token == "USDT":
          token_address=os.getenv("OPT_USDT_ADDRESS")
    else:
          token_address=0
        
    return token_address

def get_token_address(token, blockchain):
    if token == "USDC":
          token_address=os.getenv(blockchain+"_USDC_ADDRESS")
    elif token == "USDT":
          token_address=os.getenv(blockchain+"_USDT_ADDRESS")
    elif token == "ETH":
          token_address=os.getenv(blockchain+"_ETH_ADDRESS")
    else:
          token_address=0
        
    return token_address


def load_token_contract(token, web3):
    """
    Carica il contratto specificato in base al token fornito.

    Args:
        token (str): Nome del token (ad es. "USDT").
        web3 (Web3): Istanza di Web3 per l'interazione con la blockchain.

    Returns:
        contract (Contract): Contratto interagibile tramite Web3.
    """
    abi_file = os.getenv("ERC20_ABI_FILE")
    contract_address =get_token_address(token)
    # Caricamento del contratto
    contract = load_contract(contract_address, abi_file, web3)
    return contract

def load_contract(contract_address, abi_file, web3):
    """
    Carica il contratto specificato in base al token fornito.

    Args:
        token (str): Nome del token (ad es. "USDT").
        web3 (Web3): Istanza di Web3 per l'interazione con la blockchain.

    Returns:
        contract (Contract): Contratto interagibile tramite Web3.
    """

    
    # Leggere l'ABI da un file JSON
    with open(abi_file) as f:
        contract_abi = json.load(f)

    # Caricamento del contratto
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    #print("Funzioni disponibili nello smart contract:")
    #functions = contract.functions
    #function_names = [func for func in functions]
    # Stampa delle funzioni disponibili
    #for func in function_names:
    #   print(func)
    return contract



def send_transaction(transaction, web3):
    """
    Firma e invia una transazione alla blockchain.

    Args:
        transaction (dict): Transazione costruita per l'invio.
        web3 (Web3): Istanza Web3 per l'interazione con la blockchain.

    Returns:
        str: Hash della transazione inviata.
    """

    private_key = os.getenv("PRIVATE_KEY")  # Recupero della chiave privata
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Firma della transazione
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)  # Invio della transazione
    web3.eth.wait_for_transaction_receipt(tx_hash)
    time.sleep(3)
    return web3.to_hex(tx_hash)


def transferToken(amount, from_address, to_address, token, web3):
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
    amount_wei=get_wei_amount(token,amount,web3)
    contract = load_token_contract(token, web3)

    # Ottenere il nonce del mittente (numero di transazioni inviate)
    nonce = web3.eth.get_transaction_count(from_address)

    # Creazione della transazione
    transaction = contract.functions.transfer(to_address, amount_wei).build_transaction({
        "from": from_address,
        "nonce": nonce,
        "gas": 100000,  # Gas limit stimato
        "gasPrice": web3.eth.gas_price,
    })

    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
    return tx_hash


def get_infura_url(blockchain):
    url=blockchain+"_INFURA_URL"
    get_url = os.getenv(url)
    return get_url
    
    
def get_node_connection(blockchain):
    """
    Crea una connessione al nodo Ethereum.

    Returns:
        Web3: Istanza connessa alla blockchain.
    """
   
    geth_url = get_infura_url(blockchain)
    print(f'URL è: {geth_url} ')
    web3 = Web3(Web3.HTTPProvider(geth_url))

    # Verifica della connessione
    if not web3.is_connected():
        raise Exception("Unable to connect to the Ethereum node")

    return web3


def get_token_balance(wallet_address, token, web3):
    """
    Ottiene il saldo di un token ERC-20.

    Args:
        wallet_address (str): Indirizzo del wallet.
        token (str): Nome del token.
        web3 (Web3): Istanza Web3.

    Returns:
        float: Saldo del token in formato leggibile.
    """
    
    contract = load_token_contract(token, web3)
    balance = contract.functions.balanceOf(wallet_address).call()
    formatted_balance = balance / 10**6  # USDT ha 6 decimali
    return formatted_balance


def get_balance(wallet_address, web3):
    """
    Ottiene il saldo ETH di un wallet.

    Args:
        wallet_address (str): Indirizzo del wallet.
        web3 (Web3): Istanza Web3.

    Returns:
        float: Saldo in Ether.
    """
    balance_wei = web3.eth.get_balance(wallet_address)
    balance_eth = web3.from_wei(balance_wei, 'ether')
    return balance_eth

def main():
    """
    Funzione principale per verificare saldo ETH e USDT.
    """
    web3 = get_node_connection("OPT")
    my_eth_address = os.getenv("MY_ADDRESS")

    # Ottenere e stampare il saldo ETH
    balance_eth = get_balance(my_eth_address, web3)
    print(f'Il saldo del wallet è: {balance_eth} ETH')

    # Ottenere e stampare il saldo USDT
    balance_usdt = get_token_balance(my_eth_address, "USDT", web3)
    print(f'Il saldo del wallet è: {balance_usdt} USDT')
     
# Esempio di trasferimento e ritiro di 10 token su aave
    hash_tx =  AAVE_deposit_Token(10, my_eth_address, "USDC", web3)
    print(f'AAVE_deposit_Token {hash_tx}')
    hash_tx =  AAVE_withdraw_Token(10, my_eth_address, "USDC", web3)
    print(f'AAVE_withdraw_Token {hash_tx}')
    # Esempio di trasferimento (commentato per evitare esecuzioni accidentali)
    to_address = "0x56C1bE64F34431249fB1E12F8D345E6E4aeA71F5"
    hash_tx = transferToken(13, my_eth_address, to_address, "USDT", web3)
    print(f'transferToken {hash_tx}')
    hash_tx =AAVE_deposit_ETH(0.001, my_eth_address,web3)
    print(f'transferToken {hash_tx}')
    hash_tx =AAVE_withdraw_ETH(0.001, my_eth_address,web3)

# Caricamento delle variabili d'ambiente dal file .env

if __name__ == "__main__":
  load_dotenv()
  main()
 