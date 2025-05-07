import json
from erc20_opt import *
import datetime
import decimal
import os
import sys
from decimal import Decimal
from web3 import Account, Web3
from abi import UNISWAP_V3_ROUTER2_ABI, WETH9_ABI, MIN_ERC20_ABI
import eth_abi.packed

#########################################################################################
# method to swap token vs eth
# Address list
#https://docs.uniswap.org/contracts/v3/reference/deployments
#
# Doc
# https://docs.uniswap.org/contracts/v3/reference/periphery/interfaces/ISwapRouter
##########################################################################################


def  approve_wrap(amount, from_address, web3):
    weth_address =os.getenv('OPT_UNI_WRAP_ADDRESS') 
    weth_contract = web3.eth.contract(address=weth_address, abi=WETH9_ABI)
    nonce = web3.eth.get_transaction_count(from_address)
    swap_router02_address =os.getenv('OPT_UNI_SWAP2_ADDRESS')
    transaction = weth_contract.functions.approve(swap_router02_address, amount).build_transaction({
     'gas': 300000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
     })   


   
    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
    print(f'approve_wrap {tx_hash}')
    return tx_hash
  
def unwrap_eth(amount,from_address,web3):
    weth_address =os.getenv('OPT_UNI_WRAP_ADDRESS') 
    weth_contract = web3.eth.contract(address=weth_address, abi=WETH9_ABI)
    nonce = web3.eth.get_transaction_count(from_address)
    
    transaction = weth_contract.functions.withdraw(amount).build_transaction({
    'gas': 300000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce
    })
 
    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
    print(f'wrap_eth {tx_hash}')
    return tx_hash  
  
def wrap_eth(amount,from_address,web3):
    weth_address =os.getenv('OPT_UNI_WRAP_ADDRESS') 
    weth_contract = web3.eth.contract(address=weth_address, abi=WETH9_ABI)
    nonce = web3.eth.get_transaction_count(from_address)
    # wrap eth
    transaction = weth_contract.functions.deposit().build_transaction({
    'gas': 300000,
    'gasPrice': web3.eth.gas_price,
    'nonce': nonce,
    'value': amount, 
    })
 
    # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
    print(f'wrap_eth {tx_hash}')
    return tx_hash

def swap_token(amount,my_eth_address, init_token, final_token ,blockchain,web3):
    
    amount_wei=get_wei_amount(init_token,amount,web3)
    init_token_address=get_token_address(init_token,blockchain)
    final_token_address =get_token_address(final_token,blockchain)
    
    if init_token == "ETH":
       wrap_eth(amount_wei,my_eth_address,blockchain,web3)
       approve_wrap(amount_wei, my_eth_address,blockchain, web3)
    
  
    swap_router =get_swap_router(blockchain)
    
    router = web3.eth.contract(address=swap_router02_address, abi=UNISWAP_V3_ROUTER2_ABI)
    
    
    nonce = web3.eth.get_transaction_count(my_eth_address)
    
    # Swap transactions

    transaction = router.functions.exactOutputSingle(
    [
        init_token_address,
        final_token_address,
        fee,
        my_eth_address,
        out_amount,
        in_amount_max,
        0,  # sqrtPriceLimitX96: a value of 0 makes this parameter inactive
    ]
    ).build_transaction(
    {
        "chainId": web3.eth.chain_id,
        "gas": int(1e7),
        "gasPrice": web3.eth.gas_price,
        "nonce": nonce
    }
    )


      # Invio della transazione
    tx_hash = send_transaction(transaction, web3)
    print(f'sell_eth_for_Token {tx_hash}')
    
    return tx_hash   

        
 
  



def main1():
    web3 = get_node_connection("BASE")
    my_eth_address = os.getenv("MY_ADDRESS")
    swap_token(0.01,my_eth_address, "USDC","ETH","BASE", web3)
 
    



# Caricamento delle variabili d'ambiente dal file .env
load_dotenv()


main1()


