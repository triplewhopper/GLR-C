import collections


class Location:
    __slots__ = ('__line', '__column')

    def __init__(self, line=0, column=0):
        self.__line = line
        self.__column = column

    @property
    def line(self) -> int:
        return self.__line

    @property
    def column(self) -> int:
        return self.__column

    def shift(self, r: int = 1):
        return Location(self.line, self.column + r)

    def nextLine(self):
        return Location(self.line + 1, 0)

    def __str__(self):
        return 'Loc<{}:{}>'.format(self.line + 1, self.column + 1)

    def __eq__(self, other: 'Location'):
        assert isinstance(other, Location)
        return self.line == other.line and self.column == other.column

    def __hash__(self):
        return hash(str(self))


class SourceLocation:
    """
    前闭后开.
    """
    __slots__ = ('__start', '__end')

    def __init__(self, start: Location, end: Location = None):
        self.__start = start
        self.__end = end if end is not None else start

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    @staticmethod
    def presentForEOF():
        return SourceLocation(Location(-1, -1))

    def __str__(self):
        if self.start.line == self.end.line:
            return '<{}:{}..{}>'.format(self.start.line + 1, self.start.column + 1, self.end.column + 1)
        return '<{}, {}>'.format(self.start, self.end)

    def __eq__(self, other: 'SourceLocation'):
        assert isinstance(other, SourceLocation)
        return self.start == other.start and self.end == other.end

    def __hash__(self):
        return hash(str(self))


class CToken:
    __slots__ = ('__token_t', '__data', '__position', '__rawData')

    def __init__(self, position: SourceLocation, token_t: str, data, rawData: str):
        self.__token_t = token_t
        self.__data = data
        self.__rawData = rawData
        self.__position = position

    @property
    def token_t(self):
        return self.__token_t

    @property
    def rawData(self) -> str:
        return self.__rawData

    @property
    def data(self):
        return self.__data

    @property
    def position(self) -> SourceLocation:
        return self.__position

    def __str__(self):
        if self.token_t == self.data:
            assert self.rawData == self.data
            return 'Tok({}, {})'.format(self.position, repr(self.data))
        if self.data == self.rawData:
            return 'Tok({}, {}, {})'.format(self.position, repr(self.token_t), repr(self.data))
        return 'Tok({}, {}, {}, raw:{})'.format(self.position, repr(self.token_t), repr(self.data), repr(self.rawData))

    __repr__ = __str__

    def __eq__(self, other: 'CToken'):
        assert isinstance(other, CToken)
        return self.position == other.position \
               and self.data == other.data \
               and self.token_t == other.token_t \
               and self.rawData == other.rawData

    def __hash__(self):
        # FIXME: 这里没有把rawData算进去
        return hash(str(self))
