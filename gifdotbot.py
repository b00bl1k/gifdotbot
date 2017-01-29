#!/usr/bin/env python
# -*- coding: utf-8 -*-

from queue import Queue

from telegram import Bot, InlineQueryResultCachedGif
from telegram.utils.webhookhandler import WebhookHandler, WebhookServer
from telegram.ext import (BaseFilter,
                          ChosenInlineResultHandler,
                          CommandHandler,
                          ConversationHandler,
                          Dispatcher,
                          Filters,
                          InlineQueryHandler,
                          MessageHandler,
                          Updater)

from settings import *
from models import Gif, GifIndex
import stemmer

CAPTION = 1

# Custom filter for GIFs
class VideoFilter(BaseFilter):

    def filter(self, message):
        return (bool(message.document) and
            ((message.document.mime_type == "video/mp4") or
             (message.document.mime_type == "image/gif")))

# Check for GIF is exist
def gif_exists(file_id):
    try:
        gif = Gif.select().where(Gif.file_id == file_id).get()
        return True
    except Gif.DoesNotExist:
        return False

# Add GIF to DB
def add_gif(file_id, owner_id, desc):
    gif = Gif(file_id=file_id, owner=owner_id)
    gif.save()
    GifIndex.add_item(gif, stemmer.stem_text(desc))

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

# Cancel upload
def cancel(bot, update):
    update.message.reply_text('Upload canceled. /help')
    return ConversationHandler.END

# Function to handle GIF description
def caption_msg(bot, update, user_data):
    msg = update.message
    author_id = int(update.message.from_user.id)

    if msg.text == '':
        msg.reply_text("Please, type some description. /cancel")
        return CAPTION
    elif stemmer.stem_text(msg.text) == '':
        msg.reply_text("Description is too short. Try again. /cancel")
        return CAPTION

    if gif_exists(user_data['file_id']):
        msg.reply_text('The GIF is already exist.')
        return ConversationHandler.END

    try:
        add_gif(user_data['file_id'], author_id, msg.text)
        msg.reply_text("The GIF has been added. Thank you!")
    except ValueError as e:
        msg.reply_text(str(e))
    except Exception as e:
        msg.reply_text("An error has occurred.")
        logger.error(str(e))
    finally:
        return ConversationHandler.END

# Function to receive GIFs
def video_msg(bot, update, user_data):
    msg = update.message
    file_id = msg.document.file_id
    author_id = int(msg.from_user.id)

    if gif_exists(file_id):
        msg.reply_text('The GIF is already exist.')
        return ConversationHandler.END

    if not msg.caption:
        user_data['file_id'] = file_id
        msg.reply_text("Now type some description. /cancel")
        return CAPTION

    try:
        add_gif(file_id, author_id, msg.caption)
        msg.reply_text("The GIF has been added. Thank you!")
    except ValueError as e:
        msg.reply_text(str(e))
    except Exception as e:
        msg.reply_text("An error has occurred.")
        logger.error(str(e))
    finally:
        return ConversationHandler.END

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
    add_handler = ConversationHandler(
        entry_points=[MessageHandler(VideoFilter(), video_msg,
            pass_user_data=True)],
        states={
            CAPTION: [MessageHandler(Filters.text, caption_msg,
                pass_user_data=True)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(add_handler)
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
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
