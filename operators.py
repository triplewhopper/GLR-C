def ternaryIf(e1, e2, e3):
    if e1:
        return e2
    return e3


def normalize(x):
    return int(bool(x))


def preIncrease(rhs):
    assert rhs in variables
    variables[rhs] += 1


def postIncrease(rhs):
    assert rhs in variables
    res = variables[rhs]
    variables[rhs] += 1
    return res


def preDecrease(rhs):
    assert rhs in variables
    variables[rhs] -= 1


def postDecrease(rhs):
    assert rhs in variables
    res = variables[rhs]
    variables[rhs] -= 1
    return res


def directAssign(lhs, rhs):
    assert lhs in variables
    variables[lhs] = rhs


def assignBySum(lhs, rhs):
    assert lhs in variables
    variables[lhs] += rhs


def assignByDifference(lhs, rhs):
    assert lhs in variables
    variables[lhs] -= rhs


def assignByProduct(lhs, rhs):
    assert lhs in variables
    variables[lhs] *= rhs


def assignByQuotient(lhs, rhs):
    assert lhs in variables
    variables[lhs] /= rhs


def assignByRemainder(lhs, rhs):
    assert lhs in variables
    variables[lhs] %= rhs


def assignByBitwiseLeftShift(lhs, rhs):
    assert lhs in variables
    variables[lhs] <<= rhs


def assignmentByBitwiseRightShift(lhs, rhs):
    assert lhs in variables
    variables[lhs] >>= rhs


def assignmentByBitwiseAND(lhs, rhs):
    assert lhs in variables
    variables[lhs] &= rhs


def assignmentByBitwiseXOR(lhs, rhs):
    assert lhs in variables
    variables[lhs] ^= rhs


def assignmentByBitwiseOR(lhs, rhs):
    assert lhs in variables
    variables[lhs] |= rhs


precedence = {
    (',', 18, 'left-to-right'): lambda lhs, rhs: rhs,
    ('=', 16, 'right-to-left'): directAssign,
    ('+=', 16, 'right-to-left'): assignBySum,
    ('-=', 16, 'right-to-left'): assignByDifference,
    ('*=', 16, 'right-to-left'): assignByProduct,
    ('/=', 16, 'right-to-left'): assignByQuotient,
    ('%=', 16, 'right-to-left'): assignByRemainder,
    ('<<=', 16, 'right-to-left'): assignByBitwiseLeftShift,
    ('>>=', 16, 'right-to-left'): assignmentByBitwiseRightShift,
    ('&=', 16, 'right-to-left'): assignmentByBitwiseAND,
    ('^=', 16, 'right-to-left'): assignmentByBitwiseXOR,
    ('|=', 16, 'right-to-left'): assignmentByBitwiseOR,
    ('?:', 15, 'right-to-left'): ternaryIf,
    ('||', 14, 'left-to-right'): lambda lhs, rhs: normalize(lhs or rhs),
    ('&&', 13, 'left-to-right'): lambda lhs, rhs: normalize(lhs and rhs),
    ('|', 12, 'left-to-right'): lambda lhs, rhs: lhs & rhs,
    ('^', 11, 'left-to-right'): lambda lhs, rhs: lhs ^ rhs,
    ('&', 10, 'left-to-right'): lambda lhs, rhs: lhs & rhs,
    ('==', 9, 'left-to-right'): lambda lhs, rhs: lhs == rhs,
    ('!=', 9, 'left-to-right'): lambda lhs, rhs: lhs != rhs,
    ('<', 8, 'left-to-right'): lambda lhs, rhs: lhs < rhs,
    ('<=', 8, 'left-to-right'): lambda lhs, rhs: lhs <= rhs,
    ('>', 8, 'left-to-right'): lambda lhs, rhs: lhs > rhs,
    ('>=', 8, 'left-to-right'): lambda lhs, rhs: lhs >= rhs,
    ('<<', 7, 'left-to-right'): lambda lhs, rhs: lhs << rhs,
    ('>>', 7, 'left-to-right'): lambda lhs, rhs: lhs >> rhs,
    ('+', 6, 'left-to-right'): lambda lhs, rhs: lhs + rhs,
    ('-', 6, 'left-to-right'): lambda lhs, rhs: lhs - rhs,
    ('*', 5, 'left-to-right'): lambda lhs, rhs: lhs * rhs,
    ('/', 5, 'left-to-right'): lambda lhs, rhs: lhs / rhs,
    ('%', 5, 'left-to-right'): lambda lhs, rhs: lhs % rhs,
    ('~', 3, 'right-to-left'): lambda rhs: ~rhs,
    ('!', 3, 'right-to-left'): lambda rhs: normalize(not rhs),
    ('+', 3, 'right-to-left'): lambda rhs: +rhs,
    ('-', 3, 'right-to-left'): lambda rhs: -rhs,
    ('&', 3, 'right-to-left'): lambda rhs: rhs.getAddress,
    ('*', 3, 'right-to-left'): lambda rhs: rhs.derefer,
    ('++', 3, 'right-to-left'): preIncrease,
    ('--', 3, 'right-to-left'): preDecrease,
    ('++', 2, 'left-to-right'): postIncrease,
    ('--', 2, 'left-to-right'): postDecrease,
    ('->', 2, 'left-to-right'): lambda lhs, rhs: NotImplementedError(),
    ('.', 2, 'left-to-right'): lambda lhs, rhs: NotImplementedError(),
}
variables = {}
operators = set(map(lambda k: k[0], precedence))


