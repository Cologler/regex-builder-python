#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from io import StringIO
from enum import Enum
from collections import namedtuple

class RegexStyle:
    python = 1
    csharp = 2


class ReduceContext:
    def __init__(self, root_node, *, parent_node=None):
        self._root_node = root_node
        self._parent_node = parent_node

    @property
    def root_node(self):
        return self._root_node

    @property
    def parent_node(self):
        return self._parent_node

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def scope(self, node):
        ''' create a scoped ReduceContext for the node. '''
        return ReduceContext(root_node=self.root_node, parent_node=node)


class CompileContext:
    def __init__(self, **kwargs):
        self._buffer = StringIO()
        self._style = kwargs.get('style', RegexStyle.python)

    @property
    def buffer(self):
        return self._buffer

    @property
    def style(self):
        return self._style


def get_char_code(value) -> int:
    ''' get unicode code point from a char. '''
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if len(value) == 1: # case char
            return ord(value)
        if value.startswith('/u'): # case unicode
            return int(value[2:], base=16)
        raise ValueError
    else:
        raise TypeError
