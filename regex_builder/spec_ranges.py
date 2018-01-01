#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
from .common import Flags, CompileContext
from .expr_abs import ICharRangeRegexExpr, ISingledCharRegexExpr
from .expr import RegexExpr, CharRangeRegexExpr

class DigitCharRangeRegexExpr(CharRangeRegexExpr):
    def __init__(self):
        super().__init__('0', '9')


class LowerCaseLetterCharRangeRegexExpr(CharRangeRegexExpr):
    def __init__(self):
        super().__init__('a', 'z')


class UpperCaseLetterCharRangeRegexExpr(CharRangeRegexExpr):
    def __init__(self):
        super().__init__('A', 'Z')


class DotCharRangeRegexExpr(RegexExpr, ICharRangeRegexExpr, ISingledCharRegexExpr):
    NOT_CHARS = '\r\n'

    def __repr__(self):
        return 'Dot()'

    def _compile(self, context: CompileContext):
        context.buffer.write('.')

    def _flag(self, f):
        return f in (Flags.char, Flags.single_char)

    def has(self, value):
        return value not in '\r\n'

    def get_order_code(self) -> int:
        return 0

    def subset(self, other) -> bool:
        for ch in self.NOT_CHARS:
            if other.has(ch):
                return False
        return True


# register all class
for cls in list(vars().values()):
    if not inspect.isclass(cls):
        continue
    if issubclass(cls, CharRangeRegexExpr) and cls is not CharRangeRegexExpr:
        ins = cls()
        CharRangeRegexExpr.RANGE_VALUE_MAP[ins._range] = ins
