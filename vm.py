import struct

mem = bytearray(256)

#
# class Register:
#     def __init__(self):
#         self.value = 0
#
#     def __iadd__(self, other):
#         self.value += other
#         return self
#
#     def setValue(self, value):
#         self.value = value


pc = 0
rsp = 0
rbp = 0


def param(*types):
    assert all(isinstance(x, type) for x in types)

    def inner1(f):
        def inner2(*args):
            assert len(args) == len(types)
            assert all(isinstance(x, y) for x, y in zip(args, types))
            return f(*args)

        return inner2

    return inner1


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
    def unpackI1(address: int) -> int:
        return Unpacker.i1.unpack_from(mem, address)[0]

    @staticmethod
    def unpackI4(address: int) -> int:
        return Unpacker.i4.unpack_from(mem, address)[0]

    @staticmethod
    def unpackI8(address: int) -> int:
        return Unpacker.i8.unpack_from(mem, address)[0]

    @staticmethod
    def unpackU1(address: int) -> int:
        return Unpacker.u1.unpack_from(mem, address)[0]

    @staticmethod
    def unpackU4(address: int) -> int:
        return Unpacker.u4.unpack_from(mem, address)[0]

    @staticmethod
    def unpackU8(address: int) -> int:
        return Unpacker.u8.unpack_from(mem, address)[0]

    @staticmethod
    def unpackF4(address: int) -> float:
        return Unpacker.f4.unpack_from(mem, address)[0]

    @staticmethod
    def unpackF8(address: int) -> float:
        return Unpacker.f8.unpack_from(mem, address)[0]

    @staticmethod
    def unpackPtr(address: int) -> int:
        return Unpacker.u8.unpack_from(mem, address)[0]


class Packer:
    @staticmethod
    def packU1(address: int):
        def inner(value: int):
            Unpacker.u1.pack_into(mem, address, value & 0xff)

        return inner

    @staticmethod
    def packU4(address: int):
        def inner(value: int):
            Unpacker.u4.pack_into(mem, address, value & 0xffff_ffff)

        return inner

    @staticmethod
    def packU8(address: int):
        def inner(value: int):
            Unpacker.u8.pack_into(mem, address, value & ((1 << 64) - 1))

        return inner

    @staticmethod
    def packF4(address: int):
        def inner(value: float):
            assert isinstance(value, float)
            Unpacker.f4.pack_into(mem, address, value)

        return inner

    @staticmethod
    def packF8(address: int):
        def inner(value: float):
            assert isinstance(value, float)
            Unpacker.f8.pack_into(mem, address, value)

        return inner

    @staticmethod
    def packPtr(address: int):
        def inner(value: int):
            assert isinstance(value, int)
            assert 0 <= value
            Unpacker.u8.pack_into(mem, address, value)

        return inner

