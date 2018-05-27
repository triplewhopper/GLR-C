class EOF(str):
    def __new__(cls, s, *args, **kwargs):
        return str.__new__(cls, s)

    def __init__(self, s):
        super(EOF, self).__init__()
        self.__hash = 233

    def __str__(self):
        return 'EOF(%s)' % super(EOF, self).__repr__()

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, EOF)

    def __lt__(self, other):
        return not (self == other)

    def __hash__(self):
        return self.__hash


class Epsilon(str):
    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, 'ε')

    def __init__(self):
        super(Epsilon, self).__init__()
        self.__hash = hash((super(Epsilon, self).__hash__(),))

    def __str__(self):
        return "Epsilon('ε')"

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Epsilon)

    def __lt__(self, other):
        return not (self == other)

    def __hash__(self):
        return self.__hash


eof = EOF('$')
epsilon = Epsilon()
#epsilon = 'ε'
