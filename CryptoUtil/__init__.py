
import os
from dotenv import load_dotenv
import logging

_version_ = '1.1.42'
load_dotenv()



logging.basicConfig(level=logging.INFO,filename='CryptoUtil.log',format='%(asctime)s %(levelname)s:%(message)s')