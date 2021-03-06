#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from io import StringIO
from collections import (
    namedtuple,
    defaultdict
)
from .common import (
    get_char_code,
    RegexStyle,
    ReduceContext,
    CompileContext,
    CACHE
)
from .expr_abs import (
    Range,
    ICharRegexExpr,
    ICharRangeRegexExpr,
    ISingledCharRegexExpr,
    IContinuousCharRangeRegexExpr,
)

ASSERT = True

class RegexExpr:
    SPEC_CHARS = frozenset('-^\\.?*+[]{}()')
    ESCAPE_MAP = dict((ord(ch), '\\' + ch) for ch in SPEC_CHARS)

    def _has_content(self):
        return True

    def __repr__(self):
        return '{}()'.format(
            type(self).__name__.replace('RegexExpr', ''),
        )

    def __or__(self, other):
        if not isinstance(other, RegexExpr):
            raise TypeError
        return OrRegexExpr(self._auto_group(self), self._auto_group(other))

    def __and__(self, other):
        if not isinstance(other, RegexExpr):
            raise TypeError
        return AndRegexExpr(self._auto_group(self), self._auto_group(other))

    def compile(self, style: RegexStyle=RegexStyle.python):
        context = CompileContext(
            style=style
        )
        self._compile(context)
        return context.buffer.getvalue()

    def _compile(self, context: CompileContext):
        raise NotImplementedError(type(self))

    def reduce(self):
        context = ReduceContext(self)
        return self._reduce(context)

    def _reduce(self, context: ReduceContext):
        return self

    def group(self, capture=True):
        return GroupedRegexExpr(self, capture)

    def repeat(self, min, max=None):
        if min is None and max is None:
            return self
        return RepeatedRegexExpr(AutoGroupedRegexExpr(self), min, max)

    def _auto_group(self, expr):
        return AutoGroupedRegexExpr(expr)


class _EmptyRegexExpr(RegexExpr):
    def __repr__(self):
        return 'Empty()'

    def _has_content(self):
        return False

    def _compile(self, context: CompileContext):
        pass

EMPTY = _EmptyRegexExpr()
CACHE[_EmptyRegexExpr] = EMPTY


class StringRegexExpr(RegexExpr):
    def __init__(self, text):
        if not isinstance(text, str):
            raise TypeError('ch must be str type.')
        self._text = text

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self._text)

    @property
    def value(self):
        return self._text

    def _compile(self, context: CompileContext):
        context.buffer.write(self._text.translate(self.ESCAPE_MAP))


class CharRegexExpr(RegexExpr, ISingledCharRegexExpr, IContinuousCharRangeRegexExpr):
    def __init__(self, ch):
        self._ch = get_char_code(ch)

    def __repr__(self):
        return 'Char({})'.format(chr(self._ch))

    @property
    def value(self):
        return self._ch

    def _compile(self, context: CompileContext):
        context.buffer.write(self.ESCAPE_MAP.get(self._ch, chr(self._ch)))

    def has(self, value):
        return value == self._ch

    def get_order_code(self) -> int:
        return self._ch

    def subset(self, other) -> bool:
        return False

    def superset(self, other) -> bool:
        return other.has(self._ch)

    def combine_with(self, other):
        if other.has(self._ch + 1):
            if isinstance(other, IContinuousCharRangeRegexExpr):
                return CharRangeRegexExpr(self._ch, other.range.end)
        return NotImplemented

    @property
    def range(self):
        return Range(self._ch, self._ch)


