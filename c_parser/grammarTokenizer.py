import re
import collections
import nfa
import c_parser.production
from typing import List, Tuple

epsilon = 'ε'
eof = '$'

Token = collections.namedtuple('Token', ['token_t', 'value', 'position'])
tokenTable = {
    'nude': re.compile(r"([a-zA-Z_]\w*)"),  # a nude can be a terminal either a intermediate
    '->': re.compile(r'(->)'),
    '|': re.compile(r'(\|)'),
    # 't': re.compile(r"'([^']*)'"),
}
# candidates = {
#     'id': re.compile(r"([a-zA-Z_]\w*|'[^']*')"),
#     '*': re.compile(r'(\*)'),
#     '+': re.compile(r'(\+)'),
#     #'t': re.compile(r"'([^']*)'"),
# }

space = re.compile(r'[ \t\r]')
nextline = re.compile(r'\n')


def tokenizer(s: str):
    i = 0

    pos = [1, 0]  # (current-line-number, index of the nearest \n in s)
    buffer: List[Token] = []
    length: int = len(s)

    def update(i, x):
        if x: return x.end()
        return i

    while i < length:
        flag = False
        while i < length and s[i] == '\n':
            pos[0] += 1
            pos[1] = i
            i += 1
            flag = True
        if i == length:
            break

        r = update(i, space.match(s, i))
        if r > i:
            flag = True
        i = r
        res, value = nfa.matchGrammarStringLiteral(s, i, length)
        if value:
            flag = True
            buffer.append(Token('terminal', value, (pos[0], i + 1 - pos[1])))
            i = res

        for candidate in tokenTable:
            res = tokenTable[candidate].match(s, i)
            if res:
                flag = True
                if res.group(1) == '->':
                    try:
                        assert buffer[-1].token_t == 'nude'
                        buffer[-1] = buffer[-1]._replace(token_t='lhs')
                    except IndexError as e:
                        raise SyntaxError('there must be a terminal or intermediate before \'->\'!')

                buffer.append(Token(candidate, res.group(1), (pos[0], i + 1 - pos[1])))
                i = res.end()
        if not flag:
            raise RuntimeError('unkown character \'%s\' at line %s, column %s:\n %s' % (
                s[i], pos[0], i + 1 - pos[1], s[max(i - 10, 0):i + 10]))
    return buffer


if __name__ == "__main__":
    with open('std.txt') as file:
        s = map(lambda x: x.strip(), file.readlines())
        s = filter(lambda x: x != '', s)
        s = '\n'.join(list(s)) + '\n'
    print(repr(s))

    s = list(tokenizer(s))
    assert len(s) > 3
    assert s[0].token_t == 'nude'
    assert s[1].token_t == 'lhs'
    assert s[2].token_t == '->'
    start = s[0].value
    i = 1
    tmp = []
    buf = []
    lhs = collections.OrderedDict()
    while i < len(s):
        if s[i].token_t == 'lhs':
            if buf:
                tmp.append(buf)
                # print(' '.join(x.value for x in buf))
                buf = []
            else:
                assert i == 1

        buf.append(s[i])
        i += 1
    if buf: tmp.append(buf)

    lhs[start + '\''] = [(start,)]
    for p in tmp:
        if p[0].value not in lhs:
            lhs[p[0].value] = []
        buf = []
        assert len(p) > 2
        for i in range(2, len(p)):
            if p[i].token_t == '|':
                lhs[p[0].value].append(tuple(buf))
                buf = []
            else:
                buf.append(p[i].value)
        if buf:
            lhs[p[0].value].append(tuple(buf))

    productions = [c_parser.production.Production(l, r) for l in lhs for r in lhs[l]]
    print(productions)
    # for i in s:
    #    print(i)
