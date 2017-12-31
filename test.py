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

    def test_print(self):
        pass


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
