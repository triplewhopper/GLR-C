import typing
from typing import cast, Optional, Callable, Generator, Generic, TypeVar, List, Union, Tuple
import instructions
from Lexer import ctoken
from AST import c_type, scopes
from enum import IntFlag, auto, Enum as PyEnum

T = TypeVar('T')


def expand(t: 'c_type.StructType', name: str) -> Generator[
    Tuple['c_type.Type', int, str], None, None]:
    for member in t.decl.classScope.members:
        dt = member.declType()
        if isinstance(dt, (c_type.PrimitiveType, c_type.Pointer)):
            yield dt, member.offset, '{}.{}'.format(name, member.name)

        elif isinstance(dt, c_type.ConstantArrayType):
            for i in range(dt.length):
                yield dt.elementType(), \
                      member.offset + i * dt.elementType.width, \
                      '{}.{}[{}]'.format(name, member.name, i)

        elif isinstance(dt, c_type.StructType):
            yield from expand(dt, '{}.{}'.format(name, member.name))
        else:
            assert 0


def consumeValue(t: 'c_type.Type', cmd: list):
    assert isinstance(t, c_type.Type)
    if isinstance(t, c_type.Void):
        return
    if t.isScalarType():
        cmd.append('pop')
        return
    assert not isinstance(t, c_type.ArrayType)
    if isinstance(t, c_type.StructType):
        for _, _, _ in expand(t, ''):
            cmd.append('pop')
        return
    assert 0


class Redeclarable(Generic[T]):
    """
    :type __prev: None|Redeclarable[T]
    :type __next: None|Redeclarable[T]
    """

    def __init__(self,
                 prev: Optional['Redeclarable[T]'] = None,
                 next: Optional['Redeclarable[T]'] = None):
        self.__prev = prev
        self.__next = next

    def getPrev(self):
        return self.__prev

    def getNext(self):
        return self.__next

    def setPrev(self, prev: 'Redeclarable[T]'):
        self.__prev = prev
        return self

    def setNext(self, next: 'Redeclarable[T]'):
        self.__next = next
        return self

    def getFirst(self):
        p = self
        while p.__prev is not None:
            p = p.__prev
        return p

    def getLast(self):
        p = self
        while p.__next is not None:
            p = p.__next
        return p
    # @property
    # def all(self):
    #     return self._all
    #
    # @property
    # def prev(self):
    #     return self._all[self._pos - 1]
    # @prev.setter
    # def prev
    #
    # @property
    # def isLatest(self):
    #     return self._pos == len(self._all) - 1
    #
    # @property
    # def isFirst(self):
    #     return self._pos == 0
    #
    # def getFirst(self):
    #     return self._all[0]
    #
    # def getLatest(self):
    #     return self._all[-1]


class Decl:
    """
    :type ID: int
    """
    counter = 0

    def __init__(self):
        self.ID = Decl.counter
        Decl.counter += 1

    def __str__(self):
        raise NotImplementedError()


class NamedDecl(Decl):
    """
    :type __name: str
    """

    def __init__(self, name: str):
        super().__init__()
        assert isinstance(name, str)
        self.__name = name

    @property
    def name(self):
        return self.__name

    def __str__(self):
        raise NotImplementedError()


class FunctionDecl(NamedDecl):
    def __init__(self, name: str, fnType: 'c_type.FunctionProtoType', stmt: Optional['CompoundStmt'] = None):
        super().__init__(name)
        assert isinstance(fnType, c_type.FunctionProtoType)
        if stmt is not None:
            assert isinstance(stmt, CompoundStmt)
        self.__fnType = c_type.QualifiedType(fnType)
        self.__stmt = stmt
        self.__entrance = []

    @property
    def stmt(self):
        return self.__stmt

    @property
    def entrance(self):
        return self.__entrance

    @stmt.setter
    def stmt(self, stmt: 'CompoundStmt'):
        assert isinstance(stmt, CompoundStmt)
        assert self.__stmt is None
        self.__stmt = stmt

    @property
    def isDefinition(self) -> bool:
        return self.__stmt is not None

    @property
    def declType(self) -> 'c_type.QualifiedType':
        return self.__fnType

    def gen(self, cmd: list):
        fn: c_type.FunctionProtoType = self.__fnType()
        sco: scopes.FnScope = self.stmt.scope
        cmd.append(['.func', self.name, self.stmt.scope.offset])
        for decl in fn.scope.parameterDecls:
            dt = decl.declType()
            if isinstance(dt, (c_type.PrimitiveType, c_type.Pointer)):
                cmd.append(instructions.LoadInstantly(
                    c_type.Int64(),
                    sco.getValueDecl(decl.name).offset,
                    '&{}'.format(decl.name)))
                cmd.append('add bp')
                cmd.append('store')
            else:
                assert isinstance(dt, c_type.StructType)
                for type, offset, name in reversed(list(expand(dt, decl.name))):
                    cmd.append(instructions.LoadInstantly(c_type.Int64(), offset, '&{}'.format(name)))
                    cmd.append('add bp')
                    cmd.append('store')

        self.__stmt.gen1(cmd)
        cmd.append('ret')

    def __str__(self):
        return '<{0} name="{4}" ID="{1}">{2}{3}</{0}>' \
            .format(self.__class__.__name__, self.ID, self.__fnType, self.__stmt, self.name)


#
# class FnPrototypeDecl(Decl, Redeclarable['FnPrototypeDecl']):
#     def __init__(self, fnType: 'c_type.QualifiedType'):
#         super().__init__()
#         assert isinstance(fnType(), c_type.FunctionProtoType)
#         self.__fnType = fnType
#
#     def __str__(self):
#         return '<{0} ID="{1}">{2}</{0}>' \
#             .format(self.__class__.__name__, self.ID, self.__fnType)
#

class ValueDecl(NamedDecl):
    """
    :type __declType: QualifiedType
    :type __offset:     int
    """

    # :type scope: AST.environment.Scope
    # __slots__ = ('__declType', '__offset')

    # def __init__(self, name: str, qualifiedType, env):
    def __init__(self, name: str,
                 qualifiedType: 'c_type.QualifiedType', isGlobal: bool = False):
        # """
        # :type name:             str
        # :type qualifiedType:    QualifiedType
        # :type env:              AST.environment.Scope
        # """
        super().__init__(name)
        assert isinstance(qualifiedType, c_type.QualifiedType)
        self.__offset = None
        self.__declType = qualifiedType
        self.__isGlobal = isGlobal
        # self.scope = env
        # self.scope.insertValueDecl(name, self, self.declType)

    @property
    def isGlobal(self):
        return self.__isGlobal

    @property
    def offset(self):
        assert self.__offset is not None
        return self.__offset

    @offset.setter
    def offset(self, value: int):
        assert isinstance(value, int)
        assert self.__offset is None
        self.__offset = value

    @property
    def declType(self):
        return self.__declType

    # def setType(self, newType):
    #     assert isinstance(newType, QualifiedType)
    #     self.__declType = newType
    #     return self

    # def getOffset(self):
    #     return self.offset
    #
    # def setOffset(self, offset: int):
    #     assert isinstance(offset, int)
    #     self.offset = offset

    def __str__(self):
        return '<{0} name="{1}">' \
               '<id>{id}</id>' \
               '<offset>{offset}</offset>' \
               '<width>{width}</width>' \
               '<declType>{declType}</declType>' \
               '</{0}>' \
            .format(self.__class__.__name__,
                    self.name,
                    id=self.ID,
                    declType=self.__declType,
                    offset=self.__offset,
                    width=self.__declType.width)


class ParamVarDecl(ValueDecl):
    def __init__(self, index: int, qualifiedType: 'c_type.QualifiedType', name: str = ''):
        super().__init__(name, qualifiedType)
        self.__index = index

    @property
    def index(self) -> int:
        return self.__index

    def __str__(self):
        if self.name:
            return '<{0} name="{1}" index="{2}">{3}</{0}>' \
                .format(self.__class__.__name__,
                        self.name,
                        self.index,
                        self.declType)

        return '<{0} index="{1}">{2}</{0}>' \
            .format(self.__class__.__name__, self.index, self.declType)


class TagDecl(NamedDecl, Redeclarable['TagDecl']):
    """
    :type __classScope:       None|scopes.TypedefDeclExcludedScope
    :type __isDefinition:     bool
    :type __isBeingDefined:   None|bool
    """

    # :type
    # tagKind: TagDecl.TagKind
    # class TagKind(IntFlag):
    #     TK_struct = auto()
    #     TK_union = auto()
    #     TK_enum = auto()
    #     TK_class = auto()

    # def __init__(self, tk: TagKind, name: str, scope, isDefinition: bool = False, isBeingDefined: bool = None):
    #     NamedDecl.__init__(self, name)
    #     Redeclarable.__init__(self, None)
    #     assert isinstance(isDefinition, bool)
    #     if isDefinition:
    #         assert isinstance(isBeingDefined, bool)
    #     else:
    #         assert isBeingDefined is None
    #
    #     self.tagKind = TagDecl.TagKind(tk)
    #     self._scope = scope
    #     self.isDefinition = isDefinition
    #     self.isBeingDefined = isBeingDefined
    #     self.declType = None

    def __init__(self,
                 name: str,
                 scope: Optional['scopes.TypedefDeclExcludedScope'] = None,
                 isDefinition: bool = False):
        NamedDecl.__init__(self, name)
        Redeclarable.__init__(self)
        assert isinstance(isDefinition, bool)
        if isDefinition:
            self.__isBeingDefined = True
        else:
            self.__isBeingDefined = None

        self.__classScope = scope
        self.__isDefinition = isDefinition
        self._declType = None

    @property
    def declType(self):
        assert self._declType is not None
        return self._declType

    @property
    def classScope(self):
        return self.__classScope

    @property
    def isDefinition(self):
        return self.__isDefinition

    @property
    def isBeingDefined(self):
        assert self.__isDefinition is True
        return self.__isBeingDefined

    @isBeingDefined.setter
    def isBeingDefined(self, val: bool):
        assert val is False
        assert self.__isDefinition is True
        assert self.__isBeingDefined is True
        self.__isBeingDefined = False

    def __eq__(self, other):
        assert self.__class__ == other.__class__
        # if self.tagKind != other.tagKind:
        #     return False
        if self.isDefinition != other.isDefinition:
            return False
        if not self.classScope == other.classScope:
            return False
        return True

    def __str__(self):
        raise NotImplementedError()


