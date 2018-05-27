import re
from Lexer.ctoken import CToken, SourceLocation, Location
from Lexer import nfa
from AST import c_type
from typing import Tuple, Union, List, Callable, Any, Optional

builtinTypes = {'char', 'double', 'int', 'long', 'short', 'void', 'float', 'signed', 'unsigned', }
keywords = {'enum', 'struct', 'union', 'for', 'do', 'while', 'break',
            'continue', 'if', 'else', 'goto', 'switch', 'case', 'default', 'return',
            'auto', 'extern', 'register', 'static', 'const', 'sizeof', 'typedef', 'volatile'}
symbols = {'{', '}', ';', '(', ')', '[', ']', '"', '\'', ',', '=', '+=', '-=', '*=', '/=', '%=', '<<=', '>>=',
           '&=', '^=', '|=', '?', ':', '||', '&&', '|', '^', '&', '==', '!=', '<', '<=',
           '>', '>=', '<<', '>>', '+', '-', '*', '/', '%', '~', '!', '+',
           '-', '&', '*', '++', '--', '++', '--', '->', '.', '...'}

identifier = re.compile(r'[a-zA-Z_]\w*')
keyword = re.compile('|'.join('\\b' + word + '\\b' for word in keywords))
int32 = re.compile(r"(\d+(?=\b)(?!\.))")
uint32 = re.compile(r"(\d+)[uU]\b")
int64 = re.compile(r'(\d+)(?:ll|LL)\b')
uint64 = re.compile(r"(\d+)(?:[uU](?:LL|ll|[Ll]))\b")
float32 = re.compile(r"(\d+(\.\d*?|\.?\d*e-?\d+)?|\d*(\.\d*?|\.?\d*e-?\d+))(?:[fF]\b)")
double64 = re.compile(r"(\d*(?:\.?\d*e-?\d+|\.\d*))\b")
comment = re.compile(r"(?:/\*.*?\*/)|(?://[^\n]*)", re.S | re.M)
octal = re.compile(r"(0[0-7]+)([uU])?(ll|LL|[Ll])?\b")
hexadecimal = re.compile(r"(0[xX][0-9a-fA-F]+)([uU])?(ll|LL|[Ll])?\b")

# (current-line-number, index of the nearest \n in s)

constantTag = 'constant'
identifierTag = 'identifier'


def defaultreturn(f):
    def execute(s: str, l: int, r: int, loc: Optional[List[int]] = None) -> Tuple[int, str]:

        res = f(s, l, r) if loc is None else f(s, l, r, loc)
        if not res:
            return l, ''
        else:
            return res

    return execute


@defaultreturn
def matchNum(s: str, l: int, r: int) -> Tuple[int, Tuple[Union[int, float], 'c_type.PrimitiveType']]:
    res = float32.match(s, l, r)
    if res:
        return res.end(), (float(res.group(1)), c_type.Float())

    res = double64.match(s, l, r)
    if res:
        return res.end(), (float(res.group(1)), c_type.Double())

    res = uint64.match(s, l, r)
    if res:
        return res.end(), (int(res.group(1)), c_type.UInt64())

    res = int64.match(s, l, r)
    if res:
        return res.end(), (int(res.group(1)), c_type.Int64())

    res = uint32.match(s, l, r)
    if res:
        return res.end(), (int(res.group(1)), c_type.UInt32())

    res = int32.match(s, l, r)
    if res:
        return res.end(), (int(res.group(1)), c_type.Int32())

    res = octal.match(s, l, r)
    if res:
        value = int(res.group(1), 8)
        type = c_type.Int32()
        if value >= 2 ** 31:
            type = c_type.Int64()
            if res.group(2).capitalize() == 'U':
                type = c_type.UInt64()

        else:
            if res.group(3).capitalize() == 'L':
                type = c_type.UInt32()

            elif res.group(3).capitalize() == 'LL':
                type = c_type.UInt64()

        return res.end(), (value, type)

    res = hexadecimal.match(s, l, r)
    if res:
        value = int(res.group(1), 8)
        type = c_type.Int32()
        if value >= 2 ** 31:
            type = c_type.Int64()
            if res.group(2).capitalize() == 'U':
                type = c_type.UInt64()

        else:
            if res.group(3).capitalize() == 'L':
                type = c_type.UInt32()

            elif res.group(3).capitalize() == 'LL':
                type = c_type.UInt64()

        return res.end(), (value, type)


@defaultreturn
def matchIdentifier(s: str, l: int, r: int) -> Tuple[int, str]:
    res = identifier.match(s, l, r)
    if res:
        return res.end(), res.group()


