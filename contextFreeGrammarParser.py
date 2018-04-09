from c_parser import Grammar
import tokenizer
from c_parser import ValueExpressionParser
if __name__ == '__main__':
    GG = Grammar('std.txt')
    # GG = Grammar('std.txt')
    #    print(collection)
    s = list(tokenizer.tokenizeFromFile('stmt.txt'))
    # for token in s:
    #     print(token)
    p = ValueExpressionParser(GG)
    with open('ast.html', 'w', encoding='utf-8') as file:
        rt = p.parse(s)
        file.write('''
        <html>
        <meta charset="utf-8">
        <head><script src="https://apps.bdimg.com/libs/jquery/2.1.4/jquery.min.js"></script>
        <script src="fuck.js"></script></head>
        <body>
        ''')
        file.write(str(rt))
        file.write('<h1>AST</h1>')
        file.write(str(rt()))
        file.write('</body></html>')
