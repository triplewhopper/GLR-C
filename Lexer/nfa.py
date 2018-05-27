import re

from tag import Tag
from AST import c_type
from typing import Tuple, Iterable

hexadecimal = re.compile('[0-9a-fA-F]+')
octal = re.compile('[0-7]+')
escapestart = set(r'01234567xabfnrtv\'"')
table = {
    'a': '\a', 'b': '\b', 'f': '\f',
    'n': '\n', 'r': '\r', 't': '\t',
    'v': '\v', '\\': '\\', '\'': '\'',
    '\"': '\"'
}


def matchLiteralGeneral(s: str, start: int, end: int, quotation: str, tag: str):
    def check(f):
        def execute():
            nonlocal i
            if i == end:
                raise RuntimeError(r'missing terminating %c character' % quotation)
            yield from f()

        return execute

    length = 0
    i = start + 1

    @check
    def stat1():
        nonlocal length
        nonlocal i
        if s[i] == '\\':
            i += 1
            yield from stat2()
        elif s[i] == '\n':
            raise RuntimeError(r"'\n' should not be here")
        elif s[i] == quotation:
            length = i + 1 - start
            return
        else:
            yield s[i]
            i += 1
            yield from stat1()

    @check
    def stat2():
        nonlocal i
        if s[i] not in escapestart:
            raise RuntimeError(r"unknown escape sequence: '\%s'" % (s[i]))
        elif s[i] == 'x':
            i += 1
            yield from stat3()
        elif s[i] in table:
            yield table[s[i]]
            i += 1
            yield from stat1()
        else:
            yield from stat4()

    @check
    def stat3():
        nonlocal i
        match = hexadecimal.match(s, i)
        if match:
            value = int(match.group(), 16)
            if value >= 256:
                raise RuntimeError("hex escape sequence out of range")
            yield chr(value)
            assert isinstance(match.group(), str)
            i += len(match.group())
            yield from stat1()
        else:
            raise RuntimeError(r"\x used with no following hex digits")

    @check
    def stat4():
        nonlocal i
        match = octal.match(s, i)
        if match:
            value = int(match.group(), 8)
            if value >= 256:
                raise RuntimeError("octal escape sequence out of range")
            yield chr(value)
            assert isinstance(match.group(), str)
            i += len(match.group())
            yield from stat1()
        else:
            raise RuntimeError()

    if start < end and s[start] == quotation:
        i = start + 1
        res = tuple(stat1())
        return start + length, res
    return start, ''


def matchCharacterLiteral(s: str, start: int, end: int) -> Tuple[int, Tuple[int, 'c_type.Int32']]:
    res1, res2 = matchLiteralGeneral(s, start, end, '\'', Tag.charLiteral)
    val = 0
    for c in res2:
        val = (val << 4) + ord(c)

    if len(res2) > 3:  # \', c, \'
        raise RuntimeError(r"multi-character character constant '%s'", res2)
    elif len(res2) == 2:
        raise RuntimeError("empty char constant")
    return res1, (val, c_type.Int32())


def matchStringLiteral(s: str, start: int, end: int) -> Tuple[int, Tuple[str, ...]]:
    return matchLiteralGeneral(s, start, end, '\"', Tag.stringLiteral)


def matchGrammarStringLiteral(s, start, end) -> Tuple[int, str]:
    a, b = matchLiteralGeneral(s, start, end, '\"', Tag.stringLiteral)
    return a, ''.join(b)


if __name__ == '__main__':
    s = r"'0'"
    f = lambda s: matchCharacterLiteral(s, 0, len(s))

    print(f(s))
    u = r'"\'hello\'\nworld!"'
    g = lambda s: matchStringLiteral(s, 0, len(s))
    print(g(u))
