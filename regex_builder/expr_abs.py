#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

class ICharRegexExpr:
    ''' represent the expr is a char expr. '''
    pass

class ISingledCharRegexExpr(ICharRegexExpr):
    ''' the expr can display without [] scope. '''
    pass

class ICharRangeRegexExpr(ICharRegexExpr):
    def has(self, value) -> bool:
        '''
        return whether the value in range.
        '''
        raise NotImplementedError(type(self))

    def get_order_code(self) -> int:
        '''
        return the code for sort.
        '''
        raise NotImplementedError(type(self))

    def subset(self, other) -> bool:
        '''
        return whether other is subset of self.
        '''
        raise NotImplementedError(type(self))
