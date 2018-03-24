from collections import deque

from ctoken import CToken
from c_parser.constants import epsilon, eof
from c_parser.itemset import ItemSet
from c_parser.canonicalLR_1_collection import CanonicalLR1Collection

class GLR1Parser:
    def __init__(self, G):
        self.G = G
        self.collection = CanonicalLR1Collection(G)
        self.action = None
        self.goto = None
        self.preprocess()

    def preprocess(self):
        print('itemSet.count=', ItemSet.count)
        factory = lambda: {i: {} for i in range(len(self.collection))}
        action = factory()
        record = factory()
        goto = factory()
        for i in range(ItemSet.count):
            I = self.collection.at(i)
            # print(i, end='')
            for item in sorted(I):
                A = item.lhs
                a = item.currentCharacter
                b = item.a
                # print('[%s, %s; %s]' % (A, a, b), end='')
                if a == epsilon:
                    # print('A', end='')
                    if A == self.G.start:
                        # [S' → S•,$]
                        assert eof not in action[i]
                        assert b == eof
                        action[i][eof] = ('accept', '')
                    else:
                        # [A → α•, b]

                        if b in action[i]:
                            if action[i][b][0] == 'reduce':
                                print('Priority conflict at action[%s,%s][%s]=%s' % (i, a, b, action[i][b]))
                                action[i][b] = ('reduce', min(action[i][b][1], item.production.key))
                            elif action[i][b][0] == 'shift':
                                print('shift/reduce conflict against action[%s:%s][%s]=%s' % (i, item, b, action[i][b]))
                                continue
                        action[i][b] = ('reduce', item.production.key)
                elif a in self.G.terminal:
                    # print('B', end='')
                    # [A → α•aβ, b]
                    action[i][a] = ('shift', self.collection.goto(i, a))
                else:
                    # print('C', end='')
                    if a in goto[i]:
                        tmp = ('goto', self.collection.goto(i, a))
                        if goto[i][a] != tmp:
                            assert tmp == ('goto', self.collection.goto(i, a))
                            # print('conflict in goto[%s][%s] at %s against %s' % (i,a,goto[i][a],tmp))
                    goto[i][a] = ('goto', self.collection.goto(i, a))
            # print()
        self.action = action
        self.goto = goto
        self.genTable()
        return self

    def genTable(self):
        with open('screen.html', 'w', encoding='utf-8') as file:
            print = file.write

            def th(x: str or list or int = '', **kwargs) -> None:
                print('<th %s>%s</th>' % (' '.join(map(lambda k: '%s="%s"' % (k, kwargs[k]), kwargs.keys())), x))

            def td(x: str or list or int = '', args='') -> None:
                print('<td %s>%s</td>' % (args, x))

            print('<html><body>')
            print('<table border="1">')
            print('<tr><th></th>')
            inters = sorted(self.G.intermediate)
            terminals = sorted(self.G.terminal)

            th('ACTION', colspan=len(terminals))
            th('GOTO', colspan=len(inters))
            print('</tr>')
            print('<tr>')
            th()
            for i in terminals:
                th(i)

            for i in inters:
                th(i)
            print('</tr>')
            for i in range(len(self.collection)):
                print('<tr>')
                th(i)
                for j in terminals:
                    if j in self.action[i]:
                        td('%s' % (self.action[i][j],))
                    else:
                        td()
                for j in inters:
                    if j in self.goto[i]:
                        td('%s' % (self.goto[i][j],))
                    else:
                        td()
                print('</tr>')
            print('</table>')

            print('<table border="1">')
            for i in range(len(self.G)):
                print('<tr>')
                th(i)
                td(self.G[i])
                print('</tr>')
            print('</table>')

            print('<table border="1">')
            for i in range(len(self.collection.indexByInt)):
                print('<tr>')
                th(i, rowspan=1 + len(self.collection.indexByInt[i]))
                print('</tr>')
                for prod in sorted(self.collection.indexByInt[i]):
                    print('<tr>')
                    td(prod)
                    print('</tr>')
            print('</table>')
            print('</body></html>')
        return self

    def parse(self, tokens: list, Node: type):
        stack = deque([0])
        nodestack = deque()
        cur = -1
        tokens = iter(tokens)

        def stackTop():
            assert stack
            return stack[len(stack) - 1]

        def next():
            nonlocal cur
            cur += 1
            try:
                return tokens.__next__()
            except StopIteration:
                return CToken(token_t=eof, value='', position=(-1, -1))

        a = next()
        while True:
            s = stackTop()
            print('stack:', stack)
            print('node:', nodestack)
            print('s=%s,a=%s,i=%s' % (s, a, cur))
            if a.token_t in self.action[s]:
                curAction = self.action[s][a.token_t]
            else:
                raise RuntimeError(
                    'unexcpected \'%s\' after \'%s\' token, cur = %s, row %s, column %s\n expected tokens are listed as below:\n %s' %
                    (a, nodestack[len(nodestack) - 1], cur, a.position[0], a.position[1],self.action[s].keys()))


            if curAction[0] == 'shift':
                stack.append(curAction[1])
                nodestack.append(Node(a.value, ()))
                a = next()
            elif curAction[0] == 'reduce':
                index = curAction[1]
                A, β = self.G[index].lhs, self.G[index].rhs
                # A → β
                tmp = []
                for i in range(len(β)):
                    tmp.append(nodestack.pop())
                    stack.pop()
                tmp.reverse()
                t = stackTop()
                stack.append(self.goto[t][A][1])
                nodestack.append(Node(A, tmp))
                print(self.G[index])
            elif curAction[0] == 'accept':
                print('accept')
                break
            else:
                assert 0
        # print(nodestack[0])
        # dfs = nodestack[0].dfs()
        # print(dfs)
        res = []

        def printlist(x, *args):
            if not isinstance(x, list):
                res.append('<li>%s,%s</li>' % (args, x))
                return
            res.append('<ul>')
            for i in range(len(x)):
                printlist(x[i], *(args + (i + 1,)))

            res.append('</ul>')

        # printlist(dfs)
        return nodestack[0]
