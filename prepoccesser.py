import re
from stream import Stream


def removeComments(code):
    length = len(code)
    flag = [True] * length
    r = 0

    def singleLine():
        nonlocal r
        while code[r] != '\n':
            flag[r] = False
            r += 1

    def multiLine():
        nonlocal r
        while code[r:r + 2] != '*/':
            flag[r] = False
            if r + 2 == length:
                raise SyntaxError('SyntaxError: unexpected EOF while parsing\n%s,size=%s' % (s[r:r + 2], size))
            r += 1
        flag[r] = flag[r + 1] = False

    def default():
        nonlocal r
        r += 1

    while r < length:
        {
            '//': singleLine,
            '/*': multiLine
        }.get(code[r:r + 2], default)()
    return ''.join(Stream(enumerate(code)).filter(lambda c: flag[c[0]]).map(lambda c: c[1]).collect())


#with open('sample.cpp') as file:
#    s = ''.join(file.readlines())
# print(f(s))
