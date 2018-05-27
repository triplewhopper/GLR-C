from Parser import grammar
from Lexer import tokenizer
from Parser import parser
from AST import scopes
import instructions
# from AST import environment as Env
# from AST.environment import Scope, ScopeFlags
from typing import FrozenSet, Dict

if __name__ == '__main__':
    GG = grammar.Grammar('std.txt')
    # GG = Grammar('std.txt')
    #    print(collection)
    s = list(tokenizer.tokenizeFromFile('stmt.c'))
    # for token in s:
    #     print(token)
    p = parser.Parser(GG)
    with open('ast.xml', 'w', encoding='utf-8') as file:
        rt = p.parse(s)
        file.write('''<?xml version="1.0" encoding="utf-8"?>''')
        file.write('<GGG>')
        file.write('<{0}>{1}</{0}>\n\n'.format('ParseTree', str(rt)))
        scope = scopes.GlobalScope()
        rt.visit(scope)
        # for c in ast:
        #     # cmd.extend(c.gen())
        #     c.gen1(cmd)
        # for i, c in enumerate(cmd):
        #     if isinstance(c, list):
        #         c.append(i)

        file.write('{0}'
                   '</GGG>'.format(str(scope)))
        code, funcs = scope.gen()

        for i, ln in enumerate(code):
            print(i, ln)
        vm = instructions.HAHA(code, funcs, 8)
        vm.mainloop()

        # file.write('{0}'
        #            '<AST>{1}</AST></GGG>'.format(str(scope), str(ast)))
        # rt = ET.ElementTree(rt.dump())
        # rt.write(file, encoding='unicode')
        # a.visit(Env.FileScope())
