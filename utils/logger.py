import logging
import os
import sys
from datetime import datetime

from utils.paths import LOG


#
# logger_both = logging.getLogger('both')
# logger_both.setLevel(logging.DEBUG)
#
# output_file_handler = logging.FileHandler(f"log_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.log")
# stdout_handler = logging.StreamHandler(sys.stdout)
#
# logger_both.addHandler(output_file_handler)
# logger_both.addHandler(stdout_handler)


def initFileLogger(prefix: str):
    logger = logging.getLogger('task'+prefix)
    logger.setLevel(logging.DEBUG)

    output_file_handler = logging.FileHandler(os.path.join(LOG, f"log_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}_{prefix}.log"), encoding='utf8')

    logger.addHandler(output_file_handler)
    return logger


def getLogger(prefix: str):
    return logging.getLogger('task'+prefix)