class RecordDecl(TagDecl):
    __slots__ = ()

    # def __init__(self, name: str, classScope: Optional['environment.Scope'] = None, isDefinition: bool = False):
    def __init__(self, name: str, classScope: Optional['scopes.StructScope'] = None,
                 isDefinition: bool = False):
        super().__init__(c_type.StructType.newTagName(name), classScope, isDefinition)
        self._declType = c_type.StructType(self, self.name)

    @property
    def classScope(self) -> 'scopes.StructScope':
        return cast(scopes.StructScope, super().classScope)

    @property
    def declType(self) -> 'c_type.StructType':
        assert self._declType is not None
        return self._declType

    def __str__(self):
        assert self.isBeingDefined is False
        return '<{0} tag="{1}" isDefinition="{2}">' \
               '<id>{id}</id>' \
               '<prev>{prev}</prev>' \
               '<scope>{scope}</scope>' \
               '</{0}>' \
            .format(self.__class__.__name__, self.name,
                    self.isDefinition,
                    id=self.ID,
                    prev=self.getPrev().ID if self.getPrev() else -1,
                    scope=self.classScope)


class TypedefDecl(NamedDecl):
    """
    :type __underlyingType: c_type.QualifiedType
    """

    # def __init__(self, name, underlyingType, env):
    def __init__(self,
                 name: str,
                 underlyingType: 'c_type.QualifiedType'):
        # """
        # :type name:             str
        # :type underlyingType:   QualifiedType
        # :type env:              AST.environment.Scope
        # """
        super().__init__(name)
        assert isinstance(underlyingType, c_type.QualifiedType)
        # self.name = name
        self.__underlyingType = underlyingType
        # self.scope = env
        # self.scope.insertTypedefDecl(name, self, self.underlyingType)

    def __str__(self):
        return '<{0} name="{1}">' \
               '<id>{id}</id>' \
               '<type>{type}</type>' \
               '</{0}>' \
            .format(self.__class__.__name__,
                    self.name,
                    id=self.ID,
                    type=self.underlyingType
                    )

    @property
    def underlyingType(self):
        return self.__underlyingType


#
# class Stmt:
#     def __init__(self):
#         self.scope = None
#
#

class Stmt(Generic[T]):
    def __init__(self, env):
        self.__scope: T = env

    @property
    def scope(self) -> T:
        return self.__scope

    # def gen(self) -> list:
    #     raise NotImplementedError(self.__class__.__name__)
    #     # yield

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        raise NotImplementedError(self.__class__.__name__)


def getScalarExpression(expr: 'Expr', env: 'scopes.ControlScope'):
    assert isinstance(expr, Expr)
    if not expr.type().isScalarType():
        if not isinstance(expr.type(), c_type.ArrayType):
            assert 0 and "要求括号中的表达式为Scalar Type"
        else:
            expr = ImplicitCastExpr(
                CastExpr.CastKind.ArrayToPointerDecayed,
                c_type.QPointer(expr.type().elementType),
                expr, env)

    return expr


class IfStmt(Stmt['scope.IfScope']):
    """
    :type expr:     Expr
    :type stmt:     Stmt
    :type elseStmt: None|Stmt
    """
    __slots__ = ['expr', 'stmt', 'elseStmt']

    def __init__(self,
                 env: 'scopes.IfScope',
                 expr: 'Expr',
                 stmt: Stmt,
                 elseStmt: Optional[Stmt] = None):
        super().__init__(env)
        assert isinstance(expr, Expr)
        assert isinstance(stmt, Stmt)
        if elseStmt is not None:
            assert isinstance(elseStmt, Stmt)
        self.expr = getScalarExpression(expr, env)
        self.stmt = stmt
        self.elseStmt = elseStmt

    def gen1(self,
             cmd: list,
             continuePos: Optional[bool] = None,
             breakPos: Optional[bool] = None):
        endif = ['.end if']
        el = ['.else']

        if self.elseStmt:
            cmd.append('.if')
            self.expr.rvalue1(cmd)
            cmd.append(('jz', el))
            self.stmt.gen1(cmd, continuePos, breakPos)
            cmd.append(('jmp', endif))
            cmd.append(el)
            self.elseStmt.gen1(cmd, continuePos, breakPos)
            cmd.append(endif)

        else:
            cmd.append('.if')
            self.expr.rvalue1(cmd)
            cmd.append(('jz', endif))
            self.stmt.gen1(cmd, continuePos, breakPos)
            cmd.append(endif)

    def __str__(self):
        return '<{0}>{1}{2}{3}</{0}>' \
            .format(self.__class__.__name__, self.expr, self.stmt, self.elseStmt or '')


class ForStmt(Stmt['scope.ForScope']):
    def __init__(self, env: 'scopes.ForScope',
                 e1: Optional['Expr'], e2: Optional['Expr'], e3: Optional['Expr'],
                 stmt: Stmt):
        super().__init__(env)
        self.e1 = e1
        self.e2 = e2
        self.e3 = e3
        self.stmt = stmt

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        cond = ['.cond']
        next = ['.next']
        endFor = ['.end for']
        cmd.append('.for')
        if self.e1 is not None:
            self.e1.rvalue1(cmd)
            consumeValue(self.e1.type(), cmd)

        cmd.append(cond)

        if self.e2 is not None:
            self.e2.rvalue1(cmd)

        else:
            cmd.append(instructions.LoadInstantly(c_type.Int32(), 1))

        cmd.append(('jz', endFor))
        self.stmt.gen1(cmd, next, endFor)
        cmd.append(next)
        if self.e3 is not None:
            self.e3.rvalue1(cmd)
            consumeValue(self.e3.type(), cmd)
        cmd.append(('jmp', cond))
        cmd.append(endFor)

    def __str__(self):
        e1 = '<e1/>'
        e2 = '<e2/>'
        e3 = '<e3/>'
        if self.e1 is not None:
            e1 = '<e1>{}</e1>'.format(self.e1)
        if self.e2 is not None:
            e2 = '<e2>{}</e2>'.format(self.e2)
        if self.e3 is not None:
            e3 = '<e3>{}</e3>'.format(self.e3)

        return '<{0}>{1}{2}{3}{4}</{0}>'.format(self.__class__.__name__, e1, e2, e3, self.stmt)


class WhileStmt(Stmt['scope.WhileScope']):
    def __init__(self, env: 'scopes.WhileScope', expr: 'Expr', stmt: Stmt):
        super().__init__(env)
        assert isinstance(expr, Expr)
        assert isinstance(stmt, Stmt)
        self.expr = getScalarExpression(expr, env)
        self.stmt = stmt

    # def gen(self):
    #     e = self.expr.gen()
    #     s = self.stmt.gen()
    #     return ['while', e, 'jz', s, 'jmp', 'end while']

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        w = ['.while']
        endwhile = ['.end while']

        cmd.append(w)
        self.expr.rvalue1(cmd)
        cmd.append(('jz', endwhile))
        self.stmt.gen1(cmd, w, endwhile)
        cmd.append(('jmp', w))
        cmd.append(endwhile)

    def __str__(self):
        return '<{0}>{1}{2}</{0}>'.format(self.__class__.__name__, self.expr, self.stmt)


class DoStmt(Stmt):
    def __init__(self, env: 'scopes.DoScope', stmt: Stmt, expr: 'Expr'):
        super().__init__(env)
        self.stmt = stmt
        self.expr = expr

    # def gen(self):
    #     e = self.expr.gen()
    #     s = self.stmt.gen()
    #     return ['do', s, 'while', e, 'jz 2', 'jmp -5' 'end while']

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        do = ['.do']
        enddo = ['.end do while']

        cmd.append(do)
        self.stmt.gen1(cmd, do, enddo)
        self.expr.rvalue1(cmd)
        cmd.append(('jz', enddo))
        cmd.append(('jmp', do))
        cmd.append(enddo)

    def __str__(self):
        return '<{0}>{1}{2}</{0}>'.format(self.__class__.__name__, self.stmt, self.expr)


class ReturnStmt(Stmt):
    def __init__(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]', expr: Optional['Expr'] = None):
        super().__init__(env)
        self.expr = expr

        if self.expr is not None:
            self.expr = tryToDeduceTypeForAssignment(env.fnFather.fnType.returnType, self.expr, env)
            if env.fnFather.fnType.returnType != self.expr.type:
                if isinstance(env.fnFather.fnType.returnType(), c_type.Void):
                    raise RuntimeError("void function '{}' should not return a value".
                                       format(env.fnFather.tok.data))
                else:
                    raise RuntimeError("函数{}的返回值类型为{},但是这个return的表达式类型为{}"
                                       .format(env.fnFather.tok.data, env.fnFather.fnType.returnType, self.expr.type))
        elif not isinstance(env.fnFather.fnType.returnType(), c_type.Void):
            raise RuntimeError("non-void function '{}' should return a value"
                               .format(env.fnFather.tok.data))

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        if self.expr is not None:
            self.expr.rvalue1(cmd)

        cmd.append('ret')

    def __str__(self):
        if self.expr is None:
            return '<{0}/>'.format(self.__class__.__name__)
        return '<{0}>{1}</{0}>'.format(self.__class__.__name__, self.expr)


