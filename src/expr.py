#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from io import StringIO
from collections import namedtuple

from .common import (
    get_char_code,
    RegexStyle,
    Flags,
    ReduceContext,
    CompileContext
)

ASSERT = True

class RegexExpr:
    SPEC_CHARS = frozenset('-^\\.?*+[]{}()')
    ESCAPE_MAP = dict((ord(ch), '\\' + ch) for ch in SPEC_CHARS)

    def _flag(self, f: Flags):
        ''' return expr has spec flag. '''
        return False

    def _has_content(self):
        return True

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
        return RepeatedRegexExpr(self, min, max)

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


class CharRegexExpr(RegexExpr):

    def __init__(self, ch):
        if not isinstance(ch, str):
            raise TypeError('ch must be str type.')
        if len(ch) != 1:
            raise ValueError('len of ch must be 1.')
        self._ch = ch

    def __repr__(self):
        return 'Char({})'.format(self._ch)

    def _flag(self, f: Flags):
        return f is Flags.char

    @property
    def value(self):
        return self._ch

    def _compile(self, context: CompileContext):
        context.buffer.write(self.ESCAPE_MAP.get(ord(self._ch), self._ch))


_Range = namedtuple('_Range', ['start', 'end'])
def _has(self, val):
    return self[0] <= val <= self[1]
_Range.has = _has

class CharRangeRegexExpr(RegexExpr):
    ORD_0_9 = _Range(ord('0'), ord('9'))
    ORD_A_Z = _Range(ord('A'), ord('Z'))
    ORD_a_z = _Range(ord('a'), ord('z'))

    RANGE_VALUE_MAP = {}

    def __init__(self, start: (str, int), end: (str, int)):
        start = get_char_code(start)
        end = get_char_code(end)
        assert end >= start
        self._range = _Range(start, end)

    def _flag(self, f):
        return f is Flags.char

    def _reduce(self, context: ReduceContext):
        if self._range.start == self._range.end:
            return CharRegexExpr(self.start)

        expr = self.RANGE_VALUE_MAP.get(self._range, self)

        if context.root_node is self:
            return CharsOrRegexExpr(expr)

        return self

    def __repr__(self):
        return 'Range({}-{})'.format(self.start, self.end)

    def _compile_char(self, context: CompileContext, ch_ord):
        for r in (self.ORD_0_9, self.ORD_a_z, self.ORD_A_Z):
            # pylint: disable=E1101
            if r.has(ch_ord):
                context.buffer.write(chr(ch_ord))
                return
            # pylint: enable=E1101

        context.buffer.write('\\u')
        context.buffer.write(hex(ch_ord)[2:].upper())

    def _compile(self, context: CompileContext):
        buffer = context.buffer
        self._compile_char(context, self._range.start)
        buffer.write('-')
        self._compile_char(context, self._range.end)

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

    def has(self, val):
        # pylint: disable=E1101
        return self._range.has(ord(val))

    def is_next(self, val):
        return ord(val) == self._range.end + 1

    def is_prev(self, val):
        return ord(val) == self._range.start - 1

    def next(self):
        return CharRangeRegexExpr(self.start, chr(self._range.end+1))

    def prev(self):
        return CharRangeRegexExpr(chr(self._range.start+1), self.end)

    @classmethod
    def combine(cls, items: list) -> list:
        if len(items) in (0, 1):
            return items

        ret = []
        items = list(items) # clone
        items = sorted(items, key=lambda x: x.range.start)
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
            assert isinstance(left, CharRangeRegexExpr)
            assert isinstance(right, CharRangeRegexExpr)
        if left.range.start > right.range.start:
            left, right = right, left # keep start of left <= start of right
        if left.range.has(right.range.start):
            return CharRangeRegexExpr(left.range.start, max(left.range.end, right.range.end)),
        elif left.range.end + 1 == right.range.start:
            return CharRangeRegexExpr(left.range.start, right.range.end),
        else:
            return left, right


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
                yield expr._reduce(context)


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
                exprs[idx] = CharsOrRegexExpr(expr).reduce()
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
        if not exprs:
            return EMPTY
        if len(exprs) == 1:
            return exprs[0]
        if all(e._flag(Flags.char) for e in exprs):
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


