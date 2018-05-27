import struct

mem = bytearray(10000)

char_t = struct.Struct('c')
uchar_t = struct.Struct('b')
int32_t = struct.Struct('i')
uint32_t = struct.Struct('I')
int64_t = struct.Struct('q')
uint64_t = struct.Struct('Q')
double_t = struct.Struct('d')
float_t = struct.Struct('f')
ptr_t = struct.Struct('P')


def getChar(address):
    return char_t.unpack_from(mem, address)[0]


def getUChar(address):
    return uchar_t.unpack_from(mem, address)[0]


def getInt32(address):
    return int32_t.unpack_from(mem, address)[0]


def getUInt32(address):
    return uint32_t.unpack_from(mem, address)[0]


def getInt64(address):
    return int64_t.unpack_from(mem, address)[0]


def getUInt64(address):
    return uint64_t.unpack_from(mem, address)[0]


def getDouble(address):
    return double_t.unpack_from(mem, address)[0]


def getFloat(address):
    return float_t.unpack_from(mem, address)[0]


def getPtr(address):
    return ptr_t.unpack_from(mem, address)[0]


def setChar(address, value):
    char_t.pack_into(mem, address, value)


def setUChar(address, value):
    uchar_t.pack_into(mem, address, value)


def setInt32(address, value):
    int32_t.pack_into(mem, address, value)


def setUInt32(address, value):
    uint32_t.pack_into(mem, address, value)


def setInt64(address, value):
    int64_t.pack_into(mem, address, value)


def setUInt64(address, value):
    uint64_t.pack_into(mem, address, value)


def setDouble(address, value):
    double_t.pack_into(mem, address, value)


def setFloat(address, value):
    float_t.pack_into(mem, address, value)


def setPtr(address, value):
    ptr_t.pack_into(mem, address, value)


def memset(ptr: int, value: int, num: int):
    assert num >= 0
    assert 0 <= value < 256
    while num > 0:
        mem[ptr + num] = value
        num -= 1
    return ptr


def memmove(destination: int, source: int, num: int):
    if destination == source:
        return destination
    if destination < source:
        i = 0
        while i < num:
            mem[destination + i] = mem[source + i]
            i += 1
    else:
        i = num - 1
        while i >= 0:
            mem[destination + i] = mem[source + i]
            i -= 1
    return destination
