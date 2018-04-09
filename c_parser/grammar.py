from collections import OrderedDict

from c_parser import grammarTokenizer
from c_parser.constants import eof
from c_parser.production import Production
import hashlib
from typing import List, Tuple, Dict, FrozenSet
from c_parser.grammarTokenizer import Token


class Grammar:
    def __readFromFile(self, filename: str):
        with open(filename) as file:
            #            s = map(lambda x: x.strip(), file.readlines())
            #            s = filter(lambda x: x != '', s)
            s = ''.join(list(file.readlines())) + '\n'
        return s

    def __init__(self, *filename):
        s: str = self.__readFromFile(*filename)
        self.sha1 = hashlib.sha1(s.encode('utf-8')).hexdigest()
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
                    # print(' '.join(x.value for x in buf))
                    buf = []
                else:
                    assert i == 1

            buf.append(s[i])
            i += 1
        if buf:
            tmp.append(buf)

        lhs: OrderedDict[str, List[Tuple[str]]] = OrderedDict()
        self.__start = start + '\''
        lhs[self.__start] = [(start,)]
        for p in tmp:
            if p[0].value not in lhs:
                lhs[p[0].value] = []
            buf: List[str] = []
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
        self.lhs: Dict[str, List[int]] = {}
        for i, p in enumerate(self.productions):
            if p.lhs not in self.lhs:
                self.lhs[p.lhs] = []
            self.lhs[p.lhs].append(i)
            p.relativeOrder=len(self.lhs[p.lhs])

        print(self.productions)
        self.intermediate: FrozenSet[str] = frozenset(lhs.keys())
        self.characters: FrozenSet[str] = self.intermediate | \
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