def wrapper(f):
    def execute(*s):
        print('begin ', end='', sep='')
        print(f.__name__, end='', sep='')
        args = ','.join(map(lambda x: x.__repr__(), s))
        print('(', args, ')', sep='')
        # sep='')
        res = f(*s)
        print('end ', f.__name__, '(', args, ') with return value ', res, sep='')
        return res

    return execute


def findAll(e, seq):
    def index(generator):
        for i in generator:
            if seq[i] == e.operator:
                yield i

    #    if isinstance(e, str):
    #        return index(ILeftRightAssociative.order(seq))
    return index(type(e).order(seq))


class OperatorBase:
    def __init__(self, name, precedence, func=None):
        self._name = str(name)
        self.func = func
        self.precedence = precedence

    @property
    def operator(self):
        return self._name


class BinaryOperatorBase(OperatorBase):

    def match(self, expr, f) -> None or list:
        for pos in findAll(self, expr):
            l = expr[:pos]
            r = expr[pos + 1:]
            #    print('"',''.join(l),'" ',op,' "',''.join(r),'"',sep='')
            lv = f(l)
            if not lv: continue
            rv = f(r)
            if rv:
                self.lhs = lv
                self.rhs = rv
                return [self, lv, rv]

    def __call__(self):
        return self.func(self.lhs, self.rhs)

    def __repr__(self):
        return "bi('" + str(self.operator) + "')"

    __str__ = __repr__

    @staticmethod
    def order(seq):
        raise NotImplementedError()


class ILeftRightAssociative:

    @staticmethod
    def order(seq):
        return range(len(seq))


class IRightLeftAssociative:

    @staticmethod
    def order(seq):
        return range(len(seq) - 1, -1, -1)


class BinaryOpLeftRight(ILeftRightAssociative, BinaryOperatorBase):
    order = ILeftRightAssociative.order


class BinaryOpRightLeft(BinaryOperatorBase, IRightLeftAssociative):
    order = IRightLeftAssociative.order


class AssignmentOperator(BinaryOpRightLeft):
    def __repr__(self):
        return "assign('" + str(self.operator) + "')"

    __str__ = __repr__


class UnaryOperatorBase(OperatorBase):
    def __repr__(self):
        return "unary('" + str(self.operator) + "')"

    __str__ = __repr__


class PostfixUnaryOp(UnaryOperatorBase, ILeftRightAssociative):
    order = ILeftRightAssociative.order

    def __repr__(self):
        return "post('" + str(self.operator) + "')"

    def match(self, expr, f) -> None or list:
        for pos in findAll(self, expr):
            l = expr[:pos]
            lv = f(l)
            if lv:
                self.lhs = lv
                return [lv, self]


