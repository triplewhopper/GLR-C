import re

from tag import Tag
from ctoken import CToken

keywords = {'enum',
            'struct', 'union',  'for', 'do', 'while', 'break',
            'continue', 'if', 'else', 'goto', 'switch', 'case', 'default', 'return',
            'auto', 'extern', 'register', 'static', 'const', 'sizeof', 'typedef', 'volatile'}
operators = {'(', ')', '[', ']', '"', '\'', ',', '=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=',
             '&=', '^=', '|=', '?', ':', '||', '&&', '|', '^', '&', '==', '!=', '<', '<=',
             '>', '>=', '<<', '>>', '+', '-', '*', '/', '%', '~', '!', '+',
             '-', '&', '*', '++', '--', '++', '--', '->', '.'}

specialSymbols = {
    '{', '}', ';'
}
identifier = re.compile(r'[a-zA-Z_]\w*')
# operator = re.compile('|'.join(map(re.escape, operators)))
specialSymbol = re.compile('|'.join(map(re.escape, specialSymbols)))
keyword = re.compile('|'.join(map(lambda word: '\\b' + word + '\\b', keywords)))
int32 = re.compile(r"(?P<int32>\d+(?=\b)(?!\.))")
uint32 = re.compile(r"(?P<uint32>\d+)[uU]\b")
int64 = re.compile(r'(?P<int64>\d+)(?:ll|LL)\b')
uint64 = re.compile(r"(?P<uint64>\d+)(?:[uU](?:LL|ll|[Ll]))\b")
float32 = re.compile(r"(?P<float>\d*(\.\d*?|\.?\d*e-?\d+)?)(?:[fF]\b)")
double64 = re.compile(r"(?P<double>\d*(?:\.?\d*e-?\d+|\.\d*))\b")
comment = re.compile(r"(?:/\*.*?\*/)|(?://[^\n]*)", re.S | re.M)
octal = re.compile(r"0(?P<octal>[0-7]+)[uU]?(?:ll|LL|[Ll])\b")
hexadecimal = re.compile(r"0[xX](?P<hexadecimal>[0-9a-fA-F]+)[uU]?(?:ll|LL|[Ll])\b")


def defaultreturn(f):
    def execute(s, l, r):
        res = f(s, l, r)
        if not res:
            return l, ''
        else:
            return res

    return execute


@defaultreturn
def matchNum(s, l, r):
    for c in (float32, double64, uint64, int64, uint32, int32, octal, hexadecimal):
        res = c.match(s, l, r)
        if res:
            return res.end(), CToken(res.group(1), Tag.numLiteral)


@defaultreturn
def matchIdentifier(s, l, r):
    res = identifier.match(s, l, r)
    if res:
        return res.end(), CToken(res.group(), Tag.identifier)


@defaultreturn
def matchComments(s, l, r):
    res = comment.match(s, l, r)
    if res:
        return res.end(), CToken(res.group(), Tag.comment)


@defaultreturn
def matchKeyword(s, l, r):
    tmp, token = matchIdentifier(s, l, r)
    if token in keywords:
        return tmp, CToken(token, Tag.keyword)


@defaultreturn
def matchSpecialSymbol(s, l, r):
    if s[l] in specialSymbols:
        return l + 1, CToken(s[l], Tag.specialSymbol)


@defaultreturn
def matchOperator(s, l, r):
    # it seems that the argument r is not used.
    for i in (3, 2, 1):
        if s[l:l + i] in operators:
            return l + i, CToken(s[l:l + i], Tag.operator)

# for c in (float32, double64, uint64, int64, uint32, int32, octal, hexadecimal):
#     res = c.match(s)
#     if res:
#         print(res.groupdict())


#
# def escapeCharacter(s: str, i: int, state):
#     if i == len(s):
#         return None
#     table = {
#         'a': '\a', 'b': '\b', 'f': '\f',
#         'n': '\n', 'r': '\r', 't': '\t',
#         'v': '\v', '\\': '\\', '\'': '\'',
#         '\"': '\"'
#     }
#     if s[i] in table:
#         return strliteral(s, i + 1, state + [table[s[i]]])
#     raise RuntimeError('illegal escape character \'\\%s\'!' % s[i])
#
#
# def accept(s, i, state):
#     if i == len(s):
#         return state
#     elif s[i] == '\\':
#         raise RuntimeError('backslash out of quotation marks!')
#     elif s[i] == '"':
#         return strliteral(s, i + 1, state)
#     elif s[i] in {'\t', ' '}:
#         return start(s, i + 1, state)
#     else:
#         return state
#
#
# def strliteral(s: str, i: int, state):
#     if i == len(s):
#         raise RuntimeError('[Error] end of statement within the quotation marks!')
#     if s[i] == '"':
#         return accept(s, i + 1, state)
#     if s[i] == '\\':
#         return escapeCharacter(s, i + 1, state)
#     return strliteral(s, i + 1, state + [s[i]])

#
# def numliteral(s, i, state):
#     def isNum(x) -> bool:
#         if isinstance(x, (int, float)): return True
#         if not isinstance(x, str): return False
#         if x == '': return False
#         for s in filter(lambda s: s != '' and s != '.', x.partition('.')):
#             if not s.isnumeric():
#                 return False
#         return True
#
#     # print(expr)
#     l = start
#     r = end
#     while l < r:
#         mid = l + r >> 1
#         if isNum(expr[start:mid + 1]):
#             l = mid + 1
#         else:
#             r = mid
#         # print('l=%s,r=%s,mid=%s'%(l,r,mid))
#     return l, expr[start:l]

#
# def charliteral(s, i, state):
#     if i == len(s):
#         raise RuntimeError('[Error] end of statement within the quotation marks!')
#     if s[i] == "'":
#         length = len(state)
#         if length == 0:
#             raise RuntimeError('[Error] empty character constant')
#         if length > 1:
#             raise RuntimeWarning('[Warning] multi-character character constant [-Wmultichar]')
#         return accept(s, i + 1, state)
#     if s[i] == '\\':
#         return escapeCharacter(s, i + 1, state)
#     return charliteral(s, i + 1, state + [s[i]])

#
# def start(s: str, i: int = 0, state=[]):
#     if i == len(s):
#         return state
#     elif s[i] == '"':
#         return strliteral(s, i + 1, state)
#     elif s[i] == "'":
#         return charliteral(s, i + 1, state)
#     else:
#         return state
#
#
# for i in start("'a'"):
#     print(i.__repr__(), sep='', end='')
# print()
