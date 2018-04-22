#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
from envparse import Env
from algoliasearch import algoliasearch
from telegram import Bot, InlineQueryResultCachedGif, ParseMode
from telegram.ext import (BaseFilter,
                          ChosenInlineResultHandler,
                          CommandHandler,
                          ConversationHandler,
                          Dispatcher,
                          Filters,
                          InlineQueryHandler,
                          MessageHandler,
                          Updater)

# Configuration
env = Env(
    BOT_TOKEN=str,
    ALGOLIA_API_KEY=str,
    ALGOLIA_APP_ID=str,
    ALGOLIA_INDEX_NAME=str,
    MODERATOR_ID=dict(cast=str, default=''),
    LOG_LEVEL=dict(cast=lambda l: getattr(logging, l.upper(), logging.INFO),
        default='INFO'),
    WEBHOOK=bool,
    WEBHOOK_HOST=str,
    WEBHOOK_PORT=int,
    WEBHOOK_PATH=str,
    WEBHOOK_URL=str
)
env.read_envfile()

BOT_TOKEN = env('BOT_TOKEN')
ALGOLIA_APP_ID = env('ALGOLIA_APP_ID')
ALGOLIA_API_KEY = env('ALGOLIA_API_KEY')
ALGOLIA_INDEX_NAME = env('ALGOLIA_INDEX_NAME')
MODERATOR_ID = env('MODERATOR_ID')
WEBHOOK = env('WEBHOOK')
WEBHOOK_HOST = env('WEBHOOK_HOST')
WEBHOOK_PORT = env('WEBHOOK_PORT')
WEBHOOK_PATH = env('WEBHOOK_PATH')
WEBHOOK_URL = env('WEBHOOK_URL')

# Setup logging
logging.basicConfig(level=env('LOG_LEVEL'),
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%d-%m-%Y %H:%M:%S')
logger = logging.getLogger(__name__)

# Conversation state
CAPTION=1
SELECTION=2

class VideoFilter(BaseFilter):

    def filter(self, message):
        return (bool(message.document) and
            ((message.document.mime_type == "video/mp4") or
             (message.document.mime_type == "image/gif")))

def start(bot, update):
    msg = u"Hello, {username}! Send me a GIF with some description."
    update.message.reply_text(msg.format(
        username=update.message.from_user.first_name))

def help(bot, update):
    text = ("This bot can help you find and share GIFs. It works automatically,"
        " no need to add it anywhere. Simply open any of your chats and type "
        "`@gifdotbot something` in the message field. Then tap on a result to "
        "send.\n\n If you want to upload your own GIF, just send it to bot and "
        "enter text description.")

    update.message.reply_text(text, parse_mode = ParseMode.MARKDOWN)

def error(bot, update, error):
    logger.exception(error)

def on_video(bot, update, user_data):
    keywords = update.message.caption
    file_id = update.message.document.file_id
    author_id = int(update.message.from_user.id)
    user_data['file_id'] = file_id

    if not keywords:
        update.message.reply_text("Please, enter text description. /cancel")
        return CAPTION

    bot.index.add_objects([{
        "keywords": keywords,
        "file_id": file_id,
        "created": datetime.now(),
        "owner": author_id,
        "rank": 0
    }])

    update.message.reply_text("The GIF was added. Thank you!")

    return ConversationHandler.END

def on_video_caption(bot, update, user_data):
    keywords = update.message.text
    file_id = user_data['file_id']
    author_id = int(update.message.from_user.id)

    if not keywords:
        update.message.reply_text("Please, enter text description. /cancel")
        return CAPTION

    bot.index.add_objects([{
        "keywords": keywords,
        "file_id": file_id,
        "created": datetime.now(),
        "owner": author_id
    }])

    update.message.reply_text("The GIF was added. Thank you!")

    return ConversationHandler.END

def remove_start(bot, update):
    author_id = int(update.message.from_user.id)
    if MODERATOR_ID != "" and author_id == int(MODERATOR_ID):
        update.message.reply_text('Please choose gif. /help')
        return SELECTION

    logger.warning("Remove attempt id={}".format(author_id))
    update.message.reply_text('You don\'t have permission to access this area. /help')
    return ConversationHandler.END

def remove_select(bot, update):
    file_id = update.message.document.file_id.strip()
    if file_id != "":
        bot.index.delete_by_query(file_id)
        update.message.reply_text('Success. Select next one or /cancel')
    else:
        update.message.reply_text('Try again or /cancel')
    return SELECTION

def cancel(bot, update):
    update.message.reply_text('Action canceled. /help')
    return ConversationHandler.END

def inline_search(bot, update):
    page = 0
    results = list()
    opts = {}

    query = update.inline_query.query

    if update.inline_query.offset != '':
        page = int(update.inline_query.offset)

    logger.info(u"Inline query: '{}' (page={})".format(query, page))

    res = bot.index.search(query, {
        "hitsPerPage": 10,
        "page": page,
    })

    for hit in res["hits"]:
        results.append(InlineQueryResultCachedGif(
            id=hit["objectID"], gif_file_id=hit["file_id"]))

    next_page = page + 1
    if next_page < res["nbPages"]:
        opts['next_offset'] = str(next_page)

    update.inline_query.answer(results, **opts)

def inline_result(bot, update):
    obj_id = update.chosen_inline_result.result_id
    logger.info("Gif with object_id={} choosen".format(obj_id))

def unknown_message(bot, update):
    if update.message:
        if update.message.text:
            if update.message.text.startswith('/'):
                text = "Unknown command. /help"
            else:
                text = "This is inline bot. /help"
        else:
            text = "Unsupported message type. /help"
        update.message.reply_text(text)

add_gif_conversation = ConversationHandler(
    entry_points=[MessageHandler(VideoFilter(), on_video,
        pass_user_data=True)],
    states={
        CAPTION: [MessageHandler(Filters.text, on_video_caption,
            pass_user_data=True)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

remove_gif_conversation = ConversationHandler(
    entry_points=[CommandHandler('remove', remove_start)],
    states={
        SELECTION: [MessageHandler(VideoFilter(), remove_select)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

def main():
    # initialize algolia client
    client = algoliasearch.Client(ALGOLIA_APP_ID, ALGOLIA_API_KEY)
    index = client.init_index(ALGOLIA_INDEX_NAME)
    index.set_settings({
        "searchableAttributes": ["keywords", "file_id"],
        'customRanking': ['asc(created)'], # fresh on top
        "typoTolerance": True,
        "disableTypoToleranceOnAttributes": ["file_id"],
        "ignorePlurals": True
    })

    # initialize bot
    upd = Updater(token=BOT_TOKEN)
    upd.bot.index = index
    dp = upd.dispatcher
    dp.add_handler(remove_gif_conversation)
    dp.add_handler(add_gif_conversation)
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(InlineQueryHandler(inline_search))
    dp.add_handler(ChosenInlineResultHandler(inline_result))
    dp.add_handler(MessageHandler(Filters.all, unknown_message))
    dp.add_error_handler(error)

    if WEBHOOK:
        upd.start_webhook(listen=WEBHOOK_HOST, port=WEBHOOK_PORT,
            url_path=WEBHOOK_PATH)
        upd.bot.set_webhook(WEBHOOK_URL)
    else:
        upd.bot.set_webhook() # remove webhook
        upd.start_polling(timeout=30)
    upd.idle()

if __name__ == "__main__":
    main()
