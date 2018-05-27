import pickle
from collections import defaultdict
from typing import Dict, List, Union, Tuple, cast, Iterable, FrozenSet
from importlib import import_module

from Lexer import tokenizer
from Lexer.ctoken import CToken, SourceLocation

from Parser.canonicalLR_1_collection import CanonicalLR1Collection
from Parser.constants import epsilon, eof
from Parser.itemset import ItemSet
from Parser.grammar import Grammar
from Parser.nodes import Intermediate, ConstantAndIdentifierNodeFactory, NullParseTreeNode, \
    ParseTreeNode, TerminalParseTreeNode
from Parser.production import Production
from Parser import nodes
from Utils.sbt import SizeBalancedTree


class Parser:
    def __init__(self, G: Grammar):
        self.G = G
        with open('sha1.txt') as old:
            oldhash = old.read()
            newhash = G.sha1
        if oldhash != newhash:
            print("New!")
            self.collection = CanonicalLR1Collection(G, ItemSet)
            print('collection got.')
            self.action = None
            self.goto = None
            self.preprocess()

            with open('data.pickle', 'wb') as f:
                pickle.dump(self.action, f)
                pickle.dump(self.goto, f)
                pickle.dump(self.collection, f)
            with open('sha1.txt', 'w') as old:
                old.write(newhash)
            print("data has been written to file.")
        else:
            print("ロード中...")
            with open('data.pickle', 'rb') as f:
                self.action = pickle.load(f)
                self.goto = pickle.load(f)
                self.collection = pickle.load(f)

            print("ロード 完了しました。")

    def preprocess(self):
        print('ExpressionItemSet.count=', ItemSet.count)
        factory = lambda: {i: {} for i in range(len(self.collection))}
        action = factory()
        goto = factory()
        for i in range(ItemSet.count):
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
                        #  assert eof not in action[i]
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
                # print('<th %s>%s</th>' % (' '.join(map(lambda k: '%s="%s"' % (k, kwargs[k]), kwargs.keys())), x))
                print(f"""<th {' '.join(f'{0}="{1}"'.format(k,kwargs[k]) for k in kwargs)}> {x}</th>""")

            def td(x: Union[str, list, int] = '', args='') -> None:
                print(f'<td {args}>{x}</td>')

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

    def parse(self, tokens: List[CToken]):

        GLRBranch.tokens = list(tokens)
        print(GLRBranch.tokens)
        GLRBranch.goto = self.goto
        initValue = GLRBranch(
            top=GLRStackNode(
                prevSet=frozenset(),
                state=0,
                nodeSet=frozenset([NullParseTreeNode()])
            ),
            iterationPos=0
        )
        activeTopStates: SizeBalancedTree[Tuple[int, int], GLRBranch] = \
            SizeBalancedTree(cmp=lambda x, y: x[0] - y[0] if x[0] - y[0] != 0 else (y[1] - x[1]),
                             data={(initValue.pos, initValue.state): initValue})
        ansCount = 0
        res: List[Intermediate] = []
        # f = open('debug.html', 'w')
        while activeTopStates:
            # print()
            # print(list(activeTopStates.items()))

            (pos, top), branch = activeTopStates.popitem()
            a: CToken = branch.nextToken()

            tmp: Dict[Tuple[int, int], List[GLRBranch]] = {}
            try:
                if a.token_t in self.action[top]:
                    curActions = self.action[top][a.token_t]
                else:
                    raise SyntaxError(
                        "unexcpected '{}' after '{}' token, "
                        "cur = {}, at {}\n "
                        "expected tokens are listed as below:\n {}"
                            .format(a.rawData,
                                    branch.top.character,
                                    branch.pos,
                                    a.position.start,
                                    self.action[top].keys()))

                for curAction in curActions:
                    if curAction[0] == 'shift':
                        # print(curAction)
                        newBranch = branch.shift(curAction[1], a)
                        # print(newBranch)
                        key = (newBranch.pos, newBranch.state)
                        if key not in tmp:
                            tmp[key] = [newBranch]
                        else:
                            tmp[key].append(newBranch)
                        # print(tmp)
                    elif curAction[0] == 'reduce':
                        # print(curAction)
                        index = curAction[1]
                        newBranches: List[GLRBranch] = branch.reduce(self.G[index])
                        # print(newBranches)
                        if not newBranches:
                            raise SyntaxError('无可规约')
                        for newBranch in newBranches:
                            key = (newBranch.pos, newBranch.state)
                            if key not in tmp:
                                tmp[key] = [newBranch]
                            else:
                                tmp[key].append(newBranch)
                        # print(self.G[index])
                    elif curAction[0] == 'accept':
                        print('accept')
                        raise StopIteration()
                    else:
                        assert 0
            except SyntaxError as e:
                print(e)
                print('この分支は失敗してしまいました。')
            except StopIteration as e:
                print('成功しました。次は分析樹です')
                # assert len(branch.top) == 1
                tot: Intermediate = None
                for node in branch.top.nodeSet:
                    tot = cast(Intermediate, node).merge(tot)
                res.append(tot)
                ansCount += 1

            for key in tmp:
                assert len(key) == 2
                branches: List[GLRBranch] = tmp[key]
                assert len(branches) > 0
                if len(branches) >= 2:
                    for i in range(1, len(branches)):
                        branches[0].merge(branches[i])
                if key not in activeTopStates:
                    activeTopStates[key] = branches[0]
                else:
                    # print('merge!')
                    activeTopStates[key].merge(branches[0])
            # print('tmp:%d\n' % len(tmp), '\n'.join('%s=> %s' % (k, v) for k, v in tmp.items()), sep='')
            # print()
            # activeTopStates.clear()

        print('ansCount=', ansCount)
        tot: Intermediate = None
        for node in res:
            tot = node.merge(tot)
        return tot


