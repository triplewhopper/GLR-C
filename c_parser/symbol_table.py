import tokenizer
from collections import UserDict
from typing import Dict, List

predeclared = frozenset(tokenizer.keywords) | frozenset(tokenizer.builtinTypes)


class SymbolTable(UserDict):
    def __init__(self):
        pass

    def __getitem__(self, item: str):
        assert isinstance(item, str)
        return self.data[item]

    def __contains__(self, item: str):
        assert isinstance(item, str)
        if item in predeclared:
            return True
        if item in self.data:
            return True
        return False

    def __setitem__(self, key: str, value):
        assert isinstance(key, str)
        assert key not in predeclared
        self.data[key] = value


class SymbolTableStack:
    def __init__(self):
        self.stack: List[SymbolTable] = []

    def __len__(self):
        return len(self.stack)

    def insertEntry(self, key, value):
        assert not self
        self.stack[-1][key] = value
        return self

    def push(self):
        self.stack.append(SymbolTable())
        return self

    def pop(self):
        return self.stack.pop()

    def top(self):
        return self.stack[-1]

    def __getShallowestEntry(self, item):
        for t in reversed(self.stack):
            if item in t:
                return t

    def __contains__(self, item: str):
        assert isinstance(item, str)
        return self.__getShallowestEntry(item) is not None

    def __getitem__(self, item: str):
        assert isinstance(item, str)
        t = self.__getShallowestEntry(item)
        if t is not None:
            return t[item]
        raise RuntimeError('%s undeclared.' % item)

    def __setitem__(self, key, value):
        assert isinstance(key, str)
        t = self.__getShallowestEntry(key)
        if t is not None:
            t[key] = value
        else:
            self.insertEntry(key, value)


stack = SymbolTableStack()
stack.push()