#
# def loadAndStore(operator):
#     def res(width, lhs, rhs1, rhs2=None):
#         assert width in (1, 4, 8)
#         load, store = None, None
#         if width == 1:
#             load, store = Unpacker.unpackU1, Packer.packU1
#         elif width == 4:
#             load, store = Unpacker.unpackU4, Packer.packU4
#         elif width == 8:
#             load, store = Unpacker.unpackU8, Packer.packU8
#         store(lhs, operator(load(rhs1), load(rhs2)))
#
#     return res
#
#
# def loadAndStoreF(operator):
#     def res(width, lhs, rhs1, rhs2=None):
#         assert width in (4, 8)
#         load, store = None, None
#         if width == 4:
#             load, store = Unpacker.unpackF4, Packer.packF4
#         elif width == 8:
#             load, store = Unpacker.unpackF8, Packer.packF8
#         if rhs2 is None:
#             store(lhs, operator(load(rhs1)))
#         else:
#             store(lhs, operator(load(rhs1), load(rhs2)))
#
#     return res
#
#
# @loadAndStore
# def add(rhs1: int, rhs2: int):
#     return rhs1 + rhs2
#
#
# @loadAndStore
# def sub(rhs1: int, rhs2: int):
#     return rhs1 - rhs2
#
#
# @loadAndStore
# def mul(rhs1, rhs2):
#     assert isinstance(rhs1, int) and isinstance(rhs2, int)
#     return rhs1 * rhs2
#
#
# @loadAndStore
# def div(rhs1, rhs2):
#     assert isinstance(rhs1, int) and isinstance(rhs2, int)
#     return rhs1 // rhs2
#
#
# def idiv(width, lhs, rhs1, rhs2):
#     assert width in (1, 4, 8)
#     load, store = None, None
#     x = 0
#     if width == 1:
#         load, store = Unpacker.unpackI1, Packer.packU1
#         x = 0xff
#     elif width == 4:
#         load, store = Unpacker.unpackI4, Packer.packU4
#         x = 0xffff_ffff
#     elif width == 8:
#         load, store = Unpacker.unpackI8, Packer.packU8
#         x = 0xffff_ffff_ffff_ffff
#     store(lhs, (load(rhs1) // load(rhs2)) & x)
#
#
# @loadAndStore
# def bitwiseAnd(rhs1, rhs2):
#     assert isinstance(rhs1, int) and isinstance(rhs2, int)
#     return rhs1 & rhs2
#
#
# @loadAndStore
# def bitwiseOr(rhs1, rhs2):
#     assert isinstance(rhs1, int) and isinstance(rhs2, int)
#     return rhs1 | rhs2
#
#
# @loadAndStore
# def bitwiseNot(rhs1):
#     assert isinstance(rhs1, int)
#     return ~rhs1
#
#
# @loadAndStore
# def neg(rhs1):
#     assert isinstance(rhs1, int)
#     return -rhs1
#
#
# @loadAndStore
# def shl(rhs1, rhs2):
#     assert isinstance(rhs1, int) and isinstance(rhs2, int)
#     return rhs1 << rhs2
#
#
# @loadAndStore
# def shr(rhs1, rhs2):
#     assert isinstance(rhs1, int) and isinstance(rhs2, int)
#     return rhs1 >> rhs2
#
#
# @loadAndStoreF
# def fadd(rhs1, rhs2):
#     assert isinstance(rhs1, float) and isinstance(rhs2, float)
#     return rhs1 + rhs2
#
#
# @loadAndStoreF
# def fsub(rhs1, rhs2):
#     assert isinstance(rhs1, float) and isinstance(rhs2, float)
#     return rhs1 - rhs2
#
#
# @loadAndStoreF
# def fmul(rhs1, rhs2):
#     assert isinstance(rhs1, float) and isinstance(rhs2, float)
#     return rhs1 + rhs2
#
#
# @loadAndStore
# def fdiv(rhs1, rhs2):
#     assert isinstance(rhs1, float) and isinstance(rhs2, float)
#     return rhs1 / rhs2
#
#
# def lt(rhs1, rhs2):
#     assert type(rhs1) == type(rhs2)
#     return int(rhs1 < rhs2)
#
#
# def le(rhs1, rhs2):
#     assert type(rhs1) == type(rhs2)
#     return int(rhs1 <= rhs2)
#
#
# def gt(rhs1, rhs2):
#     assert type(rhs1) == type(rhs2)
#     return int(rhs1 > rhs2)
#
#
# def ge(rhs1, rhs2):
#     assert type(rhs1) == type(rhs2)
#     return int(rhs1 >= rhs2)
#
#
# def eq(rhs1, rhs2):
#     assert type(rhs1) == type(rhs2)
#     return int(rhs1 == rhs2)
#
#
# def ne(rhs1, rhs2):
#     assert type(rhs1) == type(rhs2)
#     return int(rhs1 != rhs2)
#
#
# def mov(destination: int, source: int, length):
#     mem[destination:destination + length] = mem[source:source + length]
#
#
# def cmp(rhs1: int, delta: int):
#     global pc
#     if rhs1:
#         pc += delta
#
#
# def jmp(delta: int):
#     global pc
#     pc += delta
#
#
# def push(width: int, src: int):
#     global rsp
#     rsp -= width
#     mov(rsp, src, width)
#
#
# def pushq(n: int):
#     global rsp
#     rsp -= 8
#     Packer.packU8(rsp, n)
#
#
# def pop(width, destination):
#     global rsp
#     mov(destination, rsp, width)
#     rsp += width
#
#
# def popq() -> int:
#     global rsp
#     res = Unpacker.unpackU8(rsp)
#     rsp += 8
#     return res
#
#
# def call(delta: int):
#     global pc
#     global rsp
#     pushq(pc)
#     pc += delta
#
#
# def ret():
#     global pc
#     global rsp
#     pc = popq()
