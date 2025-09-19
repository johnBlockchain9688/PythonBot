
import os
import sys
from dotenv import load_dotenv
import logging
import logging.handlers

_version_ = '1.1.42'
load_dotenv()

#Set logger with required log level as base 
loggerInstance = logging.getLogger('crypto_bot')
loggerInstance.setLevel(logging.INFO)
log_location = os.getenv("LOG_LOCATION")
# Configure the handler with filePath,maxBytes and backupCount
# maxBytes - theMaxSizeOfLogFileInBytes
# backupCount - numberOFBackUpFiles to be created ex: logFile1,logFile2 etc (after log rotation)
handler = logging.handlers.RotatingFileHandler(log_location,
                                               maxBytes=100000,
                                               backupCount=30)
#Specify the required format                                               
formatter = logging.Formatter('%(asctime)s %(filename)s %(funcName)s %(lineno)d %(levelname)s %(message)s')
#Add formatter to handler
handler.setFormatter(formatter)
#Initialize logger instance with handler
loggerInstance.addHandler(handler)

# writing to stdout
handler2 = logging.StreamHandler(sys.stdout)
handler2.setLevel(logging.INFO)
handler2.setFormatter(formatter)
loggerInstance.addHandler(handler2)
