#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017~2999 - cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from io import StringIO

from .common import RegexStyle, CompileContext

class RegexExpr:
    SPEC_CHARS = frozenset('-^\\.?*+[]{}()')
    ESCAPE_MAP = dict((ord(ch), '\\' + ch) for ch in SPEC_CHARS)

    def _has_content(self):
        return True

    def _compile(self, context: CompileContext):
        raise NotImplementedError(type(self))

    def __or__(self, other):
        if not isinstance(other, RegexExpr):
            raise TypeError
        return OrRegexExpr(self, other)

    def __and__(self, other):
        if not isinstance(other, RegexExpr):
            raise TypeError
        return AndRegexExpr(self, other)

    def compile(self, style: RegexStyle=RegexStyle.python):
        context = CompileContext(
            style=style
        )
        self._compile(context)
        return context.buffer.getvalue()

    def reduce(self):
        return self

    def group(self, capture=True):
        return GroupedRegexExpr(self, capture)

    def repeat(self, min, max=None):
        if min is None and max is None:
            return self
        return RepeatedRegexExpr(self, min, max)


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

    @property
    def value(self):
        return self._ch

    def _compile(self, context: CompileContext):
        context.buffer.write(self.ESCAPE_MAP.get(ord(self._ch), self._ch))


class CharSeqRegexExpr(RegexExpr):
    ord_0 = ord('0')
    ord_9 = ord('9')
    ord_a = ord('a')
    ord_z = ord('z')
    ord_A = ord('A')
    ord_Z = ord('Z')

    def __init__(self, start: (str, int), end: (str, int)):
        if isinstance(start, str):
            start = ord(start)
        assert isinstance(start, int)
        if isinstance(end, str):
            end = ord(end)
        assert isinstance(end, int)
        self._start = start
        self._end = end

    def reduce(self):
        if self._start == self._end:
            return CharRegexExpr(self.start)
        if self._start == self.ord_0 and self._end == self.ord_9:
            from .spec_seqs import DigitCharSeqRegexExpr
            return DigitCharSeqRegexExpr()
        if self._start == self.ord_a and self._end == self.ord_z:
            from .spec_seqs import LowerCaseLetterCharSeqRegexExpr
            return LowerCaseLetterCharSeqRegexExpr()
        if self._start == self.ord_A and self._end == self.ord_Z:
            from .spec_seqs import UpperCaseLetterCharSeqRegexExpr
            return UpperCaseLetterCharSeqRegexExpr()
        return self

    def __repr__(self):
        return 'CharSeq({}-{})'.format(self.start, self.end)

    def _compile(self, context: CompileContext):
        buffer = context.buffer
        buffer.write(self.start)
        buffer.write('-')
        buffer.write(self.end)

    @property
    def start(self):
        return chr(self._start)

    @property
    def end(self):
        return chr(self._end)

    def has(self, val):
        return self._start <= ord(val) <= self._end

    def is_next(self, val):
        return ord(val) == self._end + 1

    def is_prev(self, val):
        return ord(val) == self._start - 1

    def next(self):
        return CharSeqRegexExpr(self.start, chr(self._end+1))

    def prev(self):
        return CharSeqRegexExpr(chr(self._start+1), self.end)


class _OpRegexExpr(RegexExpr):
    def __init__(self, *exprs):
        self._exprs = exprs

    @property
    def exprs(self):
        return self._exprs

    def _reduce_extend_expr(self, cls, expr):
        if not expr is EMPTY:
            if isinstance(expr, cls):
                for e in expr._exprs:
                    yield from self._reduce_extend_expr(cls, e.reduce())
            else:
                yield expr.reduce()


class AndRegexExpr(_OpRegexExpr):
    def __repr__(self):
        return 'AND({})'.format(', '.join(repr(e) for e in self._exprs))

    def reduce(self):
        exprs = []
        for expr in self._exprs:
            exprs.extend(self._reduce_extend_expr(AndRegexExpr, expr))
        for idx, expr in enumerate(exprs):
            if isinstance(expr, CharSeqRegexExpr):
                exprs[idx] = CharsOrRegexExpr(expr).reduce()
        return AndRegexExpr(*exprs)

    def _compile(self, context: CompileContext):
        for expr in self._exprs:
            expr._compile(context)


class OrRegexExpr(_OpRegexExpr):
    def __repr__(self):
        return 'OR({})'.format(', '.join(repr(e) for e in self._exprs))

    def reduce(self):
        exprs = []
        for expr in self._exprs:
            exprs.extend(self._reduce_extend_expr(OrRegexExpr, expr))
        if not exprs:
            return EMPTY
        if len(exprs) == 1:
            return exprs[0]
        if all(isinstance(e, CharRegexExpr) for e in exprs):
            return CharsOrRegexExpr(*exprs).reduce()
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

    def reduce(self):
        check = set()
        exprs = []
        char_exprs = [e for e in self._exprs if isinstance(e, CharRegexExpr)]
        charseq_exprs = [e for e in self._exprs if isinstance(e, CharSeqRegexExpr)]
        assert len(char_exprs) + len(charseq_exprs) == len(self._exprs)

        def reduce_seq(expr):
            for idx, seq_expr in enumerate(charseq_exprs):
                if seq_expr.has(expr.value):
                    return True
                elif seq_expr.is_next(expr.value):
                    charseq_exprs[idx] = seq_expr.next()
                    return True
                elif seq_expr.is_prev(expr.value):
                    charseq_exprs[idx] = seq_expr.prev()
                    return True
            return False

        for expr in char_exprs:
            if reduce_seq(expr):
                continue

            if expr.value not in check:
                exprs.append(expr.reduce())
                check.add(expr.value)

        for expr in charseq_exprs:
            exprs.append(expr.reduce())

        if len(exprs) == len(self._exprs):
            return self

        return CharsOrRegexExpr(exprs)

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


class GroupedRegexExpr(RegexExpr):
    def __init__(self, expr, capture: bool):
        self._expr = expr
        self._capture = capture

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, repr(self._expr))

    def reduce(self):
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

    def reduce(self):
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
