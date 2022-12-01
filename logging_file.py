import logging


formatter_cmd = logging.Formatter('(%(levelname)s):%(asctime)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
formatter_file = logging.Formatter('%(asctime)s - (levelerror: %(levelname)s): %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('cups_printers.log')
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter_file)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_cmd)
stream_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)