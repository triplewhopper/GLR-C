from typing import Tuple, Iterable, List, cast
from enum import IntFlag, Flag
from AST.c_exceptions import Failed
from collections import OrderedDict
from AST import nodes, scopes

error = Failed


# TODO 5/15 13:53 typedeftype混在里面太麻烦，想办法去掉。
#
# class Entry:
#     """
#     :type name: str
#     :type type: QualifiedType
#     :type value: object
#     """
#
#     def __init__(self, name, type, value):
#         """
#         :type name: str
#         :type type: QualifiedType
#         :type value: object
#         """
#         self.name = name
#         self.type = type
#         self.value = value


class ASTContext:
    pass


def join(qualifiers):
    return '' if not qualifiers else ' '.join(sorted(qualifiers))


class Type:
    LENGTH = None
    __slots__ = ()

    def __init__(self):
        pass
        # if canonical is None:
        #     canonical = QualifiedType()
        #
        # assert isinstance(canonical, QualifiedType)
        # self._canonicalType = QualifiedType(self) if canonical.isNull() else canonical

    # def isCanonical(self):
    #     return self._canonicalType() is self
    #
    # def getCanonicalTypeInternal(self):
    #     return self._canonicalType

    def isCompatibleWith(self, other: 'Type'):
        raise NotImplementedError()

    def isObjectType(self):
        pass

    def isIncompleteType(self):
        return False

    def isIncompleteOrObjectType(self):
        return not self.isFunctionType()

    def isFunctionType(self):
        return isinstance(self, FunctionProtoType)

    # def isVariablyModifiedType(self):
    #     pass

    # def isArrayType(self):
    #     return isinstance(self, ArrayType)

    # def isConstantArrayWithExprType(self):
    #     return isinstance(self, ConstantArrayWithExprType)
    #
    # def isConstantArrayWithoutExprType(self):
    #     return isinstance(self, ConstantArrayWithoutExprType)
    #
    # def isConstantArrayType(self):
    #     return isinstance(self, ConstantArrayType)
    #
    # def isIncompleteArrayType(self):
    #     return isinstance(self, IncompleteArrayType)
    def typeCode(self)->str:
        raise NotImplementedError(self.__class__.__name__)

    # def typeid(self):
    #     raise NotImplementedError(self.__class__.__name__)

    def isVoidPointerType(self):
        return False

    def isIntegerType(self):
        return isinstance(self, (Char, UChar, Int32, Int64, UInt32, UInt64))
        # return any(self.isCompatibleWith(c()) for c in (Char, UChar, Int32, Int64, UInt32, UInt64))

    def isUnsignedType(self):
        return isinstance(self, (UChar, UInt32, UInt64))
        # return any(self.isCompatibleWith(c()) for c in (UChar, UInt32, UInt64))

    # def isVoidType(self):
    #     return self.isCompatibleWith(Void())

    def isFloatingType(self):
        return isinstance(self, (Float, Double))

    def isArithmeticType(self):
        return self.isIntegerType() or self.isFloatingType()

    def isRealType(self):
        return self.isArithmeticType()

    # def isPointerType(self):
    #     if isinstance(self, Pointer):
    #         return True
    #     if isinstance(self, TypedefType):
    #         return self.type().isPointerType()
    #     return False

    # def isRecordType(self):
    #     if isinstance(self, StructType):
    #         return True
    #     if isinstance(self, TypedefType):
    #         return self.type().isRecordType()
    #     return False

    def isCharType(self):
        return any(self.isCompatibleWith(c()) for c in (Char, UChar))

    def isScalarType(self):
        return self.isArithmeticType() or isinstance(self, Pointer)

    def isIntegralType(self):
        raise NotImplementedError()

    @staticmethod
    def sup(type1, type2):
        """
        :type type1: Type
        :type type2: Type
        :rtype: Double|Char|UChar|Int32|UInt32|Int64|UInt64
        """
        assert type1.isArithmeticType() and type2.isArithmeticType()
        # assert value is not None
        if type1.isFloatingType() or type2.isFloatingType():
            return Double()  # , float(value)
        assert type1.isIntegerType() and type2.isIntegerType()
        a = [Char, UChar, Int32, UInt32, Int64, UInt64]

        def rankOfIntegerType(type):
            """
            :type type: Type
            """
            for i in range(len(a)):
                if isinstance(type, a[i]):
                    return i
            raise RuntimeError()

        return a[max(rankOfIntegerType(type1), rankOfIntegerType(type2))]()  # , int(value)

    @property
    def width(self) -> int:
        assert self.__class__.LENGTH is not None
        return self.__class__.LENGTH

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        raise NotImplementedError(self.__class__.__name__)
    # def isTypedefType(self):
    #     return False