@defaultreturn
def matchComments(s: str, l: int, r: int, loc: List[int]) -> Tuple[int, str]:
    res = comment.match(s, l, r)

    # if res:
    #     while l < r:
    #         if s[l] == '\n':
    #             print(f'commhit! s[{l}]={repr(s[l])},pos({pos[0]}, {pos[1]})')
    #             pos[0] += 1
    #             pos[1] = l
    #         l += 1
    #     return res.end(), res.group()
    # 以上は世の中でも僅かな大バカが書いたコードだ。
    # 本来はres中の'\n'を組み合わせばいいのに、
    # 結局俺が文字列のsの果てまでもループをした。ファック。
    if res:
        while l < res.end():
            if s[l] == '\n':
                # print(f'commhit! s[{l}]={repr(s[l])},pos({pos[0]}, {pos[1]})')
                loc[0] += 1
                loc[1] = l
            l += 1
        return res.end(), res.group()


@defaultreturn
def matchKeyword(s: str, l: int, r: int) -> Tuple[int, str]:
    tmp, token = matchIdentifier(s, l, r)
    if token in keywords:
        return tmp, token


@defaultreturn
def matchSymbol(s: str, l: int, r: int) -> Tuple[int, str]:
    # it seems that the argument r is not used.
    for i in (3, 2, 1):
        if l + i <= len(s) and s[l:l + i] in symbols:
            return l + i, s[l:l + i]


@defaultreturn
def matchType(s: str, l: int, r: int) -> Tuple[int, str]:
    tmp, token = matchIdentifier(s, l, r)
    if token in builtinTypes:
        return tmp, token


def matchSpace(s: str, start: int, end: int, loc: List[int]) -> Tuple[int, str]:
    assert isinstance(s, str)
    r = start
    while r < end and s[r] in (' ', '\n', '\t', '\r'):
        if s[r] == '\n':
            # print(f'hit! s[{r}]={repr(s[r])},pos({pos[0]}, {pos[1]})')
            loc[0] += 1
            loc[1] = r
        r += 1
    return r, s[start:r]


def tokenize(s: str) -> None:
    loc = [1, 0]
    i: int = 0
    length: int = len(s)
    # print(list(enumerate(s)))
    while i < length:

        flag: bool = False
        for f in (matchSpace, matchComments):
            i, _ = f(s, i, length, loc)
            if _:
                flag = True

        def match(f: Callable[[str, int, int], Tuple[int, Any]], token_t: Optional[str]):
            nonlocal flag, i
            r, data = f(s, i, length)
            if r > i:
                flag = True
                if token_t:
                    res = CToken(token_t, data, SourceLocation(loc[0], i - loc[1]))
                else:
                    res = CToken(data, data, SourceLocation(loc[0], i - loc[1]))
                i = r
                return res

        for f, token_t in ((nfa.matchCharacterLiteral, constantTag),
                           (nfa.matchStringLiteral, constantTag),
                           (matchNum, constantTag),
                           (matchKeyword, None),
                           (matchType, None),
                           (matchIdentifier, identifierTag),
                           (matchSymbol, None),
                           ):
            yie = match(f, token_t)
            if yie:
                yield yie
        if not flag:
            raise RuntimeError('unkown character \'%s\' at line %s, column %s: %s' % (
                s[i], loc[0], i - loc[1], s[max(i - 10, 0):min(i + 10, length)]))


def makeCircumflexFromTo(start: int, end: int):
    return ' ' * start + '^' * (end - start)


