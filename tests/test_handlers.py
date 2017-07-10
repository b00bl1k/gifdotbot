#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import Mock, patch
import unittest
import telegram

from tests import base
from bot import handlers, gif

class TestHandlers(base.BaseCase):

    def test_start(self):
        message = self.make_text_message('/start')
        update = telegram.Update(update_id=1, message=message)
        handlers.start(None, update)

        self.assertIn('Hello', self.text_result(message))
        self.assertIn(self.from_user.first_name, self.text_result(message))

    def test_help(self):
        message = self.make_text_message('/help')
        update = telegram.Update(update_id=1, message=message)
        handlers.help(None, update)

        self.assertIn('help', self.text_result(message))

    def test_on_video_cancel(self):
        message = self.make_text_message('/cancel')
        update = telegram.Update(update_id=1, message=message)
        result = handlers.on_video_cancel(None, update)

        self.assertEqual(result, telegram.ext.ConversationHandler.END)
        self.assertIn('/help', self.text_result(message))

    def test_on_video_without_caption(self):
        user_data = {}
        message = self.make_gif_message()
        update = telegram.Update(update_id=1, message=message)
        result = handlers.on_video(None, update, user_data)

        self.assertEqual(result, handlers.CAPTION)
        self.assertIn('/cancel', self.text_result(message))

    def test_on_video_with_caption(self):
        user_data = {}
        message = self.make_gif_message('With caption')
        update = telegram.Update(update_id=1, message=message)

        with patch('bot.gif.storage.add') as mock_add:
            mock_add.return_value = True
            result = handlers.on_video(None, update, user_data)
            self.assertEqual(result, telegram.ext.ConversationHandler.END)

        self.assertIn('added', self.text_result(message))

    def test_on_video_empty_caption(self):
        user_data = {'file_id': '12323'}
        message = self.make_text_message()
        update = telegram.Update(update_id=1, message=message)
        result = handlers.on_video_caption(None, update, user_data)

        self.assertEqual(result, handlers.CAPTION)
        self.assertIn('/cancel', self.text_result(message))

    def test_on_video_caption_add_success(self):
        user_data = {'file_id': '12323'}
        message = self.make_text_message('Text')
        update = telegram.Update(update_id=1, message=message)

        with patch('bot.gif.storage.add') as mock_add:
            mock_add.return_value = True
            result = handlers.on_video_caption(None, update, user_data)
            self.assertEqual(result, telegram.ext.ConversationHandler.END)

        self.assertIn('added', self.text_result(message))

    def test_on_video_caption_add_fail(self):
        user_data = {'file_id': '12323'}
        message = self.make_text_message('Text')
        update = telegram.Update(update_id=1, message=message)

        with patch('bot.gif.storage.add') as mock_add:
            mock_add.return_value = False
            result = handlers.on_video_caption(None, update, user_data)
            self.assertEqual(result, telegram.ext.ConversationHandler.END)

        self.assertIn('Error', self.text_result(message))