class CharRangeRegexExpr(RegexExpr, IContinuousCharRangeRegexExpr):
    ORD_0_9 = Range(ord('0'), ord('9'))
    ORD_A_Z = Range(ord('A'), ord('Z'))
    ORD_a_z = Range(ord('a'), ord('z'))

    RANGE_VALUE_MAP = {}

    def __init__(self, start: (str, int), end: (str, int)):
        start = get_char_code(start)
        end = get_char_code(end)
        assert end >= start
        self._range = Range(start, end)

    def _reduce(self, context: ReduceContext):
        if self._range.start == self._range.end:
            return CharRegexExpr(self.start)

        expr = self.RANGE_VALUE_MAP.get(self._range, self)

        if context.root_node is self:
            return CharsOrRegexExpr(expr)

        return self

    def __repr__(self):
        return 'Range({}-{})'.format(
            self._get_fmt_char(self._range.start),
            self._get_fmt_char(self._range.end),
        )

    def _get_fmt_char(self, ch_ord, *, context: CompileContext=None):
        ret = None
        for r in (self.ORD_0_9, self.ORD_a_z, self.ORD_A_Z):
            # pylint: disable=E1101
            if r.has(ch_ord):
                ret = chr(ch_ord)
                break
            # pylint: enable=E1101

        if ret is None: # generic unicode
            ret = '\\u' + hex(ch_ord)[2:].upper()

        if ASSERT:
            assert isinstance(ret, str)
        return ret

    def _compile(self, context: CompileContext):
        context.buffer.write(self._get_fmt_char(self._range.start, context=context))
        context.buffer.write('-')
        context.buffer.write(self._get_fmt_char(self._range.end, context=context))

    @property
    def range(self):
        '''
        return unicode code tuple for char range.
        for example: CharRange('0', '9').range -> (ord('0'), ord('9'))
        '''
        return self._range

    @property
    def start(self):
        return chr(self._range.start)

    @property
    def end(self):
        return chr(self._range.end)

    def has(self, value):
        # pylint: disable=E1101
        return self._range.has(value)

    def get_order_code(self) -> int:
        return self.range.start

    def subset(self, other) -> bool:
        return False

    def superset(self, other) -> bool:
        return False

    def combine_with(self, other):
        if isinstance(other, IContinuousCharRangeRegexExpr):

            if self.has(other.range.start):
                return CharRangeRegexExpr(self.range.start, max(self.range.end, other.range.end))
            elif self.range.end + 1 == other.range.start:
                return CharRangeRegexExpr(self.range.start, other.range.end)
        return NotImplemented

    @classmethod
    def combine(cls, items: list) -> list:
        ''' combine multi CharRangeRegexExpr into a new list. '''
        if len(items) in (0, 1):
            return items

        ret = []
        items = list(items) # clone
        items = sorted(items, key=lambda x: x.get_order_code())

        first = items.pop(0)
        second = items.pop(0)
        while True:
            result = cls.combine_two(first, second)
            if ASSERT:
                assert len(result) in (1, 2)
            if items:
                if len(result) == 1: # combined
                    first = result[0]
                else: # cannot combine
                    ret.append(first)
                    first = second
                second = items.pop(0)
            else:
                ret.extend(result)
                break

        return ret

    @classmethod
    def combine_two(cls, left, right) -> tuple:
        ''' combine two char range. '''
        if ASSERT:
            assert isinstance(left, ICharRangeRegexExpr)
            assert isinstance(right, ICharRangeRegexExpr)

        if left.subset(right):
            return left,

        if left.superset(right):
            return right,

        ret = left.combine_with(right)
        if ASSERT:
            assert ret is NotImplemented or isinstance(ret, ICharRangeRegexExpr)

        return (left, right) if ret is NotImplemented else (ret,)


class _OpRegexExpr(RegexExpr):
    def __init__(self, *exprs):
        if ASSERT:
            for expr in exprs:
                assert isinstance(expr, RegexExpr)
        self._exprs = exprs

    @property
    def exprs(self):
        return self._exprs

    def _reduce_extend_expr(self, context: ReduceContext, cls, expr):
        '''
        reduce and extend expr.
        if visis cls type expr, continue extend.
        '''
        if not expr is EMPTY:
            if isinstance(expr, cls):
                for e in expr._exprs:
                    yield from self._reduce_extend_expr(context, cls, e._reduce(context))
            else:
                expr = expr._reduce(context)
                if not expr is EMPTY:
                    yield expr


class AndRegexExpr(_OpRegexExpr):
    def __repr__(self):
        return 'AND({})'.format(', '.join(repr(e) for e in self._exprs))

    def _reduce(self, context: ReduceContext):
        exprs = []
        with context.scope(self) as scoped:
            for expr in self._exprs:
                exprs.extend(self._reduce_extend_expr(scoped, AndRegexExpr, expr))
            for idx, expr in enumerate(exprs):
                if isinstance(expr, CharRangeRegexExpr):
                    exprs[idx] = CharsOrRegexExpr(expr)._reduce(scoped)
        if not exprs:
            return EMPTY
        elif len(exprs) == 1:
            return exprs[0]
        else:
            return AndRegexExpr(*exprs)

    def _compile(self, context: CompileContext):
        for expr in self._exprs:
            expr._compile(context)


class OrRegexExpr(_OpRegexExpr):
    def __repr__(self):
        return 'OR({})'.format(', '.join(repr(e) for e in self._exprs))

    def _reduce(self, context: ReduceContext):
        exprs = []
        with context.scope(self) as scoped:
            for expr in self._exprs:
                exprs.extend(self._reduce_extend_expr(scoped, OrRegexExpr, expr))
            for idx, expr in enumerate(exprs):
                if isinstance(expr, CharRangeRegexExpr):
                    exprs[idx] = CharsOrRegexExpr(expr)._reduce(scoped)

        if not exprs:
            return EMPTY
        if len(exprs) == 1:
            return exprs[0]
        if all(isinstance(e, ICharRegexExpr) for e in exprs):
            return CharsOrRegexExpr(*exprs)._reduce(context)

        return OrRegexExpr(*exprs)

    def _compile(self, context: CompileContext):
        hasvalue = False
        for expr in self._exprs:
            if expr._has_content():
                if hasvalue:
                    context.buffer.write('|')
                hasvalue = True
                expr._compile(context)