class QualifiedType:
    """
    :type qualifiers: QualifiedType.TQ
    :type ptr: Type
    """
    __slots__ = ('qualifiers', 'ptr')

    class TQ(IntFlag):
        Const = 0x1
        Volatile = 0x2
        Restrict = 0x4
        CVRFlags = Const | Volatile | Restrict

    def __init__(self, ptr: Type = None, qualifiers: int = 0):
        assert ptr is None or isinstance(ptr, Type)

        qualifiers = QualifiedType.TQ(qualifiers)
        self.qualifiers = qualifiers
        # if isinstance(ptr, TypedefType):
        #     self.ptr = ptr.type
        # else:
        self.ptr = ptr

    def __call__(self):
        return self.ptr

    def isNull(self):
        return self.ptr is None

    def __str__(self):
        if self.qualifiers:
            return '<{0}>{1} {2}</{0}>' \
                .format(self.__class__.__name__, str(self.qualifiers), self.ptr)
        return '<{0}>{1}</{0}>'.format(self.__class__.__name__, self.ptr)

    def isConstQualified(self):
        return QualifiedType.TQ.Const in self.qualifiers

    # def isConstant(self, ctx: DeclScope):
    #     pass

    def addConst(self):
        self.qualifiers |= QualifiedType.TQ.Const

    def getQualifiedType(self, tQs: int):
        assert isinstance(tQs, int)
        return QualifiedType(self.ptr, tQs)

    def getWithAdditionalQualifiers(self, tQs: int):
        return QualifiedType(self.ptr, self.qualifiers | tQs)

    # def getArrayToPointerDecayType(self):
    #     assert isinstance(self.ptr, ArrayType)
    #     return QualifiedType(Pointer(self.ptr.elementType), self.qualifiers)

    def withConst(self):
        return self.getWithAdditionalQualifiers(QualifiedType.TQ.Const)

    def getDesugaredType(self):
        raise NotImplementedError()

    # def isCompatibleWith(self, other):
    #     """
    #     :type other: QualifiedType|Type
    #     """
    #     assert isinstance(other, (QualifiedType, Type))
    #     if isinstance(other, QualifiedType):
    #         return self.qualifiers == other.qualifiers and self.ptr.isCompatibleWith(other())
    #     if isinstance(other, Type):
    #         return self.qualifiers == 0 and self.ptr.isCompatibleWith(other)

    def __eq__(self, other: 'QualifiedType'):
        # assert not isinstance(other, TypedefType)
        assert isinstance(other, QualifiedType)
        # if isinstance(other, QualifiedType):
        return self.qualifiers == other.qualifiers and self.ptr == other()
        #
        # if isinstance(other, Type):
        #     return self.qualifiers == 0 and self.ptr == other
        # return False

    # def __eq__(self, other):
    #     raise NotImplementedError(self.__class__.__name__)
    # assert isinstance(other, QualifiedType)
    # return self.ptr is other() and self.qualifiers == other.qualifiers

    def __ne__(self, other: 'QualifiedType'):
        return not (self == other)
        # assert isinstance(other, QualifiedType)
        # return self.ptr is not other() or self.qualifiers != other.qualifiers

    @property
    def width(self):
        return self.ptr.width

    # @property
    # def canonicalType(self):
    #     return self.ptr._canonicalType