class SwitchStmt(Stmt):
    def __init__(self, env: 'scopes.SwitchScope',
                 expr: 'Expr', stmt: Stmt):
        super().__init__(env)
        assert isinstance(expr, Expr)
        assert isinstance(stmt, Stmt)
        assert expr.type().isIntegerType()
        self.expr = expr
        self.stmt = stmt

    @property
    def scope(self) -> 'scopes.SwitchScope':
        return self.scope

    def __str__(self):
        return '<{0}>{1}{2}</{0}>'.format(self.__class__.__name__, self.expr, self.stmt)

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        # switch = ['switch']
        endswitch = ['.end switch']
        cmd.append('.switch')
        self.expr.rvalue1(cmd)
        e = self.expr.type()
        cases = self.scope.cases()
        for v, stmt in cases.items():
            cmd.append('duplicate')
            if e.width >= stmt.constexpr.type.width:
                if e != stmt.constexpr.type():
                    cmd.append(instructions.LoadInstantly(stmt.constexpr.type(), v, 'case'))
                    cmd.append(instructions.Cast(stmt.constexpr.type(), e))

            elif e.width < stmt.constexpr.type.width:
                cmd.append(instructions.Cast(e, stmt.constexpr.type()))
                cmd.append(instructions.LoadInstantly(stmt.constexpr.type(), v, 'case'))

            cmd.append(('binary', '-'))
            cmd.append(('jz', stmt.guide))

        cmd.append('pop')
        cmd.append(('jmp', self.scope.default.guide))
        self.stmt.gen1(cmd, continuePos, endswitch)


class SwitchCase(Stmt):
    @property
    def scope(self) -> 'scopes.SwitchScope':
        return self.scope


class CaseStmt(SwitchCase):
    def __init__(self, env: 'scopes.SwitchScope',
                 constexpr: 'Expr', stmt: Stmt):
        super().__init__(env)
        assert isinstance(constexpr, Expr)
        assert isinstance(stmt, Stmt)
        assert constexpr.isIntegerConstantExpr()
        self.constexpr = constexpr
        self.stmt = stmt
        self.scope.insertCase(self)
        self.guide = ['case {}'.format(self.constexpr.value)]

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        cmd.append(self.guide)
        self.stmt.gen1(cmd, continuePos, breakPos)

    def __str__(self):
        return '<{0} case="{1}">{2}</{0}>'.format(self.__class__.__name__, self.constexpr.value, self.stmt)


class DefaultStmt(SwitchCase):
    def __init__(self, env: 'scopes.SwitchScope', stmt: Stmt):
        super().__init__(env)
        assert isinstance(env, scopes.SwitchScope)
        self.stmt = stmt
        self.scope.default = self
        self.guide = ['default']

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        cmd.append(self.guide)
        self.stmt.gen1(cmd, continuePos, breakPos)

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.__class__.__name__, self.stmt)


class LabeledStmt(Stmt):
    def __init__(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]',
                 label: str, stmt: Stmt):
        super().__init__(env)
        assert isinstance(label, str)
        assert isinstance(stmt, Stmt)
        self.label = label
        self.guide = [label]
        self.stmt = stmt

    @property
    def scope(self) -> 'Union[scopes.FnScope,scopes.NaiveScope]':
        return super().scope

    def __str__(self):
        return '<{0} label="{1}">{2}</{0}>'.format(self.__class__.__name__, self.label, self.stmt)

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        cmd.append(self.guide)
        self.stmt.gen1(cmd, continuePos, breakPos)


class JumpStmt(Stmt):
    def __init__(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]', tok: 'ctoken.CToken'):
        super().__init__(env)
        assert isinstance(tok, ctoken.CToken)
        self.tok = tok
        self.label = tok.data
        assert isinstance(self.label, str)
        # self.scope.fnFather.getStmtAssociatedWith(self.label).label

    @property
    def scope(self) -> 'Union[scopes.FnScope,scopes.NaiveScope]':
        return super().scope

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        try:
            cmd.append(('jmp', self.scope.fnFather.getStmtAssociatedWith(self.label).guide))
        except KeyError as e:
            raise RuntimeError('{}: 没有名为{}的标签！'.format(self.tok.position, self.label))


class BreakStmt(Stmt):
    def __init__(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]'):
        assert env.breakFather is not None
        super().__init__(env)

    def __str__(self):
        return '<break />'

    # def gen(self):
    #     assert AST.environment.ScopeFlags.BreakScope in self.scope.flags
    #     return ['break']

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        assert self.scope.breakFather is not None
        assert breakPos is not None
        cmd.append(('break', breakPos))


class ContinueStmt(Stmt):
    def __init__(self, env: 'Union[scopes.FnScope,scopes.NaiveScope]'):
        assert env.continueFather is not None
        super().__init__(env)

    def __str__(self):
        return '<continue />'

    # def gen(self):
    #     assert AST.environment.ScopeFlags.ContinueScope in self.scope.flags
    #     return ['continue']

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        assert self.scope.isContinueScope()
        assert continuePos is not None
        cmd.append(('continue', continuePos))


class CompoundStmt(Stmt):
    """
    :type statements: list[Stmt]
    """

    def __init__(self, env: 'scopes.NaiveScope', statements: List[Stmt]):
        super().__init__(env)
        assert isinstance(statements, list)

        assert all(isinstance(x, Stmt) for x in statements)
        self.statements = statements

    # def gen(self):
    #     res = []
    #     for s in self.statements:
    #         res.extend(s.gen())
    #     return res

    def gen1(self, cmd: list, continuePos=None, breakPos=None):
        for s in self.statements:
            s.gen1(cmd, continuePos, breakPos)

    def __str__(self):
        return '<{0}>{1}{2}</{0}>' \
            .format(self.__class__.__name__, self.scope, ''.join(map(str, self.statements)))


class EvaluateResult:
    """
    :type __value:        None|float|int
    :type __type:         QualifiedType
    :type __isLvalue:     None|bool
    __value不为None的话,说明其所属的表达式为编译期常量

    """

    def __init__(self, type: 'c_type.QualifiedType',
                 value: Optional[typing.Union[int, float]] = None,
                 isLvalue: bool = False,
                 ):  # address: Optional[int] = None

        assert isinstance(type, c_type.QualifiedType)
        if value is not None:
            assert isinstance(value, (int, float))

        # if address is not None:
        #     assert isinstance(address, int) and address >= 0

        assert isinstance(isLvalue, bool)
        self.__type = type
        self.__isLvalue = isLvalue
        # self.__address = address
        self.__value = None
        if value is not None:
            if self.__type().isFloatingType():
                self.__value = float(value)

            elif isinstance(self.__type(), c_type.Pointer):
                assert value >= 0 and "指针类型不能为负值!"
                self.__value = int(value)
                if self.__value < 0:
                    self.__value += 2 ** (8 * self.__type.width)

            elif self.__type().isIntegerType():
                self.__value = int(value)
                if self.__type().isUnsignedType() and self.__value < 0:
                    self.__value += 2 ** (8 * self.__type.width)

            else:
                assert 0 and "非法类型"

    def __str__(self):
        return '<{0} value="{value}" isLvalue="{1}">' \
               '<type>{type}</type>' \
               '</{0}>'.format(self.__class__.__name__,
                               self.__isLvalue,
                               value=self.__value,
                               type=self.__type)

    def replace(self, type=None, value=None, isLvalue=None):
        return EvaluateResult(type or self.type,
                              value or self.value,
                              isLvalue or self.isLvalue)
        # address or self.address)

    @property
    def value(self):
        # assert self.__value is not None
        return self.__value

    @property
    def type(self):
        # assert self.__type is not None
        return self.__type

    @property
    def isLvalue(self):
        return self.__isLvalue

    @property
    def isConstant(self):
        return self.value is not None


class DeclStmt:
    pass


class Expr(Stmt):
    """
    :type _result: None|EvaluateResult
    """
    intTotal = 0
    floatTotal = 0

    def __init__(self, env: 'scopes.DeclScope'):
        super().__init__(env)
        self._result = None

    @property
    def result(self):
        if self._result is None:
            self._deduceType()
            # if self.isConstant:
            #     self._evaluateConstantExpr()
        return self._result

    @property
    def type(self):
        return self.result.type

    @property
    def value(self):
        return self.result.value

    @property
    def isConstant(self):
        return self.result.isConstant

    def lvalue1(self, cmd: list):
        raise NotImplementedError(self.__class__.__name__)

    def rvalue1(self, cmd: list):
        raise NotImplementedError(self.__class__.__name__)

    def isLvalue(self) -> bool:
        assert type(self) != Expr
        return self.result.isLvalue

    def isModifiableLvalue(self) -> bool:
        assert type(self) != Expr
        return False

    def isIntegerConstantExpr(self) -> bool:
        assert type(self) != Expr
        return False

    def _deduceType(self) -> EvaluateResult:  # 1.此method会更新self.result; 2.@cached实现缓存.
        raise NotImplementedError(self.__class__.__name__)


class ExprStmt(Stmt):
    """
    :type expr: None|Expr
    """

    def __init__(self, env: 'scopes.DeclScope', expr=None):
        super().__init__(env)
        self.expr = expr

    # def gen(self):
    #     return self.expr.rvalue()
    # yield

    def gen1(self, cmd: list, loopBegin=None, loopEnd=None, endSwitch=None, endFunction=None):
        self.expr.rvalue1(cmd)
        consumeValue(self.expr.type(), cmd)

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.__class__.__name__, self.expr)


class IntegerLiteral(Expr):

    def __init__(self, v: int, type: 'c_type.QualifiedType', env):
        assert isinstance(v, int)
        assert isinstance(type, c_type.QualifiedType)
        super().__init__(env)
        self._result = EvaluateResult(type, v)

    def rvalue1(self, cmd: list):
        cmd.append(instructions.LoadInstantly(self.type(), self.value))

    def isIntegerConstantExpr(self):
        return True

    def __str__(self):
        return '<{0} value="{value}">{1}</{0}>' \
            .format(self.__class__.__name__, self.result, value=self.value)


class CharacterLiteral(IntegerLiteral):
    pass


class FloatingLiteral(Expr):
    """
    :type isExact:  bool
    """

    def __init__(self, v: float, isExact: bool, type: 'c_type.QualifiedType', env: 'scopes.DeclScope'):
        assert isinstance(v, float)
        assert isinstance(isExact, bool)
        assert isinstance(type, c_type.QualifiedType)
        super().__init__(env)

        self._result = EvaluateResult(type, v)
        self.__isExact = isExact

    def rvalue1(self, cmd: list):
        cmd.append(instructions.LoadInstantly(self.type(), self.value))

    def __str__(self):
        return '<{0} value="{value}">{1}</{0}>' \
            .format(self.__class__.__name__, self.result, value=self.value)


