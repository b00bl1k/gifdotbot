#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bot import gif

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

CAPTION = 1


# Custom filter for GIFs
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
        "send.\n\n"
        "If you want to upload your own GIF, just send it to bot and enter text"
        " description.")

    update.message.reply_text(text, parse_mode = ParseMode.MARKDOWN)

def on_video_caption(bot, update, user_data):
    keywords = update.message.text
    file_id = user_data['file_id']
    author_id = int(update.message.from_user.id)

    if update.message.text == '':
        update.message.reply_text("Please, enter text description. /cancel")
        return CAPTION

    if gif.storage.add(file_id, author_id, keywords):
        update.message.reply_text("The GIF was added. Thank you!")
    else:
        update.message.reply_text("Error: {}".format(gif.storage.error()))

    return ConversationHandler.END

def on_video(bot, update, user_data):
    keywords = update.message.caption
    file_id = update.message.document.file_id
    author_id = int(update.message.from_user.id)
    user_data['file_id'] = file_id

    if gif.storage.is_exists(file_id):
        update.message.reply_text('The GIF is already exist.')
        return ConversationHandler.END

    if not keywords:
        update.message.reply_text("Please, enter text description. /cancel")
        return CAPTION

    if gif.storage.add(file_id, author_id, keywords):
        update.message.reply_text("The GIF was added. Thank you!")
    else:
        update.message.reply_text("Error: {}".format(gif.storage.error()))

    return ConversationHandler.END

def on_video_cancel(bot, update):
    update.message.reply_text('Upload canceled. /help')
    return ConversationHandler.END

add_handler = ConversationHandler(
    entry_points=[MessageHandler(VideoFilter(), on_video,
        pass_user_data=True)],
    states={
        CAPTION: [MessageHandler(Filters.text, on_video_caption,
            pass_user_data=True)]
    },
    fallbacks=[CommandHandler('cancel', on_video_cancel)]
)
