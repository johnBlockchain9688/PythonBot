from CryptoUtil import Token
from pushbullet import Pushbullet
from dotenv import load_dotenv
import traceback
import logging
import os
import time
import sys
import requests
from CryptoUtil.Chain import Chain
from CryptoUtil.Token import Token
from CryptoUtil.AAVE import AAVE

logger = logging.getLogger('crypto_bot')




def action_done(qta: str):
    logger.info("Start action Done")
    directory =os.getenv("STOP_DIR") 
    filename = "stop.txt"
    filepath = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("stop")
    logger.info("End action Done")
    return None

def sell_token(amount_token:float, address:str, block_chain:str,token_name:str):
    logger.info(" Start SELL Token  ")
    defi_platform = AAVE(block_chain)
    token_sell =Token(block_chain,token_name)
    amount_token_float=float(amount_token)
    if amount_token_float>0:
        defi_platform.withdraw(token_name, amount_token, address)
        time.sleep(3)
        if token_sell.balance_of(address) < amount_token_float:
            raise Exception("Error insufficient Token Balance")
        amount_usdc=swap_token_usdc(amount_token,block_chain, token_name)
        time.sleep(3)
        usdc_to_aave= float(amount_usdc)
        if usdc_to_aave>0:
            defi_platform.deposit("USDC",amount_usdc,address)
        return amount_usdc
    return amount_token

def buy_token(amount_token:float, address:str, blockchain:str, token_name:str):
    defi_platform = AAVE(blockchain)
    defi_platform.withdraw("USDC", amount_token, address)
    amount_token=swap_usdc_token(amount_token,blockchain, token_name)
    defi_platform.deposit(token_name,amount_token,address)
    return amount_token

def swap_token_usdc(amount,block_chain:str, token_name:str):
    url = os.getenv("Host") + "/swap_cbtc_usdc?qta=" + str(amount)
    token=Token(block_chain, token_name)
    address="&address="+ token.address
    decimals="&decimals="+ str(token.decimals)
    symbol="&symbol="+token_name
    url=url+address+decimals+symbol
    response = requests.get(url)

    if response.ok:
        contenuto = response.text  # risposta come stringa
        if contenuto.startswith("An error occurred"):
            raise Exception(contenuto)
        else:
            return contenuto
    else:
        raise Exception("Swap Error"+ response.text)



def swap_usdc_token(amount,block_chain:str, token_name:str):
    url = os.getenv("Host") + "/swap_usdc_cbtc?qta=" + str(amount)
    token=Token(block_chain, token_name)
    address="&address="+ token.address
    decimals="&decimals="+ str(token.decimals)
    symbol="&symbol="+token_name
    url=url+address+decimals+symbol
    response = requests.get(url)

    if response.ok:
        contenuto = response.text  # risposta come stringa
        if contenuto.startswith("An error occurred"):
            raise Exception(contenuto)
        else:
            return contenuto
    else:
        raise Exception("Swap Error"+ response.text)

def do_action(block_chain:str, action_id: str, action_type:str, amount:str, target_price:float , token_name:str, address:str):
    logger.info("Entered Do Action")
    logger.info("Action type")
    token = Token(block_chain, token_name)
    logger.info("Token " +token_name )
    token_price = token.get_token_price()
    logger.info("Token price="+ str(token_price))
    if action_type=="SELL":
        if token_price>=target_price:
            logger.info("Sell at " + str(token_price) )
            qta_sell=sell_token(amount, address,block_chain, token_name)
            action_done(qta_sell)
            return "SELL EXECUTE " + qta_sell
    elif action_type=="BUY":
        if token_price <= target_price:
            logger.info("Buy at " + token_price)
            qta_buy=buy_token(amount, address, token_name)
            action_done(qta_buy)
            return "BUY EXECUTE " + qta_buy
    return  None


def main():

    try:
      directory =os.getenv("STOP_DIR") 
      filename = "stop.txt"
      filepath = os.path.join(directory, filename)
      if  os.path.exists(filepath):
        logger.info("Stop file: exit ")
        sys.exit(0)     
      else:
        logger.info("Started")
        push_key = os.getenv("PUSH_KEY")
        pb = Pushbullet(push_key)
        logger.info("Push key done")
        target_price = 113000
        token_name = "coinbase-wrapped-btc"
        amount = "0.001"
        block_chain = "ETHEREUM"
        action_id = "1"
        action_type = "SELL"
        wallet_address = os.getenv("MY_ADDRESS")

        message=do_action(block_chain, action_id, action_type, amount, target_price, token_name, wallet_address)
        if message is not None:
            push = pb.push_note("Crypto bot",message)

    except Exception as e:
               logging.error(e)
if __name__ == "__main__":
    # load .env
    load_dotenv()
    main()