class PrefixUnaryOp(UnaryOperatorBase, IRightLeftAssociative):
    order = IRightLeftAssociative.order

    def __repr__(self):
        return "prefix('" + str(self.operator) + "')"

    def match(self, expr, f) -> None or list:
        for pos in findAll(self, expr):
            r = expr[pos + 1:]
            rv = f(r)
            if rv:
                self.rhs = rv
                return [self, rv]


class ParenthesesOperator(OperatorBase, ILeftRightAssociative):
    order = ILeftRightAssociative.order

    def __init__(self):
        super(ParenthesesOperator, self).__init__('()', 15)

    def match(self, expr, f) -> None or list:
        for pos in findAll(self, expr):
            subexpr = f(expr[pos:])
            if subexpr:
                self.subexpr = subexpr
                return ['()', subexpr]

    def __repr__(self):
        return 'Prnthss()'


class FunctionCallOperator(ParenthesesOperator):

    def __init__(self):
        super(FunctionCallOperator, self).__init__('()', 15)

    def __call__(self, func, *args):
        raise NotImplementedError()


def listtotuple(x):
    return tuple(e if not isinstance(e, list) else listtotuple(e) for e in x)


class TernaryOperator(OperatorBase, IRightLeftAssociative):
    def __init__(self):
        super(TernaryOperator, self).__init__('?:', 15, ternaryIf)

    def match(self, expr, f) -> None or list:
        # def valid(expr):
        #     return filter(lambda c: c[0] < c[1],
        #                   tuple((p1, p2) for p1 in findAll('?', expr) for p2 in findAll(':', expr)))

        for p1 in findAll(self, expr):
            p2 = p1 + expr[p1].spouse
            condition, do_if, do_else = expr[:p1], expr[p1 + 1:p2], expr[p2 + 1:]
            v1 = f(condition)
            v2 = f(do_if)
            v3 = f(do_else)
            if v1 and v2 and v3:
                return [self, v1, v2, v3]

    order = IRightLeftAssociative.order

    def __call__(self, condition, do_if, do_else):
        return self.func(condition, do_if, do_else)

    def __repr__(self):
        return "ternary('" + str(self.operator) + "')"

    __str__ = __repr__


ops = []


def loadOperators():
    for k, v in precedence.items():
        if k[0] == '?:':
            ops.append(TernaryOperator())
        elif k in {('*', 3, 'right-to-left'),
                   ('~', 3, 'right-to-left'),
                   ('!', 3, 'right-to-left'),
                   ('&', 3, 'right-to-left'),
                   ('+', 3, 'right-to-left'),
                   ('-', 3, 'right-to-left'),
                   ('++', 3, 'right-to-left'),
                   ('--', 3, 'right-to-left'),
                   ('--', 2, 'left-to-right'),
                   ('++', 2, 'left-to-right')}:
            # print(v)
            f = {'right-to-left': PrefixUnaryOp, 'left-to-right': PostfixUnaryOp}[k[2]]
            ops.append(f(k[0], k[1], v))
        elif k[0] in {'=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>', '&=', '|='}:
            ops.append(AssignmentOperator(k[0], k[1], v))
        else:
            # print(v)
            f = {'right-to-left': BinaryOpRightLeft, 'left-to-right': BinaryOpLeftRight}[k[2]]
            ops.append(f(k[0], k[1], v))
    # a = [BinaryOpLeftRight(v[0], k, v[1]) for k, v in precedence.items()]
    #print(ops)


if __name__ == '__main__':
    # s =
    print(list(map(lambda x:x[0],precedence)))
    # for k, v in precedence.items():
    #     print(":('%s',%s)," % (k, v))
    #    print(a)
    # for f in assigning:
    #     print(
    #         '''
    #         def %s(lhs,rhs):
    #             assert lhs in variables
    #             variables[lhs] %s rhs
    #         ''' % (assigning[f], f))
