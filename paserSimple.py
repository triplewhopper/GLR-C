from collections import deque

productions = []
epsilon = 'ε'
eof = '$'


class Production:
    count = 0

    @staticmethod
    def create(s):
        assert isinstance(s, str)
        s = s.split(' ')
        assert len(s) >= 3
        assert s[1] == '->'
        rhs = s[2:]
        if rhs == [epsilon]:
            rhs.remove(epsilon)
        return Production(s[0], rhs)

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = tuple(rhs)
        self.key = Production.count
        Production.count += 1

    def __repr__(self):
        return self.lhs + ' -> ' + ' '.join(self.rhs)

    def __str__(self):
        return self.lhs + ' -> ' + ' '.join(self.rhs)

    def __len__(self):
        return len(self.rhs)

    def __eq__(self, other):
        return self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self):
        return hash((self.lhs, ' -> ') + self.rhs)

    def __lt__(self, other):
        return self.key < other.key


class Item:
    def __init__(self, G, n, p=0):
        self.n = n
        self.p = p
        self.G = G
        self.lhs = self.production.lhs
        self.rhs = self.production.rhs

    @property
    def production(self):
        return self.G[self.n]

    @property
    def currentCharacter(self):
        if self.p == len(self.production):
            return epsilon
        return self.rhs[self.p]

    def nextCharacter(self):
        if self.p == len(self.production):
            raise IndexError()
        if self.p == len(self.production) - 1:
            return epsilon
        return self.rhs[self.p + 1]

    def __repr__(self):
        # return 'Item'+str((self.n,self.p))
        a = ' '.join(self.rhs[:self.p])
        b = ' '.join(self.rhs[self.p:])
        if a:
            return 'Item(' + self.lhs + ' -> ' + a + '•' + b + ')'
        return 'Item(' + self.lhs + ' ->•' + b + ')'

    def __len__(self):
        return len(self.production)

    def __eq__(self, other):
        return self.n == other.n and \
               self.p == other.p

    def __hash__(self):
        return hash((self.n, self.p))

    def __lt__(self, other):
        return self.n < other.n or self.n == other.n and self.p < other.p


class Grammar:
    def __init__(self, input: list):
        assert isinstance(input[0][0], str)
        assert len(input[0]) == 1
        global productions

        start = input[0][0]
        self.__start = start + '\''
        productions = (Production.create("%s -> %s" % (self.start, start)),) + \
                      tuple(sorted(set(Production.create(i) for i in input[1:])))

        self.intermediate = frozenset(p.lhs for p in productions)

        assert self.__start in self.intermediate

        self.characters = self.intermediate | \
                          frozenset(e for x in productions for e in x.rhs)
        self.terminal = (self.characters - self.intermediate)|{eof}

    # def __init__(self, productions, S):
    #     super(Grammar, self).__init__()
    #     self.intermediate = frozenset(p.lhs for p in productions)
    #     tmp = frozenset(e for x in productions for e in x.rhs)
    #     self.terminal = (tmp | self.intermediate) - self.intermediate
    #     self.__start = S
    #     assert S in self.intermediate

    @property
    def start(self):
        return self.__start

    def __str__(self):
        return 'start: ' + self.start + '\n' + \
               'intermediates: ' + str(self.intermediate) + '\n' + \
               'terminals: ' + str(self.terminal) + '\n' + \
               '\n'.join(str(i) for i in productions) + '\n'

    def __len__(self):
        return len(productions)

    def __getitem__(self, item):
        return productions[item]

    def allProductionsStartingWith(self, x):
        assert x in self.intermediate
        return (i for i in range(len(self)) if self[i].lhs == x)


