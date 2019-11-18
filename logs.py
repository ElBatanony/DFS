import logging
import sys

logging.root.setLevel(level=logging.NOTSET)
logger = logging.getLogger('')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.addHandler(logging.FileHandler('naming_server_logs.txt'))
