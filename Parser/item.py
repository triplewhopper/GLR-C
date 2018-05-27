from Parser.constants import epsilon


class Item:
    def __init__(self, G, n, p, a):
        self.n = n
        self.p = p
        self.a = a
        self.G = G
        self.lhs = self.production.lhs
        self.rhs = self.production.rhs
        self.curChar = epsilon if self.p == len(self.production) else self.rhs[self.p]

    @property
    def production(self):
        return self.G[self.n]

    @property
    def currentCharacter(self):
        return self.curChar

    # noinspection NonAsciiCharacters
    @property
    def β(self):
        return self.rhs[self.p + 1:]

    def __repr__(self):
        # return 'Item'+str((self.n,self.p))
        r1 = ' '.join(self.rhs[:self.p])
        r2 = ' '.join(self.rhs[self.p:])
        if r1:
            return '[%s → %s•%s; %s]' % (self.lhs, r1, r2, self.a)
        return '[%s →•%s; %s]' % (self.lhs, r2, self.a)

    def __len__(self):
        return len(self.production)

    def __eq__(self, other):
        return self.n == other.n and \
               self.p == other.p and \
               self.a == other.a

    def __hash__(self):
        return hash((self.n, self.p, self.a))

    def __lt__(self, other):
        return (self.n, self.p, self.a) < (other.n, other.p, other.a)
