#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .expr import CharSeqRegexExpr

class DigitCharSeqRegexExpr(CharSeqRegexExpr):
    def __init__(self):
        super().__init__('0', '9')

    def __repr__(self):
        return 'CharSeq(0-9)'


class LowerCaseLetterCharSeqRegexExpr(CharSeqRegexExpr):
    def __init__(self):
        super().__init__('a', 'z')

    def __repr__(self):
        return 'CharSeq(a-z)'


class UpperCaseLetterCharSeqRegexExpr(CharSeqRegexExpr):
    def __init__(self):
        super().__init__('A', 'Z')

    def __repr__(self):
        return 'CharSeq(A-Z)'
