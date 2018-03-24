import operators
import literal
import ctoken
import nfa
import tag


def getLongestSpace(expr: str, start, end) -> (int, str):
    assert isinstance(expr, str)
    r = start
    while r < end and expr[r] in {' ', '\n', '\t'}:
        r += 1
    return r, expr[start:r]


def getLongestStartIdentifier(expr: str, start, end) -> (int, str):
    assert isinstance(expr, str)
    r = start
    if not expr[r].isnumeric():
        while r < end and (expr[r].isalpha() or expr[r].isdigit() or expr[r] == '_'):
            r += 1
    return r, expr[start:r]


def getLongestStartOp(expr: str, start, end) -> (int, str):
    r = start
    while r < end and expr[start:r + 1] in operators.operators:
        r += 1
    return r, expr[start:r]


def getLongestStartNum(expr, start, end):
    def isNum(x) -> bool:
        if isinstance(x, (int, float)): return True
        if not isinstance(x, str): return False
        if x == '': return False
        for s in filter(lambda s: s != '' and s != '.', x.partition('.')):
            if not s.isnumeric():
                return False
        return True

    # print(expr)
    l = start
    r = end
    while l < r:
        mid = l + r >> 1
        if isNum(expr[start:mid + 1]):
            l = mid + 1
        else:
            r = mid
        # print('l=%s,r=%s,mid=%s'%(l,r,mid))
    return l, expr[start:l]


def wrapper(f):
    def execute(*args, **kwargs):
        s = ','.join(map(repr, args))
        kws = ','.join(map(repr, kwargs.items()))
        print('begin %s(%s, %s)' % (f.__name__, s, kws))
        res = f(*args, **kwargs)
        print('end %s(%s, %s) with return value %s' % (f.__name__, s, kws, res))
        return res

    return execute


# @wrapper
# def expression(expr):
#     if not expr:
#         return None
#     if isNum(expr):
#         return int(expr)
#     if isIdentifier(expr):
#         return
#     if len(expr) == 1:
#         return expression(expr[0])
#     for op in Operator.tenary:
#         for posIf, posElse in index(expr, op):
#             l = expr[:pos]
#             r = expr[pos + 1:]
#             #    print('"',''.join(l),'" ',op,' "',''.join(r),'"',sep='')
#             lv = expression(l)
#             rv = expression(r)
#             if lv and rv:
#                 return Operator.binary[op](lv, rv)
#
#     for op in Operator.binary:
#         for pos in index(expr, op):
#             l = expr[:pos]
#             r = expr[pos + 1:]
#             #    print('"',''.join(l),'" ',op,' "',''.join(r),'"',sep='')
#             lv = expression(l)
#             rv = expression(r)
#             if lv and rv:
#                 return Operator.binary[op](lv, rv)
#     for op in Operator.preUnary:
#         for pos in index(expr, op):
#             r = expr[pos + 1:]
#             print(op, ' "', ''.join(r), '"', sep='')
#             rv = expression(r)
#             if rv:
#                 return Operator.preUnary[op](rv)
#     return None
# @wrapper


def tokenizewrapper(f):
    def execute(expr: str, start: int, end: int, hasPrecededIdentifer: bool = False):
        print('begin %s(%s, %s)' % (f.__name__, repr(expr[start:end]), hasPrecededIdentifer))
        res = f(expr, start, end, hasPrecededIdentifer)
        print('end %s(%s, %s) with return value %s' % (f.__name__, repr(expr[start:end]), hasPrecededIdentifer, res))
        return res

    return execute


