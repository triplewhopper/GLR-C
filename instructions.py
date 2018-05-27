"""
 1,2,4,8
 mov, lea, shl, shr, cmp, and, or, xor, neg, not,
 add, sub, mul, div, mod, inc, dec,

 widen

 addf, subf, mulf, divf,
 dadd, dsub, dmul, ddiv,
 idiv,
拓宽指令。
Convert from $src(signed|unsigned $width) to I_$i
Convert from I_$i to $dest(signed|unsigned $width)
Convert F_$i <-> $dest
Convert F_$i <-> I_$i
add I_$i I_$j
shl
shr
cmp
and
or
xor
div
mod
inc
dec
idiv

neg I_$i
not I_$i
8字节算数运算 shl, shr, cmp, and, or, xor, neg, not,
 add, sub, mul, div, mod, inc, dec,idiv,
double算数运算 dadd, dsub, dmul, ddiv,
Conversion。cu1, cu4, cu8, ci1, ci4, ci8, cf4, cf8
跳转指令。jmp, call, ret

binary +,-,*,/,<<,>>,&,|,%,&&,||,>,<,>=,<=,==,!=,','



 IP
 SP
 BP
 IA,IB,IC FA,FB,FC
 STACK
"""
from AST import c_type
from typing import Union, Dict, List, Tuple
from vm import Unpacker, Packer, mem

i32 = 4
f32 = 4
f64 = 8


class Act:
    def act(self):
        pass


width = {'i8': 1, 'u8': 1, 'i32': 4, 'u32': 4, 'i64': 8, 'u64': 8, 'f32': 4, 'f64': 8, 'ptr': 8}
unpacker = {'i8': Unpacker.unpackI1,
            'u8': Unpacker.unpackU1,
            'i32': Unpacker.unpackI4,
            'u32': Unpacker.unpackU4,
            'i64': Unpacker.unpackI8,
            'u64': Unpacker.unpackU8,
            'f32': Unpacker.unpackF4,
            'f64': Unpacker.unpackF8,
            'ptr': Unpacker.unpackPtr}
mask = {1: 0xff, 4: 0xffff_ffff, 8: 0xffff_ffff_ffff_ffff}


class LoadInstantly:
    __slots__ = ('__tc', '__value', '__comment')

    def __init__(self, type: 'c_type.Type', value: Union[int, float, List[int]], comment: str = '.const'):
        assert isinstance(type, c_type.Type)
        self.__tc = type.typeCode()
        self.__value = value
        self.__comment = '// ' + comment if comment else ''
        assert self.__tc in width

    def exec(self, vm: 'HAHA'):
        if isinstance(self.__value, list):
            assert len(self.__value) == 1
            self.__value = self.__value[0]
        vm.push((self.__value, width[self.__tc]))

    def __str__(self):
        return 'load :{} :{} instantly {}'.format(self.__tc, self.__value, self.__comment)


#
# class LoadRaw:
#     __slots__ = ('__width', '__src', '__comment')
#
#     def __init__(self, src: int, width: int, comment: str = ''):
#         self.__width = width
#         self.__src = src
#         self.__comment = '// ' + comment if comment else ''
#
#     def __str__(self):
#         return 'load raw from @:{} with width :{} {}'.format(self.__src, self.__width, self.__comment)

#
# class LoadFrom:
#     __slots__ = ('__tc', '__src', '__comment', '__isGlobal')
#
#     def __init__(self, type: 'c_type.Type', src: int, comment: str, isGlobal: bool = False):
#         assert isinstance(type, c_type.Type)
#         assert isinstance(src, int)
#         self.__tc = type.typeCode()
#         self.__src = src
#         self.__comment = '// ' + comment if comment else ''
#         self.__isGlobal = isGlobal
#         assert self.__tc in width
#
#     def exec(self, vm: 'HAHA'):
#         if self.__isGlobal:
#             value = unpacker[self.__tc](self.__src)
#         else:
#             value = unpacker[self.__tc](self.__src + vm.bp)
#         vm.push((value, width[self.__tc]))
#
#     def __str__(self):
#         if self.__isGlobal:
#             return 'load as {} from @{} {}'.format(self.__tc, self.__src, self.__comment)
#         return 'load as :{} from bp[{}] {}'.format(self.__tc, self.__src, self.__comment)

