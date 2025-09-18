# *********************************************************************************
# Date: 28/08/25
# Version: 1.0
# Author: John Blockchain
# mail=john.blockchain9688@gmail.com
# Description: 
# History of change:
# *****************************************************************************
import json



with open("/home/mbaraldi/mySoftware/mycryptobot/conf/aave_eth_contract_abi.json") as f:
        file_json1 = f.read()
        y = json.dumps(file_json1, ensure_ascii=True)
        print(y)