@tokenizewrapper
def tokenize(expr: str, start: int, end: int, hasPrecededIdentifer: bool = False) -> list:
    if start == end:
        return []
    if expr[start] == ';':
        return [';'] + tokenize(expr, start + 1, end)
    couple = {'(': '()', '[': '[]', '{': '{}'}
    if expr[start] in couple:
        c = expr[start]
        r = link[start]
        inner_expr = tokenize(expr, start + 1, start + r - 1)
        other = tokenize(expr, start + r, end)

        if hasPrecededIdentifer:
            # if expr[start] == '{':
            #    raise RuntimeError('"{}" cannot be attached after a identifier!')
            return [[couple[c], inner_expr]] + other
        elif expr[start] == '[':
            raise RuntimeError('subscript\'[]\' must be preceded by a identifier!')
        return [inner_expr] + other

    if expr[start] == '?':
        r = link[start]
        do_if = tokenize(expr, start + 1, start + r - 1)
        do_else = tokenize(expr, start + r, end)
        if not do_else or not do_if:
            raise RuntimeError("expected primary-expression after ':' !")
        Link = type('Link', (str,), {'spouse': len(do_if) + 1})
        return [Link('?:')] + do_if + [':'] + do_else

    def subtract(f, flag) -> list:
        r, substr = f(expr, start, end)
        if r > start:
            # tmp = expr[start:r]
            other = tokenize(expr, r, end, flag)
            return [substr] + other

    for f, flag in ((literal.matchNum, False),
                    (literal.matchIdentifier, True),
                    (literal.matchOperator, False),
                    (nfa.matchStringLiteral, True),
                    (nfa.matchCharacterLiteral, False)):
        res = subtract(f, flag)
        if res:
            return res


# class PrimaryExpression:
#     def __init__(self, *args, **kwargs):
#         if len(args) == 1:
#             self.nodes = args[0]
#         else:
#             self.nodes = [PrimaryExpression(i) for i in args]
#         self.op = kwargs.get('op', None)
#         self.association = kwargs.get('association', 'left-to-right')
#
#     def __repr__(self):
#         return 'PrimaryExpression(<%s>,%s)' % (self.op, self.nodes)
#
#     __str__ = __repr__
#
#     def __call__(self):
#         for i in range(len(self.nodes)):
#             self.nodes[i] = int(self.nodes[i])
#         if self.op is None:
#             assert isinstance(self.nodes, str) and self.nodes.isidentifier() or isinstance(self.nodes,
#                                                                                            (int, float, str))
#             return operator.variables.get(self.nodes, int(self.nodes))
#         return operator.binary[self.op](*self.nodes)
#
#     def legal(self):
#         if self.op is None:
#             assert isinstance(self.nodes, (str, int, float)) or isinstance(self.nodes, list) and len(self.nodes) == 1
#         else:
#             assert len(self.nodes) > 0
#
#     def empty(self):
#         self.legal()
#         return self.nodes == []
def tokenizefoolish(expr: str, start: int, end: int) -> list:
    assert expr
    start, _ = getLongestSpace(expr, start, end)
    if start == end:
        return

    for f in (literal.matchComments,
              nfa.matchStringLiteral,
              nfa.matchCharacterLiteral,
              literal.matchNum,
              literal.matchKeyword,
              literal.matchIdentifier,
              literal.matchSpecialSymbol,
              literal.matchOperator,
              ):
        r, substr = f(expr, start, end)
        if r > start:
            yield substr
            yield from tokenizefoolish(expr, r, end)
            break


@wrapper
def ast(expr) -> list or None:
    if not isinstance(expr, list):
        return [expr]
    if len(expr) == 1:
        return ast(expr[0])
    if not expr:
        return None
    for op in operators.ops:
        res = op.match(expr, ast)
        if res:
            return res
    return None


link = {}


def cst(s, l, r):
    pair = {'{': '{}', '(': '()', '[': '[]'}
    # pair = {'{': '}', '(': ')', '[': ']'}
    if l == r:
        return ()
    if s[l] in pair:
        # return (s[l], cst(s, l + 1, link[l]), ctoken.CToken(pair[s[l]], tag.Tag.specialSymbol)) + cst(s, link[l] + 1, r)
        return (ctoken.CToken(pair[s[l]], tag.Tag.specialSymbol), cst(s, l + 1, link[l])) \
               + cst(s, link[l] + 1, r)
    return (s[l],) + cst(s, l + 1, r)