class CharsOrRegexExpr(OrRegexExpr):

    nums = tuple(str(n) for n in range(0, 10))
    engl = tuple(chr(n) for n in range(ord('a'), ord('z') + 1))
    engu = tuple(chr(n) for n in range(ord('A'), ord('Z') + 1))

    def __repr__(self):
        return 'CharOR({})'.format(', '.join(repr(e) for e in self._exprs))

    def _flag(self, f: Flags):
        return f is Flags.char

    def _reduce(self, context: ReduceContext):
        check = set()
        extend_exprs = []
        with context.scope(self) as scoped:
            for expr in self._exprs:
                extend_exprs.extend(self._reduce_extend_expr(scoped, CharsOrRegexExpr, expr))

        exprs = []
        char_exprs = [e for e in extend_exprs if isinstance(e, CharRegexExpr)]
        range_exprs = [e for e in extend_exprs if isinstance(e, CharRangeRegexExpr)]
        if ASSERT:
            assert len(char_exprs) + len(range_exprs) == len(extend_exprs)

        def reduce_seq(expr):
            for idx, seq_expr in enumerate(range_exprs):
                if seq_expr.has(expr.value):
                    return True
                elif seq_expr.is_next(expr.value):
                    range_exprs[idx] = seq_expr.next()
                    return True
                elif seq_expr.is_prev(expr.value):
                    range_exprs[idx] = seq_expr.prev()
                    return True
            return False

        for expr in char_exprs:
            if reduce_seq(expr):
                continue

            if expr.value not in check:
                exprs.append(expr._reduce(context))
                check.add(expr.value)

        # combine char range exprs:
        combined_range_exprs = CharRangeRegexExpr.combine(range_exprs)

        for expr in combined_range_exprs:
            exprs.append(expr._reduce(context))

        if len(exprs) == len(self._exprs):
            return self

        return CharsOrRegexExpr(*exprs)

    def _compiling_shorter(self, context: CompileContext, chars: dict, src: tuple):
        in_map = [v in chars for v in src]
        count = in_map.count(True)
        if count > 0:
            # split by `in`
            groups = []
            state = None
            for i, b in enumerate(in_map):
                if b:
                    if state is False or not groups:
                        groups.append([i])
                    else:
                        groups[-1].append(i)
                state = b
            for group in groups:
                if len(group) > 2:
                    chars[src[group[0]]]._compile(context)
                    context.buffer.write('-')
                    chars[src[group[-1]]]._compile(context)
                    for i in group:
                        del chars[src[i]]

    def _compile(self, context: CompileContext):
        context.buffer.write('[')
        chars = dict((e.value, e) for e in self._exprs if isinstance(e, CharRegexExpr))
        self._compiling_shorter(context, chars, self.nums)
        self._compiling_shorter(context, chars, self.engl)
        self._compiling_shorter(context, chars, self.engu)
        for ch in chars:
            chars[ch]._compile(context)
        for expr in self._exprs:
            if not isinstance(expr, CharRegexExpr):
                expr._compile(context)
        context.buffer.write(']')


class AutoGroupedRegexExpr(RegexExpr):
    AUTO_GROUP_TYPES = frozenset([
        # type(parent, self)
        (AndRegexExpr, OrRegexExpr),
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
        if types in self.AUTO_GROUP_TYPES:
            return self if expr is self._expr else AutoGroupedRegexExpr(expr)
        else:
            return expr

    def _compile(self, context: CompileContext):
        if self._expr._has_content():
            context.buffer.write('(?:')
            self._expr._compile(context)
            context.buffer.write(')')


class GroupedRegexExpr(RegexExpr):
    def __init__(self, expr, capture: bool):
        self._expr = expr
        self._capture = capture

    def __repr__(self):
        return 'Group({})'.format(repr(self._expr))

    def _reduce(self, context: ReduceContext):
        expr = self._expr.reduce()
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
        expr = self._expr.reduce()
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
