from collections import OrderedDict
from AST import nodes, c_type
from Lexer import ctoken
import mem
from abc import abstractmethod
from typing import Generic, TypeVar, Optional, Union, Dict, List, Set

T = TypeVar('T')
U = TypeVar('U')


class IParent(Generic[T]):
    """
    :type __parent: None|T
    """

    def __init__(self, parent: Optional[T] = None):
        if parent is None:
            self.__parent = None
        else:
            self.__parent = parent

    @property
    def parent(self):
        return self.__parent

    def __eq__(self, other):
        raise NotImplementedError(self.__class__.__name__)


class IDepth(IParent):
    """
    :type __depth: int
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is None:
            self.__depth = 0
        else:
            assert isinstance(parent, IDepth)
            self.__depth = parent.depth + 1

    @property
    def depth(self):
        return self.__depth


class ValueDeclScope(IParent['ValueDeclScope']):
    def __init__(self, parent: Optional['ValueDeclScope'] = None):
        super().__init__(parent)
        self.__map: Dict[str, 'nodes.ValueDecl'] = OrderedDict()
        self.__offset = 0 if parent is None else parent.offset

    def getValueDecl(self, tag: str) -> 'nodes.ValueDecl':
        if tag in self.__map:
            return self.__map[tag]
        if self.parent is None:
            raise KeyError(tag)
        return self.parent.getValueDecl(tag)

    def _valueDecls(self):
        return self.__map.values()

    @property
    def offset(self) -> int:
        return self.__offset

    @offset.setter
    def offset(self, offset: int):
        assert isinstance(offset, int)
        self.__offset = offset

    def insertValueDecl(self, decl: 'nodes.ValueDecl') -> None:
        assert isinstance(decl, nodes.ValueDecl)
        if decl.name in self.__map:
            raise KeyError('redefinition of {}'.format(decl.name))
        else:
            self.__map[decl.name] = decl
        decl.offset = self.__offset
        self.__offset += decl.declType.width

    # def __eq__(self, other: 'ValueDeclScope'):
    #     assert isinstance(other, ValueDeclScope)
    #     return self.offset == other.offset and self.__map == other.__map

    def __str__(self):
        return ''.join(map(str, self.__map.values()))


class TypedefDeclScope(IParent['TypedefDeclScope']):
    def __init__(self, parent: Optional['TypedefDeclScope'] = None):
        # print('TypedefDeclScope')
        super().__init__(parent)
        self.__map = OrderedDict()

    def getTypedefDecl(self, tag: str) -> 'nodes.TypedefDecl':
        if tag in self.__map:
            return self.__map[tag]
        if self.parent is None:
            raise KeyError(tag)
        return self.parent.getTypedefDecl(tag)

    def insertTypedefDecl(self, decl: 'nodes.TypedefDecl') -> None:
        assert isinstance(decl, nodes.TypedefDecl)
        if decl.name in self.__map:
            raise KeyError('redefinition of {}'.format(decl.name))
        else:
            self.__map[decl.name] = decl

    # def __eq__(self, other: 'TypedefDeclScope'):
    #     assert isinstance(other, TypedefDeclScope)
    #     return self.__map == other.__map

    def __str__(self):
        return ''.join(map(str, self.__map.values()))
        # if not self.__map:
        #     return '<{0}/>'.format('TypedefDeclScope')
        # return '<{0}>{1}</{0}>'.format('TypedefDeclScope', ''.join(map(str, self.__map.values())))


class FunctionDeclScope(IParent['FunctionDeclScope']):
    def __init__(self, parent: Optional['FunctionDeclScope'] = None):
        super().__init__(parent)
        self.__fnDecls: Dict[str, 'nodes.FunctionDecl'] = OrderedDict()

    def __str__(self):
        return ''.join(map(str, self.__fnDecls.values()))
        # if not self.__fnDecls:
        #     return '<FunctionDeclScope/>'
        # return '<{0}>{1}</{0}>' \
        #     .format('FunctionDeclScope', ''.join(map(str, self.__fnDecls.values())))

    @property
    def functionDecls(self):
        return self.__fnDecls

    def getFunctionDecl(self, name: str) -> 'nodes.FunctionDecl':
        if name in self.__fnDecls:
            return self.__fnDecls[name]
        if self.parent is None:
            raise KeyError(name)
        return self.parent.getFunctionDecl(name)

    def insertFunctionDecl(self, decl: 'nodes.FunctionDecl'):
        assert isinstance(decl, nodes.FunctionDecl)
        if decl.name in self.__fnDecls:
            prev = self.__fnDecls[decl.name]
            if decl.declType != prev.declType:
                raise RuntimeError('函数{}前后定义不一致！'.format(decl.name))
            return
        self.__fnDecls[decl.name] = decl
        if self.parent is not None:
            self.parent.insertFunctionDecl(decl)


class OrdinaryIdentifierNameSpace(ValueDeclScope, TypedefDeclScope, FunctionDeclScope):

    def __init__(self, parent: Optional['OrdinaryIdentifierNameSpace'] = None):
        super().__init__(parent)
        self.__set = set()
        self.__fnSet = set()

    def insertTypedefDecl(self, decl: 'nodes.TypedefDecl') -> None:
        if decl.name in self.__set:
            raise KeyError('redefinition of {}'.format(decl.name))
        else:
            self.__set.add(decl.name)
            super().insertTypedefDecl(decl)

    def insertValueDecl(self, decl: 'nodes.ValueDecl') -> None:
        if decl.name in self.__set:
            raise KeyError('redefinition of {}'.format(decl.name))
        else:
            self.__set.add(decl.name)
            super().insertValueDecl(decl)

    def insertFunctionDecl(self, decl: 'nodes.FunctionDecl'):
        assert isinstance(decl, nodes.FunctionDecl)
        if decl.name in self.__set:
            raise KeyError('redefinition of {}'.format(decl.name))
        else:
            self.__fnSet.add(decl.name)
            super().insertFunctionDecl(decl)

    def __str__(self):
        return ValueDeclScope.__str__(self) + TypedefDeclScope.__str__(self) + FunctionDeclScope.__str__(self)

    def __len__(self):
        return len(self.__set) + len(self.__fnSet)


class RecordDeclScope(IParent['nodes.RecordDecl']):
    def __init__(self, parent: Optional['RecordDeclScope'] = None):
        super().__init__(parent)
        self.__map: Dict[str, 'nodes.RecordDecl'] = OrderedDict()

    def getRecordDecl(self, tag: str) -> 'nodes.RecordDecl':
        if tag in self.__map:
            return self.__map[tag]
        if self.parent is None:
            raise KeyError(tag)
        return self.parent.getRecordDecl(tag)

    def insertRecordDecl(self, decl: 'nodes.RecordDecl'):
        assert isinstance(decl, nodes.RecordDecl)
        if decl.name in self.__map:
            prev = self.__map[decl.name]
            if decl.declType.isIncompleteType():
                pass
            else:
                if prev.declType.isIncompleteType():
                    self.__map[decl.name] = decl
                    prev.setNext(decl)
                    decl.setPrev(prev)
                else:
                    raise RuntimeError('redefinition of struct {}'.format(decl.name))
        else:
            self.__map[decl.name] = decl

    def __len__(self):
        return len(self.__map)

    def __str__(self):
        return ''.join(map(str, self.__map.values()))


#
class DeclScope(OrdinaryIdentifierNameSpace, RecordDeclScope):
    def __init__(self, parent: Optional['DeclScope'] = None):
        # print('declScope')
        super().__init__(parent)

    def __str__(self):
        if not self:
            return '<{}/>'.format('DeclScope')
        return '<{0}>{1}{2}</{0}>' \
            .format('DeclScope',
                    OrdinaryIdentifierNameSpace.__str__(self),
                    RecordDeclScope.__str__(self))

    # def __eq__(self, other: 'DeclScope'):
    #     assert isinstance(other, DeclScope)
    #     raise NotImplementedError()

    def __len__(self):
        return OrdinaryIdentifierNameSpace.__len__(self) + RecordDeclScope.__len__(self)


class TypedefDeclExcludedScope(DeclScope):

    def __init__(self, parent: Optional['Union[TypedefDeclExcludedScope,DeclScope]'] = None):
        super().__init__(parent)

    def insertTypedefDecl(self, decl: 'nodes.TypedefDecl'):
        raise NotImplementedError()


class ILabelNamesScope:
    def insertLabel(self, labelStmt: 'nodes.LabeledStmt') -> None:
        raise NotImplementedError()

    def hasLabel(self, label: str) -> bool:
        raise NotImplementedError()

    def getStmtAssociatedWith(self, label: str) -> 'nodes.LabeledStmt':
        raise NotImplementedError()


class IGlobalConstantsContext:
    """
    :type __constants: bytearray
    :type __offsetOfConstants: int
    """

    def __init__(self):
        self.__constants = bytearray()

    @property
    def offset(self) -> int:
        raise NotImplementedError()

    @offset.setter
    def offset(self, offset: int):
        raise NotImplementedError()

    def insertConstantPointer(self, constant: int):
        assert isinstance(constant, int)
        res = self.offset
        mem.ptr_t.pack_into(self.__constants, self.offset, constant)
        self.offset += c_type.Pointer.width
        return res

    def insertConstantInt(self, constant: int, type: 'c_type.QualifiedType'):
        assert isinstance(constant, int)
        assert isinstance(type, c_type.QualifiedType)
        assert type().isIntegerType()
        res = self.offset
        {
            c_type.Int32: mem.int32_t,
            c_type.Int64: mem.int64_t,
            c_type.UInt32: mem.uint32_t,
            c_type.UInt64: mem.uint64_t,
            c_type.Char: mem.char_t,
            c_type.UChar: mem.uchar_t,
        }[type().__class__].pack_into(self.__constants, self.offset, constant)
        self.offset += type.width
        return res

    def insertConstantString(self, constant: str, type: 'c_type.QualifiedType'):
        assert isinstance(constant, str)
        assert isinstance(type, c_type.QualifiedType)
        assert isinstance(type(), c_type.Pointer) or isinstance(type(), c_type.ConstantArrayType)
        assert type().elementType().isCharType()

        arr = bytearray(constant, 'utf-8')
        arr.append(0)
        if isinstance(type(), c_type.ConstantArrayType):
            assert len(arr) == type.width

        self.__constants.extend(arr)
        res = self.offset
        self.offset += len(arr)
        return res


class StructScope(TypedefDeclExcludedScope):
    @property
    def members(self):
        return self._valueDecls()


class EnumScope:
    pass


class UnionScope:
    pass


class IFathers:

    @property
    def fnFather(self) -> 'FnScope':
        raise NotImplementedError()

    @property
    def breakFather(self) -> 'Union[SwitchScope,LoopScope]':
        raise NotImplementedError()

    @property
    def continueFather(self) -> 'LoopScope':
        raise NotImplementedError()

    @property
    def globalFather(self) -> 'GlobalScope':
        raise NotImplementedError()


class GlobalScope(DeclScope, IGlobalConstantsContext, IFathers):
    def __init__(self):
        super().__init__()
        # self.__fnDecls: Dict[str, 'nodes.FunctionDecl'] = OrderedDict()

    def __str__(self):
        return '<{0}>{1}</{0}>' \
            .format('GlobalScope',
                    super().__str__())

    @property
    def globalFather(self):
        return self

    def gen(self):
        functionDecls = self.functionDecls

        tmp = []
        for f in functionDecls.values():
            if not f.isDefinition:
                continue

            f.gen(tmp)
            # res[f.name] = tmp

        for i, c in enumerate(tmp):
            if isinstance(c, list):
                c.append(i)
                if c[0] == '.func':
                    assert not self.functionDecls[c[1]].entrance
                    self.functionDecls[c[1]].entrance.append(i)
        funcs = {name: functionDecls[name].entrance[0] for name in functionDecls}
        return tmp, funcs


class FnPrototypeScope(TypedefDeclExcludedScope):
    def __init__(self, parent: 'Union[TypedefDeclExcludedScope,DeclScope]'):
        super().__init__(parent)
        self.__params: List[nodes.ParamVarDecl] = []
        self.__paramNames: Set[str] = set()

    # def __eq__(self, other: 'FnPrototypeScope'):
    #     assert isinstance(other, FnPrototypeScope)
    # return other.__params == self.__params and

    @property
    def parameterDecls(self):
        return tuple(self.__params)

    def insertParamVarDecl(self, decl: 'nodes.ParamVarDecl'):
        assert decl.index not in self.__params
        assert decl.index == len(self.__params)
        if decl.name and decl.name in self.__paramNames:
            raise RuntimeError('redefinition of {}'.format(decl.name))
        self.__paramNames.add(decl.name)
        self.__params.append(decl)

    def lock(self):
        self.__dict__['insertParamVarDecl'] = None
        if len(self.__params) == 1 and isinstance(self.__params[0].declType(), c_type.Void):
            self.__params.pop()

    def isFnVoid(self) -> bool:
        return len(self.__params) == 0

    def canBeFunction(self) -> bool:
        if self.isFnVoid():
            return True
        if not all(param.name for param in self.__params):
            return False
        paramNames = set()
        for param in self.__params:
            if param.name:
                if param.name in paramNames:
                    return False

                paramNames.add(param.name)

        return True

    # def allParametersAreNamed(self) -> bool:
    #     return all(param.name for param in self.__params)
    #
    # def noParametersWithSameName(self) -> bool:
    #     paramNames = set()
    #     for param in self.__params:
    #         if param.name:
    #             if param.name in paramNames:
    #                 return False
    #
    #             paramNames.add(param.name)
    #
    #     return True

    def __str__(self):
        return '<{0}><params len="{1}">{2}</params>{3}</{0}>' \
            .format('FnPrototypeScope',
                    len(self.__params),
                    ''.join(map(str, self.__params)),
                    super().__str__())


class NaiveScope(DeclScope, IFathers):
    def __init__(self, parent: 'Union[FnScope,NaiveScope]', f=None, b=None, c=None, g=None):
        super().__init__(parent)
        if f is not None:
            assert isinstance(f, FnScope)
        if b is not None:
            assert isinstance(b, (SwitchScope, LoopScope))
        if c is not None:
            assert isinstance(c, LoopScope)
        self.__fnFather = f
        self.__breakFather = b
        self.__continueFather = c
        self.__globalFather = g

    def __str__(self):
        return '<{0}>{1}</{0}>'.format('NaiveScope', super().__str__())

    @property
    def fnFather(self):
        return self.__fnFather

    @property
    def breakFather(self):
        return self.__breakFather

    @property
    def continueFather(self):
        return self.__continueFather

    @property
    def globalFather(self):
        return self.__globalFather


class FnScope(DeclScope, IFathers, ILabelNamesScope):

    def __init__(self, parent: 'GlobalScope', fnProtoType: 'c_type.FunctionProtoType', tok: 'ctoken.CToken'):
        # print('FnScope')
        super().__init__(parent)
        self.__tok = tok
        self.__fnType = fnProtoType
        if not self.__fnType.scope.canBeFunction():
            raise RuntimeError('can\'t be a function')

        for decl in self.__fnType.scope.parameterDecls:
            vDecl = nodes.ValueDecl(decl.name, decl.declType)
            self.insertValueDecl(vDecl)

        self.__labels = OrderedDict()
        self.__waitingList = []

    def __str__(self):
        labels = '<labels>{}</labels>'.format(self.__labels) if self.__labels else '<labels/>'

        return '<{0}>{1}{2}</{0}>'.format('FnScope', super().__str__(), labels)

    def insertIntoWaitingList(self, identifier: str):
        assert isinstance(identifier, str)

    @property
    def tok(self):
        return self.__tok

    def insertLabel(self, labelStmt: 'nodes.LabeledStmt') -> None:
        assert isinstance(labelStmt, nodes.LabeledStmt)
        if labelStmt.label in self.__labels:
            raise KeyError('duplicate label {}'.format(labelStmt.label))
        self.__labels[labelStmt.label] = labelStmt

    def hasLabel(self, label: str) -> bool:
        return label in self.__labels

    def getStmtAssociatedWith(self, label: str) -> 'nodes.LabeledStmt':
        return self.__labels[label]

    @property
    def fnType(self):
        return self.__fnType

    @property
    def fnFather(self):
        return self

    @property
    def breakFather(self):
        return None

    @property
    def continueFather(self):
        return None

    @property
    def globalFather(self) -> 'GlobalScope':
        return self.parent


class ControlScope(NaiveScope):
    pass


class LoopScope(ControlScope):
    def __init__(self, parent: 'Union[FnScope,NaiveScope,ControlScope]'):
        super().__init__(parent, parent.fnFather, self, self, parent.globalFather)


class WhileScope(LoopScope):
    def __str__(self):
        return '<{0}>{1}</{0}>'.format('WhileScope', super().__str__())


class ForScope(LoopScope):
    def __str__(self):
        return '<{0}>{1}</{0}>'.format('ForScope', super().__str__())


class DoScope(LoopScope):
    def __str__(self):
        return '<{0}>{1}</{0}>'.format('DoScope', super().__str__())


class SwitchScope(ControlScope):
    def __init__(self, parent: 'Union[FnScope,NaiveScope]'):
        super().__init__(parent, parent.fnFather, self, parent.continueFather, parent.globalFather)
        self.__default = None
        self.__cases = OrderedDict()

    def insertCase(self, stmt: 'nodes.CaseStmt'):
        assert isinstance(stmt, nodes.CaseStmt)
        assert stmt.constexpr.isIntegerConstantExpr()
        assert stmt.constexpr.value not in self.__cases and 'duplicated case'

        self.__cases[stmt.constexpr.value] = stmt

    def cases(self) -> Dict[int, 'nodes.CaseStmt']:
        return self.__cases

    def hasDefault(self):
        return self.__default is not None

    def __str__(self):
        return '<{0}>{1}</{0}>'.format('SwitchScope', super().__str__())

    @property
    def default(self) -> 'nodes.DefaultStmt':
        assert self.hasDefault()
        return self.__default

    @default.setter
    def default(self, defaultStmt: 'nodes.DefaultStmt'):
        assert self.__default is None and 'duplicated default'
        self.__default = defaultStmt


class IfScope(ControlScope):
    def __init__(self, parent: 'Union[FnScope,NaiveScope,ControlScope]'):
        super().__init__(parent, parent.fnFather, parent.breakFather, parent.continueFather, parent.globalFather)

    def __str__(self):
        return '<{0}>{1}</{0}>'.format('IfScope', super().__str__())


class IfElseScope(ControlScope):
    pass


if __name__ == '__main__':
    FnScope(GlobalScope())
    print(FnScope.__mro__)