def tokenize1(lines: List[str]) -> List[CToken]:
    totalLines = len(lines)
    # print(list(enumerate(s)))
    tokens = []
    # for i in range(len(lines)):
    #     lines[i] = lines[i][:-1] + '  \n'

    inComment: bool = False
    for line, s in enumerate(lines):
        i: int = 0
        while i < len(s):
            if inComment:
                if s.startswith('*/', i):
                    inComment = False
                    i += 1
                i += 1
                continue
            else:
                if s[i] in (' ', '\t', '\r', '\n'):
                    i += 1
                    continue
                elif s[i] == '.':
                    loc = Location(line, i)
                    if i + 1 < len(s) and s[i + 1].isdigit():
                        # digit-sequence[opt] . digit-sequence
                        r, data = matchNum(s, i, len(s))
                        if r == i:
                            raise RuntimeError(
                                f'''对不起啊！在第{loc.line+1}行第{loc.column+1}列，这个数字好像是非法的，我不认识！
{s}{makeCircumflexFromTo(i,i+1)}'''
                            )

                        newLoc = Location(line, r)
                        tokens.append(CToken(SourceLocation(loc, newLoc), constantTag, data, s[i:r]))
                        i = r
                        continue

                    if s.startswith('...', i):
                        # '...'
                        newLoc = Location(line, i + 3)
                        tokens.append(CToken(SourceLocation(loc, newLoc), '...', '...', '...'))
                        i += 3
                        continue
                    # '.'
                    newLoc = Location(line, i + 1)
                    tokens.append(CToken(SourceLocation(loc, newLoc), s[i], s[i], s[i]))
                    i += 1
                    continue

                elif s[i].isdigit():
                    loc = Location(line, i)
                    r, data = matchNum(s, i, len(s))
                    if r == i:
                        raise RuntimeError(
                            f'''对不起啊！在第{loc.line+1}行第{loc.column+1}列，这个数字好像是非法的，我不认识！
{s}{makeCircumflexFromTo(i,i+1)}'''
                        )

                    newLoc = Location(line, r)
                    tokens.append(CToken(SourceLocation(loc, newLoc), constantTag, data, s[i:r]))
                    i = r
                    # if s[i] in '123456789':  # decimal-constant
                    #     j = i
                    #     nloc = loc
                    #     while s[j].isdigit():
                    #         j += 1
                    #         nloc = nloc.shift()
                    #
                    #     if s[j] in 'uU':  # integer-suffix
                    #         if s.startswith('ll', j + 1) or s.startswith('LL', j + 1):  # long long suffix
                    #             data = (int(s[i:j]), c_type.UInt64())
                    #             nloc = nloc.shift(2)
                    #         else:
                    #             number = int(s[i:j])
                    #             if number > 0xffff_ffff:
                    #                 raise RuntimeError(
                    #                     '''哎呀不好意思请看第{}行第{}列，您写的整数常量虽说带了个u后缀但是unsigned int 放不下哟!
                    #                     {}
                    #                     {}'''.format(line, i, number, s, makeCircumflexFromTo(i, j+1)))
                    #             data = (number, c_type.UInt32())
                    #
                    #         tokens.append(CToken(constantTag, data, SourceLocation(loc, nloc)))
                    #     elif s[j] in 'fF':
                    #         raise RuntimeError(
                    #             f'''哎呀不好意思请看第{line}行第{i}列，整数常量是不能直接写浮点后缀的哦！如果确实想要个浮点数的话请您在'{s[j]}'前面加个'.'。
                    #             {s}\n{makeCircumflexFromTo(i,j+1)}''')
                    #     elif s[j] == '.':
                    #         pass
                    #     else:
                elif s[i].isidentifier():
                    # keyword
                    # identifier
                    j = i

                    while j < len(s) and s[j].isidentifier():
                        j += 1
                    iden = s[i:j]
                    loc = Location(line, i)
                    newLoc = Location(line, j)
                    if iden in builtinTypes or iden in keywords:
                        tokens.append(CToken(SourceLocation(loc, newLoc), iden, iden, iden))

                    else:
                        # FIXME: 为了快点写出来我决定暂时牺牲一下纯洁性让tokenizer越俎代庖一下
                        tokens.append(CToken(SourceLocation(loc, newLoc), identifierTag, iden, iden))

                    i = j
                    continue

                elif s[i] == '\'':
                    r, data = nfa.matchCharacterLiteral(s, i, len(s))
                    if r == i:
                        raise RuntimeError(
                            f'''对不起啊！在第{loc.line+1}行第{loc.column+1}列，你好像是要写个字符常量，但是好像有问题，我不认识！
{s}{makeCircumflexFromTo(i,i+1)}'''
                        )
                    loc = Location(line, i)
                    newLoc = Location(line, r)
                    tokens.append(CToken(SourceLocation(loc, newLoc), constantTag, data, s[i:r]))
                    i = r
                    continue

                elif s[i] == '"':
                    r, data = nfa.matchStringLiteral(s, i, len(s))
                    if r == i:
                        raise RuntimeError(
                            f'''对不起啊！在第{loc.line+1}行第{loc.column+1}列，你好像是要写个字符串常量，但是好像有问题，我不认识！
{s}{makeCircumflexFromTo(i,i+1)}'''
                        )
                    loc = Location(line, i)
                    newLoc = Location(line, r)
                    tokens.append(CToken(SourceLocation(loc, newLoc), constantTag, data, s[i:r]))
                    i = r
                    continue
                elif s.startswith('//', i):
                    i = len(s)
                    continue

                elif s.startswith('/*', i):
                    inComment = True
                    i += 2
                    continue
                elif s.startswith('*/', i):
                    raise RuntimeError(
                        f'''对不起啊！在第{loc.line+1}行第{loc.column+1}列，多行注释的标志孤零零地悬在那里.
{s}{makeCircumflexFromTo(i,i+2)}'''
                    )
                else:
                    j = i
                    loc = Location(line, i)
                    for l in (3, 2, 1):
                        if i + l >= len(s):
                            continue

                        c = s[i:i + l]
                        if c in symbols:
                            loc = Location(line, i)
                            newLoc = Location(line, i + l)
                            tokens.append(CToken(SourceLocation(loc, newLoc), c, c, c))
                            j = i + l
                            break

                    if j == i:
                        raise RuntimeError(
                            f'''对不起啊！在第{loc.line+1}行第{loc.column+1}列，你好像是要写个符号({ascii(s[i])})，但是好像有问题，我不认识！
{s}{makeCircumflexFromTo(i,i+1)}'''
                        )
                    i = j
                    continue
    return tokens


def tokenizeFromFile(*filename):
    s: List[str] = []
    for f in filename:
        with open(f) as file:
            s.extend(file.readlines())
    return tokenize1(s)


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

    for t in tokenizeFromFile('../stmt.c'):
        print(t)
