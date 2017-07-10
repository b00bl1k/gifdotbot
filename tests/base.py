#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import Mock
import unittest
import telegram

class BaseCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.from_user = telegram.User(id=123, first_name=u'Test name')

    def make_text_message(self, text=''):
        message = telegram.Message(message_id=1, date=None, chat=None,
            from_user=self.from_user, text=text)
        message.reply_text = Mock()
        return message

    def make_gif_message(self, caption=None):
        document = telegram.Document(file_id='123', mime_type='image/gif')
        message = telegram.Message(message_id=1, date=None, chat=None,
            from_user=self.from_user, document=document, caption=caption)
        message.reply_text = Mock()
        return message

    def text_result(self, message):
        return message.reply_text.call_args[0][0]