def collectStatement(s):
    res = []
    tmp = []
    for i, e in enumerate(s):
        if e == ';':
            res.append(ctoken.CSimpleStatement(tmp, 'simple statement'))
            print('statement:', list(map(str, tmp)))
            tmp = []
        elif isinstance(e, tuple):
            tmp.append(collectStatement(e))
        else:
            tmp.append(e)
    if tmp:
        print('statement:', list(map(str, tmp)))
        res.append(ctoken.CSimpleStatement(tmp, 'simple statement'))
    return tuple(res)


def analyze(s):
    print('s=', repr(s))

    # s=PrimaryExpression(['1','1'],op='+')
    # print(s())
    s = tokenizefoolish(s, 0, len(s))
    s = tuple(filter(lambda x: tag.Tag.comment not in x.tag, s))

    try:

        stack = []
        left = ('{', '(', '[')
        right = ('}', ')', ']')  # if '::',boom! of course it's impossible, because this is C.
        for i in range(len(s)):

            if s[i] in left:
                stack.append((i, s[i]))
            elif s[i] in right:
                assert stack
                pos, ch = stack.pop()
                if right.index(s[i]) != left.index(ch):
                    raise RuntimeError()
                link[pos] = i
        if stack:
            raise RuntimeError('括号不匹配！')
        del stack
    except IndexError or RuntimeError as e:
        raise e
    except AssertionError as e:
        raise AssertionError('i=%s' % s[:i + 1])

    # print('now,s =', ' '.join(s))
    s = cst(s, 0, len(s))
    print(''.join(format(s)))
    s = collectStatement(s)
    print(''.join(format(s)))
    # #    print('ast(s) =', ast(s))
    # print('format(s)=')
    # format(s)
    # print()


def format(s, indent=0):
    if isinstance(s,ctoken.CSimpleStatement):
        yield '    ' * indent + '<<statement\n'
    else:
        yield '    ' * indent + '[\n'
    for e in s:
        if isinstance(e, tuple):
            yield from format(e, indent + 1)
        else:
            yield '    ' * (indent + 1) + str(e) + '\n'  # ' ' '
    if isinstance(s,ctoken.CSimpleStatement):
        yield '    ' * indent + 'statement>>\n'
    else:
        yield '    ' * indent + ']\n'


def formatStatement(s, indent=0):
    #
    for e in s:
        if isinstance(e, ctoken.CSimpleStatement):
            yield from formatStatement(e, indent + 1)
        else:
            yield '   |' * (indent) + str(e) + ' '

    yield '\n'
    # yield '  ' * indent + ']\n'


if __name__ == '__main__':
    tests = (r'''
int main()
{	
	char ch='4';
	dword n,m,t,can[/*something fun*/32][2];
	char str[5];
	for(dword i=0;i<32;++i) can[i][0]=0,can[i][1]=1;
	scanf("%d%d",&n,&m);
	for(dword i=1;i<=n;++i){
		scanf("%s%d",str,&t);
		if(!strcmp(str,"AND")){
			for(dword j=0;j<=31;++j)
				can[j][0]&=kth(t,j),
				can[j][1]&=kth(t,j);
		}
		else if(!strcmp(str,"OR")){
			for(dword j=0;j<=31;++j)
				can[j][0]|=kth(t,j),
				can[j][1]|=kth(t,j);
		}
		else if(!strcmp(str,"XOR")){
			for(dword j=0;j<=31;++j)
				can[j][0]^=kth(t,j),
				can[j][1]^=kth(t,j);
		}

	}
	dword ans=0,tmp=0;
	for(int i=31;i>=0;--i){
		if(can[i][0]) ans+=1<<i;
		else if(can[i][1]&&tmp+(1<<i)<=m){
			ans+=1<<i;tmp+=1<<i;
		}
	}
	cout<<ans<<"\n";
	return 0;
}

''',)
    operators.loadOperators()

    for s in tests:
        link = {}
        analyze(s)
        # s=getLongestStartNum('132')
        # data={'1+1':1,'123':3,'1':'1','132':3,'.1+1':2}
        # for k in data:

        #    print('---',k,'std:',data[k],getLongestStartNum(k))
        # s=
        # print(expression(s))
