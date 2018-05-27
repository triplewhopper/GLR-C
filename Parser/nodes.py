from typing import Iterable, Dict, Optional, Union, FrozenSet, Tuple, List, cast
from functools import reduce
from AST import c_type, nodes as ast, scopes
from Lexer import ctoken


# displayAll = False


def join(x: Optional[Iterable], delimiter=''):
    return delimiter.join(map(str, x or []))


class 不合文法(RuntimeError):
    pass


#
#
# def li(x):
#     if isinstance(x, List):
#         return f"<li>{span('list')}{ul(*x)}</li>"
#     return f"<li>{str(x)}</li>"
#
#
# def span(x):
#     return f"<span>{x}</span>"
#
#
# def f()


# 理论上符号表应该可持久化
# 这样才能保证各分支分析时互不干扰
class ParseTreeNode:
    """
    :type prevSet: frozenset[ParseTreeNode]
    """

    def __init__(self, prev: Iterable):
        # assert isinstance(character, str)
        assert isinstance(prev, Iterable)
        # self.character = character
        self.prevSet = frozenset(prev)

    def __eq__(self, other):
        raise NotImplementedError()

    def __hash__(self):
        raise NotImplementedError()

    @property
    def character(self):
        raise NotImplementedError()


class NullParseTreeNode(ParseTreeNode):
    def __init__(self):
        super(NullParseTreeNode, self).__init__(frozenset())

    def __hash__(self):
        return hash((self.__class__, self.character, self.prevSet))

    def __eq__(self, other):
        return isinstance(other, NullParseTreeNode)

    @property
    def character(self):
        return ''


class ParseTreeNodeMeta(type):
    def __instancecheck__(self, instance):
        if hasattr(instance, 'character'):
            return self.__name__ == instance.character or super().__instancecheck__(instance)
        return False


class Intermediate(ParseTreeNode, metaclass=ParseTreeNodeMeta):
    """
    :type relativeOrder :int
    """

    def __init__(self, prev, relativeOrder):
        super().__init__(prev)
        self.relativeOrder = relativeOrder

    def merge(self, other):
        """

        :type other:Intermediate
        :rtype:     IntermediateParseTreeNode
        """
        if other is None or other is self:
            return self
        # assert isinstance(other, self.__class__)
        if isinstance(other, MultiSol):
            return cast(MultiSol, other).merge(self)
        assert other.character == self.character
        assert other.prevSet == self.prevSet
        assert len(self.prevSet) == 1
        return MultiSol(self.prevSet | other.prevSet, frozenset((self, other)))

    def __hash__(self):
        return hash((self.__class__, self.relativeOrder, self.prevSet))

    def __eq__(self, other):
        assert isinstance(other, Intermediate)
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return str(self.character)

    @property
    def character(self):
        assert self.__class__.__name__ != 'Intermediate'
        return self.__class__.__name__


class MultiSol(Intermediate):
    """
    :type solutions:        frozenset[Intermediate]
    :type _character:       str
    """

    def __init__(self, prev, solutions):
        super().__init__(prev, -1)
        self.solutions = solutions
        assert len(self.solutions) > 1
        for sol in self.solutions:
            self._character = sol.character
            break

    @property
    def character(self):
        return self._character

    def __str__(self):
        sols = join("<{0}>{1}</{0}>".format(f'解{i+1}', j) for i, j in enumerate(self.solutions))

        return '<{0} total="{tot}">{sols}</{0}>' \
            .format(self.character, sols=sols, tot=len(self.solutions))

    def __getattr__(self, item):
        try:
            return tuple(getattr(sol, item) for sol in self.solutions)
        except KeyError as e:
            raise KeyError(self.character, e)

    def visit(self, *args, **kwargs):
        res = []
        for sol in self.solutions:
            try:
                res.append(sol.visit(*args, **kwargs))
            except (RuntimeError, KeyError) as e:
                print(e)
        if not res:
            raise RuntimeError('无解啊！')
        if len(res) > 1:
            raise RuntimeError('这么多解如何是好')
        return res[0]

    def __hash__(self):
        return hash((self.__class__, self.prevSet, self.solutions))

    def __eq__(self, other):
        if not hasattr(other, 'solutions'):
            return False
        return self.character == other.character \
               and self.prevSet == other.prevSet \
               and self.solutions == other.solutions

    def merge(self, other):
        """

        :param other:
        :type other:Intermediate
        :return: MultiSol
        """
        if other is None or other is self:
            return self
        assert other.character == self.character
        assert other.prevSet == self.prevSet
        assert len(self.prevSet) == 1
        if isinstance(other, MultiSol):
            solutions = self.solutions | cast(MultiSol, other).solutions
        else:
            solutions = self.solutions | {other}

        return MultiSol(self.prevSet, solutions)


class Declaration(Intermediate):
    """
    :type declarationSpecifiers:    DeclarationSpecifiers
    :type initDeclaratorList:       list[InitDeclarator]
    """

    def __init__(self, prev, relativeOrder, declarationSpecifiers, initDeclaratorList=None, semicolon: str = ';'):
        super().__init__(prev, relativeOrder)
        assert isinstance(declarationSpecifiers, DeclarationSpecifiers)
        assert 1 <= relativeOrder <= 2
        self.declarationSpecifiers = declarationSpecifiers
        if relativeOrder == 1:
            assert isinstance(initDeclaratorList, InitDeclaratorList)

            self.initDeclaratorList = initDeclaratorList.initDeclaratorList
        else:
            self.initDeclaratorList = []

    def __str__(self):
        return "<{0}>{1}{2}</{0}>" \
            .format(self.character, self.declarationSpecifiers, join(self.initDeclaratorList))

    def visit(self, env: 'scopes.DeclScope'):
        category, type0 = self.declarationSpecifiers.visit(env, bool(len(self.initDeclaratorList)))
        res = []
        for declarator in self.initDeclaratorList:
            tmp = declarator.visit(category, type0, env)
            if tmp is not None:
                assert isinstance(tmp, ast.ExprStmt)
                res.append(tmp)
        return res


class DeclarationSpecifiers(Intermediate):
    """
    :type storageClassSpecifierList:    list[StorageClassSpecifier]
    :type typeSpecifierList:            list[TypeSpecifier]
    :type typeQualifierList:            list[TypeQualifier]
    :type functionSpecifierList:        list[FunctionSpecifier]
    """

    def __init__(self, prev, relativeOrder, specifierOrQualifier, declarationSpecifiers=None):
        super().__init__(prev, relativeOrder)
        assert declarationSpecifiers is None or isinstance(declarationSpecifiers, DeclarationSpecifiers)
        key: str = {1: 'storageClassSpecifierList',
                    2: 'storageClassSpecifierList',
                    3: 'typeSpecifierList',
                    4: 'typeSpecifierList',
                    5: 'typeQualifierList',
                    6: 'typeQualifierList',
                    7: 'functionSpecifierList'}[relativeOrder]
        self.storageClassSpecifierList = []
        self.typeSpecifierList = []
        self.typeQualifierList = []
        self.functionSpecifierList = []
        self.__dict__[key].append(specifierOrQualifier)

        if declarationSpecifiers is not None:
            self.storageClassSpecifierList.extend(declarationSpecifiers.storageClassSpecifierList)
            self.typeSpecifierList.extend(declarationSpecifiers.typeSpecifierList)
            self.typeQualifierList.extend(declarationSpecifiers.typeQualifierList)
            self.functionSpecifierList.extend(declarationSpecifiers.functionSpecifierList)

        classes = [x.typeSpecifier.__class__ for x in self.typeSpecifierList]
        if sum(int(x in classes) for x in [StructOrUnionSpecifier, TypedefName, 'EnumSpecifier']) > 1:
            raise 不合文法()

        if StructOrUnionSpecifier in classes or TypedefName in classes:
            if len(self.typeSpecifierList) != 1: raise 不合文法()

    def visit(self, env: 'scopes.DeclScope', hasInitDeclaratorList: bool) -> Tuple[str, c_type.QualifiedType]:
        storageClassSpecifiers = list(frozenset(x.visit() for x in self.storageClassSpecifierList))
        assert len(storageClassSpecifiers) <= 1
        if not storageClassSpecifiers:
            category = 'var'
        else:
            category = storageClassSpecifiers[0]

        tq = TypeQualifier.getTQ(self.typeQualifierList)
        classes = [x.typeSpecifier.__class__ for x in self.typeSpecifierList]
        assert sum(int(x in classes) for x in [StructOrUnionSpecifier, TypedefName, 'EnumSpecifier']) <= 1

        if StructOrUnionSpecifier in classes:
            assert len(self.typeSpecifierList) == 1
            type0 = cast(StructOrUnionSpecifier, self.typeSpecifierList[0]).visit(env)
            if hasInitDeclaratorList and not type0.decl.isDefinition:
                raise RuntimeError("无法定义不完全类型的变量")
            type0 = c_type.QualifiedType(type0, tq)
            return category, type0

        elif TypedefName in classes:
            assert len(self.typeSpecifierList) == 1
            type0 = cast(TypedefName, self.typeSpecifierList[0]).visit(env)
            type0 = type0.getWithAdditionalQualifiers(tq)
            assert not type0.isNull()
            return category, type0

        else:
            type0 = c_type.normalize([x.visit(env) for x in self.typeSpecifierList])
            type0 = c_type.QualifiedType(type0, tq)
            return category, type0

    def __str__(self):
        a = []

        def f(x: str, y: list, delimiter=' '):
            return f"<{x}>{join(y,delimiter)}</{x}>"

        if self.storageClassSpecifierList:
            a.append(f('storageClassSpecifiers', self.storageClassSpecifierList))
        if self.typeQualifierList:
            a.append(f('typeQualifiers', self.typeQualifierList))
        if self.typeSpecifierList:
            a.append(f('typeSpecifiers', self.typeSpecifierList))
        if self.functionSpecifierList:
            a.append(f('functionSpecifier', self.functionSpecifierList))
        return "<{0}>{1}</{0}>".format(self.character, join(a))
        # return span(self.__class__.__name__) + \
        #        ul(*[x if x else 'None' for x in (
        #            self.storageClassSpecifierList,
        #            self.typeQualifierList,
        #            self.typeSpecifierList,
        #            self.functionSpecifierList)])

    __repr__ = __str__


