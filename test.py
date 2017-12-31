#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import os
import sys
import traceback
from src.builder import RegexBuilder
import unittest


class Test(unittest.TestCase):
    def test_int_range(self):
        builder = RegexBuilder()
        expr = builder.int_range(0, 255).reduce()
        self.assertEqual(expr.compile(), '|'.join([
            '[0-9]',
            '[1-9][0-9]',
            '1[0-9][0-9]',
            '2[0-4][0-9]',
            '25[0-5]'
        ]))

        builder = RegexBuilder()
        expr = builder.int_range(22, 5555).reduce()
        self.assertEqual(expr.compile(), '|'.join([
            '2[2-9]',
            '[3-9][0-9]',
            '[1-9][0-9][0-9]',
            '[1-4][0-9][0-9][0-9]',
            '5[0-4][0-9][0-9]',
            '55[0-4][0-9]',
            '555[0-5]'
        ]))

        builder = RegexBuilder()
        expr = builder.int_range(210, 567).reduce()
        self.assertEqual(expr.compile(), '|'.join([
            '21[0-9]',
            '2[2-9][0-9]',
            '[3-4][0-9][0-9]',
            '5[0-5][0-9]',
            '56[0-7]'
        ]))


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        builder = RegexBuilder()
        exprx  = builder.char('0')
        exprx |= builder.char('1')
        exprx |= builder.char('2')
        exprx |= builder.char('3')
        exprx |= builder.char('5')
        exprx |= builder.char('6')
        exprx |= builder.char('7')
        exprx |= builder.char('9')
        exprx |= builder.char(']')
        exprx |= builder.char('\\')
        exprx = exprx.repeat(3, None)
        exprx = exprx.group(capture=False)
        exprx = exprx.repeat(0, None)
        exprx |= builder.string('val\\')
        exprx = exprx.group()
        exprx |= (builder.digit() & builder.upper_case_letter())
        exprxr = exprx.reduce()
        print(exprxr.compile())

        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