class StringLiteral(Expr):

    def __init__(self, v: str, type: 'c_type.QualifiedType', env):
        assert isinstance(v, str)
        assert isinstance(type, c_type.QualifiedType)
        assert isinstance(env, scopes.IFathers)
        super().__init__(env)
        addr = env.globalFather.insertConstantString(v, type)
        self._result = EvaluateResult(type, addr, isLvalue=True)
        self.string: str = v

    def lvalue1(self, cmd: list):
        cmd.append(instructions.LoadInstantly(c_type.Int64(), self.value, ' str {}'.format(repr(self.string))))

    def isLvalue(self):
        return True

    def __str__(self):
        return '<{0} address="{1}" length="{2}">{3}</{0}>' \
            .format(self.__class__.__name__, self.value, self.type.width, repr(self.string))


class LvalueToRvalueExpr(Expr):
    def __init__(self, expr: Expr, env: 'scopes.DeclScope'):
        super().__init__(env)
        assert isinstance(expr, Expr)
        self.expr = expr
        self._result = EvaluateResult(c_type.QualifiedType(expr.type()), expr.value)

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.__class__.__name__, self.expr)

    # def rvalue(self):
    #     return self.expr.rvalue()

    def rvalue1(self, cmd: list):
        self.expr.rvalue1(cmd)


class DeclRefExpr(Expr):
    """
    :type d: ValueDecl|FunctionDecl
    """

    def __init__(self, d: typing.Union[ValueDecl, FunctionDecl], env: 'scopes.DeclScope'):
        super().__init__(env)
        assert isinstance(d, (ValueDecl, FunctionDecl))
        self.d = d
        self._result = EvaluateResult(d.declType, isLvalue=True)
        # FIXME: 函数类型总是constant的（函数指针就不一定了), 添加函数支持时要注意这一点。

    def __str__(self):
        return '<{0} name="{1}" declID="{2}">{3}</{0}>' \
            .format(self.__class__.__name__, self.d.name, self.d.ID, self.type)

    @property
    def decl(self):
        return self.d

    @decl.setter
    def decl(self, newD: NamedDecl):
        assert isinstance(newD, NamedDecl)
        self.d = newD

    def isModifiableLvalue(self):
        if isinstance(self.type(), (c_type.ArrayType, c_type.FunctionProtoType)):
            return False
        if self.type().isIncompleteType():
            return False
        if self.type.isConstQualified():
            return False
        if isinstance(self.type(), c_type.StructType):
            if any(x.isConstQualified() for x in self.d.scope.types.values()):
                return False
        # FIXME: 添加union支持的时候小心与typing.Union的重名问题
        return True

    def lvalue1(self, cmd: list):
        cmd.append(instructions.LoadInstantly(c_type.Int64(), self.d.offset, '&{}'.format(self.d.name)))
        if not self.decl.isGlobal:
            cmd.append('add bp')

    def rvalue1(self, cmd: list):
        t = self.type()
        if t.isFunctionType():
            cmd.append(instructions.LoadInstantly(
                c_type.Int64(),
                cast(FunctionDecl, self.d).entrance,
                'function {}'.format(self.d.name)))
            return

        if isinstance(t, c_type.StructType):
            cmd.append('// rvalue of {}'.format(self.decl.name))
            for type, offset, name in expand(t, self.decl.name):
                cmd.append(instructions.LoadInstantly(c_type.Int64(), offset, '&{}'.format(name)))
                if not self.decl.isGlobal:
                    cmd.append('add bp')
                cmd.append(instructions.LoadTop(type, 'rvalue of {}'.format(name)))
                # cmd.append(instructions.LoadFrom(type, offset, 'rvalue of {}'.format(name)))

            return

        self.lvalue1(cmd)
        cmd.append(instructions.LoadTop(self.type(), 'rvalue of {}'.format(self.decl.name)))

    def isLvalue(self):
        return True

    def isIntegerConstantExpr(self):
        return self.isConstant and self.type().isIntegerType()


class InitListExpr(Expr):
    def __init__(self, expressions: List[Expr], type: 'c_type.QualifiedType', env):
        super().__init__(env)
        assert isinstance(expressions, list)
        assert all(isinstance(expr, Expr) for expr in expressions)
        self.expressions = expressions


class UnaryOperator(Expr):
    def __init__(self, expr: Expr, op: str, env: 'scopes.DeclScope', isPostfix: bool = False):
        super().__init__(env)
        assert isinstance(expr, Expr)
        self.expr = expr
        self.isPostfix = isPostfix
        self.op = op
        if isinstance(self.expr.type(), c_type.ArrayType):
            if self.op != '&':
                self.expr = ImplicitCastExpr(CastExpr.CastKind.ArrayToPointerDecayed,
                                             c_type.QPointer(self.expr.type().elementType),
                                             self.expr, self.scope)
        else:
            if self.op not in ('&', '++', '--') and self.expr.isLvalue():
                self.expr = LvalueToRvalueExpr(self.expr, self.scope)

    def __str__(self):
        return '<{0} op="{1}{2}">{3}</{0}>' \
            .format(self.__class__.__name__,
                    'postfix ' if self.isPostfix else '', self.op, self.expr)

    def isLvalue(self) -> bool:
        return self.op == '*'

    def isModifiableLvalue(self):
        return self.isLvalue() and not self.type.isConstQualified()

    def isIntegerConstantExpr(self):
        return self.op in ('+', '-', '~', '!') and self.expr.isIntegerConstantExpr()

    @property
    def value(self):
        return super().value

    def lvalue1(self, cmd: list):
        assert self.isModifiableLvalue()
        assert self.value is None
        assert self.op == '*'
        self.expr.rvalue1(cmd)

    def rvalue1(self, cmd: list):
        if self.value is not None:
            cmd.append(instructions.LoadInstantly(self.type(), self.value))
            return
        if self.op == '&':
            self.expr.lvalue1(cmd)
            return
        if self.op == '*':
            self.expr.rvalue1(cmd)
            cmd.append(instructions.LoadTop(self.type(), 'indirection'))
            return
        if self.op == '+':
            return
        if self.op in ('++', '--'):
            if self.isPostfix:
                self.expr.rvalue1(cmd)
                cmd.append('duplicate')
                cmd.append('inc' if self.op == '++' else 'dec')
                self.expr.lvalue1(cmd)
                cmd.append('store')
            else:
                self.expr.lvalue1(cmd)
                cmd.append('duplicate')
                self.expr.rvalue1(cmd)
                cmd.append('inc' if self.op == '++' else 'dec')
                cmd.append('swap')
                cmd.append('store')
                cmd.append(instructions.LoadTop(self.expr.type(), 'fetch'))
            return

        self.expr.rvalue1(cmd)
        cmd.append(('unary', self.op))

    @property
    def subExprType(self):
        return self.expr.type()

    def _deduceType(self):

        def implicitCast(dest: 'c_type.QualifiedType', kind=CastExpr.CastKind.Naive):
            self.expr = ImplicitCastExpr(kind, dest, self.expr, self.scope)
            return self.expr.result

        if self.op in ('+', '-'):
            assert self.subExprType.isArithmeticType()
            self._result = self.expr.result
            if self.op == '-':
                if self.subExprType.isIntegerType() and self.subExprType.isUnsignedType():
                    # 若为无符号数，进行如下转换： unsigned char -> int, unsigned int -> long long,
                    # unsigned long long 冒着溢出的危险强行转成long long.
                    if isinstance(self.subExprType, c_type.UChar):
                        self._result = implicitCast(c_type.QualifiedType(c_type.Int32()))

                    elif isinstance(self.subExprType, (c_type.UInt32, c_type.UInt64)):
                        self._result = implicitCast(c_type.QualifiedType(c_type.Int64()))

                if self.isConstant:
                    self._result = self.result.replace(value=-self.value, isLvalue=False)

            # 若为有符号数则啥也不用干.

            return self.result
        if self.op in ('++', '--'):
            if isinstance(self.subExprType, c_type.FunctionProtoType):
                self._result = implicitCast(c_type.QPointer(self.expr.type), CastExpr.CastKind.FunctionToPointer)

            assert self.subExprType.isRealType() or isinstance(self.subExprType, c_type.Pointer)
            assert self.expr.isModifiableLvalue()
            self._result = EvaluateResult(self.expr.type)
            return self.result
        if self.op == '*':
            if isinstance(self.subExprType, c_type.FunctionProtoType):
                self._result = implicitCast(c_type.QPointer(self.expr.type), CastExpr.CastKind.FunctionToPointer)

            assert isinstance(self.subExprType, c_type.Pointer)
            self._result = EvaluateResult(type=self.subExprType.elementType, isLvalue=True)
            return self._result

        if self.op == '&':
            assert self.expr.isLvalue()
            # 这里遇到int a[*&x]其中x是常量的时候会认为*&x不是常数)
            self._result = EvaluateResult(type=c_type.QPointer(self.expr.type), isLvalue=False)
            return self.result

        elif self.op == '~':
            assert self.subExprType.isIntegerType()
            if self.expr.value is not None:
                self._result = EvaluateResult(self.expr.type, value=~self.expr.value)

            return self.result
        elif self.op == '!':
            assert self.expr.type().isScalarType()
            if self.expr.isConstant:
                self._result = EvaluateResult(c_type.QualifiedType(c_type.Int32()), 1 if self.expr.value == 0 else 1)
            else:
                self._result = EvaluateResult(c_type.QualifiedType(c_type.Int32()))
            return self.result

    # def _evaluateConstantExpr(self):
    #     e = self.expr.result
    #     if self.op == '++':
    #         raise NotImplementedError()
    #     if self.op == '--':
    #         pass
    #     if self.op == '&':
    #         pass
    #     if self.op == '*':
    #         pass
    #     if self.op == '+':
    #         self.value = e.value
    #     if self.op == '-':
    #         self.value = -e.value
    #     if self.op == '~':
    #         self.value = ~e.value
    #     if self.op == '!':
    #         self.value = 0 if e.value == 0 else 1


