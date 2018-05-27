from typing import Dict, TypeVar, Callable, Generic, Mapping, Iterator, Tuple

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')


class SBTNode(Generic[_KT, _VT]):
    default = None
    count = 0

    def __init__(self, key: _KT, value: _VT):
        self.key = key
        self.value = value
        self.size = 1
        self.left = SBTNode.default
        self.right = SBTNode.default
        self.index = SBTNode.count
        SBTNode.count += 1

    @property
    def isNull(self) -> bool:
        return self is SBTNode.default

    def __repr__(self):
        return 'SBTNode[%s](key=%s, value=%s, left=%s, right=%s)' % (
            self.index, self.key, self.value, self.left.index, self.right.index)

    def __str__(self):
        return 'SBTNode(%s: %s)' % (self.key, self.value)


class SizeBalancedTree(Mapping[_KT, _VT]):
    NullNode = SBTNode(None, None)
    NullNode.left = NullNode.right = NullNode
    SBTNode.default = NullNode
    NullNode.size = 0

    def __init__(self, cmp: Callable[[_KT, _KT], int], data: Dict[_KT, _VT] = None):
        self.rt = SizeBalancedTree.NullNode
        self.cmp = cmp
        if data is None:
            data = {}
        for k, v in data.items():
            self.insert(k, v)

    def keys(self):
        yield from self._keys(self.rt)

    def insert(self, key: _KT, value: _VT):
        self.rt = self._insert(key, value, self.rt)

    def remove(self, key: _KT):
        if self._find(key).isNull:
            return KeyError(key)
        self.rt, _ = self._remove(key, self.rt)

    def select(self, k: int):
        if k < 1 or k > len(a):
            raise IndexError(k)
        node = self._select(k, self.rt)
        return node.key, node.value

    def items(self):
        if self:
            yield from self._items(self.rt)
        else:
            raise StopIteration()

    def __iter__(self) -> Iterator[Tuple[_KT, _VT]]:
        yield from self.items()

    def __getitem__(self, item) -> _VT:
        entry = self._find(item)
        if entry.isNull:
            raise KeyError(item)
        return entry.value

    def __setitem__(self, key, value):
        entry = self._find(key)
        if entry.isNull:
            self.rt = self._insert(key, value, self.rt)
        else:
            entry.value = value

    def __str__(self):
        return 'SBT({' + ','.join('%s: %s' % (k, v) for k, v in self.items()) + '})'

    def popitem(self) -> Tuple[_KT, _VT]:
        if self.rt.isNull:
            raise KeyError('popitem(): dictionary is empty')
        node = self._select(1, self.rt)
        # print('node=', node)
        self.rt, k, v = self._remove(node.key, self.rt)
        return k, v

    def __contains__(self, item):
        assert item is not None
        return not self._find(item).isNull

    def __len__(self):
        return self.rt.size

    def _keys(self, x: SBTNode):
        if not x.left.isNull:
            yield from self._keys(x.left)
        yield x.key
        if not x.right.isNull:
            yield from self._keys(x.right)

    def _items(self, x: SBTNode):
        if not x.left.isNull:
            yield from self._items(x.left)
        yield x.key, x.value
        if not x.right.isNull:
            yield from self._items(x.right)

    def _insert(self, key: _KT, value: _VT, x: SBTNode):
        assert isinstance(x, SBTNode)
        if x.isNull:
            return SBTNode(key, value)
        else:
            x.size += 1
            c = self.cmp(key, x.key)
            if c == 0:
                raise KeyError('this key(%s) has already been in.' % ((key, x.key),))
            elif c < 0:
                x.left = self._insert(key, value, x.left)
            else:
                x.right = self._insert(key, value, x.right)
            return self.maintain(x, key >= x.key)

    def L(self, x: SBTNode):
        assert isinstance(x, SBTNode)
        b: SBTNode = x.right
        x.right = b.left
        b.left = x
        b.size = x.size
        x.size = x.left.size + x.right.size + 1
        return b

    def R(self, x: SBTNode):
        assert isinstance(x, SBTNode)
        b: SBTNode = x.left
        x.left = b.right
        b.right = x
        b.size = x.size
        x.size = x.left.size + x.right.size + 1
        return b

    def maintain(self, x: SBTNode, f: bool):
        assert isinstance(x, SBTNode)
        if not f:
            if x.left.left.size > x.right.size:
                x = self.R(x)
            elif x.left.right.size > x.right.size:
                x.left = self.L(x.left)
                x = self.R(x)
            else:
                return x
        else:
            if x.right.right.size > x.left.size:
                x = self.L(x)
            elif x.right.left.size > x.left.size:
                x.right = self.R(x.right)
                x = self.L(x)
            else:
                return x
        x.left = self.maintain(x.left, False)
        x.right = self.maintain(x.right, True)
        x = self.maintain(x, False)
        return self.maintain(x, True)

    def _remove(self, key: _KT, x: SBTNode):

        assert isinstance(x, SBTNode)

        x.size -= 1
        c = self.cmp(key, x.key)
        if (c == 0) or (c < 0 and x.left.isNull) \
                or (c > 0 and x.right.isNull):
            k, v = x.key, x.value
            if x.left.isNull or x.right.isNull:
                x = x.left if x.right.isNull else x.right
            else:
                x.left, x.key, x.value = self._remove(key, x.left)
            return x, k, v
        else:
            if c < 0:
                x.left, k, v = self._remove(key, x.left)
            else:
                x.right, k, v = self._remove(key, x.right)
            return x, k, v

    def _find(self, key: _KT):
        p = self.rt
        while not p.isNull and self.cmp(key, p.key) != 0:
            p = p.left if self.cmp(key, p.key) < 0 else p.right
        return p

    def _select(self, k: _KT, x: SBTNode):
        if k == x.left.size + 1:
            return x
        elif k <= x.left.size:
            return self._select(k, x.left)
        return self._select(k - 1 - x.left.size, x.right)


if __name__ == '__main__':
    a = SizeBalancedTree(lambda x, y: x - y)
