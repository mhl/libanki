# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
DB tools
====================

SessionHelper is a wrapper for the standard sqlalchemy session, which provides
some convenience routines, and manages transactions itself.

object_session() is a replacement for the standard object_session(), which
provides the features of SessionHelper, and avoids taking out another
transaction.
"""
__docformat__ = 'restructuredtext'

try:
    from pysqlite2 import dbapi2 as sqlite
except ImportError:
    try:
        from sqlite3 import dbapi2 as sqlite
    except:
        raise "Please install pysqlite2 or python2.5"
sqlite.enable_shared_cache(True)

from sqlalchemy import (Table, Integer, Float, Column, MetaData,
                        ForeignKey, Boolean, String, Date, UniqueConstraint)
from sqlalchemy import create_engine
from sqlalchemy.orm import mapper, sessionmaker, relation, backref, \
     object_session as _object_session
from sqlalchemy.sql import select, text, and_
from sqlalchemy.exceptions import DBAPIError, OperationalError

# sqlalchemy didn't handle the move to unicodetext nicely
try:
    from sqlalchemy import UnicodeText
except ImportError:
    from sqlalchemy import Unicode
    UnicodeText = Unicode

# dump location of non-unicode string
from sqlalchemy import util
import traceback
oldWarn = util.warn
def newWarn(*args, **kwargs):
    traceback.print_stack()
    oldWarn(*args, **kwargs)
util.warn = newWarn



metadata = MetaData()

# this class assumes the provided session is called with transactional=False
class SessionHelper(object):
    "Add some convenience routines to a session."

    def __init__(self, session, lock=False, transaction=True):
        self._session = session
        self._lock = lock
        self._transaction = transaction
        if self._transaction:
            self._session.begin()
        if self._lock:
            self._lockDB()
        self._seen = True

    def __getattr__(self, k):
        return getattr(self.__dict__['_session'], k)

    def scalar(self, sql, **args):
        return self.execute(text(sql), args).scalar()

    def all(self, sql, **args):
        return self.execute(text(sql), args).fetchall()

    def first(self, sql, **args):
        return self.execute(text(sql), args).fetchone()

    def column0(self, sql, **args):
        return [x[0] for x in self.execute(text(sql), args).fetchall()]

    def statement(self, sql, **kwargs):
        "Execute a statement without returning any results. Flush first."
        return self.execute(text(sql), kwargs)

    def statements(self, sql, data):
        "Execute a statement across data. Flush first."
        return self.execute(text(sql), data)

    def __repr__(self):
        return repr(self._session)

    def commit(self):
        self._session.commit()
        if self._transaction:
            self._session.begin()
        if self._lock:
            self._lockDB()

    def _lockDB(self):
        "Take out a write lock."
        self._session.execute(text("update decks set modified=modified"))

def object_session(*args):
    s = _object_session(*args)
    if s:
        return SessionHelper(s, transaction=False)
    return None

