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
