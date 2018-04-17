from typing import List, Tuple, Callable, Set, Iterable
import c_parser.mem
import c_parser.c_exceptions
import struct

error = c_parser.c_exceptions.Failed


class CType:
    mem = c_parser.mem.mem

    def __init__(self):
        self.qualifiers = set()

    @property
    def width(self):
        raise NotImplementedError()

    def addQualifier(self, qualifiers):
        if isinstance(qualifiers, str):
            self.qualifiers.add(qualifiers)
            return
        elif isinstance(qualifiers, (list, tuple, set, frozenset)):
            for qualifier in qualifiers:
                assert isinstance(qualifier, str)
                self.qualifiers.add(qualifier)
            return
        raise TypeError(qualifiers)

    @staticmethod
    def join(qualifiers):
        return '' if not qualifiers else ' '.join(qualifiers) + ' '


class ParenType(CType):

    def __init__(self, returnType, paramTypes):
        CType.__init__(self)
        assert isinstance(returnType, CType)
        if isValidReturnType(returnType):
            self.returnType: CType = returnType

        self.paramTypes: Tuple[CType] = tuple(Pointer(t.createFunctionPrototype())
                                              if isinstance(t, ParenType)
                                              else t
                                              for t in paramTypes)

    def createFunctionPrototype(self):
        return FunctionProtoType(self.returnType, self.paramTypes)

    def createFunction(self, entrance):
        return Function(self.returnType, self.paramTypes, entrance)

    @property
    def width(self):
        return 1

    def __str__(self):
        return '%s(%s)' % (
            self.returnType,
            ', '.join(str(x) for x in self.paramTypes)
        )


class Function(ParenType):
    @property
    def width(self):
        return 1

    def __init__(self, returnType, paramTypes, entrance):
        ParenType.__init__(self, returnType, paramTypes)
        self.entrance = entrance

    def __str__(self):
        return f"Function {super(Function, self).__str__()}"


class FunctionProtoType(ParenType):
    def __init__(self, returnType, paramTypes: Tuple[CType]):
        CType.__init__(self)
        assert not isinstance(returnType, (Array, FunctionProtoType))
        self.parenType = ParenType(returnType, paramTypes)

    def __str__(self):
        return f"FunctionPrototype {super(FunctionProtoType, self).__str__()}"

    def createFunction(self, entrance):
        return super(FunctionProtoType, self).createFunction(entrance)

    @property
    def width(self):
        return 1


class CompleteMixin:

    def __init__(self):
        pass

    @property
    def isComplete(self):
        raise NotImplementedError()

    def complete(self, *args):
        raise NotImplementedError()


class Struct(CompleteMixin, CType):
    anonymousCount = 0

    def __init__(self, tag: str = ''):
        CType.__init__(self)
        CompleteMixin.__init__(self)
        assert isinstance(tag, str)
        self.tag: str = Struct._newTagName(tag)
        self._isComplete: bool = False
        self.memberTypes: Tuple[CType] = None
        self.__width: int = 0

    @staticmethod
    def _newTagName(x: str):
        if x:
            return x
        res = 'anonymousStruct<%s>' % Struct.anonymousCount
        Struct.anonymousCount += 1
        return res

    @property
    def isComplete(self):
        return self._isComplete

    def complete(self, *args):
        if self.isComplete:
            raise error(f'struct {self.tag} is already complete.')
        self.memberTypes: Tuple[CType] = args
        self._isComplete = True

        for member in self.memberTypes:
            if isinstance(member, CompleteMixin) and not member.isComplete:
                raise error(f'{member} is incomplete yet.')
        self.__width = sum(member.width for member in self.memberTypes)
        self.__dict__['complete']=None
        return self

    def __str__(self):
        # if self._isComplete:
        #     return f'struct %s{{%s}}' % (
        #         self.tag,
        #         ', '.join(map(str, self.memberTypes)))
        return f'struct {self.tag}'

    def __hash__(self):
        return hash(self.tag)

    def __eq__(self, other):
        assert isinstance(other, Struct)
        return self.memberTypes == other.memberTypes and self.isComplete == other.isComplete

    @property
    def width(self):
        if not self.isComplete:
            raise RuntimeError()
        return self.__width


class Enum(CompleteMixin, CType):
    def __init__(self):
        super(Enum, self).__init__()
        raise NotImplementedError()


class SignMixin:
    def __init__(self, signed=True):
        self.signed = signed

    @property
    def width(self):
        raise NotImplementedError()

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.signed == other.signed


class Char(CType, SignMixin):
    LENGTH = 1

    def __init__(self, signed=True):
        CType.__init__(self)
        SignMixin.__init__(self, signed)

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'char' if self.signed else 'unsigned char')

    @property
    def width(self):
        return Char.LENGTH


class Int32(CType, SignMixin):
    LENGTH = 4

    def __init__(self, signed=True):
        CType.__init__(self)
        SignMixin.__init__(self, signed)

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'int' if self.signed else 'unsigned int')

    __repr__ = __str__

    @property
    def width(self):
        return Int32.LENGTH


class Int64(CType, SignMixin):
    LENGTH = 8

    def __init__(self, signed=True):
        CType.__init__(self)
        SignMixin.__init__(self, signed)

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'long long' if self.signed else 'unsigned long long')

    __repr__ = __str__

    @property
    def width(self):
        return Int64.LENGTH


