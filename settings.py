# -*- coding: utf-8 -*-

import logging
from envparse import Env

env = Env(
    TELEGRAM_BOT_TOKEN=str,
    TELEGRAM_WEBHOOK_URL=str,
    TELEGRAM_WEBHOOK_URI=str,
    SERVER_WEBHOOK_PORT=dict(cast=int, default=8080)
)
env.read_envfile()

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%d-%m-%Y %H:%M:%S')
logger = logging.getLogger(__name__)

BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = env('TELEGRAM_WEBHOOK_URL')
WEBHOOK_URI = env('TELEGRAM_WEBHOOK_URI')
WEBHOOK_PORT = env.int('SERVER_WEBHOOK_PORT')
