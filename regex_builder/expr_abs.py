#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from collections import namedtuple

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

    def superset(self, other) -> bool:
        '''
        return whether other is superset of self.
        '''
        raise NotImplementedError(type(self))

    def combine_with(self, other):
        '''
        return `NotImplemented` if cannot combine.
        self.get_order_code() always <= other.get_order_code()
        '''
        return NotImplemented


Range = namedtuple('Range', ['start', 'end'])
def _range_has(self, val):
    return self[0] <= val <= self[1]
Range.has = _range_has


class IContinuousCharRangeRegexExpr(ICharRangeRegexExpr):
    @property
    def range(self):
        '''
        return unicode code tuple for char range.
        for example: CharRange('0', '9').range -> (ord('0'), ord('9'))
        '''
        raise NotImplementedError(type(self))