def pmem(vm):
    print('mem:')
    for i in range(len(vm.mem)):
        print('{:02x}'.format(vm.mem[i]), end='')
        if (i + 1) % 16 == 0:
            print()
        elif (i + 1) % 8 == 0:
            print('  ', end='')
        else:
            print(' ', end='')
    print()


class LoadTop:
    __slots__ = ('__tc', '__comment')

    def __init__(self, type: 'c_type.Type', comment: str):
        assert isinstance(type, c_type.Type)
        self.__tc = type.typeCode()
        self.__comment = '// ' + comment if comment else ''

    def exec(self, vm: 'HAHA'):
        if self.__tc == 'function':
            return
        v, w = vm.pop()
        assert isinstance(v, int)
        assert w == 8
        v = unpacker[self.__tc](v)
        pmem(vm)
        vm.push((v, width[self.__tc]))

    def __str__(self):
        return 'load as :{} from @[top] {}'.format(self.__tc, self.__comment)


class Cast:
    __slots__ = ('__srcTy', '__destTy')

    def __init__(self, src: 'c_type.Type', dest: 'c_type.Type'):
        self.__srcTy = src.typeCode()
        self.__destTy = dest.typeCode()
        # assert self.__srcTy in width and self.__destTy in width

    def exec(self, vm: 'HAHA'):
        x, y = self.__srcTy, self.__destTy
        if x == 'function':
            assert y == 'ptr'
            return
        if x == 'ptr': x = 'i64'
        if y == 'ptr': y = 'i64'

        v, w = vm.pop()

        wx, wy = width[x], width[y]
        assert w == wx
        assert x[0] in ('i', 'u', 'f')
        assert y[0] in ('i', 'u', 'f')
        if y[0] == 'f':
            vm.push((float(v), wy))
            return
            # 以下y[0]!='f'.
        if x[0] == 'f':
            v = int(v) & (2 ** (8 * wy) - 1)
            if y[0] == 'i' and v >= 2 ** (8 * wy - 1):
                v -= 2 ** (8 * wy)
            vm.push((v, wy))
            return

        if wx == wy:
            if x[0] == 'u' and y[0] == 'i':
                if v >= 2 ** (8 * wy - 1):
                    v -= 2 ** (8 * wy)

            elif x[0] == 'i' and y[0] == 'u':
                v &= 2 ** (8 * wy) - 1

        elif wx < wy:
            if y[0] == 'u':
                v &= 2 ** (8 * wy) - 1

        else:
            v &= 2 ** (8 * wy) - 1
            if y[0] == 'i' and v >= 2 ** (8 * wy - 1):
                v -= 2 ** (8 * wy)

        vm.push((v, wy))

    def __str__(self):
        return 'cast from {} to {}'.format(self.__srcTy, self.__destTy)


