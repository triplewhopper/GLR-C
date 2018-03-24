from collections import deque, OrderedDict
from ctoken import CToken
from c_parser.constants import epsilon, eof
from c_parser.canonicalLR_1_collection import CanonicalLR1Collection
import pickle
from c_parser.grammar import Grammar
from c_parser.production import Production
from contextFreeGrammarParser import Node
import hashlib


class ExpressionItemSet(frozenset):
    count = 0

    def __init__(self, value):
        self.key = ExpressionItemSet.count
        self.operator = ""
        self.argc = 0
        ExpressionItemSet.count += 1

    def setConfig(self, operator, argc):
        self.operator = operator
        self.argc = argc

    def __lt__(self, other):
        return self.key < other.key

    def __repr__(self):
        return 'I_%s{%s}' % (self.key, ','.join(str(i) for i in sorted(self)))


class ValueExpressionParser:
    def __init__(self, G: Grammar):
        self.G = G
        with open('sha1.txt') as old:
            oldhash = old.read()
            newhash = G.sha1
        if oldhash != newhash:
            print("New!")
            self.collection = CanonicalLR1Collection(G, ExpressionItemSet)
            self.action = None
            self.goto = None
            self.preprocess()
            with open('action.pickle', 'wb') as actionPickle, \
                    open('goto.pickle', 'wb') as gotoPickle, \
                    open('collection.pickle', 'wb') as collectionPickle:
                pickle.dump(self.action, actionPickle)
                pickle.dump(self.goto, gotoPickle)
                pickle.dump(self.collection, collectionPickle)
            with open('sha1.txt', 'w') as old:
                old.write(newhash)
            print("data has been written to file.")
        else:
            print("ロード中...")
            with open('action.pickle', 'rb') as actionPickle, \
                    open('goto.pickle', 'rb') as gotoPickle, \
                    open('collection.pickle', 'rb') as collectionPickle:
                self.action = pickle.load(actionPickle)
                self.goto = pickle.load(gotoPickle)
                self.collection = pickle.load(collectionPickle)
            print("ロード 完了しました。")

    def preprocess(self):
        print('ExpressionItemSet.count=', ExpressionItemSet.count)
        factory = lambda: {i: {} for i in range(len(self.collection))}
        action = factory()
        goto = factory()
        for i in range(ExpressionItemSet.count):
            I = self.collection.at(i)
            # print(i, end='')
            for item in I:
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
                        action[i][eof] = {('accept', '')}
                    else:
                        # [A → α•, b]
                        #
                        if b in action[i]:
                            tmp = {t[0] for t in action[i][b]}
                            # if action[i][b][0] == 'reduce':
                            if 'reduce' in tmp:
                                print('reduce/reduce conflict at action[%s,%s][%s]=%s' % (i, a, b, action[i][b]))
                                # action[i][b] = ('reduce', min(action[i][b][1], item.production.key))
                            # elif action[i][b][0] == 'shift':
                            elif 'shift' in tmp:
                                print('shift/reduce conflict against action[%s:%s][%s]=%s' % (i, item, b, action[i][b]))
                                # continue
                        if b not in action[i]:
                            action[i][b] = set()
                        action[i][b].add(('reduce', item.production.key))
                elif a in self.G.terminal:
                    # # print('B', end='')
                    # # [A → α•aβ, b]
                    if a in action[i]:
                        tmp = {t[0] for t in action[i][a]}
                        # if action[i][a][0] == 'shift':
                        # if 'shift' in tmp:
                        #     #assert action[i][a][1] == self.collection.goto(i, a)
                        #     #continue
                        # #elif action[i][a][0] == 'reduce':
                        if 'reduce' in tmp:
                            print('shift/reduce against action[%s:%s][%s]=%s' % (i, item, a, action[i][a]))
                            print('current %s' % self.collection.goto(i, a))
                    #         # action[i][a] = ('shift', self.collection.goto(i, a))
                    #         continue
                    #         pass
                    if a not in action[i]:
                        action[i][a] = set()

                    action[i][a].add(('shift', self.collection.goto(i, a)))
                    # record[i][a] = b
                    #
                    # action[i][a] = {}
                else:
                    # print('C', end='')
                    if a in goto[i]:
                        tmp = ('goto', self.collection.goto(i, a))
                        if goto[i][a] != tmp:
                            assert tmp == ('goto', self.collection.goto(i, a))
                            print('conflict in goto[%s][%s] at %s against %s' % (i, a, goto[i][a], tmp))
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

            print('<html><meta charset=\'utf-8\'><body>')
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

    def parse(self, tokens: list):

        GLRBranch.tokens = list(tokens)
        GLRBranch.goto = self.goto
        initValue = GLRBranch(GLRNode([], 0, None, ''))
        activeTopStates = {(initValue.top, initValue.pos): initValue}
        ansCount = 0
        res = ''
        f = open('debug.html', 'w')
        while activeTopStates:
            print('activeMap:%d\n' % len(activeTopStates), '\n'.join('%s=> %s' %(k,v) for k,v in activeTopStates.items()),sep='')
            tmp = {}
            for (top, pos), branch in activeTopStates.items():
                a = branch.nextToken()
                # print('stack:', head.stack)
                # print('node:', head.nodestack)
                print('s=%s,a=%s,pos=%s' % (top, a, pos))
                print('head:', top.state)

                try:
                    if a.token_t in self.action[top.state]:
                        curActions = self.action[top.state][a.token_t]
                    else:
                        # assert head.nodestack
                        raise RuntimeError(
                            'unexcpected \'%s\' after \'%s\' token, cur = %s, row %s, column %s\n expected tokens are listed as below:\n %s' %
                            (a, head.backtraceLR().astNode, head.pos, a.position[0], a.position[1],
                             self.action[top].keys()))
                    for curAction in curActions:
                        if curAction[0] == 'shift':
                            print(curAction)
                            newBranch = branch.shift(curAction[1], Node(a.token_t, (), a.value))
                            print(newBranch)
                            key = (newBranch.top, newBranch.pos)
                            if key not in tmp:
                                tmp[key] = [newBranch]
                            else:
                                tmp[key].append(newBranch)
                            print(tmp)
                        elif curAction[0] == 'reduce':
                            print(curAction)
                            index = curAction[1]
                            # newBranches: list = branch.reduce(self.G[index])
                            # #print(newBranches)
                            # for newBranch in newBranches:
                            #     key = (newBranch.top, newBranch.pos)
                            #     if key not in tmp:
                            #         tmp[key] = [newBranch]
                            #     else:
                            #         tmp[key].append(newBranch)
                            newBranch: list = branch.reduce(self.G[index])
                            #print(newBranches)
                            key = (newBranch.top, newBranch.pos)
                            if key not in tmp:
                                tmp[key] = [newBranch]
                            else:
                                tmp[key].append(newBranch)
                            print(self.G[index])
                        elif curAction[0] == 'accept':
                            print('accept')
                            raise StopIteration()
                        else:
                            assert 0
                except RuntimeError as e:
                    print('この分支は失敗してしまいました。')
                except StopIteration as e:
                    print('成功しました。次は分析樹です')
                    res += str(branch.top.astNode)
                    ansCount += 1
            print('tmp:%d\n' % len(tmp), '\n'.join('%s=> %s' %(k,v) for k,v in tmp.items()),sep='')
            print()
            activeTopStates.clear()
            for key in tmp:
                assert len(key) == 2
                top, pos = key
                branches = tmp[key]
                assert len(branches) > 0
                if len(branches) >= 2:
                    for i in range(1, len(branches)):
                        branches[0].merge(branches[i])
                assert key not in activeTopStates
                activeTopStates[key] = branches[0]

        print('ansCount=', ansCount)
        return res


