from collections import deque

from c_parser.constants import eof, epsilon
import c_parser.itemset
from c_parser.item import Item
from c_parser.grammar import Grammar
from typing import Dict, List, Set, FrozenSet


class CanonicalLR1Collection:
    def __init__(self, grammar: Grammar, ItemSet_t: type = c_parser.itemset.ItemSet):
        self.__G = grammar
        self.__ItemSet_t = ItemSet_t
        self.__first: Dict[str, Set[str]] = {x: {x} for x in grammar.terminal}
        self.__visit: Set[str] = set()
        self.__follow = {}
        self.__closure = {}
        self.__goto = {}
        self.indexByInt: dict = None
        self.indexByFrozenSet: dict = {}
        self._collections: set = None
        print('what?')
        self._calc()
        print('/what?')
        # print([i for i in sorted(map(len,self._collections))])
        # print([len(i) for i in sorted(self._collections)])
        self.indexByInt = [0] * self.__ItemSet_t.count
        for I in self._collections:
            self.indexByFrozenSet[I] = I.key
            self.indexByInt[I.key] = I
        for i in self.__goto:
            for j in self.__goto[i]:
                if not self.__goto[i][j]:
                    continue
                self.__goto[i][j] = self.indexByFrozenSet[self.__goto[i][j]]
        self.__goto = {self.indexByFrozenSet[x]: self.__goto[x] for x in self.__goto}
        for i in self.__closure:
            if not self.__closure[i]:
                continue
            self.__closure[i] = self.indexByFrozenSet[self.__closure[i]]
        print(self.collections)
        print("总项数:%s" % (sum(len(x) for x in self._collections)))
        self._calculateFollow()
        pass

    @property
    def collections(self):
        return self._collections

    def _calc(self):
        self._collections = {
            self.__ItemSet_t(
                self._closure(
                    frozenset([Item(self.__G, 0, 0, eof)])
                )
            )
        }
        q = deque(self._collections)
        # chars = ('E', 'T', 'F', '(', 'id', ')', '+', '*')
        while q:
            I = q.popleft()
            print('len=%s' % len(q))
            for X in sorted(self.__G.characters):
                t = self._goto(I, X)
                if t and t not in self._collections:
                    self._collections.add(self.__ItemSet_t(t))
                    q.append(t)
        self._collections = frozenset(self._collections)
        return self

    def _goto(self, I: frozenset, X):
        if I in self.__goto and X in self.__goto[I]:
            return self.__goto[I][X]
        J = set()
        q = deque(I)
        while q:
            item = q.popleft()
            # [A → α•Xβ, a]
            if item.currentCharacter == X and item.p < len(item):
                item = Item(self.__G, item.n, item.p + 1, item.a)
                # [A → αX•β, a]
                q.append(item)
                J.add(item)
        if I not in self.__goto:
            self.__goto[I] = {}
        self.__goto[I][X] = self._closure(frozenset(J))
        return self.__goto[I][X]

    def goto(self, i, a):
        # assert isinstance(i, int)
        return self.__goto[i][a]

    # noinspection NonAsciiCharacters
    def _closure(self, I: frozenset):
        if I in self.__closure:
            return self.__closure[I]
        J = set(I)
        q = deque(I)
        while q:
            item = q.popleft()
            # item = [A → α•Bβ, a]
            B = item.currentCharacter
            if B in self.__G.intermediate:
                βa = item.β + (item.a,)
                for n in self.__G.allProductionsStartingWith(B):
                    # B → γ
                    for b in self.first(βa):
                        i = Item(self.__G, n, 0, b)
                        # i = [B → •γ, b]
                        if i not in J:
                            q.append(i)
                            J.add(i)
        res = frozenset(J)
        self.__closure[I] = res
        return res

    def first(self, X: str or tuple) -> set:
        if isinstance(X, str):
            if X in self.__first:
                return self.__first[X]
            res = set()
            self.__visit.add(X)
            for i in (self.__G[k] for k in self.__G.allProductionsStartingWith(X)):
                if not i.rhs:
                    res.add(epsilon)
                else:
                    if i.rhs[0] in self.__visit:
                        continue
                    j = 0
                    res |= self.first(i.rhs[0])
                    while j < len(i.rhs) and epsilon in self.first(i.rhs[j]):
                        res |= self.first(i.rhs[j])
                        j += 1
            self.__first[X] = res
            self.__visit.remove(X)
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
        for B in self.__G.intermediate:
            self.__follow[B] = set()
        self.__follow[self.__G.start] = {eof}

        for prod in self.__G.productions:
            for j, B in enumerate(prod.rhs):
                if B in self.__G.intermediate:
                    firstbeta = self.first(prod.rhs[j + 1:])
                    self.__follow[B] |= firstbeta - {epsilon}

        q = deque(self.__follow)
        while q:
            key = q.popleft()
            value = self.__follow[key]
            # print(key, value)
            for prod in (self.__G[i] for i in self.__G.allProductionsStartingWith(key)):
                for j, B in enumerate(prod.rhs):
                    if B in self.__G.intermediate and not value.issubset(self.__follow[B]):
                        if epsilon not in self.first(prod.rhs[j + 1:]):
                            continue
                        self.__follow[B] |= value
                        q.append(B)

        return self

    def follow(self, A):
        assert A in self.__G.intermediate
        return self.__follow[A]

    def at(self, x):
        if isinstance(x, int):
            return self.indexByInt[x]
        elif isinstance(x, frozenset):
            return self.indexByFrozenSet[x]

    def __str__(self):
        return str(self._collections)

    def __len__(self):
        return len(self.collections)