class SizeOfExpr(Expr):
    """
    :type isType:       bool
    :type _argument:    QualifiedType|Expr
    """

    def __init__(self, x: typing.Union['c_type.QualifiedType', Expr], env: 'scopes.DeclScope'):
        super().__init__(env)
        assert isinstance(x, (Expr, c_type.QualifiedType))
        self._argument = x
        self.isType = isinstance(x, c_type.QualifiedType)

    @property
    def argument(self):
        return self._argument

    # def getArgumentType(self):
    #     assert self.isType
    #     return self._argument
    #
    # def getArgumentExpr(self):
    #     assert not self.isType
    #     return self._argument
    #
    # def setArgument(self, x: typing.Union[QualifiedType, Expr]):
    #     assert isinstance(x, (QualifiedType, Expr))
    #     self.isType = isinstance(x, QualifiedType)
    #     self._argument = x

    def _deduceType(self):
        if self.isType:
            argType = cast(c_type.Type, self.argument())

        else:
            argType = self.argument.type()

        assert isinstance(argType, c_type.Type)
        assert isinstance(argType, c_type.Void) or (not argType.isIncompleteType() and not argType.isFunctionType())
        # FIXME: bit-field not supported

        self._result = EvaluateResult(c_type.QualifiedType(c_type.UInt32()),
                                      None if isinstance(argType, c_type.VariableArrayType) else argType.width)

        return self.result

    def isIntegerConstantExpr(self):
        return self.isConstant

    def __str__(self):
        return '<{0} isType="{1}">{2}{3}</{0}>' \
            .format(self.__class__.__name__, self.isType, self.result, self.argument)


class ArraySubscriptExpr(Expr):
    """
    :type _base: Expr
    :type _index:  Expr
    """

    def __init__(self, lhs: Expr, rhs: Expr, env: 'scopes.DeclScope'):
        super().__init__(env)
        lhsType = lhs.type()
        rhsType = rhs.type()
        if rhsType.isIntegerType():
            assert isinstance(lhsType, (c_type.ArrayType, c_type.Pointer)) and "非指针或数组不能做下标运算！"
            self._base, self._index = lhs, rhs
        elif lhsType.isIntegerType():
            assert isinstance(rhsType, (c_type.ArrayType, c_type.Pointer)) and "非指针或数组不能做下标运算！"
            self._base, self._index = rhs, lhs

        if not isinstance(self.indexType, c_type.Int64):
            self._index = ImplicitCastExpr(CastExpr.CastKind.Naive,
                                           c_type.QualifiedType(c_type.Int64()),
                                           self._index,
                                           env)
        if isinstance(self.baseType, c_type.ArrayType):
            self._base = ImplicitCastExpr(CastExpr.CastKind.ArrayToPointerDecayed,
                                          c_type.QPointer(self.baseType.elementType),
                                          self._base,
                                          env)
            self._result = EvaluateResult(self.baseType.elementType,
                                          isLvalue=True)
        else:
            self._result = EvaluateResult(self.baseType.elementType,
                                          isLvalue=True)

    @property
    def base(self):
        return self._base

    @property
    def index(self):
        return self._index

    @property
    def baseType(self) -> 'c_type.Pointer':
        return self._base.type()

    @property
    def indexType(self):
        return self._index.type()

    def lvalue1(self, cmd: list):
        assert self.isLvalue()
        _ = self.result
        self.base.rvalue1(cmd)
        self.index.rvalue1(cmd)
        cmd.append(instructions.LoadInstantly(c_type.Int64(), self.type.width, 'width of {}'.format(self.type())))
        cmd.append(('binary', '*'))
        cmd.append(('binary', '+'))

    def rvalue1(self, cmd: list):
        _ = self.result
        self.lvalue1(cmd)
        cmd.append(instructions.LoadTop(self.type(), '[]'))

    def isLvalue(self) -> bool:
        return True

    def isModifiableLvalue(self) -> bool:
        if isinstance(self.type(), c_type.ArrayType):
            return False
        if self.type().isIncompleteType():
            return False
        if self.type.isConstQualified():
            return False
        if isinstance(self.type(), c_type.StructType):
            if any(x.isConstQualified() for x in self.d.classScope.types.values()):
                return False
        # FIXME: 添加union支持的时候小心与typing.Union的重名问题
        return True

    def isIntegerConstantExpr(self) -> bool:
        return False

    def __str__(self):
        return '<{0}>{1}{2}</{0}>'.format(self.__class__.__name__, self.base, self.index)


class MemberExpr(Expr):
    def __init__(self, lhs: Expr, identifier: 'ctoken.CToken', env: 'Union[scopes.DeclScope]'):
        super().__init__(env)
        assert isinstance(lhs, Expr)
        assert isinstance(identifier, ctoken.CToken)
        assert identifier.token_t == 'identifier'
        self.__lhs = lhs
        self.__identifier = identifier
        self.__memberDecl = None
        sco = self.__lhs.type()
        if not isinstance(sco, c_type.StructType):
            raise RuntimeError()

        try:
            self.__memberDecl = sco.decl.classScope.getValueDecl(identifier.data)
            # FIXME: bit-field不能取地址(然而我不支持那种鬼畜的东西)
            if self.__lhs.type.isConstQualified():
                self._result = EvaluateResult(self.__memberDecl.declType.withConst(), isLvalue=self.__lhs.isLvalue())

            else:
                self._result = EvaluateResult(self.__memberDecl.declType, isLvalue=self.__lhs.isLvalue())

        except KeyError:
            raise RuntimeError("{}: 类型{}没有成员名为{}"
                               .format(identifier.position, self.__lhs.type(), self.__identifier.data))

    def lvalue1(self, cmd: list):
        self.__lhs.lvalue1(cmd)
        cmd.append(
            instructions.LoadInstantly(
                c_type.Int64(),
                self.__memberDecl.offset,
                'offset of {}.{}'.format(
                    cast(c_type.StructType, self.__lhs.type()).tag,
                    self.__identifier.data
                )
            )
        )
        cmd.append(('binary', '+'))

    def rvalue1(self, cmd: list):
        self.lvalue1(cmd)
        cmd.append(
            instructions.LoadTop(
                self.type(),
                'rvalue of {}.{}'.format(
                    cast(c_type.StructType, self.__lhs.type()).tag,
                    self.__identifier.data
                )
            )
        )

    def __str__(self):
        return '<{0} member="{1}">{2}{3}</{0}>' \
            .format(self.__class__.__name__, self.__identifier.data, self._result, self.__lhs)


class ArrowMemberExpr(Expr):
    def __init__(self, lhs: Expr, identifier: 'ctoken.CToken', env: 'Union[scopes.DeclScope]'):
        super().__init__(env)
        assert isinstance(lhs, Expr)
        assert isinstance(identifier, ctoken.CToken)
        assert identifier.token_t == 'identifier'
        self.__lhs = lhs
        self.__identifier = identifier
        self.__memberDecl = None
        sco = self.__lhs.type()
        if not isinstance(sco, c_type.Pointer):
            raise RuntimeError()

        sco = sco.elementType()
        if not isinstance(sco, c_type.StructType):
            raise RuntimeError()

        try:
            self.__memberDecl = sco.decl.classScope.getValueDecl(identifier.data)
            # FIXME: bit-field不能取地址(然而我不支持那种鬼畜的东西)
            if self.__lhs.type.isConstQualified():
                self._result = EvaluateResult(self.__memberDecl.declType.withConst(), isLvalue=True)

            else:
                self._result = EvaluateResult(self.__memberDecl.declType, isLvalue=True)

        except KeyError:
            raise RuntimeError("{}: 类型{}没有名为{}的成员"
                               .format(identifier.position, self.__lhs.type(), self.__identifier.data))

    def lvalue1(self, cmd: list):
        self.__lhs.rvalue1(cmd)
        cmd.append(instructions.LoadInstantly(c_type.Int64(), self.__memberDecl.offset))
        cmd.append(('binary', '+'))

    def rvalue1(self, cmd: list):
        self.lvalue1(cmd)
        cmd.append(instructions.LoadTop(self.type(), '->{}'.format(self.__identifier.data)))

    def __str__(self):
        return '<{0} member="{1}">{2}{3}</{0}>' \
            .format(self.__class__.__name__, self.__identifier.data, self._result, self.__lhs)