class PrimitiveType(Type):
    it = None

    def __new__(cls, *args, **kwargs):
        if cls.it is None:
            cls.it = super().__new__(cls)
        return cls.it

    # def __eq__(self, other):
    #     assert isinstance(other, Type)
    #     return self is other

    def __ne__(self, other: Type):
        return not (self == other)

    def rank(self):
        raise NotImplementedError()

    # def isCompatibleWith(self, other):
    #     if isinstance(other, QualifiedType):
    #         return other.isCompatibleWith(self)
    #     if isinstance(other, PrimitiveType):
    #         return self.__class__ == other.__class__
    #
    #     assert 0 and "错误类型！"

    def __eq__(self, other: Type):
        assert isinstance(other, Type)
        return self.__class__ == other.__class__
        # assert not isinstance(other, TypedefType)
        # if isinstance(other, QualifiedType):
        #     return other == self
        # if isinstance(other, PrimitiveType):

        # return True

    def __hash__(self):
        return hash(str(self))


class Char(PrimitiveType):
    LENGTH = 1
    __slots__ = ()

    def __str__(self):
        return 'char'

    def typeCode(self):
        return 'i8'

    # def rank(self):
    #     return 1

    def typeid(self):
        return 1

    __repr__ = __str__


class UChar(PrimitiveType):
    LENGTH = 1
    __slots__ = ()

    def __str__(self):
        return f'unsigned_char'

    def typeCode(self):
        return 'u8'

    # def typeid(self):
    #     return -1

    def rank(self):
        return 1

    __repr__ = __str__


class Int32(PrimitiveType):
    LENGTH = 4
    __slots__ = ()

    def __str__(self):
        return 'int'

    def typeCode(self):
        return 'i32'

    # def typeid(self):
    #     return 2

    def rank(self):
        return 2

    __repr__ = __str__


class UInt32(PrimitiveType):
    LENGTH = 4
    __slots__ = ()

    def __str__(self):
        return 'unsigned_int'

    def typeCode(self):
        return 'u32'

    # def typeid(self):
    #     return -2

    def rank(self):
        return 2

    __repr__ = __str__


class Int64(PrimitiveType):
    LENGTH = 8
    __slots__ = ()

    def __str__(self):
        return 'long_long'

    def typeCode(self):
        return 'i64'

    #
    # def typeid(self):
    #     return 3
    #
    def rank(self):
        return 3

    __repr__ = __str__


class UInt64(PrimitiveType):
    LENGTH = 8
    __slots__ = ()

    def __str__(self):
        return 'unsigned_long_long'

    def typeCode(self):
        return 'u64'

    # def typeid(self):
    #     return -3

    def rank(self):
        return 3

    __repr__ = __str__


class Double(PrimitiveType):
    LENGTH = 8
    __slots__ = ()

    def __str__(self):
        return 'double'

    def typeCode(self):
        return 'f64'

    # def typeid(self):
    #     return 4

    def rank(self):
        return 5

    __repr__ = __str__


class Float(PrimitiveType):
    LENGTH = 4
    __slots__ = ()

    def __str__(self):
        return 'float'

    def typeCode(self):
        return 'f32'

    # def typeid(self):
    #     return 5

    def rank(self):
        return 4

    __repr__ = __str__


#
# class TypedefType(Type):
#     def __init__(self, name: str, type: QualifiedType):
#         super().__init__()
#         self.name = name
#         self.type = type
#
#     # def isCompatibleWith(self, other):
#     #     if isinstance(other, Type):
#     #         return other.isCompatibleWith(self.type)
#     #     if isinstance(other, QualifiedType):
#     #         return other.isCompatibleWith(self.type)
#     #     assert 0
#
#     def __eq__(self, other):
#         # if isinstance(other, (Type, QualifiedType)):
#         #     return other == self.type
#         assert 0
#
#     # def __getattr__(self, item):
#
#     # @property
#     # def elementType(self):
#     #     assert self.type().isPointerType()
#     #     return cast(Pointer, self.type()).elementType
#     #
#     # @property
#     # def length(self):
#     #     assert self.type().isConstantArrayType()
#     #     return cast(ConstantArrayType, self.type()).length
#
#     # @property
#     def isTypedefType(self):
#         return True