class Double(CType):
    LENGTH = 8

    def __init__(self):
        super(Double, self).__init__()

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'double')

    __repr__ = __str__

    @property
    def width(self):
        return Double.LENGTH


class Float(Double):
    LENGTH = 4

    def __init__(self):
        super(Float, self).__init__()

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'float')

    __repr__ = __str__

    @property
    def width(self):
        return Float.LENGTH


class Pointer(CType):
    LENGTH = 8

    def __init__(self, pointsToType):
        super(Pointer, self).__init__()
        assert isinstance(pointsToType, CType)
        self.pointsToType = pointsToType

    def __str__(self):
        if isinstance(self.pointsToType, ParenType):
            return f'''
                {CType.join(self.qualifiers)}
                {self.pointsToType.returnType} (*)
                ({self.pointsToType.paramTypes})
                '''
        return f'{CType.join(self.qualifiers)}({self.pointsToType})*'

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        assert isinstance(other, Pointer)
        return self.pointsToType == other.pointsToType

    @property
    def width(self):
        return Pointer.LENGTH


class Array(Pointer, CompleteMixin):

    def __init__(self, pointsToType: CType, length: int = None):
        Pointer.__init__(self, pointsToType)
        CompleteMixin.__init__(self)
        self.length = length
        if isinstance(pointsToType, CompleteMixin) and not pointsToType.isComplete:
            raise error(f"array has incomplete element type '{pointsToType}'.")

    def __str__(self):
        if self.isComplete:
            return f'{CType.join(self.qualifiers)}Array({self.length}, {self.pointsToType})'
        else:
            return f'{CType.join(self.qualifiers)}IncompleteArray({self.pointsToType})'

    def __eq__(self, other):
        assert isinstance(other, Array)
        return self.pointsToType == other.pointsToType \
               and self.length == other.length

    @property
    def isComplete(self):
        return self.length is not None

    def complete(self, length):
        assert isinstance(length, int)
        self.length = length

    @property
    def width(self):
        return self.length * self.pointsToType.width


class Void(CType, CompleteMixin):
    LENGTH = 1

    def __str__(self):
        return 'void'

    @property
    def width(self):
        return Void.LENGTH

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return isinstance(other, Void)

    @property
    def isComplete(self):
        return False

    def complete(self, *args):
        raise RuntimeError('type void cannot be completed.')


def isValidReturnType(x: CType) -> bool:
    assert isinstance(x, CType)
    if isinstance(x, Void): return True
    if isinstance(x, Array): raise error(f'function cannot return type {x}')
    if isinstance(x, ParenType):
        raise error(f'function cannot return function type {x}')
    if isinstance(x, CompleteMixin):
        if x.isComplete:
            return True
        raise error(f'function cannot return incomplete type {x}')
    return True


from collections import Counter

c = [([Counter({'void': 1})],
      Void()),
     ([Counter({'char': 1})],
      Char()),
     ([Counter({'signed': 1, 'char': 1})],
      Char(True)),
     ([Counter({'unsigned': 1, 'char': 1})],
      Char(False)),
     ([Counter({'short': 1}), Counter({'signed': 1, 'short': 1}), Counter({'short': 1, 'int': 1}),
       Counter({'signed': 1, 'short': 1, 'int': 1})],
      Int32(True)),
     ([Counter({'unsigned': 1, 'short': 1}), Counter({'unsigned': 1, 'short': 1, 'int': 1})],
      Int32(False)),
     ([Counter({'int': 1}), Counter({'signed': 1}), Counter({'signed': 1, 'int': 1})],
      Int32(True)),
     ([Counter({'unsigned': 1}), Counter({'unsigned': 1, 'int': 1})],
      Int32(False)),
     ([Counter({'long': 1}), Counter({'signed': 1, 'long': 1}), Counter({'long': 1, 'int': 1}),
       Counter({'signed': 1, 'long': 1, 'int': 1})],
      Int64()),
     ([Counter({'unsigned': 1, 'long': 1}), Counter({'unsigned': 1, 'long': 1, 'int': 1})],
      Int64(False)),
     ([Counter({'long': 2}), Counter({'long': 2, 'signed': 1}), Counter({'long': 2, 'int': 1}),
       Counter({'long': 2, 'signed': 1, 'int': 1})],
      Int64()),
     ([Counter({'long': 2, 'unsigned': 1}), Counter({'long': 2, 'unsigned': 1, 'int': 1})],
      Int64(False)),
     ([Counter({'float': 1})],
      Float()),
     ([Counter({'double': 1})],
      Double()),
     ([Counter({'long': 1, 'double': 1})],
      Double())]


def normalize(specifiers: list) -> CType:
    """
    this function takes a list of specifiers, then returns an instance of CType.
    the symbol table will not be modified.
    """
    assert isinstance(specifiers, list)
    cnt = Counter(specifiers)
    for k, v in c:
        for e in k:
            if cnt == e:
                return v
    if len(specifiers) == 1:
        if isinstance(specifiers[0], c_parser.ast_node.RecordDecl):
            return specifiers[0].recordType
        if isinstance(specifiers[0], CType):
            return specifiers[0]
        # return CompleteMixin(specifiers[0].tag)
    raise RuntimeError('unknown specifiers: %s' % specifiers)
