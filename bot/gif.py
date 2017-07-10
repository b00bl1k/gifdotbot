#!/usr/bin/env python
# -*- coding: utf-8 -*-

class GifStorage():

    def __init__(self):
        self.error_msg = ''

    def add(self, file_id, author_id, keywords):
        self.error_msg = 'Not implemented'
        return False

    def is_exists(self, file_id):
        return False

    def error(self):
        return self.error_msg

storage = GifStorage()