#
# class ParenType(Type):
#     LENGTH = 1
#
#     def __init__(self, returnType, paramTypes):
#         super().__init__()
#         assert isinstance(returnType, Type)
#         if isValidReturnType(returnType):
#             self.returnType: Type = returnType
#
#         self.paramTypes: Tuple[Type] = tuple(Pointer(t.createFunctionPrototype())
#                                              if isinstance(t, ParenType)
#                                              else t
#                                              for t in paramTypes)
#
#     def isCompatibleWith(self, other):
#         raise NotImplementedError()
#
#     def createFunctionPrototype(self):
#         return FunctionProtoType(self.returnType, self.paramTypes)
#
#     def createFunction(self, entrance):
#         return FunctionType(self.returnType, self.paramTypes, entrance)
#
#     def __str__(self):
#         return '%s(%s)' % (
#             self.returnType,
#             ', '.join(str(x) for x in self.paramTypes)
#         )
#
#     def __eq__(self, other):
#         assert not isinstance(other, TypedefType)
#         raise NotImplementedError()
#
#     def __hash__(self):
#         return hash(str(self))
#

#
# class FunctionType(Type):
#     LENGTH = 0
#
#     def __init__(self, returnType: QualifiedType, scope: 'scopes.FnPrototypeScope'):
#         super().__init__()
#         self.__scope = scope
#         self.__returnType = returnType
#
#     @property
#     def scope(self):
#         return self.__scope
#
#     @property
#     def returnType(self):
#         return self.__returnType
#
#     def __str__(self):
#         return '<{0}><returnType>{1}</returnType>{2}</{0}>' \
#             .format(self.__class__.__name__, self.__returnType, self.__scope)
#
#     def __hash__(self):
#         return hash(str(self))
#
#     def __eq__(self, other: 'Type'):
#         assert isinstance(other, Type)
#         return isinstance(other, FunctionType) \
#                and self.returnType == other.returnType \
#                and self.scope == other.scope
#

class FunctionProtoType(Type):
    LENGTH = 0

    def __init__(self, returnType: QualifiedType, scope: 'scopes.FnPrototypeScope'):
        super().__init__()
        self.__scope = scope
        self.__returnType = returnType
        self.__paramTypes = tuple(x.declType for x in scope.parameterDecls)

    @property
    def scope(self) -> 'scopes.FnPrototypeScope':
        return self.__scope

    def getParameterType(self, i: int) -> QualifiedType:
        return self.__paramTypes[i]

    def parameterCount(self):
        return len(self.__paramTypes)

    @property
    def returnType(self) -> QualifiedType:
        return self.__returnType

    def __str__(self):
        return '<{0}><returnType>{1}</returnType>{2}</{0}>' \
            .format(self.__class__.__name__, self.__returnType, self.__scope)

    def typeCode(self):
        return 'function'

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other: 'Type'):
        assert isinstance(other, Type)
        return isinstance(other, FunctionProtoType) \
               and self.returnType == other.returnType \
               and self.__paramTypes == other.__paramTypes


class TagType(Type):
    """
    :type __decl: nodes.RecordDecl
    :type __tag:  str

    """

    def __init__(self, decl: 'nodes.TagDecl', tag: str):
        super().__init__()
        self.__decl = decl
        self.__tag = tag
        # self._isBeingDefined = True

    @property
    def decl(self):
        return self.__decl

    @property
    def tag(self):
        return self.__tag
    # @property
    # def isBeingDefined(self):
    #     assert self.decl.isDefinition
    #     return self._isBeingDefined
    #
    # @isBeingDefined.setter
    # def isBeingDefined(self, d: bool):
    #     assert isinstance(d, bool)
    #     assert self.decl.isDefinition
    #     self._isBeingDefined = d