class InitDeclaratorList(Intermediate):
    """
    :type initDeclaratorList: list[InitDeclarator]
    """

    def __init__(self, prev, relativeOrder, initDeclarator, placeHolder=',', initDeclaratorList=None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        assert isinstance(initDeclarator, InitDeclarator)
        assert placeHolder == ','
        assert initDeclaratorList is None or isinstance(initDeclaratorList, InitDeclaratorList)
        if relativeOrder == 1:
            assert initDeclaratorList is None
            self.initDeclaratorList = [initDeclarator]
        else:
            assert initDeclaratorList is not None
            self.initDeclaratorList = [initDeclarator] + initDeclaratorList.initDeclaratorList

    def __str__(self):
        return "<{0}>{1}</{0}>" \
            .format(self.character, join(self.initDeclaratorList))
        # return span(self.__class__.__name__) + \
        #        ul(*self.initDeclaratorList)

    __repr__ = __str__


class InitDeclarator(Intermediate):
    """
    :type declarator:   Declarator
    :type initializer:  None|Initializer
    """

    def __init__(self, prev, relativeOrder, declarator, placeHolder: str = '=', initializer=None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        assert placeHolder == '='
        self.declarator = declarator
        self.initializer = initializer

    def visit(self, category: str, type0: c_type.QualifiedType, env: 'scopes.DeclScope'):
        tok, type1 = self.declarator.visit(type0, env)
        assert isinstance(tok.data, str)
        assert isinstance(type1, c_type.QualifiedType)
        if isinstance(type1(), c_type.FunctionProtoType):
            if isinstance(type0(), c_type.FunctionProtoType):
                raise RuntimeError('{}:函数{}不能返回一个函数类型{}'
                                   .format(tok.position, tok.data, type0()))
            elif isinstance(type0(), c_type.ArrayType):
                raise RuntimeError('{}:函数{}不能返回一个数组类型{}'
                                   .format(tok.position, tok.data, type0()))
            if self.initializer:
                raise RuntimeError('{}:函数原型后面接初始化你这是想干什么？'.format(tok.position))

            if category == 'var':
                decl = ast.FunctionDecl(tok.data, type1())
                env.insertFunctionDecl(decl)

            else:
                assert category == 'typedef'
                decl = ast.TypedefDecl(tok.data, type1)
                env.insertTypedefDecl(decl)

        else:
            # print('type1={}'.format(type1()))

            if category == 'var':
                decl = ast.ValueDecl(tok.data, type1, isinstance(env, scopes.GlobalScope))
                res = None
                if self.initializer:
                    res = self.initializer.visit(decl, env)

                if decl.declType().isIncompleteType():
                    raise RuntimeError('类型{}不完全，无法用它定义变量{}, 位置:{}'
                                       .format(decl.declType(), tok.data, tok.position))

                env.insertValueDecl(decl)
                return res
            else:
                assert category == 'typedef'
                decl = ast.TypedefDecl(tok.data, type1)
                env.insertTypedefDecl(decl)
                assert self.initializer is None and "typedef不能初始化！"

    #
    def __str__(self):
        return "<{0}>{1}{2}</{0}>" \
            .format(self.character, self.declarator or '', self.initializer or '')
        # else
        #     return span(self.__class__.__name__) + ul(self.declarator)
        # return span(self.__class__.__name__) + ul(self.declarator, self.initializer)


#
class StorageClassSpecifier(Intermediate):
    """
    :type storageClassSpecifier: str
    """

    def __init__(self, prev, relativeOrder, s):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 5
        assert isinstance(s, TerminalParseTreeNode)
        self.storageClassSpecifier = s.value

    def __str__(self):
        return self.storageClassSpecifier

    def visit(self):
        return self.storageClassSpecifier

    # # def run(self, env, *args, **kwargs):
    #     assert isinstance(self.rhs[0], str)
    #     return self.rhs[0]


#
#
# class StorageClassSpecifier(Intermediate):
#     key = 16
#     relativeOrder = 2
#     rhs = ('extern',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
# class StorageClassSpecifier(Intermediate):
#     key = 17
#     relativeOrder = 3
#     rhs = ('static',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
# class StorageClassSpecifier(Intermediate):
#     key = 18
#     relativeOrder = 4
#     rhs = ('auto',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
# class StorageClassSpecifier(Intermediate):
#     key = 19
#     relativeOrder = 5
#     rhs = ('register',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
class TypeSpecifier(Intermediate):
    """
    :type typeSpecifier: str| StructOrUnionSpecifier| TypedefName
    """

    def __init__(self, prev, relativeOrder, s):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 14
        if isinstance(s, TerminalParseTreeNode):
            self.typeSpecifier = s.value
        elif isinstance(s, (StructOrUnionSpecifier, TypedefName)):
            self.typeSpecifier = s
        else:
            assert 0

    def __str__(self):
        return str(self.typeSpecifier)

    def visit(self, env):
        if isinstance(self.typeSpecifier, str):
            return self.typeSpecifier
        else:
            return self.typeSpecifier.visit(env)


#
# class TypeSpecifier(Intermediate):
#     key = 31
#     relativeOrder = 12
#     rhs = ('StructOrUnionSpecifier',)
#
#
# class TypeSpecifier(Intermediate):
#     key = 32
#     relativeOrder = 13
#     rhs = ('EnumSpecifier',)
#
#


#
class TypeQualifier(Intermediate):
    """
    :type typeQualifier: str
    """

    def __init__(self, prev, relativeOrder, typeQualifier):
        super().__init__(prev, relativeOrder)
        assert isinstance(typeQualifier, TerminalParseTreeNode)
        assert not hasattr(typeQualifier, 'type')
        self.typeQualifier = typeQualifier.value

    def visit(self):
        TQ = c_type.QualifiedType.TQ
        return {'const': TQ.Const, 'volatile': TQ.Volatile, 'restrict': TQ.Restrict}[self.typeQualifier]

    def __str__(self):
        return str(self.typeQualifier)

    @staticmethod
    def getTQ(qualifierList):
        assert isinstance(qualifierList, list)
        assert all(isinstance(x, TypeQualifier) for x in qualifierList)
        return c_type.QualifiedType.TQ(reduce(int.__or__, (x.visit() for x in qualifierList), 0))

    # def visit(self) -> str:
    #     return self.typeQualifier

    __repr__ = __str__
    # def run(self, env, *args, **kwargs):
    #     assert isinstance(self.rhs[0], str)
    #     return self.rhs[0]


class StructOrUnionSpecifier(Intermediate):
    """
    :type structOrUnion:            str
    :type tag:                      str
    :type structDeclarationList:    None|list[StructDeclaration]
    """

    def __init__(self, prev, relativeOrder: int, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 3
        self.structOrUnion = args[0].structOrUnion
        self.tag = ''
        self.structDeclarationList = None
        if relativeOrder == 1:
            assert isinstance(args[1], IdentifierParseNode)
            assert isinstance(args[3], StructDeclarationList)
            self.tag = cast(IdentifierParseNode, args[1]).value
            self.structDeclarationList = cast(StructDeclarationList, args[3]).structDeclarationList
        elif relativeOrder == 2:
            assert isinstance(args[2], StructDeclarationList)
            self.structDeclarationList = cast(StructDeclarationList, args[2]).structDeclarationList
        else:
            self.tag = cast(IdentifierParseNode, args[1]).value
        assert self.structOrUnion in ('union', 'struct')

    def visit(self, env: 'scopes.DeclScope') -> c_type.StructType:
        if self.structOrUnion == 'struct':
            if self.structDeclarationList is None:
                try:
                    return env.getRecordDecl(self.tag).declType

                except KeyError:
                    decl = ast.RecordDecl(self.tag)
                    env.insertRecordDecl(decl)
                    return decl.declType

            else:
                classScope = scopes.StructScope(env)
                decl = ast.RecordDecl(self.tag, classScope, isDefinition=True)

                env.insertRecordDecl(decl)

                for x in self.structDeclarationList:
                    x.visit(classScope)

                decl.isBeingDefined = False

                return decl.declType
        else:
            raise NotImplementedError()

    def __str__(self):
        if not self.structDeclarationList:
            return '<{0} keyword="{1}" tag="{2}" />' \
                .format(self.character,
                        self.structOrUnion,
                        self.tag)
        return '<{0} keyword="{1}" tag="{2}">{3}</{0}>' \
            .format(self.character,
                    self.structOrUnion,
                    self.tag,
                    join(self.structDeclarationList))


class StructOrUnion(Intermediate):
    """
    :type structOrUnion: str
    """

    def __init__(self, prev, relativeOrder, s):
        super().__init__(prev, relativeOrder)
        assert isinstance(s, TerminalParseTreeNode)
        self.structOrUnion = s.value


class StructDeclarationList(Intermediate):
    """
    :type structDeclarationList: list[StructDeclaration]
    """

    def __init__(self, prev, relativeOrder, structDeclaration, structDeclarationList=None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        assert isinstance(structDeclaration, StructDeclaration)
        assert structDeclarationList is None or isinstance(structDeclarationList, StructDeclarationList)
        self.structDeclarationList: List[StructDeclaration] = [structDeclaration]
        if structDeclarationList:
            self.structDeclarationList.extend(structDeclarationList.structDeclarationList)

    def __str__(self):
        return "<{0}>{1}</{0}>" \
            .format(self.character, join(self.structDeclarationList))
        # return span(self.__class__.__name__) + ul(*self.structDeclarationList)


class StructDeclaration(Intermediate):
    """
    :type specifierQualifierList:   SpecifierQualifierList
    :type structDeclaratorList:     list[StructDeclarator]
    """

    def __init__(self, prev, relativeOrder, specifierQualifierList, structDeclaratorList, placeHolder):
        super().__init__(prev, relativeOrder)
        assert placeHolder == ';'
        assert relativeOrder == 1
        assert isinstance(specifierQualifierList, SpecifierQualifierList)
        assert isinstance(structDeclaratorList, StructDeclaratorList)
        self.specifierQualifierList = specifierQualifierList
        self.structDeclaratorList = structDeclaratorList.structDeclaratorList

    def visit(self, env: 'scopes.TypedefDeclExcludedScope') -> None:
        type0 = self.specifierQualifierList.visit(env)
        for declarator in self.structDeclaratorList:
            tok, type1 = declarator.visit(type0, env)
            if isinstance(type1(), c_type.FunctionProtoType):
                raise RuntimeError("{}: struct或union不能拥有函数原型成员'{}'!".format(tok.position, tok.data))
            decl = ast.ValueDecl(tok.data, type1)
            env.insertValueDecl(decl)

    def __str__(self):
        t = []

        def f(x, y):
            return f"<{x}>{join(y,' ')}</{x}>"

        t.append(f('structDeclarations', self.structDeclaratorList))
        return "<{0}>{1}{2}</{0}>".format(self.character, self.specifierQualifierList, join(t))


class SpecifierQualifierList(Intermediate):
    """
    :type specifierList: list[TypeSpecifier]
    :type qualifierList: list[TypeQualifier]
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 4
        a = args[0]
        b = None
        assert isinstance(a, (TypeSpecifier, TypeQualifier))

        if len(args) > 1:
            b = args[1]
            assert isinstance(b, SpecifierQualifierList)

        if relativeOrder == 1:
            self.specifierList = [a] + b.specifierList
            self.qualifierList = b.qualifierList
        elif relativeOrder == 2:
            self.specifierList = [a]
            self.qualifierList = []
        elif relativeOrder == 3:
            self.specifierList = b.specifierList
            self.qualifierList = [a] + b.qualifierList
        elif relativeOrder == 4:
            self.specifierList = []
            self.qualifierList = [a]

    def __str__(self):
        return '<{0}>' \
               '<specifiers>{1}</specifiers>' \
               '<qualifiers>{2}</qualifiers>' \
               '</{0}>'.format(self.__class__.__name__, join(self.specifierList, ' '), join(self.qualifierList, ' '))

    def visit(self, env: 'scopes.DeclScope'):
        tq = TypeQualifier.getTQ(self.qualifierList)
        # print('tq={}'.format(str(tq)))
        classes = [x.typeSpecifier.__class__ for x in self.specifierList]

        assert sum(int(x in classes) for x in [StructOrUnionSpecifier, TypedefName, 'EnumSpecifier']) <= 1
        if StructOrUnionSpecifier in classes:
            assert len(self.specifierList) == 1
            type0 = c_type.QualifiedType(cast(StructOrUnionSpecifier, self.specifierList[0]).visit(env),
                                         tq)
        elif TypedefName in classes:
            assert len(self.specifierList) == 1
            type0 = cast(TypedefName, self.specifierList[0]).visit(env)
            type0 = type0.getWithAdditionalQualifiers(tq)

        else:
            type0 = c_type.normalize([x.visit(env) for x in self.specifierList])
            type0 = c_type.QualifiedType(type0, tq)
        return type0


class StructDeclaratorList(Intermediate):
    """
    :type structDeclaratorList: list[StructDeclarator]
    """

    def __init__(self, prev, relativeOrder, structDeclarator, placeHolder=',', structDeclaratorList=None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        assert placeHolder == ','
        assert isinstance(structDeclarator, StructDeclarator)
        assert structDeclaratorList is None or isinstance(structDeclaratorList, StructDeclaratorList)
        self.structDeclaratorList = [structDeclarator]
        if structDeclaratorList:
            self.structDeclaratorList.extend(structDeclaratorList.structDeclaratorList)

    def visit(self, type0: c_type.QualifiedType, env: 'scopes.TypedefDeclExcludedScope'):
        return [x.visit(type0, env) for x in self.structDeclaratorList]

    def __str__(self):
        return "<{0}>{1}</{0}>" \
            .format(self.character, join(self.structDeclaratorList))
        # return span(self.__class__.__name__) + ul(*self.structDeclaratorList)


class StructDeclarator(Intermediate):
    """
    :type declarator: Declarator
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 3
        if relativeOrder == 1:
            self.declarator = args[0]
        else:
            raise NotImplementedError()

    def visit(self, type0: c_type.QualifiedType, env: 'scopes.TypedefDeclExcludedScope'):
        return self.declarator.visit(type0, env)

    def __str__(self):
        return str(self.declarator)
    # def visit(self, env: 'environment.Scope', type0: c_type.Type) -> Tuple[str, c_type.Type]:
    #     return self.declarator.visit(env, type0)


# class EnumSpecifier(Intermediate):
#     key = 54
#     relativeOrder = 1
#     rhs = ('enum', 'identifier', '{', 'EnumeratorList', '}')
#
#
# class EnumSpecifier(Intermediate):
#     key = 55
#     relativeOrder = 2
#     rhs = ('enum', '{', 'EnumeratorList', '}')
#
#
# class EnumSpecifier(Intermediate):
#     key = 56
#     relativeOrder = 3
#     rhs = ('enum', 'identifier', '{', 'EnumeratorList', ',', '}')
#
#
# class EnumSpecifier(Intermediate):
#     key = 57
#     relativeOrder = 4
#     rhs = ('enum', '{', 'EnumeratorList', ',', '}')
#
#
# class EnumSpecifier(Intermediate):
#     key = 58
#     relativeOrder = 5
#     rhs = ('enum', 'identifier')
#
#
# class EnumeratorList(Intermediate):
#     key = 59
#     relativeOrder = 1
#     rhs = ('Enumerator',)
#
#
# class EnumeratorList(Intermediate):
#     key = 60
#     relativeOrder = 2
#     rhs = ('EnumeratorList', ',', 'Enumerator')
#
#
# class Enumerator(Intermediate):
#     key = 61
#     relativeOrder = 1
#     rhs = ('EnumerationConstant',)
#
#
# class Enumerator(Intermediate):
#     key = 62
#     relativeOrder = 2
#     rhs = ('EnumerationConstant', '=', 'ConstantExpression')


class Declarator(Intermediate):
    """
    :type pointer:          None|Pointer
    :type directDeclarator: DirectDeclarator
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 1:
            self.pointer = args[0]
            self.directDeclarator = args[1]
        else:
            self.pointer = None
            self.directDeclarator = args[0]

    def visit(self, type0: c_type.QualifiedType, env: 'scopes.DeclScope'):
        if self.pointer is None:
            return self.directDeclarator.visit(type0, env)
        type0, qualifiers = self.pointer.visit(type0)
        type0 = c_type.QualifiedType(type0, qualifiers)
        return self.directDeclarator.visit(type0, env)

    def __str__(self):
        if self.pointer is None:
            return str(self.directDeclarator)

        return "<{0}>{1}{2}</{0}>".format(self.character, self.pointer, self.directDeclarator)


class DirectDeclarator(Intermediate):
    """
    :type identifier:           IdentifierParseNode
    :type declarator:           Declarator
    :type directDeclarator:     DirectDeclarator
    :type subscript:            None|AssignmentExpression
    :type parameterTypeList:    None|ParameterTypeList
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 14
        if relativeOrder == 1:
            assert isinstance(args[0], IdentifierParseNode)
            self.identifier = cast(IdentifierParseNode, args[0])
        elif relativeOrder == 2:
            self.declarator = args[1]
        else:
            self.directDeclarator = args[0]
            if relativeOrder in (3, 6):  # DirectDeclarator "[" "]"
                self.subscript = ''
            elif relativeOrder in (4, 5, 7, 8, 9):
                self.subscript = args[-2]
            # elif relativeOrder == 5:  # DirectDeclarator "[" AssignmentExpression "]"
            #     self.subscript = args[2]
            # elif relativeOrder == 6:
            #     #DirectDeclarator "[" TypeQualifierList"]"
            #     self.subscript = args[2]
            # elif relativeOrder == 7:
            #     #DirectDeclarator "[" static TypeQualifierList AssignmentExpression "]"
            #     self.subscript = args[-2]
            # elif relativeOrder == 8:
            #     raise NotImplementedError()
            # elif relativeOrder == 9:
            #     raise NotImplementedError()
            elif relativeOrder in (10, 11):
                self.subscript = '*'
            # elif relativeOrder == 10:
            #     raise NotImplementedError()
            # elif relativeOrder == 11:
            #     raise NotImplementedError()
            elif relativeOrder == 12:
                self.parameterTypeList = args[2]
            elif relativeOrder == 13:
                raise NotImplementedError()
            elif relativeOrder == 14:
                self.parameterTypeList = None
        pass

    def visit(self, type0: c_type.QualifiedType, env: 'scopes.DeclScope') -> Tuple[ctoken.CToken, c_type.QualifiedType]:
        if self.relativeOrder == 1:
            assert not type0.isNull()

            return self.identifier.tok, type0

        elif self.relativeOrder == 2:
            return self.declarator.visit(type0, env)

        elif self.relativeOrder in (3, 6):
            type0 = c_type.IncompleteArrayType(type0)
            type0 = c_type.QualifiedType(type0)
            return self.directDeclarator.visit(type0, env)

        elif self.relativeOrder in (4, 5, 7, 8, 9):
            subscript = self.subscript.visit(env)

            assert isinstance(subscript, ast.Expr)
            assert subscript.isConstant is True
            assert isinstance(subscript.value, int)

            type0 = c_type.ConstantArrayWithExprType(type0, subscript.value, subscript)
            type0 = c_type.QualifiedType(type0)
            return self.directDeclarator.visit(type0, env)

        # elif self.relativeOrder == 6:
        #     type0 = c_type.ArrayType(type0)
        #     type0 = c_type.QualifiedType(type0)
        #     return self.directDeclarator.visit(type0, env)
        #
        elif self.relativeOrder in (10, 11):
            assert isinstance(env, scopes.FnPrototypeScope)
            type0 = c_type.IncompleteArrayType(type0)
            type0 = c_type.QualifiedType(type0)
            return self.directDeclarator.visit(type0, env)

        elif self.relativeOrder == 12:
            env1 = scopes.FnPrototypeScope(env)
            self.parameterTypeList.visit(env1)
            type0 = c_type.FunctionProtoType(type0, env1)
            type0 = c_type.QualifiedType(type0)
            return self.directDeclarator.visit(type0, env)
        elif self.relativeOrder == 13:
            assert 0 and '不支持!'
        elif self.relativeOrder == 14:
            env1 = scopes.FnPrototypeScope(env)
            # env1.insertParamVarDecl(ast.ParamVarDecl(0, c_type.QualifiedType(c_type.Void())))
            type0 = c_type.FunctionProtoType(type0, env1)
            type0 = c_type.QualifiedType(type0)
            return self.directDeclarator.visit(type0, env)

    def __str__(self):
        # res = span(self.__class__.__name__) + str(self.relativeOrder)
        # tmp = []
        if self.relativeOrder == 1:
            return str(self.identifier)
        if self.relativeOrder == 2:
            return str(self.declarator)
        if self.relativeOrder <= 11:
            return '<{0}>{1}<{2}>{3}</{2}></{0}>'.format('ArrayType', self.directDeclarator, 'size',
                                                         self.subscript or '')
        return '<{0}>{1}{2}</{0}>'.format('Func', self.directDeclarator, self.parameterTypeList or '')


class Pointer(Intermediate):
    """
    :type typeQualifierList:    list[TypeQualifier]
    :type pointer:              None|Pointer
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 4
        self.typeQualifierList = []
        self.pointer = None
        if relativeOrder == 1:
            pass
        elif relativeOrder == 2:
            t = args[1]
            assert isinstance(t, TypeQualifierList)
            self.typeQualifierList = t.typeQualifierList
        elif relativeOrder == 3:
            t = args[1]
            p = args[2]
            assert isinstance(t, TypeQualifierList)
            assert isinstance(p, Pointer)
            self.typeQualifierList = t.typeQualifierList
            self.pointer = p
        elif relativeOrder == 4:
            assert isinstance(args[1], Pointer)
            self.pointer = args[1]

    # def visit(self, type0: c_type.Type) -> Tuple[c_type.Type, List[TypeQualifier]]:
    #     type0 = c_type.Pointer(type0)
    #     if self.pointer is None:
    #         return type0, self.typeQualifierList
    #     type0.addQualifier(self.typeQualifierList)
    #     return self.pointer.visit(type0)
    def visit(self, type0: c_type.QualifiedType):
        type0 = c_type.Pointer(type0)
        tq = TypeQualifier.getTQ(self.typeQualifierList)
        if self.pointer is None:
            return type0, tq
        type0 = c_type.QualifiedType(type0, tq)
        return self.pointer.visit(type0)

    def __str__(self):
        if self.typeQualifierList or self.pointer:
            return "<{0}>{1}{2}</{0}>" \
                .format(self.character, join(self.typeQualifierList), self.pointer or '')
            # return span(self.__class__.__name__) + ul(self.pointer, self.typeQualifierList)
        return "<{0} />".format(self.character)
        # return span(self.__class__.__name__) + ul(self.pointer)


class TypeQualifierList(Intermediate):
    """
    :type typeQualifierList: list[TypeQualifier]
    """

    def __init__(self, prev, relativeOrder, typeQualifier, typeQualifierList=None):
        super().__init__(prev, relativeOrder)
        assert isinstance(typeQualifier, TypeQualifier)
        if typeQualifierList is None:
            self.typeQualifierList = [typeQualifier]
        else:
            assert isinstance(typeQualifierList, TypeQualifierList)
            self.typeQualifierList = [typeQualifier] + typeQualifierList.typeQualifierList

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, join(self.typeQualifierList))


class ParameterTypeList(Intermediate):
    """
    :type parameterTypeList: list[ParameterDeclaration]
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 2:
            raise NotImplementedError()
        p = args[0]
        assert isinstance(p, ParameterList)
        self.parameterTypeList: List[ParameterDeclaration] = p.parameterList

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, join(self.parameterTypeList))

    def visit(self, env: 'scopes.FnPrototypeScope'):
        for i, p in enumerate(self.parameterTypeList):
            # if isinstance(p, list):
            #     for e in p:
            #         e.visit(i, env)
            # else:
            p.visit(i, env)

        env.lock()


class ParameterList(Intermediate):
    """
    :type parameterList: list[ParameterDeclaration]
    """

    def __init__(self, prev, relativeOrder, parameterDeclaration, placeHolder=',', parameterList=None):
        super().__init__(prev, relativeOrder)
        assert placeHolder == ','
        assert parameterList is None or isinstance(parameterList, ParameterList)
        assert 1 <= relativeOrder <= 2
        assert isinstance(parameterDeclaration, ParameterDeclaration)
        self.parameterList = [parameterDeclaration]
        if parameterList is not None:
            self.parameterList.extend(parameterList.parameterList)

    def visit(self, env):
        raise NotImplementedError()


class ParameterDeclaration(Intermediate):
    """
    :type declarationSpecifiers:    DeclarationSpecifiers
    :type declarator:               None|Declarator
    :type abstractDeclarator:       None|AbstractDeclarator
    """

    def __init__(self, prev, relativeOrder, declarationSpecifiers, declarator=None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 3
        assert isinstance(declarationSpecifiers, DeclarationSpecifiers)
        self.declarationSpecifiers = declarationSpecifiers
        self.declarator = None
        self.abstractDeclarator = None
        if declarator is not None:
            if isinstance(declarator, Declarator):
                self.declarator = declarator
            elif isinstance(declarator, AbstractDeclarator):
                self.abstractDeclarator = declarator
            else:
                assert 0

    @staticmethod
    def transform(type1: c_type.QualifiedType) -> 'c_type.QualifiedType':
        if isinstance(type1(), c_type.FunctionProtoType):
            return c_type.QPointer(type1)
        if isinstance(type1(), c_type.ArrayType):
            return c_type.QualifiedType(
                c_type.Pointer(cast(c_type.ArrayType, type1()).elementType)
            ).withConst()
        return type1

    def visit(self, index: int, env: 'scopes.FnPrototypeScope') -> None:
        category, type0, = self.declarationSpecifiers.visit(env, True)
        if category == 'typedef':
            raise RuntimeError('typedef are not allow in the scope of function prototype!')
        assert category == 'var'
        if self.declarator:
            tok, type1 = self.declarator.visit(type0, env)
            assert isinstance(tok.data, str)
            type1 = ParameterDeclaration.transform(type1)
            #
            # except RuntimeError:
            #     raise RuntimeError('类型{}不完全，无法用它定义变量{},位置:{}'
            #                        .format(type1(), tok.data, tok.position))

            decl = ast.ParamVarDecl(index, type1, tok.data)
            env.insertParamVarDecl(decl)
        elif self.abstractDeclarator:
            type1 = self.abstractDeclarator.visit(type0, env)
            type1 = ParameterDeclaration.transform(type1)
            decl = ast.ParamVarDecl(index, type1)
            env.insertParamVarDecl(decl)
        else:
            type0 = ParameterDeclaration.transform(type0)
            decl = ast.ParamVarDecl(index, type0)
            env.insertParamVarDecl(decl)

    def __str__(self):
        if self.relativeOrder <= 2:
            return '<{0}>{1}{2}</{0}>' \
                .format(self.character, self.declarationSpecifiers, self.declarator or self.abstractDeclarator)
        return '<{0}>{1}</{0}>' \
            .format(self.character, self.declarationSpecifiers)

    __repr__ = __str__


# class IdentifierList(Intermediate):
#     key = 93
#     relativeOrder = 2
#     rhs = ('identifier', ',', 'IdentifierList')
#

class Typename(Intermediate):
    """
    :type specifierQualifierList:   SpecifierQualifierList
    :type abstractDeclarator:       None|AbstractDeclarator
    """

    def __init__(self, prev, relativeOrder, specifierQualifierList, abstractDeclarator=None):
        super().__init__(prev, relativeOrder)

        assert isinstance(specifierQualifierList, SpecifierQualifierList)
        assert 1 <= relativeOrder <= 2

        self.specifierQualifierList = specifierQualifierList
        # self.qualifierList = specifierQualifierList.qualifierList
        self.abstractDeclarator = None
        if abstractDeclarator is not None:
            assert isinstance(abstractDeclarator, AbstractDeclarator)
            self.abstractDeclarator = abstractDeclarator

    def visit(self, env: 'scopes.DeclScope'):
        type0 = self.specifierQualifierList.visit(env)
        # print('最初 type0 は {}'.format(type0))
        if self.abstractDeclarator:
            return self.abstractDeclarator.visit(type0, env)
        else:
            return type0

    def __str__(self):
        return '<{0}>{1}{2}</{0}>' \
            .format(self.__class__.__name__, self.specifierQualifierList, self.abstractDeclarator or '')


class AbstractDeclarator(Intermediate):
    """
    :type pointer:                  None|Pointer
    :type directAbstractDeclarator: None|DirectAbstractDeclarator
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 3
        self.pointer = None
        self.directAbstractDeclarator = None
        if relativeOrder == 1:
            p = args[0]
            assert isinstance(p, Pointer)
            self.pointer = p
        elif relativeOrder == 2:
            p = args[0]
            d = args[1]
            assert isinstance(p, Pointer)
            assert isinstance(d, DirectAbstractDeclarator)
            self.pointer = p
            self.directAbstractDeclarator = d
        else:
            d = args[0]
            assert isinstance(d, DirectAbstractDeclarator)
            self.directAbstractDeclarator = d

    def __str__(self):
        # if not self.directAbstractDeclarator:
        #     return str(self.directAbstractDeclarator)
        return '<{0}>{1}{2}</{0}>' \
            .format(self.character, self.pointer or '', self.directAbstractDeclarator or '')

    def visit(self, type0: c_type.QualifiedType, env: 'scopes.DeclScope'):
        if self.pointer is None:
            return self.directAbstractDeclarator.visit(type0, env)
        type0, qualifiers = self.pointer.visit(type0)
        type0 = c_type.QualifiedType(type0, qualifiers)
        if self.directAbstractDeclarator is None:
            return type0
        return self.directAbstractDeclarator.visit(type0, env)


#
# class AbstractDeclarator(Intermediate):
#     key = 97
#     relativeOrder = 2
#     rhs = ('Pointer', 'DirectAbstractDeclarator')
#
#
# class AbstractDeclarator(Intermediate):
#     key = 98
#     relativeOrder = 3
#     rhs = ('DirectAbstractDeclarator',)
#

class DirectAbstractDeclarator(Intermediate):
    """
    :type abstractDeclarator:           None|AbstractDeclarator
    :type directAbstractDeclarator:     None|DirectAbstractDeclarator
    :type typeQualifierList:            None|list[TypeQualifier]
    :type subscript:                    None|AssignmentExpression
    :type parameterTypeList:            None|ParameterTypeList
    :type relativeOrder:                int
    """

    def __str__(self):
        if self.relativeOrder == 1:
            return str(self.abstractDeclarator)
        if self.relativeOrder in (10, 11, 20, 21):
            return '<{0}>{1}{2}</{0}>' \
                .format('Func', self.directAbstractDeclarator or '', self.parameterTypeList or '')
        return '<{0}>{1}<{2}>{3}</{2}></{0}>' \
            .format('ArrayType', self.directAbstractDeclarator or '', 'size', self.subscript or '罡')

    def __init__(self, prev, relativeOrder, *args):
        assert 1 <= relativeOrder <= 21
        super().__init__(prev, relativeOrder)
        self.abstractDeclarator = None
        self.directAbstractDeclarator = None
        self.typeQualifierList = None
        self.subscript = None
        self.parameterTypeList = None
        self.relativeOrder = relativeOrder

        def ab(x):
            tmp = args[x]
            assert isinstance(tmp, AbstractDeclarator)
            self.abstractDeclarator = tmp

        def d(x):
            tmp = args[x]
            assert isinstance(tmp, DirectAbstractDeclarator)
            self.directAbstractDeclarator = tmp

        def t(x):
            tmp = args[x]
            assert isinstance(tmp, TypeQualifierList)
            self.typeQualifierList = tmp.typeQualifierList

        def a(x):
            tmp = args[x]
            assert isinstance(tmp, AssignmentExpression)
            self.subscript = tmp

        def p(x):
            tmp = args[x]
            assert isinstance(tmp, ParameterTypeList)
            self.parameterTypeList = tmp

        if relativeOrder == 1:
            ab(1)
        elif 2 <= relativeOrder <= 11:
            d(0)
            if relativeOrder == 2:
                t(2)
                a(3)
            elif relativeOrder == 3:
                a(2)
            elif relativeOrder == 4:
                t(2)
            elif relativeOrder == 5:
                pass
            elif relativeOrder == 6:
                t(3)
                a(4)
            elif relativeOrder == 7:
                a(3)
            elif relativeOrder == 8:
                d(0)
                t(2)
                a(4)
            elif relativeOrder == 9:
                pass
            elif relativeOrder == 10:
                p(2)
                self.subscript = '*'
            elif relativeOrder == 11:
                self.subscript = '*'
        elif relativeOrder == 12:
            t(1)
            a(2)
        elif relativeOrder == 13:
            a(1)
        elif relativeOrder == 14:
            t(1)
        elif relativeOrder == 15:
            pass
        elif relativeOrder == 16:
            t(2)
            a(3)
        elif relativeOrder == 17:
            a(2)
        elif relativeOrder == 18:
            t(1)
            a(3)
        elif relativeOrder == 19:
            pass
        elif relativeOrder == 20:
            p(1)
        elif relativeOrder == 21:
            pass

    def visit(self, type0: c_type.QualifiedType, env: 'scopes.DeclScope'):
        if self.relativeOrder == 1:
            # "(" AbstractDeclarator ")"
            return self.abstractDeclarator.visit(type0, env)
        elif self.relativeOrder in (2, 3):
            # DirectAbstractDeclarator "[" TypeQualifierList AssignmentExpression "]"
            # DirectAbstractDeclarator "[" AssignmentExpression "]"

            e = self.subscript.visit(env)
            if not e.isConstant:
                raise RuntimeError('数组大小不可为变量！')
            if not isinstance(e.value, int):
                raise RuntimeError('数组大小必须是整形常量！')

            type0 = c_type.ConstantArrayWithExprType(type0, e.value, e)
            type0 = c_type.QualifiedType(type0)
            return self.directAbstractDeclarator.visit(type0, env)

        elif self.relativeOrder in (4, 5):
            # DirectAbstractDeclarator "[" TypeQualifierList "]"
            # DirectAbstractDeclarator "["  "]"
            type0 = c_type.IncompleteArrayType(type0)
            type0 = c_type.QualifiedType(type0)
            return self.directAbstractDeclarator.visit(type0, env)

        elif self.relativeOrder in (6, 7, 8):
            # DirectAbstractDeclarator "[" static TypeQualifierList AssignmentExpression "]"
            # DirectAbstractDeclarator "[" static AssignmentExpression "]"
            # DirectAbstractDeclarator "[" TypeQualifierList static AssignmentExpression "]"

            e = self.subscript.visit(env)
            assert e.isIntegerConstantExpr()
            assert isinstance(e.value, int)
            # TODO: int expr
            type0 = c_type.ConstantArrayWithExprType(type0, e.value, e)
            type0 = c_type.QualifiedType(type0)
            return self.directAbstractDeclarator.visit(type0, env)

        elif self.relativeOrder == 9:
            # DirectAbstractDeclarator "[" "*" "]"
            assert isinstance(env, scopes.FnPrototypeScope)
            type0 = c_type.IncompleteArrayType(type0)
            type0 = c_type.QualifiedType(type0)
            return self.directAbstractDeclarator.visit(type0, env)

        elif self.relativeOrder == 10:
            # DirectAbstractDeclarator "(" ParameterTypeList ")"
            env1 = scopes.FnPrototypeScope(env)
            self.parameterTypeList.visit(env1)
            type0 = c_type.FunctionProtoType(type0, env1)
            type0 = c_type.QualifiedType(type0)
            return self.directAbstractDeclarator.visit(type0, env)

        elif self.relativeOrder == 11:
            # DirectAbstractDeclarator "("  ")"
            env1 = scopes.FnPrototypeScope(env)
            env1.insertParamVarDecl(ast.ParamVarDecl(0, c_type.QualifiedType(c_type.Void())))
            type0 = c_type.FunctionProtoType(type0, env1)
            type0 = c_type.QualifiedType(type0)
            return self.directAbstractDeclarator.visit(type0, env)

        elif self.relativeOrder in (12, 13, 16, 17, 18):
            # "[" AssignmentExpression "]"

            e = self.subscript.visit(env)
            assert isinstance(e.value, int)
            # TODO: int expr
            type0 = c_type.ConstantArrayWithExprType(type0, e.value, e)
            type0 = c_type.QualifiedType(type0)
            return type0

        elif self.relativeOrder in (14, 15):
            # "["  "]"
            type0 = c_type.QualifiedType(c_type.IncompleteArrayType(type0))
            return type0

        elif self.relativeOrder == 19:
            # "[" "*" "]"
            assert isinstance(env, scopes.FnPrototypeScope)
            type0 = c_type.IncompleteArrayType(type0)
            type0 = c_type.QualifiedType(type0)
            return type0
        elif self.relativeOrder == 20:
            # "(" ParameterTypeList ")"
            env1 = scopes.FnPrototypeScope(env)
            self.parameterTypeList.visit(env1)
            type0 = c_type.FunctionProtoType(type0, env1)
            type0 = c_type.QualifiedType(type0)
            return type0

        elif self.relativeOrder == 21:
            # "("  ")"
            env1 = scopes.FnPrototypeScope(env)
            type0 = c_type.FunctionProtoType(type0, env1)
            type0 = c_type.QualifiedType(type0)
            return type0


class TypedefName(Intermediate):

    def __init__(self, prev, relativeOrder: int, s: str):
        super().__init__(prev, relativeOrder)
        assert relativeOrder == 1
        assert isinstance(s, IdentifierParseNode)
        self.typedefName = s

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, self.typedefName)

    def visit(self, env: 'scopes.DeclScope') -> 'c_type.QualifiedType':
        decl = env.getTypedefDecl(self.typedefName.value)

        return decl.underlyingType


class FunctionSpecifier(Intermediate):
    key = 121
    relativeOrder = 1
    rhs = ('inline',)


class Initializer(Intermediate):
    """
    :type expr:             None|Expression
    :type initializerList:  None|InitializerList
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 3
        self.expr = None
        self.initializerList = None
        if relativeOrder == 1:
            self.expr = args[0]
        else:
            self.initializerList = args[1]

    def visit(self, decl, env: 'scopes.DeclScope'):
        raise NotImplementedError()
        if isinstance(env, scopes.GlobalScope):
            if self.relativeOrder == 1:
                assert isinstance(self.expr, AssignmentExpression)
                assert isinstance(decl, ast.ValueDecl)
                lhs = ast.DeclRefExpr(decl, env)
                rhs = self.expr.visit(env)
                if not rhs.isConstant:
                    raise RuntimeError("initializer element is not a compile-time constant")
                rhs = ast.tryToDeduceTypeForAssignment(lhs.type, rhs, env)
                if rhs.type != lhs.type:
                    raise RuntimeError('initialize {} with {} is illegal'.format(lhs.type, rhs.type))

                # return ast.ExprStmt(env, ast.AssignmentExpr(lhs, rhs, env))
            elif self.relativeOrder == 2:
                raise NotImplementedError()

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, self.expr or self.initializerList)


class InitializerList(Intermediate):
    # InitializerList->
    #      Designation Initializer
    #     |Initializer
    #     |InitializerList "," Designation Initializer
    #     |InitializerList ","             Initializer
    """
    :type initializerList: list[Initializer|(Designation, Initializer)]
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 4

        if relativeOrder == 1:
            assert len(args) == 2
            self.initializerList = [(args[0], args[1])]
        elif relativeOrder == 2:
            assert len(args) == 1
            self.initializerList = [args[0]]
        elif relativeOrder == 3:
            assert len(args) == 4
            initializerList = args[0]
            assert isinstance(initializerList, InitializerList)
            self.initializerList = initializerList.initializerList + [(args[-2], args[-1])]
        elif relativeOrder == 4:
            assert len(args) == 3
            initializerList = args[0]
            assert isinstance(initializerList, InitializerList)
            self.initializerList = initializerList.initializerList + [args[-1]]

    def visit(self, env):
        if self.relativeOrder == 1:
            pass

        raise NotImplementedError()

    def __str__(self):
        t = []
        for initializer in self.initializerList:
            if isinstance(initializer, tuple):
                t.append('<{0}>{1}{2}</{0}>'.format('pair', initializer[0], initializer[1]))
            else:
                t.append(initializer)
        return '<{0}>{1}</{0}>'.format(self.character, join(t))


class Designation(Intermediate):
    #
    # Designation->
    #    DesignatorList "="
    """
    :type designatorList: DesignatorList
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert relativeOrder == 1
        self.designatorList = args[0]

    def visit(self, qualType: 'c_type.QualifiedType', env: 'scopes.DeclScope'):
        return self.designatorList.visit(qualType, 0, env)

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, self.designatorList)


class DesignatorList(Intermediate):
    """
    :type designatorList: list[Designator]
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 1:
            self.designatorList = [args[0]]
        else:
            designatorList = args[1]
            assert isinstance(designatorList, DesignatorList)
            self.designatorList = [args[0]] + designatorList.designatorList

    def visit(self, qualType: 'c_type.QualifiedType', addr: int, env: 'scopes.DeclScope'):
        for designator in self.designatorList:
            qualType, addr, env = designator.visit(qualType, env)
        return addr

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, join(self.designatorList))


class Designator(Intermediate):
    """
    :type designator: IdentifierParseNode|ConstantExpression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        assert isinstance(args[1], (ConstantExpression, IdentifierParseNode))

        self.designator = args[1]

    def __str__(self):
        if self.relativeOrder == 1:
            return '<{0} cls="{1}">{2}</{0}>'.format(self.character, '[]', self.designator)
        return '<{0} cls="{1}">{2}</{0}>'.format(self.character, '.', self.designator)

    def visit(self, qualType, env: 'scopes.DeclScope'):
        assert isinstance(qualType, c_type.QualifiedType)
        type = qualType()
        if self.relativeOrder == 1:
            assert isinstance(self.designator, ConstantExpression)
            e = self.designator.visit(env)

            assert isinstance(e, ast.Expr)  # 防sb
            assert e.isConstant  # 必须为常量表达式
            assert isinstance(type, c_type.ArrayType)  # 都用下标了当然只能是对数组初始化

            if isinstance(type, c_type.ConstantArrayType):
                result = e.result
                assert isinstance(result.value, int)  # 下标必须是整数
                if isinstance(type, c_type.ConstantArrayWithExprType):
                    assert 0 <= result.value < type.length  # 下标必须非负且不能越界
                if isinstance(type.elementType(), c_type.StructType):
                    env = cast(c_type.StructType, type.elementType()).decl.classScope
                return ast.ArrayDesignator(result.value, env)
                # return type.elementType, \
                #        cast(int, addr + result.value * type.elementType.width), \
                #        env
            assert 0

        assert isinstance(self.designator, IdentifierParseNode)
        iden = self.designator.value
        assert isinstance(iden, str)
        assert isinstance(type, c_type.StructType)
        idenType = type.decl.classScope.getValueType(iden)
        assert isinstance(idenType, c_type.QualifiedType)
        if isinstance(idenType(), c_type.StructType):
            env = idenType().decl.classScope
        return ast.FieldDesignator(iden, type.decl.classScope)
        # return idenType, type.decl.scope.getOffsetByName(iden), env


class PrimaryExpression(Intermediate):
    """
    :type e: IdentifierParseNode|Literal|Expression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 4
        if relativeOrder <= 3:
            assert isinstance(args[0], Literal)
            self.e = cast(Literal, args[0])
        else:
            assert isinstance(args[1], Expression)
            self.e = cast(Expression, args[1])

    def __str__(self):
        # if displayAll:
        #     return '<{0}>{1}</{0}>'.format(self.character, self.e)
        return str(self.e)

    def visit(self, env: 'scopes.DeclScope'):
        return self.e.visit(env)


class PostfixExpression(Intermediate):
    """
    :type operator:         None|str
    :type eList:   list[Expression]
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 10
        if relativeOrder == 1:
            assert isinstance(args[0], PrimaryExpression)
            self.eList = [cast(PrimaryExpression, args[0]).e]
            self.operator = None
        elif relativeOrder <= 8:
            assert isinstance(args[0], PostfixExpression)
            self.eList = [args[0]]

            if relativeOrder == 2:
                assert isinstance(args[2], Expression)
                self.eList.append(args[2])
                self.operator = '[]'
            elif relativeOrder == 3:
                assert len(args) == 3
                self.operator = '()'
            elif relativeOrder == 4:
                assert isinstance(args[2], ArgumentExpressionList)
                self.eList.append(args[2])
                self.operator = '()'
            elif relativeOrder in (5, 6):
                assert isinstance(args[1], TerminalParseTreeNode)
                assert isinstance(args[2], IdentifierParseNode)
                self.eList.append(args[2])
                self.operator = cast(TerminalParseTreeNode, args[1]).value
            elif relativeOrder in (7, 8):
                assert isinstance(args[1], TerminalParseTreeNode)
                self.operator = cast(TerminalParseTreeNode, args[1]).value
        else:
            assert isinstance(args[1], Typename)
            assert isinstance(args[4], InitializerList)
            self.eList = [args[1], args[4]]
            self.operator = 'CompoundLiteral'

    def visit(self, env: 'scopes.DeclScope'):
        if self.relativeOrder == 1:
            return self.eList[0].visit(env)
        if self.relativeOrder == 2:
            lhs = self.eList[0].visit(env)
            rhs = self.eList[1].visit(env)

            assert isinstance(lhs, ast.Expr)
            assert isinstance(rhs, ast.Expr)
            return ast.ArraySubscriptExpr(lhs, rhs, env)
        if self.relativeOrder == 3:
            fn = self.eList[0].visit(env)
            return ast.CallExpr(fn, [], env)
        if self.relativeOrder == 4:
            assert isinstance(self.eList[1], ArgumentExpressionList)
            fn = self.eList[0].visit(env)
            args = cast(ArgumentExpressionList, self.eList[1]).visit(env)
            return ast.CallExpr(fn, args, env)
        if self.relativeOrder == 5:
            lhs = self.eList[0].visit(env)
            rhs = self.eList[1]
            assert isinstance(rhs, IdentifierParseNode)
            return ast.MemberExpr(lhs, rhs.tok, env)
        if self.relativeOrder == 6:
            lhs = self.eList[0].visit(env)
            rhs = self.eList[1]
            assert isinstance(rhs, IdentifierParseNode)
            return ast.ArrowMemberExpr(lhs, rhs.tok, env)
        if self.relativeOrder in (7, 8):
            e = self.eList[0].visit(env)
            assert isinstance(e, ast.Expr)
            return ast.UnaryOperator(e, self.operator, env, isPostfix=True)
        assert 0 and "此处尚未完成!"

    def __str__(self):
        # if displayAll:
        #     return '<{0} operator="{1}">{2}</{0}>' \
        #         .format('Postfix', self.operator or '', join(self.eList))
        if self.operator is None:
            assert len(self.eList) == 1
            return str(self.eList[0])
        return '<{0} operator="{1}">{2}</{0}>' \
            .format('Postfix', self.operator, join(self.eList))


class ArgumentExpressionList(Intermediate):
    """
    :type eList: list[AssignmentExpression]
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 1:
            assert isinstance(args[0], AssignmentExpression)
            self.eList = [args[0]]
        else:
            assert isinstance(args[0], ArgumentExpressionList)
            assert isinstance(args[2], AssignmentExpression)
            self.eList = cast(ArgumentExpressionList, args[0]).eList + [args[2]]

    def visit(self, env: 'scopes.DeclScope'):
        return [e.visit(env) for e in self.eList]

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, join(self.eList))


class UnaryExpression(Intermediate):
    """
    :type operator:         None|str
    :type e:    PostfixExpression|UnaryExpression|CastExpression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 6
        self.operator = None
        if relativeOrder == 1:
            assert isinstance(args[0], PostfixExpression)
            self.e = args[0]
        elif relativeOrder in (2, 3, 5):
            assert isinstance(args[0], TerminalParseTreeNode)
            assert isinstance(args[1], UnaryExpression)
            self.operator = cast(TerminalParseTreeNode, args[0]).value
            assert self.operator in ('++', '--', 'sizeof')
            self.e = args[1]
        elif relativeOrder == 4:
            assert isinstance(args[0], UnaryOp)
            assert isinstance(args[1], CastExpression)
            self.operator = cast(UnaryOp, args[0]).operator
            self.e = args[1]
        elif relativeOrder == 6:
            assert isinstance(args[0], TerminalParseTreeNode)
            assert isinstance(args[2], Typename)
            self.operator = cast(TerminalParseTreeNode, args[0]).value
            assert self.operator == 'sizeof'
            self.e = args[2]

    def visit(self, env: 'scopes.DeclScope'):
        if self.relativeOrder == 1:
            return self.e.visit(env)
        # 类型转换的问题
        if self.relativeOrder in (2, 3, 4):
            return ast.UnaryOperator(self.e.visit(env), self.operator, env)
        return ast.SizeOfExpr(self.e.visit(env), env)

    def __str__(self):
        # if displayAll:
        #     return '<{0} operator="{1}">{2}</{0}>'.format('Unary', self.operator or '', self.e)
        if self.operator is None:
            return str(self.e)
        return '<{0} operator="{1}">{2}</{0}>'.format('Unary', self.operator, self.e)


class UnaryOp(Intermediate):
    """
    :type operator: str
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 11
        self.operator = cast(TerminalParseTreeNode, args[0]).value
        if not isinstance(self, AssignmentOp):
            assert self.operator in ('&', '*', '+', '-', '~', '!')
        else:
            assert self.operator in {'=', '*=', '/=', '%=', '+=', '-=', '<<=', '>>=', '&=', '^=', '|='}

    def __str__(self):
        return self.operator


class CastExpression(Intermediate):
    """
    :type typename: None|Typename
    :type e: UnaryExpression|CastExpression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 1:
            assert isinstance(args[0], UnaryExpression)
            self.typename = None
            self.e = args[0]
        else:
            assert isinstance(args[1], Typename)
            assert isinstance(args[-1], CastExpression)
            self.typename = args[1]
            self.e = args[-1]

    def visit(self, env: 'scopes.DeclScope'):
        if self.relativeOrder == 1:
            return self.e.visit(env)
        assert isinstance(self.typename, Typename)
        assert isinstance(self.e, CastExpression)
        type0 = self.typename.visit(env)

        e = self.e.visit(env)
        print('type0={}'.format(type0))
        assert isinstance(type0, c_type.QualifiedType)
        return ast.CStyleCastExpr(ast.CastExpr.CastKind.Naive, type0, e, env)

    def __str__(self):
        if self.typename is None:
            return str(self.e)
        return '<{0}>{1}{2}</{0}>'.format('Cast', self.typename, self.e)


class MultiplicativeExpression(Intermediate):

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)

        self.e1 = args[0]
        self.operator = None
        self.e2 = None
        if relativeOrder > 1:
            self.e2 = args[2]
            self.operator = cast(TerminalParseTreeNode, args[1]).value

    def visit(self, env: 'scopes.DeclScope') -> ast.Expr:
        if self.relativeOrder == 1:
            assert self.operator is None
            return self.e1.visit(env)
        e1 = self.e1.visit(env)
        e2 = self.e2.visit(env)
        # TODO: type check
        return ast.BinaryOperator(self.operator, e1, e2, env)

    def __str__(self):
        if self.operator is None:
            return str(self.e1)
        return '<{0} operator="{1}">{2}{3}</{0}>' \
            .format('Binary', self.operator, self.e1, self.e2)


class AdditiveExpression(MultiplicativeExpression):
    pass


class ShiftExpression(MultiplicativeExpression):
    pass


class RelationalExpression(MultiplicativeExpression):
    pass


class EqualityExpression(MultiplicativeExpression):
    pass


class ANDExpression(MultiplicativeExpression):
    pass


class ExclusiveORExpression(MultiplicativeExpression):
    pass


class InclusiveORExpression(MultiplicativeExpression):
    pass


class LogicalANDExpression(MultiplicativeExpression):
    pass


class LogicalORExpression(MultiplicativeExpression):
    pass


class ConditionalExpression(Intermediate):

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        assert isinstance(args[0], LogicalORExpression)
        self.e1 = args[0]
        self.e2 = None
        self.e3 = None
        if relativeOrder > 1:
            assert isinstance(args[2], Expression)
            assert isinstance(args[-1], ConditionalExpression)
            self.e2 = args[2]
            self.e3 = args[-1]

    def visit(self, env: 'scopes.DeclScope') -> ast.Expr:
        if self.relativeOrder == 1:
            return self.e1.visit(env)
        e1 = self.e1.visit(env)
        e2 = self.e2.visit(env)
        e3 = self.e3.visit(env)
        # TODO: type check
        return ast.CondExpr(e1, e2, e3, env)

    def __str__(self):
        if self.relativeOrder == 1:
            return str(self.e1)
        return '<{0}>{1}{2}{3}</{0}>' \
            .format('Conditional', self.e1, self.e2, self.e3)


class AssignmentExpression(Intermediate):
    """
    :type e1:       ConditionalExpression|UnaryExpression
    :type e2:       None|Expression
    :type operator: None|str
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        assert isinstance(args[0], (ConditionalExpression, UnaryExpression))
        self.e1 = args[0]
        self.e2 = None
        self.operator = None
        if relativeOrder > 1:
            assert isinstance(args[-1], AssignmentExpression)
            assert isinstance(args[1], AssignmentOp)
            self.e2 = args[-1]
            self.operator = cast(AssignmentOp, args[1]).operator

    def visit(self, env: 'scopes.DeclScope') -> ast.Expr:
        if self.relativeOrder == 1:
            return self.e1.visit(env)
        rhs = self.e2.visit(env)
        lhs = self.e1.visit(env)
        assert self.operator in {'=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=', '&=', '^=', '|='}
        if self.operator != '=':
            rhs = ast.BinaryOperator(self.operator[:-1], lhs, rhs, env)
        return ast.AssignmentExpr(lhs, rhs, env)
        # TODO: type check
        # return ast.AssignmentExpr(self.operator, lhs, rhs, env)

    def __str__(self):
        if self.relativeOrder == 1:
            return str(self.e1)
        return '<{0} operator="{1}">{2}{3}</{0}>' \
            .format('Assignment', self.operator, self.e1, self.e2)


class AssignmentOp(UnaryOp):
    pass


class Expression(Intermediate):
    """
    :type e1: Expression|AssignmentExpression
    :type e2: None|AssignmentExpression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 1:
            assert isinstance(args[0], AssignmentExpression)
            self.e1 = args[0]
            self.e2 = None
        else:
            assert isinstance(args[0], Expression)
            assert isinstance(args[2], AssignmentExpression)
            self.e1 = args[0]
            self.e2 = args[2]

    def visit(self, env: 'scopes.DeclScope'):
        if self.relativeOrder == 1:
            return self.e1.visit(env)
        e1 = self.e1.visit(env)
        e2 = self.e2.visit(env)
        return ast.BinaryOperator(',', e1, e2, env)

    def __str__(self):
        if self.relativeOrder == 1:
            return str(self.e1)
        return '<{0}>{1}{2}</{0}>' \
            .format('Expression', self.e1, self.e2 or '')


class ConstantExpression(Intermediate):
    """
    :type e: ConditionalExpression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert relativeOrder == 1
        assert isinstance(args[0], ConditionalExpression)
        self.e = args[0]

    def visit(self, env: 'scopes.DeclScope'):
        return self.e.visit(env)

    def __str__(self):
        return '<{0}>{1}</{0}>' \
            .format('ConstantExpr', self.e)


class Statement(Intermediate):
    """
    :type stmt:  LabeledStatement
                |CompoundStatement
                |ExpressionStatement
                |SelectionStatement
                |IterationStatement
                |JumpStatement

    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 6
        self.stmt = args[0]

    def __str__(self):
        return str(self.stmt)

    def visit(self, env: 'scopes.DeclScope'):  # , father=None):
        return self.stmt.visit(env)
        # f = 0
        # if father is not None:
        #     assert father in ('switch', 'do', 'while', 'for', 'if', 'else')
        #     if father in ('while', 'do', 'switch', 'for'):
        #         f |= ScopeFlags.BreakScope
        #     if father in ('while', 'do', 'for'):
        #         f |= ScopeFlags.ContinueScope
        #     # if father in ('if', 'switch', 'while', 'for', 'else'):
        #     #     f |= ScopeFlags.ControlScope
        #     # if father in ('if', 'switch', 'while', 'for'):
        #     #     f |= ScopeFlags.ControlScope
        #     scope = 'environment.Scope'(env, env.flags | f)
        #     return self.stmt.visit(scope)


class LabeledStatement(Intermediate):
    """
    :type identifier:   None|str
    :type case:         None|ConstantExpression
    :type default:      None|bool
    :type stmt:         Statement
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 3
        self.identifier = None
        self.case = None
        self.default = None
        self.stmt = args[-1]

        if relativeOrder == 1:
            x = args[0]
            assert isinstance(x, IdentifierParseNode)
            self.identifier = x.value
        elif relativeOrder == 2:
            x = args[1]
            assert isinstance(x, ConstantExpression)
            self.case = x
        else:
            self.default = True

    def visit(self, env: 'scopes.DeclScope'):
        stmt = self.stmt.visit(env)
        if self.relativeOrder == 1:
            assert isinstance(env, (scopes.FnScope, scopes.NaiveScope))
            stmt = ast.LabeledStmt(env, self.identifier, stmt)
            env.insertLabel(stmt)
            return stmt

        if self.relativeOrder == 2:
            if not isinstance(env, scopes.SwitchScope):
                raise RuntimeError("case只能出现在switch里面")

            case = self.case.visit(env)
            assert case.isIntegerConstantExpr()
            caseStmt = ast.CaseStmt(env, case, stmt)
            env.insertCase(caseStmt)
            return caseStmt
        if self.relativeOrder == 3:
            assert isinstance(env, scopes.SwitchScope)
            default = ast.DefaultStmt(env, stmt)
            env.default = default
            return default

    def __str__(self):
        if self.relativeOrder == 1:
            return '<{0} label="{1}">{2}</{0}>' \
                .format(self.character, self.identifier, self.stmt)
        if self.relativeOrder == 2:
            return '<{0}>{1}{2}</{0}>'.format('case', self.case, self.stmt)
        return '<{0}>{1}</{0}>' \
            .format('default', self.stmt)


class CompoundStatement(Intermediate):
    """
    :type blockItemList: BlockItemList
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 1:
            self.blockItemList = args[1]
        else:
            self.blockItemList = None

    def visit(self, env: 'Union[scopes.FnScope,scopes.NaiveScope,scopes.ControlScope]'):
        if not isinstance(env, scopes.FnScope):
            env = scopes.NaiveScope(env, env.fnFather, env.breakFather, env.continueFather)
        if self.blockItemList is None:
            return ast.CompoundStmt(env, [ast.ExprStmt(env)])
        return ast.CompoundStmt(env, self.blockItemList.visit(env))

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, self.blockItemList or '')