class GLRNode:
    def __init__(self, prev: list, state: int, astNode: Node, character: str):
        self.state: int = state
        # if astNode is None:
        #    assert 0
        # self.astNode: list = list(astNode) if isinstance(astNode, set) else [astNode]
        self.astNode: Node = astNode
        self.character: str = character
        assert astNode is None or self.character==self.astNode.character
        self.prev = tuple(prev)

    def __hash__(self):
        return hash(('GLRNode', self.state, self.astNode))
        # return hash(repr(self))

    def __eq__(self, other):
        assert isinstance(other, GLRNode)
        return self.state == other.state and self.astNode == other.astNode  # and self.prev == other.prev

    def __repr__(self):
        # return '[%s; state:%s "%s": %s]' % (
        #     self.prev, self.state, self.character, '[' + ','.join(str(x) for x in self.astNode) + ']')
        return '(%s, %s \'%s\')' % (
            ''.join(str(x) for x in self.prev), self.state, self.character)


class GLRBranch:
    tokens = []
    goto = None

    def __init__(self, top: GLRNode, iterationPos: int = 0):
        self._top: GLRNode = top
        self._p: int = iterationPos

    def backtraceLR(self, n: int = 0) -> list or GLRNode:
        if n == 0:
            return self._top
        assert n >= 1
        res = []
        p = self.backtraceLR()
        for i in range(n):
            assert p
            res.append(p)
            p = p.prev
        res.reverse()
        return res

    def backtraceGLR(self, cur: GLRNode, production: Production, rhs: list, pointer=-1):
        try:
            if cur.character != production.rhs[pointer]:
                return []
        except (IndexError, AttributeError):
            # 匹配完文法符号了
            newTop = GLRNode([cur],
                             GLRBranch.goto[cur.state][production.lhs][1],
                             Node(production.lhs, [rhs[::-1]]),
                             production.lhs)
            return GLRBranch(newTop, self._p)

        assert isinstance(cur.astNode, Node)
        # assert not (set(listOfAllPossibleRhses).intersection(cur.astNode))

        rhs.append(cur.astNode)
        res = None
        if len(cur.prev) == 1:
            res = self.backtraceGLR(cur.prev[0], production, rhs, pointer - 1)
        else:
            for pre in cur.prev:
                candidate = self.backtraceGLR(pre, production, rhs, pointer - 1)
                if candidate:
                    if res:
                        res.top.astNode.merge(candidate.top.astNode)
                    else:
                        res=candidate

        rhs.pop()
        return res

    def nextToken(self):
        if self._p >= len(GLRBranch.tokens):
            return CToken(token_t=eof, value='', position=(-1, -1))
        else:
            return GLRBranch.tokens[self._p]

    def shift(self, state: int, node):
        return GLRBranch(GLRNode([self._top], state, node, node.character), self._p + 1)

    def reduce(self, production: Production):
        res = self.backtraceGLR(self._top, production, [])
        return res

    def merge(self, other):
        assert isinstance(other, GLRBranch)
        assert other.top == self.top
        assert other.pos == self.pos
        self._top.prev += other.top.prev

    def __repr__(self):
        # return 'Branch(%s,%s)' % (self._top.state, self._top.astNode)
        return str(self._top)

    def __eq__(self, other):
        return self._top == other.top and self._p == other.pos

    def __hash__(self):
        return hash((self._top, self._p))

    @property
    def pos(self):
        return self._p

    @property
    def top(self):
        return self._top
