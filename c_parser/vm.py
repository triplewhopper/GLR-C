import struct

mem = bytearray(10000000)


class Register:
    def __init__(self):
        self.value = 0

    def __iadd__(self, other):
        self.value += other
        return self

    def setValue(self, value):
        self.value = value


pc = 0
rsp = 0
rbp = 0


class Unpacker:
    i1 = struct.Struct('c')
    i4 = struct.Struct('i')
    i8 = struct.Struct('q')
    u1 = struct.Struct('c')
    u4 = struct.Struct('I')
    u8 = struct.Struct('Q')
    f4 = struct.Struct('f')
    f8 = struct.Struct('d')

    @staticmethod
    def unpackI1(address):
        return Unpacker.i1.unpack_into(mem, address)

    @staticmethod
    def unpackI4(address):
        return Unpacker.i4.unpack_into(mem, address)

    @staticmethod
    def unpackI8(address):
        return Unpacker.i8.unpack_into(mem, address)

    @staticmethod
    def unpackU1(address):
        return Unpacker.u1.unpack_into(mem, address)

    @staticmethod
    def unpackU4(address):
        return Unpacker.u4.unpack_into(mem, address)

    @staticmethod
    def unpackU8(address):
        return Unpacker.u8.unpack_into(mem, address)

    @staticmethod
    def unpackF4(address):
        return Unpacker.f4.unpack_into(mem, address)

    @staticmethod
    def unpackF8(address):
        return Unpacker.f8.unpack_into(mem, address)

    @staticmethod
    def unpackPtr(address):
        return Unpacker.u8.unpack_into(mem, address)


def checkInt(f):
    def res(value):
        assert isinstance(value, int)
        return f(value)

    return res


class Packer:
    @staticmethod
    @checkInt
    def packU1(address, value):
        Unpacker.u1.pack_into(mem, address, value & 0xff)

    @staticmethod
    @checkInt
    def packU4(address, value):
        Unpacker.u4.pack_into(mem, address, value & 0xffff_ffff)

    @staticmethod
    @checkInt
    def packU8(address, value):
        Unpacker.u8.pack_into(mem, address, value & ((1 << 64) - 1))

    @staticmethod
    def packF4(address, value):
        assert isinstance(value, float)
        Unpacker.f4.pack_into(mem, address, value)

    @staticmethod
    def packF8(address, value):
        assert isinstance(value, float)
        Unpacker.f8.pack_into(mem, address, value)

    @staticmethod
    def packPtr(address, value):
        assert isinstance(value, int)
        assert 0 <= value
        Unpacker.u8.pack_into(mem, address, value)


def loadAndStore(operator):
    def res(width, lhs, rhs1, rhs2=None):
        assert width in (1, 4, 8)
        load, store = None, None
        if width == 1:
            load, store = Unpacker.unpackU1, Packer.packU1
        elif width == 4:
            load, store = Unpacker.unpackU4, Packer.packU4
        elif width == 8:
            load, store = Unpacker.unpackU8, Packer.packU8
        store(lhs, operator(load(rhs1), load(rhs2)))

    return res


def loadAndStoreF(operator):
    def res(width, lhs, rhs1, rhs2=None):
        assert width in (4, 8)
        load, store = None, None
        if width == 4:
            load, store = Unpacker.unpackF4, Packer.packF4
        elif width == 8:
            load, store = Unpacker.unpackF8, Packer.packF8
        if rhs2 is None:
            store(lhs, operator(load(rhs1)))
        else:
            store(lhs, operator(load(rhs1), load(rhs2)))

    return res





@loadAndStore
def add(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 + rhs2


@loadAndStore
def sub(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 - rhs2


@loadAndStore
def mul(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 * rhs2


@loadAndStore
def div(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 // rhs2


def idiv(width, lhs, rhs1, rhs2):
    assert width in (1, 4, 8)
    load, store = None, None
    x = 0
    if width == 1:
        load, store = Unpacker.unpackI1, Packer.packU1
        x = 0xff
    elif width == 4:
        load, store = Unpacker.unpackI4, Packer.packU4
        x = 0xffff_ffff
    elif width == 8:
        load, store = Unpacker.unpackI8, Packer.packU8
        x = 0xffff_ffff_ffff_ffff
    store(lhs, (load(rhs1) // load(rhs2)) & x)


@loadAndStore
def bitwiseAnd(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 & rhs2


@loadAndStore
def bitwiseOr(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 | rhs2


@loadAndStore
def bitwiseNot(rhs1):
    assert isinstance(rhs1, int)
    return ~rhs1


@loadAndStore
def neg(rhs1):
    assert isinstance(rhs1, int)
    return -rhs1


@loadAndStore
def shl(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 << rhs2


@loadAndStore
def shr(rhs1, rhs2):
    assert isinstance(rhs1, int) and isinstance(rhs2, int)
    return rhs1 >> rhs2


@loadAndStoreF
def fadd(rhs1, rhs2):
    assert isinstance(rhs1, float) and isinstance(rhs2, float)
    return rhs1 + rhs2


@loadAndStoreF
def fsub(rhs1, rhs2):
    assert isinstance(rhs1, float) and isinstance(rhs2, float)
    return rhs1 - rhs2


@loadAndStoreF
def fmul(rhs1, rhs2):
    assert isinstance(rhs1, float) and isinstance(rhs2, float)
    return rhs1 + rhs2


@loadAndStore
def fdiv(rhs1, rhs2):
    assert isinstance(rhs1, float) and isinstance(rhs2, float)
    return rhs1 / rhs2


def lt(rhs1, rhs2):
    assert type(rhs1) == type(rhs2)
    return int(rhs1 < rhs2)


def le(rhs1, rhs2):
    assert type(rhs1) == type(rhs2)
    return int(rhs1 <= rhs2)


def gt(rhs1, rhs2):
    assert type(rhs1) == type(rhs2)
    return int(rhs1 > rhs2)


def ge(rhs1, rhs2):
    assert type(rhs1) == type(rhs2)
    return int(rhs1 >= rhs2)


def eq(rhs1, rhs2):
    assert type(rhs1) == type(rhs2)
    return int(rhs1 == rhs2)


def ne(rhs1, rhs2):
    assert type(rhs1) == type(rhs2)
    return int(rhs1 != rhs2)


def mov(destination: int, source: int, length):
    mem[destination:destination + length] = mem[source:source + length]


def cmp(rhs1: int, delta: int):
    global pc
    if rhs1:
        pc += delta


def jmp(delta: int):
    global pc
    pc += delta


def push(width: int, src: int):
    global rsp
    rsp -= width
    mov(rsp, src, width)


def pushq(n: int):
    global rsp
    rsp -= 8
    Packer.packU8(rsp, n)


def pop(width, destination):
    global rsp
    mov(destination, rsp, width)
    rsp += width


def popq() -> int:
    global rsp
    res = Unpacker.unpackU8(rsp)
    rsp += 8
    return res


def call(delta: int):
    global pc
    global rsp
    pushq(pc)
    pc += delta


def ret():
    global pc
    global rsp
    pc = popq()