class BlockItemList(Intermediate):
    """
    :type blockItemList: list[BlockItem]
    """

    def __init__(self, prev, relativeOrder, blockItem, blockItemList=None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        self.blockItemList = [blockItem]
        if blockItemList is not None:
            assert isinstance(blockItemList, BlockItemList)
            self.blockItemList.extend(blockItemList.blockItemList)

    def visit(self, env):
        res = []

        for blockItem in self.blockItemList:
            tmp = blockItem.visit(env)
            if tmp is not None:
                if isinstance(tmp, list):
                    # FIXME: 多解node要是这么处理就完蛋了
                    res.extend(tmp)
                else:
                    res.append(tmp)
        return res

    def __str__(self):
        # items = ''.join(f'<i_{0}>{1}</{0}>'.format(i, item) for i, item in enumerate(self.blockItemList))
        return '<{0}>{1}</{0}>'.format(self.character, join(self.blockItemList))
        # return span(self.__class__.__name__) + ul(*self.blockItemList)


class BlockItem(Intermediate):
    """
    :type statement:    None|Statement
    :type declaration:  None|Declaration
    """

    def __init__(self, prev, relativeOrder, item: Union[Statement, Declaration]):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        self.statement = None
        self.declaration = None
        if relativeOrder == 1:
            self.declaration = item
        else:
            self.statement = item

    def visit(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]'):
        if self.statement is None:
            return self.declaration.visit(env)
        else:
            return self.statement.visit(env)

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.character, self.statement or self.declaration)


