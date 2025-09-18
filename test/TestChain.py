from CryptoUtil.Chain import Chain
from CryptoUtil.Token import Token
from CryptoUtil.AAVE import AAVE
import os

print(f'create Chain object')

#platform=AAVE("base")
token= Token("nn","dd")
defi_platform= AAVE("ETHEREUM")
my_address = os.getenv("MY_ADDRESS")
#defi_platform.deposit_eth(0.02,my_address)
#defi_platform.borrow_eth(0.001,my_address)
#defi_platform.repay_eth(0.002,my_address)
#defi_platform.withdraw_eth(0.07,my_address)
#Se > deposito ripaga tutto
#defi_platform.deposit("AAVE",100,my_address)
#defi_platform.borrow("WBTC",0.01,my_address)
#defi_platform.withdraw("AAVE",1,my_address)
defi_platform.get_user_account_data(my_address)

