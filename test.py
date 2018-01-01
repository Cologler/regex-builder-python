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
    def test_base_api(self):
        builder = RegexBuilder()
        self.assertEqual(builder.digit().reduce().compile(), '[0-9]')
        self.assertEqual(builder.lower_case_letter().reduce().compile(), '[a-z]')
        self.assertEqual(builder.upper_case_letter().reduce().compile(), '[A-Z]')
        self.assertEqual(builder.char_range('/u2E80', '/u9FFF').reduce().compile(), '[\\u2E80-\\u9FFF]')

    def test_range_combine(self):
        builder = RegexBuilder()
        expr = builder.lower_case_letter() | builder.upper_case_letter()
        self.assertEqual(expr.reduce().compile(), '[a-zA-Z]')
        expr |= builder.char_range(ord('Z'), ord('a'))
        self.assertEqual(expr.reduce().compile(), '[A-z]')

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

    def test_ipv4(self):
        builder = RegexBuilder()
        expr = builder.int_range(0, 255)
        expr &= builder.char('.')
        expr &= builder.int_range(0, 255)
        expr &= builder.char('.')
        expr &= builder.int_range(0, 255)
        expr &= builder.char('.')
        expr &= builder.int_range(0, 255)
        self.assertEqual(expr.reduce().compile(), '\\.'.join([
            '(?:[0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
            '(?:[0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
            '(?:[0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
            '(?:[0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
        ]))

    def test_ipv4_grouped(self):
        builder = RegexBuilder()
        expr =  builder.int_range(0, 255).group()
        expr &= builder.char('.')
        expr &= builder.int_range(0, 255).group()
        expr &= builder.char('.')
        expr &= builder.int_range(0, 255).group()
        expr &= builder.char('.')
        expr &= builder.int_range(0, 255).group()
        self.assertEqual(expr.reduce().compile(), '\\.'.join([
            '([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
            '([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
            '([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
            '([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])',
        ]))

    def test_char_range(self):
        builder = RegexBuilder()
        expr =  builder.char('0')
        expr |= builder.char('1')
        expr |= builder.char('2')
        expr |= builder.char('3')
        expr |= builder.char('5')
        self.assertEqual(expr.reduce().compile(), '[0-35]')
        expr |= builder.char('4')
        self.assertEqual(expr.reduce().compile(), '[0-5]')

    def test_print(self):
        return
        import colorama
        colorama.init()
        print()
        print(colorama.Fore.LIGHTRED_EX + '*' * 60)
        builder = RegexBuilder()
        expr = builder.lower_case_letter() | builder.upper_case_letter()
        expr |= builder.char_range(ord('Z'), ord('a'))
        print(expr.reduce().compile())
        print(expr.reduce())
        print('*' * 60 + colorama.Fore.RESET)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
