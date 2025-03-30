# logging to betterstack.com 
from utils.config import LOGGER_TOKEN
from logtail import LogtailHandler
import logging

handler = LogtailHandler(
    source_token=LOGGER_TOKEN,
    host='https://s1193983.eu-nbg-2.betterstackdata.com',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = []
logger.addHandler(handler)


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)  # Add Console handler
