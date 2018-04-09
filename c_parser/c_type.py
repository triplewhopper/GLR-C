from typing import List, Tuple, Callable, Set, Iterable
from c_parser.ast_node import RecordDecl


class CType:
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


class FunctionProtoType(CType):
    def __init__(self, returnType, argTypes: Tuple[CType]):
        super(FunctionProtoType, self).__init__()
        assert not isinstance(returnType, (Array, FunctionProtoType))
        self.argTypes: Tuple[CType] = argTypes
        self.returnType: CType = returnType

    def __str__(self):
        return '%s(%s)' % (
            self.returnType,
            ', '.join(str(x) for x in self.argTypes)
        )

    @property
    def width(self):
        return 1


class Function(FunctionProtoType):
    def __init__(self, returnType, argTypes, functionName, addr):
        super(Function, self).__init__(returnType, argTypes)
        self.functionName = functionName
        self.addr = addr

    def __str__(self):
        return '%s %s(%s)' % (
            self.returnType,
            self.functionName,
            ', '.join(str(x) for x in self.argTypes)
        )


class IncompleteStruct(CType):
    def __init__(self, tag):
        super(IncompleteStruct, self).__init__()
        assert isinstance(tag, str) and tag
        self.tag = tag

    def __str__(self):
        return 'struct %s' % self.tag


class Struct(IncompleteStruct):
    anonymousCount = 0

    def __init__(self, tag: str = '', *args):
        super(Struct, self).__init__(tag)
        if not tag:
            self.tag: str = 'anonymousStruct<%s>' % Struct.anonymousCount
            Struct.anonymousCount += 1
        else:
            self.tag: str = tag
        self.memberTypes: Tuple[CType] = args
        self.__width = sum(member.width for member in self.memberTypes)

    def __str__(self):
        return 'struct %s{%s}' % (
            self.tag,
            ', '.join(
                str(member)
                for member in self.memberTypes))

    def __hash__(self):
        return hash(self.tag)

    def __eq__(self, other):
        assert isinstance(other, Struct)
        return self.memberTypes == other.memberTypes

    @property
    def width(self):
        return self.__width


class Enum(CType):
    def __init__(self):
        super(Enum, self).__init__()
        raise NotImplementedError()


class Sign(CType):
    def __init__(self, signed=True):
        super(Sign, self).__init__()
        self.signed = signed

    @property
    def width(self):
        raise NotImplementedError()

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.signed == other.signed


class Char(Sign):
    LENGTH = 1

    def __init__(self, signed=True):
        super(Char, self).__init__(signed)

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'char' if self.signed else 'unsigned char')

    @property
    def width(self):
        return Char.LENGTH


class Int32(Sign):
    LENGTH = 4

    def __init__(self, signed=True):
        super(Int32, self).__init__(signed)

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'int' if self.signed else 'unsigned int')

    __repr__ = __str__

    @property
    def width(self):
        return Int32.LENGTH


class Int64(Sign):
    LENGTH = 8

    def __init__(self, signed=True):
        super(Int64, self).__init__(signed)

    def __str__(self):
        return '%s%s' % (CType.join(self.qualifiers), 'long long' if self.signed else 'unsigned long long')

    __repr__ = __str__

    @property
    def width(self):
        return Int32.LENGTH


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
        self.pointsToType = pointsToType

    def __str__(self):
        return '%s(%s)*' % (CType.join(self.qualifiers), self.pointsToType)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        assert isinstance(other, Pointer)
        return self.pointsToType == other.pointsToType

    @property
    def width(self):
        return Pointer.LENGTH


class Array(Pointer):
    def __init__(self, pointsToType: CType, length: int):
        super(Array, self).__init__(pointsToType)
        self.length = length

    def __str__(self):
        return '%sarray(%d, %s)' % (CType.join(self.qualifiers), self.length, self.pointsToType)

    def __eq__(self, other):
        assert isinstance(other, Array)
        return self.pointsToType == other.pointsToType \
               and self.length == other.length

    @property
    def width(self):
        return self.length * self.pointsToType.width


class Void(CType):
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


def normalize(specifiers: list):
    assert isinstance(specifiers, list)
    cnt = Counter(specifiers)
    for k, v in c:
        for e in k:
            if cnt == e:
                return v
    if len(specifiers) == 1 and isinstance(specifiers[0], RecordDecl):
        return IncompleteStruct(specifiers[0].tag)
    raise RuntimeError('unknown specifiers: %s' % specifiers)