class ExpressionStatement(Intermediate):
    """
    :type e: None|Expression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        self.e = None
        if relativeOrder == 1:
            assert isinstance(args[0], Expression)
            self.e = args[0]

    def visit(self, env: 'Union[scopes.FnScope,scopes.ControlScope,scopes.NaiveScope]'):
        if self.e is None:
            return ast.ExprStmt(env)
        return ast.ExprStmt(env, self.e.visit(env))

    def __str__(self):
        if self.e is None:
            return '<{0} />'.format(self.character)
        return '<{0}>{1}</{0}>'.format(self.character, self.e)


class SelectionStatement(Intermediate):
    """
    :type expression:   Expression
    :type flag:         str
    :type stmt:         Statement
    :type elseStmt:     None|Statement
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 3
        self.elseStmt = None
        self.flag = ''
        if relativeOrder <= 2:
            assert len(args) in (5, 7)
            self.flag = 'if'
            self.expression = args[2]
            self.stmt = args[4]
            if relativeOrder == 2:
                assert len(args) == 7
                self.elseStmt = args[-1]
                # 下面处理悬空else
                if isinstance(self.stmt.stmt, SelectionStatement) \
                        and self.stmt.stmt.flag == 'if' \
                        and self.stmt.stmt.elseStmt is None:
                    raise 不合文法()

        elif relativeOrder == 3:
            assert len(args) == 5
            self.flag = 'switch'
            self.expression = args[2]
            self.stmt = args[-1]

    def visit(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]'):
        if self.flag == 'if':
            env1 = scopes.IfScope(env)
            expr = self.expression.visit(env1)
            stmt = self.stmt.visit(env1)
            elseStmt = None
            if self.elseStmt:
                elseStmt = self.elseStmt.visit(env1)
            return ast.IfStmt(env1, expr, stmt, elseStmt)
        if self.flag == 'switch':
            env1 = scopes.SwitchScope(env)
            expr = self.expression.visit(env1)
            stmt = self.stmt.visit(env1)
            assert self.elseStmt is None
            return ast.SwitchStmt(env1, expr, stmt)

    def __str__(self):
        if self.flag == 'if':
            return '<{0}>{1}{2}{3}</{0}>' \
                .format(self.flag, self.expression, self.stmt, self.elseStmt)
        if self.flag == 'switch':
            return '<{0}>{1}{2}</{0}>' \
                .format(self.flag, self.expression, self.stmt)
        raise NotImplementedError()
    # def visit(self, env: Scope):
    #     if self.flag == 'if':
    #         pass
    #     elif self.flag == 'switch':
    #         pass
    #     else:
    #         assert 0


