import re

from tag import Tag
from ctoken import CToken

hexadecimal = re.compile('[0-9a-fA-F]+')
octal = re.compile('[0-7]+')
escapestart = set(r'01234567xabfnrtv\'"')
table = {
    'a': '\a', 'b': '\b', 'f': '\f',
    'n': '\n', 'r': '\r', 't': '\t',
    'v': '\v', '\\': '\\', '\'': '\'',
    '\"': '\"'
}


def matchLiteralGeneral(s, start, end, quotation, tag):
    def check(f):
        def execute(i):
            if i == end:
                raise RuntimeError(r'missing terminating %c character' % quotation)
            yield from f(i)

        return execute

    length = 0

    @check
    def stat1(i):
        nonlocal length
        if s[i] == '\\':
            yield from stat2(i + 1)
        elif s[i] == '\n':
            raise RuntimeError(r"'\n' should not be here")
        elif s[i] == quotation:
            length = i + 1 - start
            return
        else:
            yield s[i]
            yield from stat1(i + 1)

    @check
    def stat2(i):
        if s[i] not in escapestart:
            raise RuntimeError(r"unknown escape sequence: '\%s'" % (s[i]))
        yield from stat5(i)
        yield from stat4(i)
        if s[i] == 'x':
            yield from stat3(i + 1)

    @check
    def stat3(i):
        match = hexadecimal.match(s, i)
        if match:
            value = int(match.group(), 16)
            if value >= 256:
                raise RuntimeError("hex escape sequence out of range")
            yield match.group()
            yield from stat1(i + 1)
        else:
            raise RuntimeError(r"\x used with no following hex digits")

    @check
    def stat4(i):
        match = octal.match(s, i)
        if match:
            value = int(match.group(), 8)
            if value >= 256:
                raise RuntimeError("octal escape sequence out of range")
            yield match.group()
            yield from stat1(i + 1)

    @check
    def stat5(i):
        if s[i] in table:
            yield table[s[i]]
        yield from stat1(i + 1)

    if start < end and s[start] == quotation:


        res = ''.join(stat1(start + 1))
        #        print('start:%s,end:%s,res:%s' % (start, end, repr(res)))
        return start + length, quotation + res + quotation
    return start, ''


def matchCharacterLiteral(s, start, end):
    res1, res2 = matchLiteralGeneral(s, start, end, '\'', Tag.charLiteral)
    if len(res2) > 3:  # \', c, \'
        raise RuntimeError(r"multi-character character constant '%s'", res2)
    elif len(res2) == 2:
        raise RuntimeError("empty char constant")
    return res1, res2


def matchStringLiteral(s, start, end):
    return matchLiteralGeneral(s, start, end, '\"', Tag.stringLiteral)