class CanonicalLR0Collection:
    def __init__(self, G: Grammar):
        self.G = G
        self.__first = {x: {x} for x in G.terminal}
        self.__follow = {}
        self.__closure = {}
        self.__goto = {}
        self.indexByInt = {}
        self.indexByFrozenSet = {}
        self._collections = None
        self._calc()
        # print([i for i in sorted(map(len,self._collections))])
        # print([len(i) for i in sorted(self._collections)])

        for I in self._collections:
            self.indexByFrozenSet[I] = I.key
            self.indexByInt[I.key] = I
        for i in self.__goto:
            for j in self.__goto[i]:
                if not self.__goto[i][j]:
                    continue
                self.__goto[i][j] = self.indexByFrozenSet[self.__goto[i][j]]
        for i in self.__closure:
            if not self.__closure[i]:
                continue
            self.__closure[i] = self.indexByFrozenSet[self.__closure[i]]
        print(self.collections)
        self._calculateFollow()
        pass
    @property
    def collections(self):
        return self._collections

    def _calc(self):
        self._collections = {ItemSet(self._closure(frozenset([Item(self.G, 0, 0)])))}
        q = deque(self._collections)
        #chars = ('E', 'T', 'F', '(', 'id', ')', '+', '*')
        while q:
            I = q.popleft()
            for X in G.characters:
                t = self._goto(I, X)
                if t and t not in self._collections:
                    self._collections.add(ItemSet(t))
                    q.append(t)
        self._collections = frozenset(self._collections)

    def _goto(self, I: frozenset, X):
        if I in self.__goto and X in self.__goto[I]:
            return self.__goto[I][X]
        J = set()
        q = list(I)
        while q:
            item = q.pop(0)
            if item.currentCharacter == X and item.p < len(item):
                item = Item(self.G, item.n, item.p + 1)
                q.append(item)
                J.add(item)
        if I not in self.__goto:
            self.__goto[I] = {}
        self.__goto[I][X] = self._closure(frozenset(J))
        return self.__goto[I][X]

    def goto(self, i, a):
        assert isinstance(i, int)
        if a not in self.__goto[self.indexByInt[i]]:
            assert 0
        return self.__goto[self.indexByInt[i]][a]

    def _closure(self, I: frozenset):
        if I in self.__closure:
            return self.__closure[I]
        J = set(I)
        q = list(I)
        while q:
            B = q.pop(0).currentCharacter
            if B in self.G.intermediate:
                for n in self.G.allProductionsStartingWith(B):
                    i = Item(self.G, n, 0)
                    if i not in J:
                        q.append(i)
                        J.add(i)
        res = frozenset(J)
        self.__closure[I] = res
        return res

    def first(self, X: str or list) -> set:
        if isinstance(X, str):
            if X in self.__first:
                return self.__first[X]
            res = set()
            for i in productions:
                if i.lhs == X:
                    if not i.rhs:
                        res.add(epsilon)
                    else:
                        if i.rhs[0] == X:
                            continue
                        j = 0
                        res |= self.first(i.rhs[0])
                        while j < len(i.rhs) and epsilon in self.first(i.rhs[j]):
                            res |= self.first(i.rhs[j])
                            j += 1
            self.__first[X] = res
            return res
        elif isinstance(X, tuple):
            res = set()
            i = 0
            while i < len(X) and epsilon in self.first(X[i]):
                i += 1
            if i == len(X):
                res.add(epsilon)
                i -= 1
            while i >= 0:
                res |= self.first(X[i]) - {epsilon}
                i -= 1

            return res

    def _calculateFollow(self):
        for B in self.G.intermediate:
            self.__follow[B] = set()
        self.__follow[self.G.start] = {eof}

        for prod in productions:
            for j, B in enumerate(prod.rhs):
                if B in self.G.intermediate:
                    firstbeta = self.first(prod.rhs[j + 1:])
                    self.__follow[B] |= firstbeta - {epsilon}

        q = deque(self.__follow)
        while q:
            key = q.popleft()
            value = self.__follow[key]
            # print(key, value)
            for prod in list(filter(lambda x: key == x.lhs, productions)):
                for j, B in enumerate(prod.rhs):
                    if B in self.G.intermediate and not value.issubset(self.__follow[B]):
                        if epsilon not in self.first(prod.rhs[j + 1:]):
                            continue
                        self.__follow[B] |= value
                        q.append(B)

        pass

    def follow(self, A):
        assert A in self.G.intermediate
        return self.__follow[A]

    def at(self, x):
        if isinstance(x, int):
            return self.indexByInt[x]
        elif isinstance(x, frozenset):
            return self.indexByFrozenSet[x]

    def __str__(self):
        return str(self._collections)