class HAHA:
    def __init__(self, cmd: list, entrance: Dict[str, int], sp: int = 0, memSize: int = 100):
        assert isinstance(cmd, list)
        assert isinstance(entrance, dict)
        self.__cmd = cmd
        self.pc = entrance['main']
        self.bp = sp
        self.sp = sp
        self.stack: List = []
        # self.width:List[int] = []
        self.__frames = []
        self.mem = mem

    def get(self):
        res = self.__cmd[self.pc]
        print(self.stack)
        print('bp={}, sp={}'.format(self.bp, self.sp))
        print('..{} {}'.format(self.pc, res))
        self.pc += 1
        return res

    def mainloop(self):
        self.call(self.__cmd[self.pc])
        while self.__frames:
            act = self.get()
            if hasattr(act, 'exec'):
                act.exec(self)
                continue
            if isinstance(act, list):
                a = act[0]
                b = act[-1]
                assert isinstance(a, str)
                assert isinstance(b, int)
                continue
            if isinstance(act, tuple):
                predicate = act[0]

                assert predicate in ('jz', 'jmp', 'break', 'continue', 'unary', 'binary')
                if predicate == 'jz':
                    arg = act[1][-1]
                    assert isinstance(arg, int)
                    value, _ = self.pop()
                    if value == 0:
                        self.pc = arg
                elif predicate in ('jmp', 'break', 'continue'):
                    arg = act[1][-1]
                    assert isinstance(arg, int)
                    self.pc = arg
                elif predicate == 'binary':
                    arg = act[1]
                    assert isinstance(arg, str)
                    self.binary(arg)
                elif predicate == 'unary':
                    arg = act[1]
                    assert isinstance(arg, str)
                    self.unary(arg)
                continue
            if isinstance(act, str):
                if act[0] == '.' or act.startswith('//'):
                    continue
                elif act == 'add bp':
                    (v, w) = self.pop()
                    v += self.bp
                    self.push((v, w))
                elif act == 'add sp':
                    (v, w) = self.pop()
                    v += self.sp
                    self.push((v, w))
                elif act == 'call':
                    (func, _) = self.pop()
                    assert _ == 8
                    print('call function @{}'.format(func))
                    self.call(self.__cmd[func])
                elif act == 'store':  # -2
                    (addr, _) = self.pop()
                    assert _ == 8
                    (value, width) = self.pop()
                    assert isinstance(value, (int, float))
                    if isinstance(value, int):
                        assert width in (1, 4, 8)
                        if width == 1:
                            Packer.packU1(addr)(value)
                        elif width == 4:
                            Packer.packU4(addr)(value)
                        else:
                            Packer.packU8(addr)(value)
                    else:
                        assert width in (4, 8)
                        if width == 4:
                            Packer.packF4(addr)(value)
                        else:
                            Packer.packF8(addr)(value)
                    pmem(self)
                elif act == 'ret':
                    self.ret()
                elif act == 'duplicate':
                    self.duplicate()
                elif act == 'inc':  # 0
                    self.inc()
                elif act == 'dec':  # 0
                    self.dec()
                elif act == 'push sp':  # +1
                    self.push((self.sp, 8))
                elif act == 'pop':  # -1
                    self.pop()
                elif act == 'swap':
                    self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
                else:
                    assert 0
                continue

    def top(self):
        return self.stack[-1]

    def push(self, x):
        self.stack.append(x)

    def call(self, entrance: list):
        (_, funcName, x, lineNumber) = entrance
        assert _ == '.func'
        self.__frames.append((self.bp, x, self.pc))
        print('frames:', self.__frames)
        assert isinstance(x, int)
        self.bp = self.sp
        self.sp += x
        self.jmp(entrance[-1])

    def jmp(self, dest: int):
        assert isinstance(dest, int)
        self.pc = dest

    def ret(self):
        (self.bp, x, self.pc) = self.__frames.pop()
        print('frames:', self.__frames)
        assert isinstance(x, int)
        self.sp -= x

    def pop(self):  # -1
        return self.stack.pop()

    def binary(self, op: str):  # -2+1
        assert op in {'+', '-', '*', '/', '%', '<<', '>>', '>', '<', '>=', '<=', '==', '!=', '&&', '||', '&', '|'}
        y, ty = self.stack.pop()
        x, tx = self.stack.pop()
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))
        assert ty in (1, 4, 8)
        assert tx == ty
        # if op == ',':
        if op == '+':
            self.push((x + y, tx))
        elif op == '-':
            self.push((x - y, tx))
        elif op == '*':
            self.push((x * y, tx))
        elif op == '/':
            if isinstance(x, float) or isinstance(y, float):
                self.push((x / y, tx))
            else:
                self.push((x // y, tx))
        elif op == '%':
            self.push((x % y, tx))
        elif op == '<<':
            self.push((x << y, tx))
        elif op == '>>':
            self.push((x >> y, tx))
        elif op == '>':
            self.push((int(x > y), i32))
        elif op == '<':
            self.push((int(x < y), i32))
        elif op == '>=':
            self.push((int(x >= y), i32))
        elif op == '<=':
            self.push((int(x <= y), i32))
        elif op == '==':
            self.push((int(x == y), i32))
        elif op == '!=':
            self.push((int(x != y), i32))
        elif op == '&&':
            self.push((int(x and y), i32))
        elif op == '||':
            self.push((int(x or y), i32))
        elif op == '&':
            self.push((x & y, tx))
        elif op == '|':
            self.push((x | y, tx))

    def duplicate(self):  # +1
        self.push(self.stack[-1])

    def inc(self):  # -1+1
        (v, w) = self.pop()
        assert isinstance(v, (int, float))
        self.push((v + 1, w))

    def dec(self):  # -1+1
        (v, w) = self.pop()
        assert isinstance(v, (int, float))
        # FIXME: unsigned
        self.push((v - 1, w))

    def unary(self, op: str):  # -1+1
        assert op in {'-', '~', '!'}
        value, width = self.pop()
        if op == '-':
            assert isinstance(value, (int, float))
            self.push((-value, width))
        elif op == '~':
            assert isinstance(value, int)
            self.push((~value, width))
        elif op == '!':
            self.push((0 if value == 0 else 1, width))

#
# class JZ:
#     __slots__ = ['arg']
#
#     def __init__(self, arg=None):
#         self.arg = arg
#
#
# class Register:
#     """
#     :type _value: int|float
#     """
#
#     def __init__(self, value=0):
#         assert isinstance(value, (int, float))
#         self._value = value
#
#     def get(self):
#         raise NotImplementedError()
#
#     def set(self, value):
#         raise NotImplementedError()
#
#
# class IntegerContainer:
#     def get(self) -> int:
#         raise NotImplementedError()
#
#     def set(self, value: int):
#         raise NotImplementedError()
#
#
# class FloatingContainer:
#     def get(self) -> float:
#         raise NotImplementedError()
#
#     def set(self, value: float):
#         raise NotImplementedError()
#
#
# class IntegerRegister(Register, IntegerContainer):
#
#     def __init__(self, value=0):
#         assert isinstance(value, int)
#         super().__init__()
#
#     def get(self):
#         return self._value
#
#     # def getAsSigned(self):
#     #     if self._value & (1<<63):
#     #         return self._value-(1<<64)
#     #     return self._value
#     def set(self, value: int):
#         assert isinstance(value, int)
#         self._value = value
#
#     def convertTo(self, other):
#         if isinstance(other, IntegerAccessor):
#             other.set(self.get())
#         elif isinstance(other, FloatingAccessor):
#             other.set(float(self.get()))
#         else:
#             assert 0
#
#
# class FloatingRegister(Register, FloatingContainer):
#     def __init__(self, value=0):
#         assert isinstance(value, float)
#         super().__init__()
#
#     def get(self):
#         return self._value
#
#     def set(self, value: float):
#         assert isinstance(value, float)
#         self._value = value
#
#     def convertTo(self, other):
#         if isinstance(other, IntegerAccessor):
#             other.set(int(self.get()))
#         elif isinstance(other, FloatingAccessor):
#             other.set(self.get())
#         else:
#             assert 0
#
#
# class Accessor:
#     """
#     :type address: int
#     :type width: int
#     """
#
#     def __init__(self, address: int, width: int):
#         assert isinstance(address, int)
#         assert isinstance(width, int)
#         assert address >= 0 and width in (1, 4, 8)
#         self.address = address
#         self.width = width
#
#     def convertTo(self, register: Union[IntegerRegister, FloatingRegister]):
#         raise NotImplementedError()
#
#
# class IntegerAccessor(Accessor, IntegerContainer):
#     def __init__(self, address: int, width: int, signed: bool):
#         assert isinstance(signed, bool)
#         super().__init__(address, width)
#         if width == 1:
#             self.set = Packer.packU1(self.address)
#             self.get = Unpacker.unpackI1 if signed else Unpacker.unpackU1
#
#         elif width == 4:
#             self.set = Packer.packU4(self.address)
#             self.get = Unpacker.unpackI4 if signed else Unpacker.unpackU4
#
#         elif width == 8:
#             self.set = Packer.packU8(self.address)
#             self.get = Unpacker.unpackI8 if signed else Unpacker.unpackU8
#
#         self.signed = signed
#
#     def convertTo(self, other: Union[IntegerContainer, FloatingContainer]):
#         if isinstance(other, IntegerContainer):
#             other.set(self.get(self.address))
#         elif isinstance(other, FloatingContainer):
#             other.set(float(self.get(self.address)))
#         else:
#             assert 0
#
#
# class FloatingAccessor(Accessor, FloatingContainer):
#     def __init__(self, address: int, width: int):
#         super().__init__(address, width)
#         assert width in (4, 8)
#         if width == 4:
#             self.set = Packer.packF4(self.address)
#             self.get = Unpacker.unpackF4
#
#         elif width == 8:
#             self.set = Packer.packF8(self.address)
#             self.get = Unpacker.unpackF8
#
#     def convertTo(self, other: Union[IntegerContainer, FloatingContainer]):
#         if isinstance(other, IntegerContainer):
#             other.set(int(self.get(self.address)))
#         elif isinstance(other, FloatingContainer):
#             other.set(self.get(self.address))
#         else:
#             assert 0
#
#
# class VM:
#     def __init__(self, mem: bytearray):
#         self.i = [IntegerRegister() for i in range(100)]
#         self.f = [FloatingRegister() for i in range(100)]
#         self.mem = mem
#
#     def mov(self, destination: int, source: int, length: int):
#         assert isinstance(destination, int)
#         assert isinstance(source, int)
#         assert isinstance(length, int)
#         self.mem[destination:destination + length] = self.mem[source:source + length]
#
#     def loadConstInt(self, at: int, val: int):
#         self.i[at].set(val)
#
#     def loadConstFloat(self, at: int, val: float):
#         self.f[at].set(val)
#
#     def add(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() + self.i[c].get())
#
#     def sub(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() - self.i[c].get())
#
#     def mul(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() * self.i[c].get())
#
#     def div(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() // self.i[c].get())
#
#     def mod(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() % self.i[c].get())
#
#     def biAND(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() & self.i[c].get())
#
#     def biOR(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() | self.i[c].get())
#
#     def biXOR(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() ^ self.i[c].get())
#
#     def shl(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() << self.i[c].get())
#
#     def shr(self, a: int, b: int, c: int):
#         self.i[a].set(self.i[b].get() >> self.i[c].get())
#
#     def neg(self, a: int, b: int):
#         self.i[a].set(-self.i[b].get())
#
#     def biNot(self, a: int, b: int):
#         self.i[a].set(~self.i[b].get())
#
#     def i2f(self, a: int, b: int):
#         self.i[a].convertTo(self.f[b])
#
#     def f2i(self, a: int, b: int):
#         self.f[a].convertTo(self.i[b])
#
#     def addf(self, a: int, b: int, c: int):
#         self.f[a].set(self.f[b].get() + self.f[c].get())
#
#     def subf(self, a: int, b: int, c: int):
#         self.f[a].set(self.f[b].get() - self.f[c].get())
#
#     def mulf(self, a: int, b: int, c: int):
#         self.f[a].set(self.f[b].get() * self.f[c].get())
#
#     def divf(self, a: int, b: int, c: int):
#         self.f[a].set(self.f[b].get() // self.f[c].get())
#
#
# class OperandStack(list):
#     def __init__(self):
#         super().__init__()
#
#     def append(self, x: Union[int, float]):
#         assert isinstance(x, (int, float))
#         super().append(x)
#         return self
#
#     def popAsInt(self):
#         assert self
#         return int(self.pop())
#
#     def popAsFloat(self):
#         assert self
#         return float(self.pop())
#
#
# if __name__ == '__main__':
#     o = OperandStack()
#     o.append()
