import hashlib
from collections import OrderedDict, defaultdict
from typing import List, Tuple, FrozenSet

from Lexer import grammarTokenizer
from Parser.constants import eof, EOF
from Lexer.grammarTokenizer import Token
from Parser.production import Production


class Grammar:
    """
    :type __start:      str
    :type productions:  list[Production]
    :type lhs:          defaultdict[str, list[int]]
    :type intermediate: frozenset[str]
    :type characters:   frozenset[str]
    :type terminal:     frozenset[str|EOF]
    """

    def __readFromFile(self, filename: str):
        with open(filename) as file:
            #            s = map(lambda x: x.strip(), file.readlines())
            #            s = filter(lambda x: x != '', s)
            s = ''.join(list(file.readlines())) + '\n'
        return s

    def __init__(self, *filename):
        s: str = self.__readFromFile(*filename)
        self.sha1: str = hashlib.sha1(s.encode('utf-8')).hexdigest()
        s: List[Token] = grammarTokenizer.tokenizer(s)
        assert len(s) > 3
        assert s[0].token_t == 'nude'
        assert s[1].token_t == 'lhs'
        assert s[2].token_t == '->'
        start: str = s[0].value
        i: int = 1
        tmp: List[List[Token]] = []
        buf: List[Token] = []
        while i < len(s):
            if s[i].token_t == 'lhs':
                if buf:
                    tmp.append(buf)
                    buf = []
                else:
                    assert i == 1

            buf.append(s[i])
            i += 1
        if buf:
            tmp.append(buf)

        lhs = OrderedDict()
        self.__start = start + '_Begin'
        lhs[self.__start] = [(start,)]

        for p in tmp:
            if p[0].value not in lhs:
                lhs[p[0].value] = []
            buf1: List[str] = []
            assert len(p) > 2
            for i in range(2, len(p)):
                if p[i].token_t == '|':
                    lhs[p[0].value].append(tuple(buf1))
                    buf1 = []
                else:
                    buf1.append(p[i].value)
            if buf1:
                lhs[p[0].value].append(tuple(buf1))

        assert start in lhs.keys()

        self.productions = [Production(l, r) for l in lhs for r in lhs[l]]
        self.lhs = defaultdict(list)
        for i, p in enumerate(self.productions):
            self.lhs[p.lhs].append(i)
            p.relativeOrder = len(self.lhs[p.lhs])

        print(self.productions)
        self.intermediate = frozenset(lhs.keys())
        self.characters = self.intermediate | \
                          frozenset(e for x in self.productions for e in x.rhs)
        self.terminal = (self.characters - self.intermediate) | {eof}
        print('terminals:')
        print(self.terminal)
        print('intermediate:')
        print(self.intermediate)

    @property
    def start(self):
        return self.__start

    def __str__(self):
        return f'''
            start: {self.start}
            intermediates: {sorted(self.intermediate)}
            terminals: {sorted(self.terminal)}''' \
               + "\n".join(str(i) for i in self.productions) + '\n'

    def __len__(self):
        return len(self.productions)

    def __getitem__(self, item):
        return self.productions[item]

    def allProductionsStartingWith(self, x: str):
        assert x in self.intermediate
        return self.lhs[x]


if __name__ == '__main__':
    g = Grammar('../std.txt')
    strMethod = f"""\"\"\"
    <span>{{0}}</span><ul>
    {{1}}
    </ul>\"\"\""""
    with open('../lhs.py', 'w') as f:
        f.write(f'''from playground import *
''')
        for p in g.productions:
            f.write(f'''
class {p.lhs}(Base, metaclass=LHS):
    key = {p.key}
    relativeOrder = {p.relativeOrder}
    rhs = {p.rhs}
    def __init__(self):
''')