class StructType(TagType):
    countForAnonymous = 0

    def __init__(self, decl: 'nodes.RecordDecl', tag: str):
        assert isinstance(tag, str)
        assert tag
        super().__init__(decl, tag)
        # self._isComplete: bool = False
        # self.memberTypes: Tuple[QualifiedType] = None
        # self.env = env

    # def isCompatibleWith(self, other):
    #     assert isinstance(other, Type)
    #     if not isinstance(other, StructType):
    #         return False
    #     return self.tag == other.tag and self.decl == other.decl

    def isIncompleteType(self):
        if self.decl.isDefinition:
            return self.decl.isBeingDefined
        return True

    @staticmethod
    def newTagName(x: str = ''):
        if x: return x
        res = 'anonymousStruct<{}>'.format(StructType.countForAnonymous)
        StructType.countForAnonymous += 1
        return res

    def __str__(self):
        return '<{0} tag="{1}" linkID="{2}"/>' \
            .format('struct', self.tag, self.decl.ID)

    def __hash__(self):
        return hash(self.tag)

    def __eq__(self, other: Type):
        # assert isinstance(other, (Type, QualifiedType))
        assert isinstance(other, Type)
        # if isinstance(other, QualifiedType):
        #     return other == self
        return other is self

    @property
    def width(self):
        if self.isIncompleteType():
            raise RuntimeError()
        return self.decl.classScope.offset


class Enum(Type):
    def __init__(self):
        super(Enum, self).__init__()
        raise NotImplementedError()


class Pointer(Type):
    """
    :type elementType: QualifiedType
    """
    LENGTH = 8

    def __init__(self, elementType: QualifiedType):
        assert isinstance(elementType, QualifiedType)
        super(Pointer, self).__init__()
        # if isinstance(elementType, TypedefType):
        #     self.elementType = elementType.type
        # else:
        self.elementType = elementType
        # assert self.addable()

    def __str__(self):
        # if isinstance(self.elementType, ParenType):
        #     return '''<{0}> <{1}>{2}</{1}> <{3}>{4}</{3}> </{0}>''' \
        #         .format('FuncPointer',
        #                 'ReturnType', self.elementType.returnType,
        #                 'ParamTypes', self.elementType.paramTypes)
        return '<{0}>{1}</{0}>'.format('Pointer', self.elementType)

    # def isCompatibleWith(self, other):
    #     assert isinstance(other, (Type, QualifiedType))
    #     return other.isCompatibleWith(self.elementType)

    def isVoidPointerType(self):
        return isinstance(self.elementType(), Void)

    def typeCode(self):
        return 'ptr'

    def __hash__(self):
        return hash(str(self))

    def addable(self):
        return isinstance(self.elementType(), Void) or not self.elementType().isIncompleteType()

    @staticmethod
    def newVoidPointer():
        return QualifiedType(Pointer(QualifiedType(Void())))

    def __eq__(self, other: 'Type'):
        assert isinstance(other, Type)
        return isinstance(other, Pointer) and self.elementType == other.elementType


def QPointer(t: QualifiedType) -> QualifiedType:
    return QualifiedType(Pointer(t))


class ArrayType(Type):
    """
    :type elementType: QualifiedType
    """

    def __init__(self, elementType: QualifiedType):
        super().__init__()
        assert isinstance(elementType, QualifiedType)
        # if isinstance(elementType, TypedefType):
        #     self.elementType = elementType.type
        # else:
        self.elementType = elementType
        if elementType().isIncompleteType():
            raise error(f"array has incomplete element type '{elementType}'.")

    def __str__(self):
        raise NotImplementedError(self.__class__.__name__)

    def __eq__(self, other: 'Type'):
        assert isinstance(other, Type)
        return isinstance(other, ArrayType) and self.elementType == other.elementType

    @property
    def width(self) -> int:
        raise NotImplementedError()

    def __hash__(self):
        return hash(str(self))


class ConstantArrayType(ArrayType):
    def __init__(self, elementType: QualifiedType, length: int):
        super().__init__(elementType)
        assert isinstance(length, int)
        self.length = length

    def __str__(self):
        return '<{0} length="{1}">{2}</{0}>'.format(self.__class__.__name__, self.length, self.elementType)

    def __eq__(self, other):
        assert isinstance(other, Type)
        return isinstance(other, ConstantArrayType) \
               and self.elementType == other.elementType \
               and self.length == other.length
        # if super().__eq__(other) and isinstance(other, ConstantArrayType):
        #     return self.length == other.length
        #
        # return False

    def typeCode(self):
        return 'arr[{}]'.format(self.length)

    @property
    def width(self):
        return self.length * self.elementType.width


