import re
from ctoken import CToken
import nfa
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
octal = re.compile(r"(0[0-7]+)[uU]?(?:ll|LL|[Ll])\b")
hexadecimal = re.compile(r"(0[xX][0-9a-fA-F]+)([uU])?(ll|LL|[Ll])?\b")

pos = [1, 0]  # (current-row-number, index of the nearest \n in s)

constantTag='constant'
identifierTag='identifier'

def defaultreturn(f):
    def execute(s, l, r):
        res = f(s, l, r)
        if not res:
            return l, ''
        else:
            return res

    return execute


@defaultreturn
def matchNum(s: str, l: int, r: int):
    for c in (float32, double64, uint64, int64, uint32, int32, octal, hexadecimal):
        res = c.match(s, l, r)
        if res:
            return res.end(), res.group(1)


@defaultreturn
def matchIdentifier(s, l, r):
    res = identifier.match(s, l, r)
    if res:
        return res.end(), res.group()


@defaultreturn
def matchComments(s, l, r):
    res = comment.match(s, l, r)
    if res:
        while l < r:
            if s[l] == '\n':
                pos[0] += 1
                pos[1] = l
            l += 1
        return res.end(), res.group()


@defaultreturn
def matchKeyword(s, l, r):
    tmp, token = matchIdentifier(s, l, r)
    if token in keywords:
        return tmp, token


@defaultreturn
def matchSymbol(s, l, r):
    # it seems that the argument r is not used.
    for i in (3, 2, 1):
        if s[l:l + i] in symbols:
            return l + i, s[l:l + i]


@defaultreturn
def matchType(s, l, r):
    tmp, token = matchIdentifier(s, l, r)
    if token in builtinTypes:
        return tmp, token


def matchSpace(expr: str, start, end) -> (int, str):
    assert isinstance(expr, str)
    r = start
    while r < end and expr[r] in {' ', '\n', '\t'}:
        if expr[r] == '\n':
            pos[0] += 1
            pos[1] = r
        r += 1
    return r, expr[start:r]


def tokenize(s: str):
    pos = [1, 0]
    i = 0
    length = len(s)

    while i < length:
        flag = False
        for f in (matchSpace, matchComments):
            i, _ = f(s, i, length)
            if _:
                flag = True

        def match(f, token_t):
            nonlocal flag, i
            r, value = f(s, i, length)
            if r > i:
                flag = True
                if token_t:
                    res = CToken(token_t, value, (pos[0], i + 1 - pos[1]))
                else:
                    res = CToken(value, value, (pos[0], i + 1 - pos[1]))
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
            raise RuntimeError('unkown character \'%s\' at row %s, column %s: %s' % (
                s[i], pos[0], i + 1 - pos[1], s[max(i - 10, 0):min(i + 10, length)]))


def tokenizeFromFile(*filename):
    s = ''
    for f in filename:
        with open(f) as file:
            s += '\n'.join(file.readlines())
    return tokenize(s)


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

    with open('stmt.txt') as file:
        s = ''.join(file.readlines())
        for t in tokenize(s):
            print(t)
    del file
