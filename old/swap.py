
from erc20_opt import *
import os
from abi import WETH9_ABI
from old.Uniswap import  Uniswap # or whatever you name this script
from CryptoUtil.Token import Token

#########################################################################################
# method to swap token vs eth
# Address list
#https://docs.uniswap.org/contracts/v3/reference/deployments
#
# Doc
# https://docs.uniswap.org/contracts/v3/reference/periphery/interfaces/ISwapRouter
# https://github.com/snarflakes/uniswap-python-swapper
##########################################################################################

def get_swap_router(blockChain=None):
    url = blockChain + "_UNI_SWAP4_ADDRESS"
    get_url = os.getenv(url)
    return get_url

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
    start_token= Token (blockchain,init_token)
    amount_wei=start_token.get_wei_amount(amount)
    init_token_address=get_token_address(init_token,blockchain)
    final_token_address =get_token_address(final_token,blockchain)
    
    #if init_token == "ETH":
    #   wrap_eth(amount_wei,my_eth_address,blockchain,web3)
    #   approve_wrap(amount_wei, my_eth_address,blockchain, web3)
    
    #A seconda del tipo di pool puo esserci un router diverso. Quindi la coppia di cui devo
    #fare lo swap determina il tipo del mio pool. Nel caso cbtc -- usdc e' la v4. quindi devo usare
    #quella in test. Non posso sapere a priori la versione del router
    #per essere sicuri devi guardare in metamask che scelga proprio la tua versione
    #swap_router =get_swap_router(blockchain)
    
    #router = web3.eth.contract(address=swap_router, abi=UNISWAP_V4_ROUTER_ABI)
    #nonce = web3.eth.get_transaction_count(my_eth_address)
    private_key=os.getenv("PRIVATE_KEY")  # Recupero della chiave privata
    provider_url=get_infura_url(blockchain)

    uniswap = Uniswap(
    wallet_address=my_eth_address,
    private_key=private_key,
    provider=provider_url,  # Used to auto-detect chain
    web3=web3
    )

   # 4. Perform a swap (SWAP_EXACT_IN)
   # Example: Swap 1 tokenIn -> tokenOut at 0.3% fee in a v3 pool
    tx_hash =0

    tx_hash = uniswap.make_trade(
        from_token=init_token_address,
        to_token=final_token_address,
        amount=amount_wei,
        fee=3000,  # e.g., 3000 for a 0.3% Uniswap V3 pool
        slippage=0.5,  # non-functional right now. 0.5% slippage tolerance
        pool_version="v3"  # can be "v3" or "v4"
      )
    return tx_hash

        
 
  


if __name__ == "__main__":
    load_dotenv()
    main1()


def main1():
    web3 = get_node_connection("ETH")
    my_eth_address = os.getenv("MY_ADDRESS")
    swap_token(1,my_eth_address, "USDC","USDT","ETH", web3)
 
    



# Caricamento delle variabili d'ambiente dal file .env




