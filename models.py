# -*- coding: utf-8 -*-

import datetime

from peewee import (Model,
                    DateTimeField,
                    ForeignKeyField,
                    BigIntegerField,
                    CharField,
                    IntegerField,
                    TextField,
                    OperationalError)

from playhouse.sqlite_ext import (FTSModel,
                                  SqliteExtDatabase,
                                  SearchField)
from playhouse.migrate import (migrate,
                               SqliteMigrator,
                               SqliteDatabase)

db = SqliteExtDatabase('bot.db')

class Gif(Model):
    file_id = CharField(max_length=100)
    created = DateTimeField(default=datetime.datetime.now)
    owner = BigIntegerField()
    rank = BigIntegerField(default=0)

    class Meta:
        database = db

    def __repr__(self):
        return "<Gif(id={}, owner={}, rank={})>".format(
            self.file_id, self.owner, self.rank)

class GifIndex(FTSModel):
    keywords = SearchField()

    class Meta:
        database = db

    @staticmethod
    def add_item(gif, keywords):
        GifIndex.insert({
            GifIndex.docid: gif.id,
            GifIndex.keywords: keywords}).execute()

    def __repr__(self):
        return "<GifIndex> {}".format(self.keywords)

if __name__ == "__main__":
    db.create_tables([Gif, GifIndex])
    GifIndex.rebuild()
    GifIndex.optimize()