class ConstantArrayWithExprType(ConstantArrayType):
    def __init__(self, elementType: QualifiedType, length: int, sizeExpr):
        super().__init__(elementType, length)
        self.sizeExpr = sizeExpr


class ConstantArrayWithoutExprType(ConstantArrayType):
    def __init__(self, elementType: QualifiedType, length: int):
        super().__init__(elementType, length)


class IncompleteArrayType(ArrayType):
    def __init__(self, elementType: QualifiedType):
        super().__init__(elementType)

    def __str__(self):
        return '<{0}>{1}</{0}>'.format(self.__class__.__name__, self.elementType)

    def __eq__(self, other):
        return isinstance(other, IncompleteArrayType) and self.elementType == other.elementType

    def createConstantArrayType(self, length):
        return ConstantArrayType(self.elementType, length)

    def isIncompleteType(self):
        return True

    @property
    def width(self):
        return Pointer.width


class VariableArrayType(ArrayType):
    pass


class Void(PrimitiveType):
    LENGTH = 1

    def __str__(self):
        return 'void'

    def __eq__(self, other):
        # assert isinstance(other, (Type, QualifiedType))
        assert isinstance(other, Type)
        return isinstance(other, Void)
        # if isinstance(other, QualifiedType):
        #     return other == self

    # def typeid(self):
    #     return 0

    def isIncompleteType(self):
        return True


def isValidReturnType(x: QualifiedType) -> bool:
    assert isinstance(x, QualifiedType)
    if isinstance(x(), Void): return True
    if isinstance(x(), ArrayType): raise error(f'function cannot return type {x}')
    if isinstance(x(), ParenType):
        raise error(f'function cannot return function type {x}')
    if x().isIncompleteType():
        raise error(f'function cannot return incomplete type {x}')
    return True


from collections import Counter

builtinTypes = frozenset(
    ['void', 'char', 'short', 'int', 'long', 'float', 'double', 'signed', 'unsigned', '_Bool', '_Complex'])
__c: List[Tuple[List[Counter], Type]] = \
    [([Counter({'void': 1})], Void()),
     ([Counter({'char': 1})], Char()),
     ([Counter({'signed': 1, 'char': 1})], Char()),
     ([Counter({'unsigned': 1, 'char': 1})], UChar()),
     ([Counter({'short': 1}), Counter({'signed': 1, 'short': 1}),
       Counter({'short': 1, 'int': 1}),
       Counter({'signed': 1, 'short': 1, 'int': 1})], Int32()),
     ([Counter({'unsigned': 1, 'short': 1}),
       Counter({'unsigned': 1, 'short': 1, 'int': 1})], UInt32()),
     ([Counter({'int': 1}), Counter({'signed': 1}), Counter({'signed': 1, 'int': 1})],
      Int32()),
     ([Counter({'unsigned': 1}), Counter({'unsigned': 1, 'int': 1})], UInt32()),
     ([Counter({'long': 1}), Counter({'signed': 1, 'long': 1}),
       Counter({'long': 1, 'int': 1}),
       Counter({'signed': 1, 'long': 1, 'int': 1})], Int64()),
     ([Counter({'unsigned': 1, 'long': 1}),
       Counter({'unsigned': 1, 'long': 1, 'int': 1})], UInt64()),
     ([Counter({'long': 2}), Counter({'long': 2, 'signed': 1}),
       Counter({'long': 2, 'int': 1}),
       Counter({'long': 2, 'signed': 1, 'int': 1})], Int64()),
     ([Counter({'long': 2, 'unsigned': 1}),
       Counter({'long': 2, 'unsigned': 1, 'int': 1})], UInt64()),
     ([Counter({'float': 1})], Float()),
     ([Counter({'double': 1})], Double()),
     ([Counter({'long': 1, 'double': 1})], Double())]


def normalize(specifiers: List[str]):
    assert frozenset(specifiers).issubset(builtinTypes)
    cntr = Counter(specifiers)
    for x in __c:
        if cntr in x[0]:
            return x[1]
    raise KeyError('illegal type specifiers:{0}'.format(' '.join(map(str, specifiers))))
