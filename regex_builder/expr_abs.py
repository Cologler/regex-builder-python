#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

class ICharRangeRegexExpr:
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


class ISingledCharRegexExpr:
    ''' the expr can display without [] scope. '''
    pass