class IterationStatement(Intermediate):
    """
    :type flag:     str
    :type e1:       None|Expression
    :type e2:       None|Expression
    :type e3:       None|Expression
    :type stmt:     Statement
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 13
        if relativeOrder == 1:
            self.flag = 'while'
        elif relativeOrder == 2:
            self.flag = 'do'
        else:
            self.flag = 'for'

        if relativeOrder == 1:  # while
            self.e1 = args[2]
            self.stmt = args[4]
        elif relativeOrder == 2:  # do while
            self.stmt = args[1]
            self.e1 = args[4]
        else:
            self.stmt = args[-1]
            args = tuple(x for x in args[:-1] if not isinstance(x, TerminalParseTreeNode))
            self.e1 = None
            self.e2 = None
            self.e3 = None
            if relativeOrder == 3:  # for(e;e;e) {}
                assert len(args) == 3
                self.e1, self.e2, self.e3 = args
            elif relativeOrder in (4, 5, 6):
                assert len(args) == 2
                if relativeOrder == 4:
                    self.e1, self.e2 = args
                elif relativeOrder == 5:
                    self.e1, self.e3 = args
                else:
                    self.e2, self.e3 = args
            elif relativeOrder in (7, 8, 9):
                assert len(args) == 1
                if relativeOrder == 7:
                    self.e1, = args
                elif relativeOrder == 8:
                    self.e2, = args
                else:
                    self.e3, = args
            assert all(e is None or isinstance(e, Expression) for e in (self.e1, self.e2, self.e3))
            # for e in (self.e1, self.e2, self.e3):
            #     if e is not None:
            #         assert isinstance(e, Expression)

    def visit(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]'):
        if self.flag == 'while':
            env = scopes.WhileScope(env)
            expr = self.e1.visit(env)
            stmt = self.stmt.visit(env)
            return ast.WhileStmt(env, expr, stmt)
        if self.flag == 'do':
            env = scopes.DoScope(env)
            expr = self.e1.visit(env)
            stmt = self.stmt.visit(env)
            return ast.DoStmt(env, stmt, expr)
        if self.flag == 'for':
            env = scopes.ForScope(env)
            e1, e2, e3 = None, None, None
            # FIXME: 此处暂未考虑for的括号里塞定义的情况
            if self.e1 is not None:
                e1 = self.e1.visit(env)
            if self.e2 is not None:
                e2 = self.e2.visit(env)
            if self.e3 is not None:
                e3 = self.e3.visit(env)
            stmt = self.stmt.visit(env)
            return ast.ForStmt(env, e1, e2, e3, stmt)

    def __str__(self):
        if self.flag == 'for':
            return '<{0}>{1}{2}{3}{4}</{0}>' \
                .format(self.flag,
                        self.e1 or '<null/>',
                        self.e2 or '<null/>',
                        self.e3 or '<null/>',
                        self.stmt)
        return '<{0}>{1}{2}</{0}>'.format(self.flag, self.e1, self.stmt)


class JumpStatement(Intermediate):
    """
    :type keyword:      str
    :type identifier:   None|ctoken.CToken
    :type e:            None|Expression
    """

    def __init__(self, prev, relativeOrder, *args):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 5
        self.keyword = cast(TerminalParseTreeNode, args[0]).value
        self.identifier = None
        self.e = None
        if relativeOrder == 1:
            self.identifier = cast(IdentifierParseNode, args[1]).tok
        elif relativeOrder == 4:
            self.e = cast(Expression, args[1])

    def visit(self, env: 'Union[scopes.FnScope, scopes.NaiveScope]'):
        if self.relativeOrder == 1:
            assert self.keyword == 'goto'
            return ast.JumpStmt(env, self.identifier)

        if self.relativeOrder == 2:
            assert self.keyword == 'continue'
            assert env.continueFather is not None
            return ast.ContinueStmt(env)

        if self.relativeOrder == 3:
            assert self.keyword == 'break'
            assert env.breakFather is not None
            return ast.BreakStmt(env)

        if self.relativeOrder == 4:
            assert self.keyword == 'return'
            assert self.e is not None
            expr = self.e.visit(env)
            assert env.fnFather is not None
            return ast.ReturnStmt(env, expr)

        if self.relativeOrder == 5:
            assert self.keyword == 'return'
            assert env.fnFather is not None
            return ast.ReturnStmt(env)

    def __str__(self):
        return '<{0}>{1}{2}</{0}>'.format(self.keyword, self.identifier or '', self.e or '')


class FunctionDefinition(Intermediate):
    def __init__(self, prev, relativeOrder: int,
                 declarationSpecifiers: DeclarationSpecifiers,
                 declarator: Declarator,
                 compoundStmt: CompoundStatement):
        super().__init__(prev, relativeOrder)
        self.declarationSpecifiers = declarationSpecifiers
        self.declarator = declarator
        self.compoundStmt = compoundStmt

    def visit(self, env: 'scopes.GlobalScope'):
        category, type0 = self.declarationSpecifiers.visit(env, True)
        assert category == 'var'
        assert not isinstance(type0(), c_type.FunctionProtoType)
        if type0().isIncompleteType() and not isinstance(type0(), c_type.Void):
            raise RuntimeError('不完全类型{}不能作函数返回值的类型!'.format(type0))

        if isinstance(type0(), c_type.ArrayType):
            raise RuntimeError('数组类型{}不能作函数返回值的类型!'.format(type0))

        tok, type1 = self.declarator.visit(type0, env)
        x = type1()
        assert isinstance(tok.data, str)
        if not isinstance(x, c_type.FunctionProtoType):
            raise RuntimeError('{}好像不是函数定义啊？在{}'.format(tok.data, tok.position))

        env1 = scopes.FnScope(env, x, tok)
        decl = ast.FunctionDecl(tok.data, x)
        env.insertFunctionDecl(decl)
        env.getFunctionDecl(tok.data).stmt = self.compoundStmt.visit(env1)

    def __str__(self):
        return '<{0}>{1}{2}{3}</{0}>'.format(self.__class__.__name__, self.declarationSpecifiers, self.declarator,
                                             self.compoundStmt)


class DeclarationList(Intermediate):
    """
    :type declarationList: list[Declaration]
    """

    def __init__(self, prev, relativeOrder: int, declaration: Declaration, declarationList=None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        self.declarationList = [declaration]
        if relativeOrder == 2:
            if isinstance(declarationList, DeclarationList):
                self.declarationList.extend(declarationList.declarationList)

    def __str__(self):
        raise NotImplementedError()


class TranslationUnit(Intermediate):
    """
    :type translationUnitList: list[ExternalDeclaration]
    """

    def __init__(self, prev, relativeOrder: int, externalDeclaration: 'ExternalDeclaration',
                 translationUnit: 'Optional[TranslationUnit]' = None):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        self.translationUnitList = [externalDeclaration]
        if relativeOrder == 2:
            self.translationUnitList += translationUnit.translationUnitList

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.__class__.__name__, join(self.translationUnitList))

    def visit(self, env: 'scopes.GlobalScope'):
        for x in self.translationUnitList:
            x.visit(env)
        return


class ExternalDeclaration(Intermediate):
    """
    :type functionDefinition:   None|FunctionDefinition
    :type declaration:          None|Declaration
    """

    def __init__(self, prev, relativeOrder: int, stuff):
        super().__init__(prev, relativeOrder)
        assert 1 <= relativeOrder <= 2
        self.functionDefinition = None
        self.declaration = None
        if relativeOrder == 1:
            assert isinstance(stuff, FunctionDefinition)
            self.functionDefinition = stuff
        elif relativeOrder == 2:
            assert isinstance(stuff, Declaration)
            self.declaration = stuff

    def __str__(self):
        return '<{0}>{1}</{0}>' \
            .format(self.__class__.__name__, str(self.functionDefinition or self.declaration))

    def visit(self, env: 'scopes.GlobalScope'):
        if self.relativeOrder == 1:
            return self.functionDefinition.visit(env)
        elif self.relativeOrder == 2:
            return self.declaration.visit(env)


class TerminalParseTreeNode(ParseTreeNode):
    """
    :type tok:   ctoken.CToken
    """

    def __init__(self, prev: FrozenSet[ParseTreeNode], tok: 'ctoken.CToken'):
        super(TerminalParseTreeNode, self).__init__(prev)
        self.tok = tok

    def __str__(self):
        return self.__class__.__name__ + ' ' + ascii(self.value)

    def __eq__(self, other):
        if isinstance(other, TerminalParseTreeNode):
            return self.prevSet == other.prevSet and self.tok == other.tok
        elif isinstance(other, str):
            return other == self.value
        else:
            assert 0

    @property
    def value(self):
        return self.tok.token_t

    @property
    def character(self):
        return self.tok.token_t

    def __hash__(self):
        return hash((self.__class__, self.character, self.value, self.prevSet))

    def __call__(self, *args, **kwargs):
        return self.value


class Literal(TerminalParseTreeNode):

    def __init__(self, prev: FrozenSet[ParseTreeNode],
                 tok: 'ctoken.CToken', type: Optional['c_type.Type']):
        super().__init__(prev, tok)
        self.type: Optional[c_type.Type] = type

    def __str__(self):
        return str(self.type) + ' ' + ascii(self.value)

    def __eq__(self, other):
        assert isinstance(other, Literal)
        return (self.character, self.prevSet, self.value, self.type) == \
               (other.character, other.prevSet, other.value, other.type)

    @property
    def character(self):
        return 'constant'

    def __hash__(self):
        return hash((self.__class__, self.character, self.value, self.prevSet, self.type))

    def __call__(self, *args, **kwargs):
        return self.value, self.type


class IntegerLiteral(Literal):
    """
    :type __value: int
    """

    def __init__(self, prev: 'FrozenSet[ParseTreeNode]',
                 tok: 'ctoken.CToken', type: 'c_type.Type'):
        super(IntegerLiteral, self).__init__(prev, tok, type)
        self.__value = self.tok.data[0]
        assert isinstance(self.__value, int)

    @property
    def value(self) -> int:
        return self.__value

    def __str__(self):
        return '<{0}>{1}</{0}>'.format('int', repr(self.value))

    def visit(self, env: 'scopes.DeclScope'):
        assert isinstance(self.value, int)
        return ast.IntegerLiteral(self.value,
                                  c_type.QualifiedType(self.type),
                                  env)


class StringLiteral(Literal):
    """
    :type __value:  str
    :type __length: int
    """

    def __init__(self, prev: 'FrozenSet[ParseTreeNode]', tok: 'ctoken.CToken'):
        self.__value = ''.join(tok.data)
        assert isinstance(self.__value, str)
        self.__length = len(self.__value) + 1
        t = c_type.Char()
        t = c_type.QualifiedType(t)
        t = c_type.ConstantArrayType(t, self.__length)
        super(StringLiteral, self).__init__(prev, tok, t)

    @property
    def value(self) -> str:
        return self.__value

    def __str__(self):
        return '<{0}>{1}</{0}>'.format('string', repr(self.value))

    def visit(self, env: 'scopes.DeclScope'):
        assert isinstance(self.value, str)
        return ast.StringLiteral(self.value,
                                 c_type.QualifiedType(self.type),
                                 env)


class FloatingLiteral(Literal):
    """
    :type __value: float
    """

    def __init__(self, prev: 'FrozenSet[ParseTreeNode]',
                 tok: 'ctoken.CToken', type: 'c_type.Type'):
        super(FloatingLiteral, self).__init__(prev, tok, type)
        self.__value = self.tok.data[0]
        assert isinstance(self.__value, float)

    @property
    def value(self) -> float:
        return self.__value

    def __str__(self):
        return '<{0}>{1}</{0}>'.format('float', repr(self.value))

    def __call__(self, *args, **kwargs):
        return self.value

    def visit(self, env: 'scopes.DeclScope'):
        assert isinstance(self.value, float)
        return ast.FloatingLiteral(self.value,
                                   True,
                                   c_type.QualifiedType(self.type),
                                   env)


class IdentifierParseNode(Literal):
    """
    :type __value:    str
    """

    def __init__(self, prev: 'FrozenSet[ParseTreeNode]', tok: 'ctoken.CToken'):
        super(IdentifierParseNode, self).__init__(prev, tok, type=None)
        self.__value = self.tok.data
        assert isinstance(self.__value, str)

    @property
    def value(self) -> str:
        return self.__value

    def __str__(self):
        return '<{0}>{1}</{0}>'.format('Identifier', repr(self.value))

    @property
    def character(self):
        return 'identifier'

    def __call__(self, *args, **kwargs):
        return self.value

    def visit(self, env: 'scopes.DeclScope'):
        try:
            return ast.DeclRefExpr(env.getValueDecl(self.value), env)
        except KeyError as e:
            try:
                return ast.DeclRefExpr(env.getFunctionDecl(self.value), env)
            except KeyError as e:
                raise KeyError("{}: '{}' is not declared.".format(self.tok.position, self.value))


from Lexer import tokenizer


def ConstantAndIdentifierNodeFactory(tok: 'ctoken.CToken', prev: FrozenSet[ParseTreeNode]):
    if tok.token_t == tokenizer.identifierTag:
        assert isinstance(tok.data, str)
        return IdentifierParseNode(prev, tok)

    if tok.token_t == tokenizer.constantTag:
        assert isinstance(tok.data, tuple)
        if all(isinstance(x, str) for x in tok.data):
            return StringLiteral(prev, tok)
        assert len(tok.data) == 2
        type = tok.data[1]
        assert isinstance(type, c_type.Type)
        if type.isIntegerType():
            return IntegerLiteral(prev, tok, type)
        elif type.isFloatingType():
            return FloatingLiteral(prev, tok, type)
    raise NotImplementedError()
