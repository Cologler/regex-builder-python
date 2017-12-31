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

        exprxr = builder.int_range(0, 255).reduce()
        print(exprxr.compile())
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
