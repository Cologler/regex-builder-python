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


class Flags:
    char = 1


class ReduceContext:
    def __init__(self, root_node=None):
        self._root_node = root_node

    @property
    def root_node(self):
        return self._root_node

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def scope(self, root_node):
        return ReduceContext(root_node=root_node)


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
