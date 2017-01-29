#!/usr/bin/env python
# -*- coding: utf-8 -*-

from queue import Queue

from telegram import Bot, InlineQueryResultCachedGif
from telegram.utils.webhookhandler import WebhookHandler, WebhookServer
from telegram.ext import (BaseFilter,
                          ChosenInlineResultHandler,
                          CommandHandler,
                          Dispatcher,
                          Filters,
                          InlineQueryHandler,
                          MessageHandler,
                          Updater)

from settings import *
from models import Gif, GifIndex
import stemmer

# Custom filter for GIFs
class VideoFilter(BaseFilter):

    def filter(self, message):
        return (bool(message.document) and
            ((message.document.mime_type == "video/mp4") or
             (message.document.mime_type == "image/gif")))

# Welcome message
def start(bot, update):
    msg = u"Hello, {username}! Send me a gif with some description."
    update.message.reply_text(msg.format(
        username=update.message.from_user.first_name))

# Help message
def help(bot, update):
    msg = ("1. Type @gifdotbot in the message field in any chat, " +
           "then type some keywords.\r\n" +
           "2. Select any GIF to instantly send it to the chat.\r\n" +
           "3. To upload your own GIF just send it to bot with description " +
           "in caption.")
    update.message.reply_text(msg)

# Error handling function
def error(bot, update, error):
    logger.error(u'Update "{}" caused error "{}"'.format(update, error))

# Function to receive animations
def video_msg(bot, update):
    try:
        msg = update.message or update.edited_message
        if not msg.caption:
            raise ValueError('You forgot caption. Try edit your GIF.')

        file_id = msg.document.file_id
        author_id = int(msg.from_user.id)

        try:
            gif = Gif.select().where(Gif.file_id == file_id).get()
            raise ValueError('The GIF is already exist.')
        except Gif.DoesNotExist:
            pass

        keywords = stemmer.stem_text(msg.caption)
        gif = Gif(file_id=file_id, owner=author_id)
        gif.save()
        GifIndex.add_item(gif, keywords)
        logger.info(u"GIF added: '{}'".format(msg.caption))
        msg.reply_text("The GIF has been added. Thank you!")

    except ValueError as e:
        msg.reply_text(str(e))
    except Exception as e:
        logger.error(str(e))
        msg.reply_text("An error has occurred.")

# Function to receive other messages
def other_msg(bot, update):
    update.message.reply_text("Unknown message. /help")

# Function for handling choosen animation
def inline_result(bot, update):
    gifid = int(update.chosen_inline_result.result_id)
    logger.info("Gif with id={} choosen".format(gifid))
    query = (Gif
             .update(rank=Gif.rank + 1)
             .where(Gif.id == gifid))
    query.execute()

# Inline query handling
def inline_query(bot, update):
    limit = 10
    offset = 0
    results = list()

    query = update.inline_query.query

    if update.inline_query.offset != '':
        offset = int(update.inline_query.offset)

    logger.info(u"Inline query: '{}' (offset={})".format(query, offset))

    gifs = Gif.select().limit(limit).offset(offset)

    if query:
        terms = stemmer.stem_text(query)
        gifs = (gifs.join(
                    GifIndex,
                    on=(Gif.id == GifIndex.docid))
                .where(GifIndex.match(terms))
                .order_by(GifIndex.bm25()))
    else:
        gifs = gifs.order_by(Gif.rank.desc())

    for gif in gifs:
        results.append(InlineQueryResultCachedGif(
            id=str(gif.id), gif_file_id=gif.file_id))

    opts = {}
    if results:
        if len(results) == limit:
            opts['next_offset'] = offset + limit

    update.inline_query.answer(results, **opts)

def set_handlers(dp):
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(VideoFilter(), video_msg, allow_edited=True))
    dp.add_handler(ChosenInlineResultHandler(inline_result))
    dp.add_handler(InlineQueryHandler(inline_query))
    dp.add_handler(MessageHandler(Filters.all, other_msg))
    dp.add_error_handler(error)

def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(bot, None, 0)
    set_handlers(dp)
    update_queue = Queue()

    httpd = WebhookServer(('127.0.0.1', WEBHOOK_PORT),
        WebhookHandler, update_queue, WEBHOOK_URI, bot)

    while True:
        try:
            httpd.handle_request()
            if not update_queue.empty():
                update = update_queue.get()
                dp.process_update(update)
        except KeyboardInterrupt:
            exit(0)

if __name__ == "__main__":
    main()
