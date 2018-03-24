import expression as expr

type_name = {
    'int',
    'char',
    'float',
    'double',
}
def identifier(s):
    pass

def registerVar(seq,start,end,state):
    pass

def start(seq):
    def start(seq, start, end, state=None):
        if seq[0] in type_name:
            registerVar(seq, start + 1, end, seq[0])
            print('declare', seq[1:], 'as', seq[0])

    return start(seq, 0, len(seq))

if __name__ == '__main__':
    s = 'int a,b,c'
    with open('goto.c') as file:
       s = ''.join(file.readlines())
    print(s)
    expr.analyze(s)

    #print(expr.split(';',[[1],';','4'],recursive=True))
