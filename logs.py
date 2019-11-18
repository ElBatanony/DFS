import logging
import sys

logger = logging.getLogger()


def initialize_logs(file_name):
    logging.root.setLevel(level=logging.NOTSET)
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.addHandler(logging.FileHandler(file_name))
