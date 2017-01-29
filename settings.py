# -*- coding: utf-8 -*-

import logging
from envparse import Env

def log_level(level):
    levels = {'DEBUG': logging.DEBUG,
              'INFO': logging.INFO,
              'WARNING': logging.WARNING,
              'ERROR': logging.ERROR,
              'CRITICAL': logging.CRITICAL}

    if level not in levels.keys():
        return logging.INFO
    else:
        return levels[level]


env = Env(
    TELEGRAM_BOT_TOKEN=str,
    TELEGRAM_WEBHOOK_URL=str,
    TELEGRAM_WEBHOOK_URI=str,
    SERVER_WEBHOOK_PORT=dict(cast=int, default=8080),
    LOG_LEVEL=dict(cast=log_level, default='INFO')
)
env.read_envfile()

logging.basicConfig(level=env('LOG_LEVEL'),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%d-%m-%Y %H:%M:%S')
logger = logging.getLogger(__name__)

BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = env('TELEGRAM_WEBHOOK_URL')
WEBHOOK_URI = env('TELEGRAM_WEBHOOK_URI')
WEBHOOK_PORT = env.int('SERVER_WEBHOOK_PORT')
