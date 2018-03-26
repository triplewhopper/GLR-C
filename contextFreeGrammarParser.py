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

    def merge(self, other):
        """

        :param other:
        :type other:Node
        :return: Node
        """
        if other is None:
            return self
        assert isinstance(other, Node)
        assert other.character == self.character
        assert other.prev==self.prev
        assert self.value is None
        return Node(self.character, self.rhses | other.rhses, self.prev | other.prev)

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
        if hash(self) !=hash(other):
            return False
        return self.character == other.character and self.rhses == other.rhses and self.value == other.value \
               and self.prev == other.prev

    def __repr__(self):
        return str(self.character)


if __name__ == '__main__':
    GG = Grammar('std.txt')
    # GG = Grammar('std.txt')
    #    print(collection)
    s = list(tokenizer.tokenizeFromFile('stmt.txt'))
    # for token in s:
    #     print(token)
    p = ValueExpressionParser(GG)
    with open('ast.html', 'w', encoding='gbk') as file:
        rt = p.parse(s)
        file.write('<html><body>')
        file.write(str(rt))
        file.write('</body></html>')