def groupByPrev(nodes: Union[Iterable[Intermediate], Iterable[TerminalParseTreeNode]]) \
        -> Dict['FrozenSet[ParseTreeNode]', Intermediate]:
    """
    :type nodes:    frozenset[Intermediate]|list[Intermediate]
    :rtype:         dict[frozenset[ParseTreeNode], Intermediate]
    """
    groups = defaultdict(list)
    """:type:defaultdict[frozenset[ParseTreeNode], list[Intermediate]]"""

    # print([isinstance(node, Intermediate) for node in nodes])
    if all(isinstance(node, Intermediate) for node in nodes):

        for node in nodes:
            groups[node.prevSet].append(node)

        def merge(nodes: List[Intermediate]) -> Intermediate:
            assert nodes
            res = None
            assert all(isinstance(node, Intermediate) for node in nodes)
            for node in nodes:
                res = node.merge(res)
            return res

        return {key: merge(groups[key]) for key in groups}
    else:
        assert all(isinstance(node, TerminalParseTreeNode) for node in nodes)
        return {node.prevSet: node for node in nodes}


class GLRStackNode:
    """
    :type prevSet:frozenset[GLRStackNode]
    :type state:int
    :type nodeSet:frozenset[ParseTreeNode]
    :type character:str
    """
    __slots__ = ('prevSet', 'state', 'nodeSet', 'character')

    def __init__(self, prevSet: FrozenSet['GLRStackNode'], state: int, nodeSet: FrozenSet['ParseTreeNode']):
        assert len(set(x.character for x in nodeSet)) <= 1
        assert isinstance(prevSet, frozenset)
        assert all(isinstance(x, GLRStackNode) for x in prevSet)
        assert isinstance(state, int)
        assert isinstance(nodeSet, frozenset)
        assert all(isinstance(x, ParseTreeNode) for x in nodeSet)

        self.state = state
        self.nodeSet = frozenset(nodeSet)
        self.character = ''
        for node in self.nodeSet:
            self.character = node.character
            break
        self.prevSet = frozenset(prevSet)

    def __hash__(self):
        return hash((self.__class__, self.state, self.nodeSet))
        # return hash(repr(self))

    def __eq__(self, other):
        assert isinstance(other, GLRStackNode)
        return self.state == other.state
        # and self.parseTreeNodes == other.parseTreeNodes  # and self.prev == other.prev

    def __repr__(self):
        if self.nodeSet and len(self.nodeSet) > 1:
            return "({0}, {1} '{2}'{3})" \
                .format(''.join(str(x) for x in self.prevSet),
                        self.state,
                        self.nodeSet and self.character,
                        len(self.nodeSet))
        if self.nodeSet and len(self.nodeSet) == 1:
            return "({0}, {1} '{2}')" \
                .format(''.join(str(x) for x in self.prevSet),
                        self.state,
                        self.nodeSet and self.character)
        else:
            assert not self.prevSet
            return '({0})'.format(self.state)

    def merge(self, other: 'GLRStackNode'):

        assert isinstance(other, GLRStackNode)
        assert self.state == other.state
        assert self.character == other.character

        return GLRStackNode(prevSet=self.prevSet | other.prevSet,
                            state=self.state,
                            nodeSet=frozenset(
                                groupByPrev(self.nodeSet | other.nodeSet).values())
                            )


