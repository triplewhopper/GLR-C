from c_parser import GLR1Parser
from c_parser import Grammar
import tokenizer
from collections import namedtuple
from c_parser import ValueExpressionParser


class Node:
    def __init__(self, character: str, rhs: list or tuple, value=None):
        self.character = character
        self.value = value
        self.rhses = (tuple(rhs),) if rhs else ()
        self.__hash = hash((self.character, self.value, self.rhses))


    def __str__(self):
        if len(self.rhses) == 1:
            return '%s<ul>%s</ul>' % (self.character, ''.join('<li>%s</li>' % i for i in self.rhses[0]))
        if len(self.rhses) >= 2:
            return '%s<ul>%s</ul>' % (
                self.character,
                ''.join(
                    '<li>解%s<ul>%s</ul></li>' % (
                        i + 1, ''.join(
                            '<li>%s</li>'% k for k in j))
                    for i, j in enumerate(self.rhses)))
        return '%s' % (self.character) if self.character == self.value else '%s' % self.value
        # if self.ch:
        #     return ' (%s) ' % (''.join('%s' % i for i in self.ch),)
        # return '\'%s\'' % (self.character) if self.character == self.value else '%s' % self.value

    def merge(self, another):  # 合并两个具有相同character的节点
        assert isinstance(another, Node)
        assert self.character == another.character
        self.rhses += another.rhses
        return self

    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return self.character == other.ast_node_t and self.rhses == other.ch

    # def dfs(self):
    #     if not self.ch:
    #         return self.name
    #     if self.name == 'S':
    #         return [self.ch[0].dfs(), self.ch[1].dfs()]
    #     elif self.name == 'START':
    #         return self.ch[0].dfs()
    #     elif self.name == 'PRODUCTIONS':
    #         assert self.ch[0].name == 'PRODUCTION'
    #         res = [self.ch[0].dfs()]
    #         if len(self.ch) > 1:
    #             res.extend(self.ch[1].dfs())
    #         return res
    #     elif self.name == 'PRODUCTION':
    #         return [[self.ch[0].dfs(), rhs] for rhs in self.ch[2].dfs()]
    #     elif self.name == 'RHS':
    #         res = self.ch[0].dfs()
    #         if isinstance(res[0], list):
    #             return res
    #         return [self.ch[0].dfs()]
    #     elif self.name == 'MULTIPLE_RHS':
    #         assert self.ch[1].name == '|'
    #         return self.ch[0].dfs() + self.ch[2].dfs()
    #     elif self.name == 'SINGLE_RHS':
    #         if self.ch[0].name == 'SINGLE_RHS':
    #             return self.ch[0].dfs() + [self.ch[1].dfs()]
    #         return [self.ch[0].dfs()]

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
