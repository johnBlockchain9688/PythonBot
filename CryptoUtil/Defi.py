# *********************************************************************************
# Date: 30/06/25
# Version: 1.0
# Author: John Blockchain
# mail=john.blockchain9688@gmail.com
# Description: 
# History of change:
# *****************************************************************************
from CryptoUtil.Chain import Chain
import logging
logger = logging.getLogger(__name__)

class Defi:
    def __init__(self, chain: str):
        self.chain_name=chain
        self.blockChain=Chain(chain)
        self.web3=self.blockChain.web3