class GLRBranch:
    """
    :type _top:GLRStackNode
    :type _p:int
    :type character: str
    """
    tokens: List[CToken] = []
    goto = None
    __slots__ = ('_top', '_p', 'character')

    def __init__(self, top: GLRStackNode, iterationPos: int = 0):
        self._top = top
        self._p = iterationPos
        self.character = self._top.character

    @property
    def state(self):
        #        assert len(set(x.state for x in self._top)) == 1
        return self._top.state

    def backtraceGLR(self, cur: GLRStackNode,
                     production: Production,
                     nodes: Dict['frozenset[Intermediate]', Intermediate],
                     pointer: int = -1) \
            -> Dict[int, 'GLRBranch']:
        try:

            if cur.character != production.rhs[pointer]:
                return {}
        except (IndexError, AttributeError):
            # 匹配完文法符号了
            newTop = GLRStackNode(prevSet=frozenset([cur]),
                                  state=GLRBranch.goto[cur.state][production.lhs][1],
                                  nodeSet=frozenset([nodes[prev]
                                                     for prev in nodes
                                                     if prev.issubset(cur.nodeSet)
                                                     ]
                                                    )
                                  )
            return {newTop.state: GLRBranch(newTop, self._p)}
        res: Dict[int, GLRBranch] = {}
        if len(cur.prevSet) == 1:
            for prev in cur.prevSet:
                res = self.backtraceGLR(prev, production, nodes, pointer - 1)
        else:
            for pre in cur.prevSet:

                candidate = self.backtraceGLR(pre, production, nodes, pointer - 1)
                if candidate:
                    for k, v in candidate.items():
                        if k not in res:
                            res[k] = v
                        else:
                            res[k].merge(v)
        return res

    def dfs(self, cur: ParseTreeNode, production: Production, rhs: List[ParseTreeNode],
            pointer=-1) -> 'List[nodes.Intermediate]':
        try:  # 単独にparseTreeNodeに深度優先捜索をやってみる

            if cur.character != production.rhs[pointer]:
                return []
        except (IndexError, AttributeError):
            # 匹配完文法符号了

            module = import_module('Parser.nodes')
            Node = getattr(module, production.lhs)
            # module=__import__('playground')
            # Node=module.table[production.key]
            try:
                return [Node(
                    [cur],  # prev
                    production.relativeOrder,
                    *rhs[::-1]
                )]
            except TypeError as e:
                raise TypeError(Node, e)
        rhs.append(cur)
        res: List[Intermediate] = []

        for pre in cur.prevSet:
            try:
                candidate = self.dfs(pre, production, rhs, pointer - 1)
                if candidate:
                    res.extend(candidate)
            except nodes.不合文法:
                pass
        rhs.pop()
        return res

    def nextToken(self) -> CToken:
        if self._p >= len(GLRBranch.tokens):
            return CToken(SourceLocation.presentForEOF(), eof, '', rawData='')
        else:
            return GLRBranch.tokens[self._p]

    def shift(self, state: int, ctoken: CToken) -> 'GLRBranch':
        if ctoken.token_t in {tokenizer.constantTag, tokenizer.identifierTag}:
            node = ConstantAndIdentifierNodeFactory(ctoken, prev=self.top.nodeSet)
        else:
            node = TerminalParseTreeNode(prev=self.top.nodeSet, tok=ctoken)
        glrnode = GLRStackNode(
            prevSet=frozenset([self._top]),
            nodeSet=frozenset([node]),
            state=state
        )
        return GLRBranch(glrnode, self._p + 1)

    def reduce(self, production: Production) -> 'List[GLRBranch]':

        newNodes: List[Intermediate] = []
        for node in self.top.nodeSet:
            try:
                tmp = self.dfs(node, production, [])
                newNodes.extend(tmp)
            except nodes.不合文法:
                pass
        if not newNodes:
            return []
        newBranches = self.backtraceGLR(self._top, production, groupByPrev(newNodes))
        return list(newBranches.values())

    def merge(self, other) -> None:
        assert isinstance(other, GLRBranch)
        # assert other.top == self.top
        assert other.pos == self.pos
        self._top: GLRStackNode = self._top.merge(other.top)

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
