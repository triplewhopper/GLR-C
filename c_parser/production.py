class Production:
    count = 0

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = tuple(e[1:-1] if e[0] == '"' and e[-1] == '"' else e for e in rhs)
        self.key = Production.count
        self.relativeOrder: int = None
        self.__hash = hash((self.lhs, '→') + self.rhs)
        Production.count += 1

    def __repr__(self):
        return f"{self.lhs} → {' '.join(self.rhs)}"

    def __str__(self):
        return f"{self.lhs} → {' '.join(self.rhs)}"

    def __len__(self):
        return len(self.rhs)

    def __eq__(self, other):
        return self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self):
        return self.__hash

    def __lt__(self, other):
        return self.key < other.key
