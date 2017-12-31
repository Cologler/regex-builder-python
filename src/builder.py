#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .expr import (
    RegexExpr,
    CharRegexExpr,
    CharSeqRegexExpr,
    StringRegexExpr,
    EMPTY
)
from .spec_seqs import (
    DigitCharSeqRegexExpr,
    LowerCaseLetterCharSeqRegexExpr,
    UpperCaseLetterCharSeqRegexExpr
)

class RegexBuilder:
    def digit(self) -> RegexExpr:
        return DigitCharSeqRegexExpr()

    def lower_case_letter(self) -> RegexExpr:
        return LowerCaseLetterCharSeqRegexExpr()

    def upper_case_letter(self) -> RegexExpr:
        return UpperCaseLetterCharSeqRegexExpr()

    def char(self, ch: str) -> RegexExpr:
        return CharRegexExpr(ch)

    def string(self, text: str) -> RegexExpr:
        return StringRegexExpr(text)

    def int_range(self, min_value: int, max_value: int) -> RegexExpr:
        # for example:
        # (0, 255) -> RegexExpr(
        #     [0-9]                   |
        #     [1-9][0-9]              |
        #     1[0-9][0-9]             |
        #     2[0-4][0-9]             |
        #     25[0-5]                 |
        # )
        # (22, 5555) -> RegexExpr(
        #    2[2-9]                   |
        #    [3-9][0-9]               |
        #    [1-9][0-9][0-9]          |
        #    [1-4][0-9][0-9][0-9]     |
        #    5[0-4][0-9][0-9]         |
        #    55[0-4][0-9]             |
        #    555[0-5]
        # )
        # (210, 567) -> RegexExpr(
        #    21[0-9]                  |
        #    2[2-9][0-9]              |
        #    [3-4][0-9][0-9]          |
        #    5[0-5][0-9]              |
        #    56[0-7]                  |
        #
        if not isinstance(min_value, int) or not isinstance(max_value, int):
            raise TypeError
        if min_value > max_value:
            raise ValueError
        min_value_str = str(min_value)
        max_value_str = str(max_value)

        expr = EMPTY

        if len(min_value_str) == len(max_value_str):
            range_1 = range(1, len(min_value_str))
        else:
            range_1 = range(0, len(min_value_str))

        for handling in reversed(range_1):
            cur_expr = EMPTY
            for ch in min_value_str[0:handling]:
                cur_expr &= self.char(ch)
            start = ord(min_value_str[handling])
            if handling < len(min_value_str) - 1:
                start += 1
            cur_expr &= CharSeqRegexExpr(start, '9')
            for _ in range(handling, len(min_value_str) - 1):
                cur_expr &= self.digit()
            expr |= cur_expr

        for length in range(len(min_value_str) + 1, len(max_value_str)):
            for _ in range(0, length):
                if _ == 0:
                    cur_expr = CharSeqRegexExpr('1', '9')
                else:
                    cur_expr &= self.digit()
            expr |= cur_expr

        for handling in range(0, len(max_value_str)):
            cur_expr = EMPTY
            if handling == 0:
                if len(min_value_str) == len(max_value_str):
                    start = ord(min_value_str[handling]) + 1
                else:
                    start = '1'
            else:
                start = '0'
            end = ord(max_value_str[handling])
            if handling < len(max_value_str) - 1:
                end -= 1
            for i in range(0, handling):
                cur_expr &= self.char(max_value_str[i])
            cur_expr &= CharSeqRegexExpr(start, end)
            for i in range(handling + 1, len(max_value_str)):
                cur_expr &= self.digit()
            expr |= cur_expr

        return expr