class ItemSet(frozenset):
    count = 0

    def __init__(self, value):
        # super(ItemSet, self).__init__(value)
        self.key = ItemSet.count
        ItemSet.count += 1

    def __lt__(self, other):
        return self.key < other.key

    def __repr__(self):
        return 'I_%s{%s}' % (self.key, ','.join(str(i) for i in sorted(self)))


def format(x: dict):
    indent = 0
    s = '  '
    for k, v in x.items():
        print(k)
        indent += 1
        for i in sorted(v):
            print(s * indent + str(i))
        indent -= 1
    print()


def calculate(G):
    collection = CanonicalLR0Collection(G)
    print('itemSet.count=', ItemSet.count)
    action = {i: {} for i in range(len(collection.collections))}
    goto = {i: {} for i in range(len(collection.collections))}
    # print([(i, I) for i, I in collection.indexByInt.items()])

    for i in range(ItemSet.count):
        I = collection.at(i)
        print(i, end='')
        for item in sorted(I):
            A = item.lhs
            a = item.currentCharacter
            print('(%s,%s)' % (A, a), end='')
            if a == epsilon:
                print('A', end='')
                if A == G.start:
                    assert eof not in action[i]
                    action[i][eof] = ('accept',)
                else:
                    for followA in collection.follow(A):
                        if followA in action[i]:
                            if action[i][followA] != ('reduce', item.production.key):
                                # print('i=', i, 'I=', I)
                                # print(item)
                                # print('action[%s][%s]=%s' % (i, followA, action[i][followA]))
                                assert 0
                        action[i][followA] = ('reduce', item.production.key)
            elif a in G.terminal:
                print('B', end='')
                if a in action[i]:
                    if action[i][a] != ('shift', collection.goto(i, a)):
                        assert 0
                action[i][a] = ('shift', collection.goto(i, a))
            else:
                print('C', end='')
                if a in goto[i]:
                    tmp = ('goto', collection.goto(i, a))
                    if goto[i][a] != tmp:
                        assert tmp == ('goto', collection.goto(i, a))
                        # print('conflict in goto[%s][%s] at %s against %s' % (i,a,goto[i][a],tmp))
                goto[i][a] = ('goto', collection.goto(i, a))
        print()

    print(len(collection.collections))
    parse('id = * id'.split(' '), action, goto)


class Node:
    def __init__(self, name, children):
        self.name = name
        self.children = tuple(children)

    def __str__(self):
        if self.children:
            return '%s<ul>%s</ul>' % (self.name, ''.join('<li>%s</li>' % i for i in self.children))
        return '%s' % (self.name)

    __repr__ = __str__


def parse(tokens: list, action: dict, goto: dict):
    tokens.append(eof)
    stack = deque([0])
    nodestack = deque()
    cur = -1

    def stackTop():
        assert stack
        return stack[len(stack) - 1]

    def next():
        nonlocal cur
        cur += 1
        return tokens[cur]

    a = next()
    while True:
        s = stackTop()
        print('stack:', stack)
        print('node:', nodestack)
        # print('s=%s,a=%s,i=%s' % (s, a, cur))
        curAction = action[s][a]
        if curAction[0] == 'shift':
            stack.append(curAction[1])
            nodestack.append(Node(a, ()))
            a = next()
        elif curAction[0] == 'reduce':
            index = curAction[1]
            A, beta = productions[index].lhs, productions[index].rhs
            tmp = []
            for i in range(len(beta)):
                tmp.append(nodestack.pop())
                stack.pop()
            tmp.reverse()
            node = Node(A, tmp)
            t = stackTop()
            stack.append(goto[t][A][1])
            nodestack.append(node)
            print(productions[index])
        elif curAction[0] == 'accept':
            print('accept')
            break
        else:
            assert 0


if __name__ == '__main__':
    with open('cfg.txt') as file:
        s = list(filter(lambda x: x != '', ''.join(file.readlines()).split('\n')))

    G = Grammar(s)
    # print(collection)
    calculate(G)
    stack = [0]

    # items = sorted(items)
    # items = groupby(items,key=lambda x:(x.n,x.p))
    # items = list(map(lambda x:list(x[1]),items))
