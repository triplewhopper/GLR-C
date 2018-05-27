from c_parser import GLR1Parser
from c_parser import Grammar
import tokenizer
from collections import namedtuple
from c_parser import ValueExpressionParser
from typing import List, Iterable, FrozenSet, Tuple


class Node:
    def __init__(self, character: str, rhses, prev, value=None):
        """

        :param character:
        :type character:str
        :param rhses:
        :type rhses:Iterable[Iterable[Node]]
        :param prev:
        :type prev:Iterable[Node]
        :param value:
        """
        self.character: str = character
        self.value = value
        self.rhses: FrozenSet[Tuple[Node]] = frozenset(tuple(x) for x in rhses)
        self.prev: FrozenSet[Node] = frozenset(prev)
        self.__hash = hash((self.character, self.value, self.rhses, self.prev))

    def __str__(self):
        if len(self.rhses) == 1:
            return '%s<ul>%s</ul>' % (self.character, ''.join('<li>%s</li>' % j for i in self.rhses for j in i))
        if len(self.rhses) >= 2:
            return '%s<ul>%s</ul>' % (
                self.character,
                ''.join(
                    '<li>解%s<ul>%s</ul></li>' % (
                        i + 1, ''.join(
                            '<li>%s</li>' % k for k in j))
                    for i, j in enumerate(self.rhses)))
        return '%s' % (self.character) if self.character == self.value else '%s' % self.value
        # if self.ch:
        #     return ' (%s) ' % (''.join('%s' % i for i in self.ch),)
        # return '\'%s\'' % (self.character) if self.character == self.value else '%s' % self.value

    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        assert isinstance(other, Node)
        if hash(self) != hash(other):
            return False
        return self.character == other.character and self.rhses == other.rhses and self.value == other.value \
               and self.prev == other.prev

    def __repr__(self):
        return str(self.character)


class ExpressionNode(Node):
    def __init__(self, character: str, rhses, prev, value=None):
        """

        :param character:
        :type character:str
        :param rhses:
        :type rhses:Iterable[Iterable[Node]]
        :param prev:
        :type prev:Iterable[Node]
        :param value:
        """
        super(ExpressionNode, self).__init__(character, rhses, prev, value)
    def invoke(self):
