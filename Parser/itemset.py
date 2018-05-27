class ItemSet(frozenset):
    count = 0

    def __init__(self, value):
        super(ItemSet, self).__init__()
        self.key = ItemSet.count
        ItemSet.count += 1

    def __lt__(self, other):
        return self.key < other.key

    def __repr__(self):
        return 'I_%s{%s}' % (self.key, ','.join(str(i) for i in sorted(self)))
