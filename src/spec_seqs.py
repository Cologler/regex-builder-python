#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
from .expr import CharRangeRegexExpr

class DigitCharRangeRegexExpr(CharRangeRegexExpr):
    def __init__(self):
        super().__init__('0', '9')

    def __repr__(self):
        return 'CharSeq(0-9)'

class LowerCaseLetterCharRangeRegexExpr(CharRangeRegexExpr):
    def __init__(self):
        super().__init__('a', 'z')

    def __repr__(self):
        return 'CharSeq(a-z)'

class UpperCaseLetterCharRangeRegexExpr(CharRangeRegexExpr):
    def __init__(self):
        super().__init__('A', 'Z')

    def __repr__(self):
        return 'CharSeq(A-Z)'

# register all class
for cls in list(vars().values()):
    if not inspect.isclass(cls):
        continue
    if issubclass(cls, CharRangeRegexExpr) and cls is not CharRangeRegexExpr:
        ins = cls()
        CharRangeRegexExpr.RANGE_VALUE_MAP[ins._range] = ins
