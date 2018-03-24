from collections import OrderedDict

from c_parser import grammarTokenizer
from c_parser.constants import eof
from c_parser.production import Production
import hashlib

class Grammar:
    def __readFromFile(self, filename: str):
        with open(filename) as file:
            s = map(lambda x: x.strip(), file.readlines())
            s = filter(lambda x: x != '', s)
            s = '\n'.join(list(s)) + '\n'
        return s

    def __init__(self, *filename):
        s = self.__readFromFile(*filename)
        self.sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()
        s = grammarTokenizer.tokenizer(s)
        assert len(s) > 3
        assert s[0].token_t == 'nude'
        assert s[1].token_t == 'lhs'
        assert s[2].token_t == '->'
        start = s[0].value
        i = 1
        tmp = []
        buf = []
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

        lhs = OrderedDict()
        self.__start = start + '\''
        lhs[self.__start] = [(start,)]
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

        assert start in lhs.keys()

        self.productions = [Production(l, r) for l in lhs for r in lhs[l]]
        self.lhs = {}
        for i, p in enumerate(self.productions):
            if p.lhs not in self.lhs:
                self.lhs[p.lhs] = []
            self.lhs[p.lhs].append(i)

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
        return 'start: ' + self.start + '\n' + \
               'intermediates: ' + str(sorted(self.intermediate)) + '\n' + \
               'terminals: ' + str(sorted(self.terminal)) + '\n' + \
               '\n'.join(str(i) for i in self.productions) + '\n'

    def __len__(self):
        return len(self.productions)

    def __getitem__(self, item):
        return self.productions[item]

    def allProductionsStartingWith(self, x):
        assert x in self.intermediate
        return self.lhs[x]