class CallExpr(Expr):
    def __init__(self, fn: Expr, args: List[Expr], env):
        super().__init__(env)
        self.__fn = fn
        self.__args = args
        self.numArgs = len(args)

    @property
    def callee(self):
        return self.__fn

    @callee.setter
    def callee(self, f: Expr):
        assert isinstance(f, Expr)
        self.__fn = f

    @property
    def calleeType(self) -> 'Union[c_type.Pointer,c_type.FunctionProtoType]':
        return self.__fn.type()

    def getDirectCallee(self):
        raise NotImplementedError()

    def getNumArgs(self):
        return self.numArgs

    def getArg(self, arg: int):
        assert isinstance(arg, int)
        return self.__args

    def setArg(self, arg: int, argExpr: Expr):
        assert isinstance(arg, int)
        assert isinstance(argExpr, Expr)
        self.__args[arg] = argExpr

    def __str__(self):
        return '<{0}><callee>{1}</callee>{2}</{0}>' \
            .format(self.__class__.__name__, self.callee, ''.join(map(str, self.__args)))

    def lvalue1(self, cmd: list):
        self.rvalue1(cmd)
        dt = self.type()
        if isinstance(dt, (c_type.PrimitiveType, c_type.Pointer)):
            cmd.append('push sp')
            cmd.append('store')
        else:
            assert isinstance(dt, c_type.StructType)
            for type, offset, name in reversed(list(expand(dt, dt.decl.name))):
                cmd.append(instructions.LoadInstantly(c_type.Int64(), offset, '&{}'.format(name)))
                cmd.append('add sp')
                cmd.append('store')

        cmd.append('push sp')

    def rvalue1(self, cmd: list):
        cmd.append('// prepare to call a func with {} parameter(s)'.format(self.getNumArgs()))
        i = 0
        for param in reversed(self.__args):
            cmd.append('// param {}'.format(i))
            i += 1
            param.rvalue1(cmd)
        self.callee.rvalue1(cmd)
        cmd.append('call')

    def _deduceType(self):
        if isinstance(self.calleeType, c_type.FunctionProtoType):
            self.callee = ImplicitCastExpr(
                CastExpr.CastKind.FunctionToPointer,
                c_type.QPointer(self.callee.type),
                self.callee,
                self.scope
            )

        assert isinstance(self.calleeType, c_type.Pointer)
        p = self.calleeType
        assert isinstance(p.elementType(), c_type.FunctionProtoType)
        fnType = cast(c_type.FunctionProtoType, p.elementType())
        if self.getNumArgs() > fnType.parameterCount():
            raise RuntimeError('too many arguments to function call, expected {}, have {}'
                               .format(fnType.parameterCount(), self.getNumArgs()))

        if self.getNumArgs() < fnType.parameterCount():
            raise RuntimeError('too few arguments to function call, expected {}, have {}'
                               .format(fnType.parameterCount(), self.getNumArgs()))

        for i in range(self.getNumArgs()):
            self.__args[i] = tryToDeduceTypeForAssignment(
                fnType.getParameterType(i),
                self.__args[i],
                self.scope
            )
            if self.__args[i].type != fnType.getParameterType(i):
                raise RuntimeError("实参'{}'与形参'{}'类型不符"
                                   .format(self.__args[i].type, fnType.getParameterType(i)))

            # if isinstance(arg.type(), c_type.FunctionProtoType):
            #     self.__args[i] = ImplicitCastExpr(
            #         CastExpr.CastKind.FunctionToPointer,
            #         c_type.QPointer(arg.type),
            #         self.__args[i],
            #         self.scope
            #     )
            #     arg = self.__args[i]
            #
            # if t == arg.type:
            #     continue
            #
            # if t().isArithmeticType() and arg.type().isArithmeticType():
            #     rx = cast(c_type.PrimitiveType, t()).rank()
            #     ry = cast(c_type.PrimitiveType, arg.type()).rank()
            #     if rx < ry:
            #         raise RuntimeError('不能进行隐式窄化强制类型转换!')
            #     if rx > ry:
            #         self.__args[i] = ImplicitCastExpr(CastExpr.CastKind.Naive, t, self.__args[i], self.scope)
            #
            #     continue
            #
            # raise RuntimeError('不相符的类型，期望{}，实际上是{}'.format(t, arg.type))
        self._result = EvaluateResult(fnType.returnType)

    def getNumCommas(self):
        return 0 if self.numArgs == 0 else self.numArgs - 1

    def isBuiltinCall(self):
        raise NotImplementedError()

    def getCallReturnType(self):
        pass


class CondExpr(Expr):
    def __init__(self, e1: Expr, e2: Expr, e3: Expr, env: 'scopes.DeclScope'):
        super().__init__(env)
        self.e1 = e1
        self.e2 = e2
        self.e3 = e3


class CastExpr(Expr):
    class CastKind(PyEnum):
        Naive = 1
        ArrayToPointerDecayed = 2
        FunctionToPointer = 4

    def __init__(self, castKind, typeCastTo: 'c_type.QualifiedType', expr: Expr, env: 'scopes.DeclScope'):
        super().__init__(env)
        assert isinstance(castKind, CastExpr.CastKind)
        self.kind = castKind
        self.expr = expr
        self.typeCastTo = typeCastTo


class ImplicitCastExpr(CastExpr):
    def __init__(self, castKind, typeCastTo: 'c_type.QualifiedType', expr: Expr, env: 'scopes.DeclScope'):
        assert isinstance(env, scopes.DeclScope)
        super().__init__(castKind, typeCastTo, expr, env)

        self._result = EvaluateResult(self.typeCastTo, value=self.expr.value)

    def _deduceType(self):
        return self._result

    def lvalue1(self, cmd: list):
        self.expr.lvalue1(cmd)
        if self.kind not in (CastExpr.CastKind.ArrayToPointerDecayed,):
            cmd.append(instructions.Cast(self.expr.type(), self.type()))

    def rvalue1(self, cmd: list):
        if self.isConstant:  # 此处会运行deduceType
            cmd.append(instructions.LoadInstantly(self.type(), self.value))

        else:
            if self.kind == CastExpr.CastKind.ArrayToPointerDecayed:
                self.expr.lvalue1(cmd)
            else:
                self.expr.rvalue1(cmd)
                cmd.append(instructions.Cast(self.expr.type(), self.type()))

    def __str__(self):
        return '<{0} castKind="{castKind}"><type>{1}</type>{2}</{0}>' \
            .format(self.__class__.__name__,
                    self.type,
                    self.expr,
                    castKind=self.kind)


class ExplictCastExpr(CastExpr):
    def __init__(self, castKind, typeCastTo: 'c_type.QualifiedType', expr: Expr, env: 'scopes.DeclScope'):
        super().__init__(castKind, typeCastTo, expr, env)

    def __str__(self):
        return '<{0}><ToType>{1}</ToType>{2}</{0}>' \
            .format(self.__class__.__name__, self._result, self.expr)


class CStyleCastExpr(CastExpr):
    def __init__(self, castKind, typeCastTo: 'c_type.QualifiedType', expr: Expr, env: 'scopes.DeclScope'):
        assert isinstance(typeCastTo, c_type.QualifiedType)
        super().__init__(castKind, typeCastTo, expr, env)

        if not isinstance(self.expr.type(), c_type.ArrayType):
            if self.expr.isLvalue():
                self.expr = LvalueToRvalueExpr(self.expr, self.scope)
        else:
            self.expr = ImplicitCastExpr(CastExpr.CastKind.ArrayToPointerDecayed,
                                         c_type.QPointer(self.expr.type().elementType),
                                         self.expr, self.scope)

    def __str__(self):
        return '<{0}><ToType>{1}</ToType>{2}</{0}>' \
            .format(self.__class__.__name__, self.result, self.expr)

    def isIntegerConstantExpr(self):
        return self.isConstant and self.type().isIntegerType()

    def rvalue1(self, cmd: list):
        if self.isConstant:  # 此处会运行deduceType
            cmd.append(instructions.LoadInstantly(self.type(), self.value))
            return

        self.expr.rvalue1(cmd)
        if isinstance(self.type(), c_type.Void):
            cmd.append('pop')

        else:
            cmd.append(instructions.Cast(self.expr.type(), self.type()))
            # cmd.append(f'cast from {self.expr.type().typeCode()} to {self.type().typeCode()}')

    def _deduceType(self):
        e = self.expr.result
        destType = self.typeCastTo()
        if isinstance(destType, c_type.Void):
            self._result = EvaluateResult(self.typeCastTo)
        else:
            assert not destType.isIncompleteType() and "期望完全（complete）的类型作为强制类型转换的目标类型"
            if isinstance(e.type(), c_type.ArrayType):
                self.expr = ImplicitCastExpr(CastExpr.CastKind.ArrayToPointerDecayed,
                                             c_type.QPointer(e.type().elementType),
                                             self.expr,
                                             self.scope)
                e = self.expr.result
            assert destType.isScalarType() and e.type().isScalarType() and "目标类型和待转换表达式的类型 期望scalar type。"
            if isinstance(destType, c_type.Pointer):
                assert not e.type().isFloatingType() and "浮点数类型不能强制转换成指针类型"

            self._result = EvaluateResult(self.typeCastTo, value=self.expr.value)

        return self.result

    # def _evaluateConstantExpr(self):
    #     e = self.expr.result
    #     if isinstance(self.destType(), Void):
    #         self.value = None
    #         return self.result
    #
    #     assert self.destType().isScalarType() and e.type().isScalarType() and "sb了！快看看怎么回事！"
    #     self.value = e.value
    #     return self.result


