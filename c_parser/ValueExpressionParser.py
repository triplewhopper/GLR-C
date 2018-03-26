from collections import deque, OrderedDict
from ctoken import CToken
from c_parser.constants import epsilon, eof
from c_parser.canonicalLR_1_collection import CanonicalLR1Collection
import pickle
from c_parser.grammar import Grammar
from c_parser.production import Production
from contextFreeGrammarParser import Node
from typing import Dict, List, Tuple, Union, FrozenSet, Iterable, Set
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

            def th(x: Union[str, list, int] = '', **kwargs) -> None:
                print('<th %s>%s</th>' % (' '.join(map(lambda k: '%s="%s"' % (k, kwargs[k]), kwargs.keys())), x))

            def td(x: Union[str, list, int] = '', args='') -> None:
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
        initValue = GLRBranch(GLRNode([], 0, [Node('', (), ())]), 0)
        # initValue = GLRBranch(GLRNode([], 0, []), 0)
        activeTopStates: Dict[(int, int), GLRBranch] = {(initValue.state, initValue.pos): initValue}
        ansCount = 0
        res = ''
        # f = open('debug.html', 'w')
        while activeTopStates:
            print('activeMap:%d\n' % len(activeTopStates),
                  '\n'.join('%s=> %s' % (k, v) for k, v in activeTopStates.items()), sep='')
            tmp: Dict[(int, int), List[GLRBranch]] = {}
            for (top, pos), branch in activeTopStates.items():
                a: CToken = branch.nextToken()
                # print('stack:', head.stack)
                # print('node:', head.nodestack)
                print('s=%s,a=%s,pos=%s' % (top, a, pos))
                print('head:', top)

                try:
                    if a.token_t in self.action[top]:
                        curActions = self.action[top][a.token_t]
                    else:
                        # assert head.nodestack
                        raise RuntimeError(
                            'unexcpected \'%s\' after \'%s\' token, cur = %s, row %s, column %s\n expected tokens are listed as below:\n %s' %
                            (a, head.backtraceLR().astNode, head.pos, a.position[0], a.position[1],
                             self.action[top].keys()))
                    for curAction in curActions:
                        if curAction[0] == 'shift':
                            #print(curAction)
                            newBranch = branch.shift(curAction[1], a)
                            #print(newBranch)
                            key = (newBranch.state, newBranch.pos)
                            if key not in tmp:
                                tmp[key] = [newBranch]
                            else:
                                tmp[key].append(newBranch)
                            #print(tmp)
                        elif curAction[0] == 'reduce':
                            #print(curAction)
                            index = curAction[1]
                            newBranches: List[GLRBranch] = branch.reduce(self.G[index])
                            # print(newBranches)
                            for newBranch in newBranches:
                                key = (newBranch.state, newBranch.pos)
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
                    # assert len(branch.top) == 1
                    res += ''.join(str(x) for x in branch.top.astNodes)
                    ansCount += 1
            #print('tmp:%d\n' % len(tmp), '\n'.join('%s=> %s' % (k, v) for k, v in tmp.items()), sep='')
            print()
            activeTopStates.clear()
            for key in tmp:
                assert len(key) == 2
                branches: List[GLRBranch] = tmp[key]
                assert len(branches) > 0
                if len(branches) >= 2:
                    for i in range(1, len(branches)):
                        branches[0].merge(branches[i])
                assert key not in activeTopStates
                activeTopStates[key] = branches[0]

        print('ansCount=', ansCount)
        return res


class GLRNode:
    def __init__(self, prev, state: int, astNodes):
        """

        :param prev
        :param state:
        :param astNodes:
        :type prev:Iterable[GLRNode]
        :type state:int
        :type astNodes:Iterable[Node]
        """
        # assert len(set(y.character for x in astNodes.values() for y in x)) <= 1
        assert len(set(x.character for x in astNodes)) <= 1
        self.state: int = state
        # if astNode is None:
        #    assert 0
        # self.astNode: list = list(astNode) if isinstance(astNode, set) else [astNode]
        # self.asrNodes是按照node的prev跟self.prev中的哪一个方向一致来 分组的。
        self.astNodes: FrozenSet[Node] = frozenset(astNodes)
        self.character: str = ''
        for node in self.astNodes:
            self.character = node.character
            break
        # for v in astNodes.values():
        #     for node in v:
        #         self.character = node.character
        #         break
        #     break
        self.prev: FrozenSet[GLRNode] = frozenset(prev)

    def __hash__(self):
        return hash(('GLRNode', self.state, self.astNodes))
        # return hash(repr(self))

    def __eq__(self, other):
        assert isinstance(other, GLRNode)
        return self.state == other.state  # and self.astNodes == other.astNodes  # and self.prev == other.prev

    def __repr__(self):
        if self.astNodes and len(self.astNodes) > 1:
            return '(%s, %s \'%s\'%s)' % (
                ''.join(str(x) for x in self.prev), self.state, self.astNodes and self.character, len(self.astNodes))
        if self.astNodes and len(self.astNodes) == 1:
            return '(%s, %s \'%s\')' % (
                ''.join(str(x) for x in self.prev), self.state, self.astNodes and self.character)
        else:
            assert not self.prev
            return '(%s)' % (
                self.state)

    def merge(self, other):
        """

        :param other:
        :type other:GLRNode
        :return:GLRNode
        """
        assert isinstance(other, GLRNode)
        assert self.state == other.state
        assert self.character == other.character
        # dictionary: Dict[int, FrozenSet[Node]] = dict(self.astNodes)
        # for k, v in other.astNodes.items():
        #     if k not in dictionary:
        #         dictionary[k] = v
        #     else:
        #         dictionary[k] |= v

        intersection = self.prev & other.prev
        c: bool = len(intersection) == 0 or len(intersection) == 1 and GLRNode([], 0,
                                                                               [Node('', (), [])]) in intersection
        #assert c
        # assert len(frozenset(self.astNodes).intersection(other.astNodes)) == 0

        return GLRNode(self.prev | other.prev, self.state, self.astNodes | other.astNodes)
        # return GLRNode(self.prev | other.prev, self.state, dictionary)