class CharsOrRegexExpr(OrRegexExpr, ICharRegexExpr):
    ''' expr for `[]` '''

    nums = tuple(n for n in range(0, 10))
    engl = tuple(n for n in range(ord('a'), ord('z') + 1))
    engu = tuple(n for n in range(ord('A'), ord('Z') + 1))

    def __repr__(self):
        return 'CharOR({})'.format(', '.join(repr(e) for e in self._exprs))

    def _reduce(self, context: ReduceContext):
        check = set()
        extend_exprs = []
        with context.scope(self) as scoped:
            for expr in self._exprs:
                extend_exprs.extend(self._reduce_extend_expr(scoped, CharsOrRegexExpr, expr))

        range_exprs = []
        for expr in extend_exprs:
            if ASSERT:
                assert isinstance(expr, ICharRangeRegexExpr)
            range_exprs.append(expr)

        exprs = []

        # combine char range exprs:
        combined_range_exprs = CharRangeRegexExpr.combine(range_exprs)

        for expr in combined_range_exprs:
            exprs.append(expr._reduce(context))

        if len(exprs) == 1 and isinstance(exprs[0], ISingledCharRegexExpr):
            return exprs[0]

        return CharsOrRegexExpr(*exprs)

    def _compile(self, context: CompileContext):
        context.buffer.write('[')
        for expr in self._exprs:
            expr._compile(context)
        context.buffer.write(']')

class GroupedRegexExpr(RegexExpr):
    def __init__(self, expr, capture: bool):
        self._expr = expr
        self._capture = capture

    def __repr__(self):
        return 'Group({})'.format(repr(self._expr))

    def _reduce(self, context: ReduceContext):
        with context.scope(self) as scoped:
            expr = self._expr._reduce(scoped)
            if expr is self._expr:
                return self
            return GroupedRegexExpr(expr, self._capture)

    def _has_content(self):
        return self._expr._has_content()

    def _compile(self, context: CompileContext):
        buffer = context.buffer
        if self._has_content():
            buffer.write('(')
            if not self._capture:
                buffer.write('?:')
            self._expr._compile(context)
            buffer.write(')')


class RepeatedRegexExpr(RegexExpr):
    def __init__(self, expr, min, max):
        if min is None and max is None:
            raise ValueError
        if min is not None:
            if not isinstance(min, int):
                raise TypeError('min must be int type.')
            if min < 0:
                raise ValueError('min must >= 0')
        if max is not None:
            if not isinstance(max, int):
                raise TypeError('max must be int type.')
            if max < 0:
                raise ValueError('max must >= 0')
            if min is not None and max < min:
                raise ValueError('max must >= min')
        self._expr = expr
        self._min = min
        self._max = max

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, repr(self._expr))

    def _reduce(self, context: ReduceContext):
        with context.scope(self) as scoped:
            expr = self._expr._reduce(scoped)
            if expr is self._expr:
                return self
            return RepeatedRegexExpr(expr, self._min, self._max)

    def _has_content(self):
        return self._expr._has_content()

    def _compile(self, context: CompileContext):
        if self._has_content():
            buffer = context.buffer
            self._expr._compile(context)
            if self._max is None:
                if self._min == 0:
                    buffer.write('*')
                    return
                elif self._min == 1:
                    buffer.write('?')
                    return
            buffer.write('{')
            if self._min == self._max: # both not None
                buffer.write(str(self._min))
            else:
                buffer.write('' if self._min is None else str(self._min))
                buffer.write(',')
                buffer.write('' if self._max is None else str(self._max))
            buffer.write('}')


class AutoGroupedRegexExpr(RegexExpr):
    AUTO_GROUP_TYPES = frozenset([
        # type(parent, self)
        (AndRegexExpr, OrRegexExpr),
        (RepeatedRegexExpr, OrRegexExpr),
        (RepeatedRegexExpr, AndRegexExpr),
    ])

    def __init__(self, expr):
        self._expr = expr

    def __repr__(self):
        return 'AutoGroup({})'.format(repr(self._expr))

    def _reduce(self, context: ReduceContext):
        expr = self._expr
        while True:
            expr = expr._reduce(context)
            if not isinstance(expr, AutoGroupedRegexExpr):
                break
        types = (type(context.parent_node), type(expr))
        #print(types)
        if types in self.AUTO_GROUP_TYPES:
            return self if expr is self._expr else AutoGroupedRegexExpr(expr)
        else:
            return expr

    def _compile(self, context: CompileContext):
        if self._expr._has_content():
            context.buffer.write('(?:')
            self._expr._compile(context)
            context.buffer.write(')')