class BinaryOperator(Expr):
    """
    :type _lhs: Expr
    :type _rhs: Expr
    """

    def __init__(self, op: str, lhs: Expr, rhs: Expr, env: 'scopes.DeclScope'):
        super().__init__(env)
        self.op = op
        self._lhs = lhs
        self._rhs = rhs
        if self._lhs.isLvalue():
            self._lhs = LvalueToRvalueExpr(self._lhs, env)
        if self._rhs.isLvalue():
            self._rhs = LvalueToRvalueExpr(self._rhs, env)
        # self.subExprs = [lhs, rhs]

    def getOp(self):
        return self.op

    def setOp(self, o: str):
        assert isinstance(o, str)
        self.op = o

    def getLHS(self):
        return self._lhs

    def setLHS(self, e: Expr):
        assert isinstance(e, Expr)
        self._lhs = e

    def getRHS(self):
        return self._rhs

    def setRHS(self, e: Expr):
        assert isinstance(e, Expr)
        self._rhs = e

    def isIntegerConstantExpr(self):
        return self.isConstant and self.type().isIntegerType()

    def __str__(self):
        return '<{0} op="{1}">' \
               '{result}' \
               '{2}{3}' \
               '</{0}>' \
            .format(self.__class__.__name__, self.op, self.getLHS(), self.getRHS(), result=self.result)

    def rvalue1(self, cmd: list):
        if self.isConstant:  # 此处会运行deduceType
            cmd.append(instructions.LoadInstantly(self.type(), self.value))
            return

        if self.op == ',':
            self.getLHS().rvalue1(cmd)
            cmd.append('pop')
            self.getRHS().rvalue1(cmd)
            return
        self.getLHS().rvalue1(cmd)
        self.getRHS().rvalue1(cmd)

        if isinstance(self._lhs.type(), c_type.Pointer) and self._rhs.type().isIntegerType():
            cmd.append(instructions.LoadInstantly(c_type.Int64(), self._rhs.type.width))
            cmd.append(('binary', '*'))
            cmd.append(('binary', self.op))
            return

        e = self.type()
        l = self._lhs.type()
        r = self._rhs.type()
        if self.op not in {'>', '<', '>=', '<=', '==', '!=', '||', '&&', ','}:
            assert e == l == r
        cmd.append(('binary', self.op))

    def _deduceType(self):

        op = self.op
        scope = self.scope

        def implicitCast(castKind, setter: Callable[[Expr], None], getter: Callable[[], Expr],
                         dest: 'c_type.QualifiedType'):
            setter(ImplicitCastExpr(castKind, dest, getter(), scope))
            x: EvaluateResult = getter().result
            y = x.type()
            return x, y

        def deduceBoth():
            lhs: EvaluateResult = self.getLHS().result
            rhs: EvaluateResult = self.getRHS().result
            left = lhs.type()
            right = rhs.type()
            if isinstance(left, c_type.ArrayType):
                lhs, left = implicitCast(CastExpr.CastKind.ArrayToPointerDecayed,
                                         self.setLHS, self.getLHS, c_type.QPointer(left.elementType))
            if isinstance(right, c_type.ArrayType):
                rhs, right = implicitCast(CastExpr.CastKind.ArrayToPointerDecayed,
                                          self.setRHS, self.getRHS, c_type.QPointer(right.elementType))
            return lhs, rhs, left, right

        def arithmeticConvert(lhs: EvaluateResult, rhs: EvaluateResult, left: 'c_type.Type', right: 'c_type.Type'):

            t = c_type.Type.sup(left, right)
            assert t == left or t == right
            assert int(t == left and t != right) + int(t != left and t == right) <= 1

            if t == left and t != right:
                t = c_type.QualifiedType(t)
                rhs, right = implicitCast(CastExpr.CastKind.Naive,
                                          self.setRHS, self.getRHS, t)

            elif t != left and t == right:
                t = c_type.QualifiedType(t)
                lhs, left = implicitCast(CastExpr.CastKind.Naive,
                                         self.setLHS, self.getLHS, t)
            else:
                t = c_type.QualifiedType(t)
            assert isinstance(t, c_type.QualifiedType)
            return t, lhs, rhs, left, right

        def relationalOp():
            self._result = EvaluateResult(c_type.QualifiedType(c_type.Int32()))
            return self._evaluateConstantExpr(lhs, rhs, left, right)

        def areBothArithmeticType(left: 'c_type.Type', right: 'c_type.Type'):
            return left.isArithmeticType() and right.isArithmeticType()

        lhs, rhs, left, right = deduceBoth()
        assert left.isScalarType() and right.isScalarType()

        if areBothArithmeticType(left, right):
            # 都是算数类型
            type, lhs, rhs, left, right = arithmeticConvert(lhs, rhs, left, right)
            self._result = EvaluateResult(type)
            assert left == right == self.type()

        if op in ('*', '/', '%'):

            assert areBothArithmeticType(left, right) and \
                   "运算符'*', '/' ,'%' 两侧期望算数类型。"

            if op == '/' and rhs.isConstant:
                assert rhs.value is not None and "sb了！快看看怎么回事！"
                assert rhs.value != 0 and "期望除数非0。"

            if op == '%':
                assert self.type().isIntegerType() and "运算符'%'两侧期望整数类型。"
            return self._evaluateConstantExpr(lhs, rhs, left, right)

        elif op in ('+', '-'):
            if areBothArithmeticType(left, right):
                return self._evaluateConstantExpr(lhs, rhs, left, right)

            if isinstance(left, c_type.Pointer) and isinstance(right, c_type.Pointer):
                # 都是指针类型
                assert op == '-' and "两个指针只能相减不能相加"
                assert lhs.type == rhs.type and "期望两个相容的类型"
                assert left.addable() and "期望左操作数为指向void或完全类型的指针(实际上构造指针对象的时候就已经检查了）"

                self._result = EvaluateResult(c_type.QualifiedType(c_type.Int64()))
                return self._evaluateConstantExpr(lhs, rhs, left, right)

            def AreAPointerAndAnIntegerRespectively(x: 'c_type.Type', y: 'c_type.Type'):
                return isinstance(x, c_type.Pointer) and y.isIntegerType()

            def isAPointerPlusAnInteger(x: 'c_type.Type', y: 'c_type.Type'):
                return self.op == '+' and AreAPointerAndAnIntegerRespectively(x, y)

            if isAPointerPlusAnInteger(right, left):
                self._lhs, self._rhs = self._rhs, self._lhs
                lhs, rhs = self._lhs, self._rhs
                left, right = lhs.type(), rhs.type()

            if AreAPointerAndAnIntegerRespectively(left, right):
                assert isinstance(left, c_type.Pointer)
                assert left.addable() and "期望左操作数为指向void或完全类型的指针"
                assert right.isIntegerType()

                self._result = EvaluateResult(lhs.type)
                return self._evaluateConstantExpr(lhs, rhs, left, right)

            assert 0 and "sb了！快看看怎么回事！"
        elif op in ('<<', '>>'):
            assert left.isIntegerType() and right.isIntegerType() and "运算符'<<'和'>>'两侧期望整数类型。"

            if rhs.isConstant:
                assert rhs.value >= 0 and "运算符'<<'和'>>'右侧的值期望非负。"

            return self._evaluateConstantExpr(lhs, rhs, left, right)

        elif op in ('<', '>', '<=', '>='):
            if areBothArithmeticType(left, right):  # neglect Complex
                return relationalOp()

            if isinstance(left, c_type.Pointer) and isinstance(right, c_type.Pointer):
                assert left == right and "期望两个相容的类型"
                return relationalOp()

            assert 0 and "非法操作数类型"

        elif op in ('==', '!='):
            if areBothArithmeticType(left, right):  # neglect Complex
                return relationalOp()

            if isinstance(left, c_type.Pointer) and isinstance(right, c_type.Pointer):
                if left == right:
                    return relationalOp()

                if left.isVoidPointerType():
                    implicitCast(CastExpr.CastKind.Naive,
                                 self.setLHS, self.getLHS, rhs.type)
                    return relationalOp()

                if right.isVoidPointerType():
                    implicitCast(CastExpr.CastKind.Naive,
                                 self.setRHS, self.getRHS, lhs.type)
                    return relationalOp()

                assert 0 and "两边的指针应当指向同一类型"

            if left.isIntegerType() and isinstance(right, c_type.Pointer):
                if lhs.isConstant and lhs.value == 0:
                    implicitCast(CastExpr.CastKind.Naive,
                                 self.setLHS, self.getLHS, c_type.Pointer.newVoidPointer())
                    return relationalOp()

                assert 0 and "左操作数应为null pointer constant"

            if right.isIntegerType() and isinstance(left, c_type.Pointer):

                if rhs.isConstant and rhs.value == 0:
                    implicitCast(CastExpr.CastKind.Naive,
                                 self.setRHS, self.getRHS, c_type.Pointer.newVoidPointer())
                    return relationalOp()

                assert 0 and "右操作数应为null pointer constant"
            assert 0 and "sb了！快看看怎么回事！"
        elif op in ('&', '|', '^'):
            assert self.type().isIntegerType() and "期望整数类型"
            return self._evaluateConstantExpr(lhs, rhs, left, right)

        elif op in ('||', '&&'):
            assert left.isScalarType() and right.isScalarType() and "运算符'||'和'&&'两侧期望scalar type。"
            self._result = EvaluateResult(c_type.QualifiedType(c_type.Int32()))

            return self._evaluateConstantExpr(lhs, rhs, left, right)

        elif op == ',':
            self._result = EvaluateResult(rhs.type)

            return self._evaluateConstantExpr(lhs, rhs, left, right)

        assert 0 and "sb了！快看看怎么回事！"

    def _evaluateConstantExpr(self, lhs: EvaluateResult, rhs: EvaluateResult, left: 'c_type.Type',
                              right: 'c_type.Type'):

        if (lhs.value and rhs.value) is None:
            return self._result

        op = self.op

        # def evaluateBoth():
        #     lhs: EvaluateResult = self.getLHS().result
        #     rhs: EvaluateResult = self.getRHS().result
        #     left = lhs.type()
        #     right = rhs.type()
        #     return lhs, rhs, left, right

        def areBothArithmeticType(left: 'c_type.Type', right: 'c_type.Type'):
            return left.isArithmeticType() and right.isArithmeticType()

        # lhs, rhs, left, right = evaluateBoth()
        if op in ('+', '-'):

            if areBothArithmeticType(left, right):
                if op == '+':
                    self._result = self.result.replace(value=lhs.value + rhs.value)

                elif op == '-':
                    self._result = self.result.replace(value=lhs.value - rhs.value)

                return self.result
            elif isinstance(left, c_type.Pointer):
                if isinstance(right, c_type.Pointer):
                    assert left == right
                    self._result = self.result.replace(value=(lhs.value - rhs.value) / left.width)
                    return self.result

                elif right.isIntegerType():
                    if op == '+':
                        self._result = self.result.replace(value=lhs.value + rhs.value * left.width)

                    if op == '-':
                        self._result = self.result.replace(value=lhs.value - rhs.value * left.width)

                    return self.result
                assert 0 and "sb了！快看看怎么回事！"

            elif left.isIntegerType():
                self._result = self.result.replace(value=lhs.value * right.width + rhs.value)
                return self.result
            else:
                assert 0 and "sb了！快看看怎么回事！"
        if op in {'*', '/', '%', '<<', '>>', '<', '>', '<=',
                  '>=', '==', '!=', '&', '|', '^', '||', '&&', ','}:
            value = 0
            if op == '*':
                value = lhs.value * rhs.value
            if op == '/':
                value = lhs.value // rhs.value
            if op == '%':
                value = rhs.value % rhs.value
            if op == '>>':
                value = lhs.value >> rhs.value
            elif op == '<<':
                value = lhs.value << rhs.value
            elif op == '<':
                value = int(lhs.value < rhs.value)
            elif op == '>':
                value = int(lhs.value > rhs.value)
            elif op == '<=':
                value = int(lhs.value <= rhs.value)
            elif op == '>=':
                value = int(lhs.value >= rhs.value)
            elif op == '==':
                value = int(lhs.value == rhs.value)
            elif op == '!=':
                value = int(lhs.value != rhs.value)
            elif op == '&':
                value = lhs.value & rhs.value
            elif op == '|':
                value = lhs.value | rhs.value
            elif op == '^':
                value = lhs.value ^ rhs.value
            elif op == '||':
                value = int(lhs.value or rhs.value)
            elif op == '&&':
                value = int(lhs.value and rhs.value)
            elif op == ',':
                value = rhs.value
            else:
                assert 0 and "sb了！快看看怎么回事！"
            self._result = self.result.replace(value=value)
            return self.result


