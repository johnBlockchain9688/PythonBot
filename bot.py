# *********************************************************************************
# Date: 27/08/25
# Version: 1.2 (extended logging)
# Author: John Blockchain
# Mail: john.blockchain9688@gmail.com
# Description: Automated crypto trading bot interacting with AAVE and tokens.
# History of change:
#   - Fixed bug in action_done (wrong variable name)
#   - Added directory creation for STOP_DIR
#   - Added timeout for requests
#   - Improved error handling and input validation
#   - Fixed wrong call to buy_token
#   - Safer logging (no sensitive data)
#   - Added more detailed logging info for debugging and monitoring
# *********************************************************************************

from CryptoUtil import Token
from pushbullet import Pushbullet
from dotenv import load_dotenv
import traceback
import logging
import os
import time
import requests
from CryptoUtil.Token import Token
from CryptoUtil.AAVE import AAVE


logger = logging.getLogger('crypto_bot')


def action_done(qta: str):
    """Creates a stop file to signal the bot to stop further actions."""
    logger.info("Start action_done process")
    directory = os.getenv("STOP_DIR")

    if not directory:
        logger.error("STOP_DIR environment variable not set")
        raise Exception("STOP_DIR environment variable not set")

    os.makedirs(directory, exist_ok=True)
    filename = "stop.txt"
    filepath = os.path.join(directory, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("stop")
        logger.info(f"Stop file created at {filepath}")
    except Exception as e:
        logger.error(f"Error writing stop file: {e}", exc_info=True)
        raise
    logger.info("End action_done process")


def sell_token(amount_token: float, address: str, block_chain: str, token_name: str):
    """Withdraws a token from AAVE, swaps it into USDC, and re-deposits the USDC."""
    logger.info(f"Start SELL Token: {amount_token} {token_name} on {block_chain} for {address}")

    try:
        amount_token_float = float(amount_token)
    except ValueError:
        logger.error(f"Invalid token amount: {amount_token}")
        raise Exception(f"Invalid token amount: {amount_token}")

    defi_platform = AAVE(block_chain)
    token_sell = Token(block_chain, token_name)

    if amount_token_float > 0:
        logger.info("Withdrawing token from AAVE")
        defi_platform.withdraw(token_name, amount_token, address)
        time.sleep(3)

        balance = token_sell.balance_of(address)
        logger.info(f"Balance after withdraw: {balance}")
        if balance is None or balance < amount_token_float:
            raise Exception("Error: insufficient Token Balance")

        logger.info("Swapping token to USDC")
        amount_usdc = swap_token_usdc(amount_token, block_chain, token_name)
        logger.info(f"Swap result: {amount_usdc} USDC")
        time.sleep(3)

        try:
            usdc_to_aave = float(amount_usdc)
        except ValueError:
            logger.error(f"Invalid USDC amount returned: {amount_usdc}")
            raise Exception(f"Invalid USDC amount returned: {amount_usdc}")

        if usdc_to_aave > 0:
            logger.info(f"Depositing {usdc_to_aave} USDC into AAVE")
            defi_platform.deposit("USDC", amount_usdc, address)

        return amount_usdc

    logger.warning("Sell skipped because amount <= 0")
    return amount_token


def buy_token(amount_token: float, address: str, blockchain: str, token_name: str):
    """Withdraws USDC, swaps it into another token, and deposits the token into AAVE."""
    logger.info(f"Start BUY Token: {amount_token} {token_name} on {blockchain} for {address}")

    try:
        amount_token_float = float(amount_token)
    except ValueError:
        logger.error(f"Invalid token amount: {amount_token}")
        raise Exception(f"Invalid token amount: {amount_token}")

    defi_platform = AAVE(blockchain)
    logger.info(f"Withdrawing {amount_token_float} USDC from AAVE")
    defi_platform.withdraw("USDC", amount_token_float, address)

    logger.info("Swapping USDC to target token")
    amount_token_out = swap_usdc_token(amount_token_float, blockchain, token_name)
    logger.info(f"Swap result: {amount_token_out} {token_name}")

    logger.info(f"Depositing {amount_token_out} {token_name} into AAVE")
    defi_platform.deposit(token_name, amount_token_out, address)

    return amount_token_out


def swap_token_usdc(amount, block_chain: str, token_name: str):
    """Calls external API to swap a token into USDC."""
    host = os.getenv("Host")
    if not host:
        logger.error("Host environment variable not set")
        raise Exception("Host environment variable not set")

    token = Token(block_chain, token_name)
    url = f"{host}/swap_cbtc_usdc?qta={amount}&address={token.address}&decimals={token.decimals}&symbol={token_name}"

    logger.info(f"Calling API for token→USDC swap: {url}")
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as e:
        logger.error("Network error during swap_token_usdc", exc_info=True)
        raise Exception(f"Network error while swapping token to USDC: {e}")

    if response.ok:
        contenuto = response.text.strip()
        logger.debug(f"API response: {contenuto}")
        if contenuto.startswith("An error occurred"):
            logger.error(f"API returned error: {contenuto}")
            raise Exception(contenuto)
        return contenuto
    else:
        logger.error(f"Swap Error: {response.text}")
        raise Exception("Swap Error: " + response.text)


def swap_usdc_token(amount, block_chain: str, token_name: str):
    """Calls external API to swap USDC into another token."""
    host = os.getenv("Host")
    if not host:
        logger.error("Host environment variable not set")
        raise Exception("Host environment variable not set")

    token = Token(block_chain, token_name)
    url = f"{host}/swap_usdc_cbtc?qta={amount}&address={token.address}&decimals={token.decimals}&symbol={token_name}"

    logger.info(f"Calling API for USDC→token swap: {url}")
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as e:
        logger.error("Network error during swap_usdc_token", exc_info=True)
        raise Exception(f"Network error while swapping USDC to token: {e}")

    if response.ok:
        contenuto = response.text.strip()
        logger.debug(f"API response: {contenuto}")
        if contenuto.startswith("An error occurred"):
            logger.error(f"API returned error: {contenuto}")
            raise Exception(contenuto)
        return contenuto
    else:
        logger.error(f"Swap Error: {response.text}")
        raise Exception("Swap Error: " + response.text)


def do_action(block_chain: str, action_id: str, action_type: str, amount: str,
              target_price: float, token_name: str, address: str):
    """Executes a BUY or SELL action depending on the target price."""
    logger.info(f"Entered do_action: {action_type} {amount} {token_name} if price {'>=' if action_type=='SELL' else '<='} {target_price}")
    token = Token(block_chain, token_name)

    try:
        token_price = token.get_token_price()
    except Exception as e:
        logger.error("Error retrieving token price", exc_info=True)
        raise Exception(f"Error retrieving token price: {e}")

    if token_price is None:
        logger.error("Token price could not be retrieved")
        raise Exception("Token price could not be retrieved")

    logger.info(f"Token {token_name}, current price={token_price}")

    if action_type.upper() == "SELL":
        if token_price >= target_price:
            logger.info(f"Condition met: SELL at {token_price}")
            qta_sell = sell_token(amount, address, block_chain, token_name)
            action_done(qta_sell)
            return f"SELL EXECUTED {qta_sell}"

    elif action_type.upper() == "BUY":
        if token_price <= target_price:
            logger.info(f"Condition met: BUY at {token_price}")
            qta_buy = buy_token(amount, address, block_chain, token_name)
            action_done(qta_buy)
            return f"BUY EXECUTED {qta_buy}"

    logger.info("No action executed (conditions not met)")
    return None


def main():
    """Main entry point: checks stop file, executes action, and sends a Pushbullet notification."""
    logger.info("Bot starting...")
    try:
        directory = os.getenv("STOP_DIR")
        if not directory:
            logger.error("STOP_DIR environment variable not set")
            raise Exception("STOP_DIR environment variable not set")

        filename = "stop.txt"
        filepath = os.path.join(directory, filename)

        if os.path.exists(filepath):
            logger.warning("Stop file found: exiting")
            return
        else:
            logger.info("Stop file not found, proceeding with bot execution")

            push_key = os.getenv("PUSH_KEY")
            if not push_key:
                logger.error("PUSH_KEY environment variable not set")
                raise Exception("PUSH_KEY environment variable not set")

            pb = Pushbullet(push_key)
            logger.info("Pushbullet initialized successfully")

            # Example trade parameters
            target_price = 113000
            token_name = "coinbase-wrapped-btc"
            amount = "0.001"
            block_chain = "ETHEREUM"
            action_id = "1"
            action_type = "SELL"
            wallet_address = os.getenv("MY_ADDRESS")

            if not wallet_address:
                logger.error("MY_ADDRESS environment variable not set")
                raise Exception("MY_ADDRESS environment variable not set")

            logger.info(f"Executing action {action_id}: {action_type} {amount} {token_name}")
            message = do_action(block_chain, action_id, action_type, amount,
                                target_price, token_name, wallet_address)
            if message:
                pb.push_note("Crypto bot", message)
                logger.info(f"Notification sent: {message}")
            else:
                logger.info("No trade executed this run")

    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        traceback.print_exc()
    logger.info("Bot execution finished")


if __name__ == "__main__":
    load_dotenv()
    main()