class GLRBranch:
    tokens: List[CToken] = []
    goto = None

    def __init__(self, top: GLRNode, iterationPos: int = 0):
        self._top: GLRNode = top
        self._p: int = iterationPos
        self.character: str = self._top.character

    @property
    def state(self):
        #        assert len(set(x.state for x in self._top)) == 1
        return self._top.state

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

    def backtraceGLR(self, cur: GLRNode, production: Production, nodes: Dict[FrozenSet[Node], Node], pointer=-1):
        try:  # 単独にastNodeに深度優先捜索をやってみる

            if cur.character != production.rhs[pointer]:
                return {}
        except (IndexError, AttributeError):
            # 匹配完文法符号了
            newTop = GLRNode([cur],
                             GLRBranch.goto[cur.state][production.lhs][1],
                             [nodes[prev] for prev in nodes if prev.issubset(cur.astNodes)])
            return {newTop.state: GLRBranch(newTop, self._p)}
        res: Dict[int, GLRBranch] = {}
        if len(cur.prev) == 1:
            for prev in cur.prev:
                res = self.backtraceGLR(prev, production, nodes, pointer - 1)
        else:
            for pre in cur.prev:

                candidate = self.backtraceGLR(pre, production, nodes, pointer - 1)
                if candidate:
                    for k, v in candidate.items():
                        if k not in res:
                            res[k] = v
                        else:
                            res[k].merge(v)
        return res

    def dfs(self, cur: Node, production: Production, rhs: List[Node], pointer=-1):
        try:  # 単独にstNodeに深度優先捜索をやってみる

            if cur.character != production.rhs[pointer]:
                return []
        except (IndexError, AttributeError):
            # 匹配完文法符号了

            return [Node(
                production.lhs,
                [rhs[::-1]],
                [cur])]
        rhs.append(cur)
        res: List[Node] = []
        if len(cur.prev) == 1:
            for prev in cur.prev:
                res = self.dfs(prev, production, rhs, pointer - 1)
                break
        else:
            for pre in cur.prev:
                candidate = self.dfs(pre, production, rhs, pointer - 1)
                if candidate:
                    res.extend(candidate)
        rhs.pop()
        return res

    def nextToken(self) -> CToken:
        if self._p >= len(GLRBranch.tokens):
            return CToken(token_t=eof, value='', position=(-1, -1))
        else:
            return GLRBranch.tokens[self._p]

    def shift(self, state: int, ctoken: CToken):
        node = Node(ctoken.token_t, (), self.top.astNodes, ctoken.value)
        astNodes = [node]
        glrnode = GLRNode([self._top], state, astNodes)
        return GLRBranch(glrnode, self._p + 1)

    def reduce(self, production: Production):

        def groupByPrev(nodes: List[Node]) -> Dict[FrozenSet[Node], Node]:
            res: Dict[FrozenSet[Node], List[Node]] = {}
            for node in nodes:
                if node.prev not in res:
                    res[node.prev] = [node]
                else:
                    res[node.prev].append(node)

            def merge(nodes: List[Node]):
                assert nodes
                assert isinstance(nodes[0], Node)
                res = None
                for node in nodes:
                    res = node.merge(res)
                return res

            for key in res:
                res[key] = merge(res[key])
            return res

        try:
            newNodes: List[Node] = list(x for node in self.top.astNodes for x in self.dfs(node, production, []))
        except TypeError as e:
            print(e)
            assert 0
        assert newNodes
        newBranches = self.backtraceGLR(self._top, production, groupByPrev(newNodes))
        return list(newBranches.values())

    def merge(self, other):
        assert isinstance(other, GLRBranch)
        # assert other.top == self.top
        assert other.pos == self.pos
        self._top: GLRNode = self._top.merge(other.top)

    def __repr__(self):
        # return 'Branch (%s,%s)' % (self._top.state, self._top.astNode)
        return 'し' + str(self._top)

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