class AssignmentExpr(Expr):
    """
    :type lhs:Expr
    :type rhs:Expr
    """

    def __init__(self, lhs: Expr, rhs: Expr, env: 'scopes.DeclScope'):
        super().__init__(env)
        self._lhs = lhs
        self._rhs = rhs
        # FIXME: 这里因为没有类继承AssignmentExpr才敢这么写
        self._result = self._deduceType()

    def getLHS(self):
        return self._lhs

    def setLHS(self, expr: Expr):
        assert isinstance(expr, Expr)
        self._lhs = expr

    def getRHS(self):
        return self._rhs

    def setRHS(self, expr: Expr):
        assert isinstance(expr, Expr)
        self._rhs = expr

    def __str__(self):
        # assert isinstance(self._r)
        return '<{0}><type>{1}</type>{2}{3}</{0}>'.format(self.__class__.__name__, self.type, self._lhs,
                                                          self._rhs)

    # def rvalue(self):
    #     _ = self.result
    #     assert self.type() == self._rhs.type() == self._lhs.type()
    #     # 上面的断言不能删，它可以确保先运行deduceType
    #     res = self._lhs.lvalue()
    #     res.extend(self._rhs.rvalue())
    #     res.append(f'store')
    #     return res

    def rvalue1(self, cmd: list):
        _ = self.result
        assert self.type() == self._rhs.type() == self._lhs.type()
        # 上面的断言不能删，它可以确保先运行deduceType
        self._rhs.rvalue1(cmd)
        cmd.append('duplicate')
        self._lhs.lvalue1(cmd)
        cmd.append(f'store')

    def _deduceType(self):
        assert self._result is None

        # def implicitCastRHS(dest: 'c_type.QualifiedType'):
        #     self._rhs = ImplicitCastExpr(CastExpr.CastKind.Naive, dest, self._rhs, self.scope)
        #     return self._rhs.result, self._rhs.result.type()
        #
        assert self.getLHS().isModifiableLvalue()
        self.setRHS(tryToDeduceTypeForAssignment(self.getLHS().type, self.getRHS(), self.scope))
        if self.getRHS().type() != self.getLHS().type():
            raise RuntimeError('不能将{}类型的值赋给{}'.format(self.getRHS().type(), self.getLHS().type()))

        self._result = EvaluateResult(self._lhs.type)
        pass
        # lhs, rhs = self.getLHS().result, self.getRHS().result
        # left, right = lhs.type(), rhs.type()
        # self._result = EvaluateResult(lhs.type)
        #
        # if left.isArithmeticType():
        #     if right.isArithmeticType():
        #         assert isinstance(left, c_type.PrimitiveType)
        #         assert isinstance(right, c_type.PrimitiveType)
        #         if left.rank() == right.rank():
        #             if left != right:
        #                 rhs, right = implicitCastRHS(lhs.type)
        #
        #         elif left.rank() > right.rank():
        #             rhs, right = implicitCastRHS(lhs.type)
        #             assert self.type == self._lhs.type == rhs.type
        #
        #         else:
        #             assert 0 and "精度降低的赋值必须加上强制类型转换"
        #
        #         return self.result
        #     elif isinstance(right, c_type.Pointer):
        #         assert 0 and "不能把指针类型赋给算数类型"
        #
        # elif isinstance(left, c_type.StructType):
        #     assert left == right
        # elif isinstance(left, c_type.Pointer):
        #     if isinstance(right, c_type.Pointer):
        #         pl = left.elementType()
        #         pr = right.elementType()
        #         assert (lhs.type.qualifiers == lhs.type.qualifiers | rhs.type.qualifiers) \
        #                and "the type pointed to by the left " \
        #                    "has all the qualifiers of the type pointed to by the right;"
        #         # - both operands are pointers to qualified or unqualified versions of compatible types,
        #         #   and the type pointed to by the left has all the qualifiers of the type pointed to by the
        #         #   right;
        #         if pl == pr:
        #             return self.result
        #         elif isinstance(pl, c_type.Void) or isinstance(pr, c_type.Void):
        #             rhs, right = implicitCastRHS(lhs.type)
        #             return self.result
        #         # - one operand is a pointer to an object or incomplete type and the other is a pointer to a
        #         #   qualified or unqualified version of void, and the type pointed to by the left has all
        #         #   the qualifiers of the type pointed to by the right;
        #     else:
        #         assert right.isIntegerType() and "不能把非整数类型赋给指针"
        #         assert rhs.isConstant and "此处应为null pointer constant"
        #         assert rhs.value == 0 and "应为null pointer constant"
        #         rhs, right = implicitCastRHS(lhs.type)
        #
        #         # - the left operand is a pointer and the right is a null pointer constant; or
        #         # - the left operand has type _Bool and the right is a pointer.


def tryToDeduceTypeForAssignment(qleft: 'c_type.QualifiedType', rhs: Expr, scope: 'scopes.DeclScope') -> Expr:
    left = qleft()
    right = rhs.type()
    if qleft == rhs.type:
        return rhs

    if isinstance(right, c_type.FunctionProtoType):
        rhs = ImplicitCastExpr(
            CastExpr.CastKind.FunctionToPointer,
            c_type.QPointer(rhs.type),
            rhs,
            scope
        )
        right = rhs.type()
    if isinstance(right, c_type.ArrayType):
        rhs = ImplicitCastExpr(
            CastExpr.CastKind.ArrayToPointerDecayed,
            c_type.QualifiedType(c_type.Pointer(right.elementType)).withConst(),
            rhs,
            scope
        )
        right = rhs.type()

    def implicitCastRHS(dest: 'c_type.QualifiedType'):
        return ImplicitCastExpr(CastExpr.CastKind.Naive, dest, rhs, scope)

    if left.isArithmeticType():
        if right.isArithmeticType():
            assert isinstance(left, c_type.PrimitiveType)
            assert isinstance(right, c_type.PrimitiveType)
            if left.rank() == right.rank():
                assert left != right
                return implicitCastRHS(qleft)

            elif left.rank() > right.rank():
                return implicitCastRHS(qleft)

            else:
                raise RuntimeError("不能将'{}'隐式转换为'{}'".format(right, left))

        elif isinstance(right, c_type.Pointer):
            raise RuntimeError("不能将'{}'类型的值赋给'{}'".format(right, left))

    # elif isinstance(left, c_type.StructType):
    #     assert left == right
    #     return rhs
    elif isinstance(left, c_type.Pointer):
        if isinstance(right, c_type.Pointer):
            pl = left.elementType()
            pr = right.elementType()
            assert (qleft.qualifiers == qleft.qualifiers | rhs.type.qualifiers) \
                   and "the type pointed to by the left " \
                       "has all the qualifiers of the type pointed to by the right;"
            # - both operands are pointers to qualified or unqualified versions of compatible types,
            #   and the type pointed to by the left has all the qualifiers of the type pointed to by the
            #   right;
            if pl == pr:
                return rhs

            elif isinstance(pl, c_type.Void) or isinstance(pr, c_type.Void):
                return implicitCastRHS(qleft)
            # - one operand is a pointer to an object or incomplete type and the other is a pointer to a
            #   qualified or unqualified version of void, and the type pointed to by the left has all
            #   the qualifiers of the type pointed to by the right;
        else:

            if not right.isIntegerType():
                raise RuntimeError("不能将'{}'赋给'{}'".format(right, left))

            if not rhs.isConstant or rhs.value != 0:
                raise RuntimeError("此处应为null pointer constant")

            return implicitCastRHS(qleft)
    else:
        return rhs
        # - the left operand is a pointer and the right is a null pointer constant; or
        # - the left operand has type _Bool and the right is a pointer.


class Designator:
    def __init__(self, env: 'scopes.DeclScope', outer=None):
        assert isinstance(env, scopes.DeclScope)
        self.outer = outer
        self.scope = env


class FieldDesignator(Designator):
    def __init__(self, fieldName: str, env: 'scopes.DeclScope', outer=None):
        super().__init__(env, outer)
        assert isinstance(fieldName, str)
        self.fieldName = fieldName

    def __str__(self):
        return '.{}'.format(self.fieldName)


class ArrayDesignator(Designator):
    def __init__(self, index: int, env: 'scopes.DeclScope', outer=None):
        super().__init__(env, outer)
        assert isinstance(index, int)
        assert index >= 0
        self.index = index

    def __str__(self):
        return '[{}]'.format(self.index)


class DesignatedInitExpr(Expr):
    def __init__(self, type: 'c_type.QualifiedType', designators: List[Designator], initializer: Expr,
                 env: 'scopes.DeclScope'):
        super().__init__(env)
        assert isinstance(designators, list)
        assert all(isinstance(designator, Designator) for designator in designators)
        assert isinstance(initializer, Expr)
        self.designators = designators
        for designators in self.designators:
            designators.outer = self
        self.initializer = initializer
        self._result = EvaluateResult(type)

    def __str__(self):
        return '<{0}>{1}{2}</{0}>' \
            .format(self.__class__.__name__, ''.join(map(str, self.designators)), self.initializer)

    def isConstant(self):
        return False

    def isLvalue(self):
        return False

#
#
# class UnaryExprOrTypeTraitExpr(Expr):
#     def __init__(self, unaryExprOrTypename):
#         super().__init__()
#         pass
#
#
# class ConditionalExpr(Expr):
#     def __init__(self, condition, doIfTrue, doElse):
#         super(ConditionalExpr, self).__init__()
#         self.condition = condition
#         self.doIfTrue = doIfTrue
#         self.doElse = doElse
