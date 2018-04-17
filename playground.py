from collections import Counter
table={}
class LHS(type):
    # @classmethod
    # def __prepare__(metacls, name, bases):
    #     print(f'name={name},bases={bases}')
    #     return {}

    def __new__(cls, name, bases, classdict, **kwargs):
        print(f'{name},classdict={classdict}')
        res = super().__new__(cls, name, bases, dict(classdict))
        table[classdict['key']]=res
        return res



class DeclarationListBegin(metaclass=LHS):
    key = 0
    relativeOrder = 1
    rhs = ('DeclarationList',)


class Declaration(metaclass=LHS):
    key = 1
    relativeOrder = 1
    rhs = ('DeclarationSpecifiers', 'InitDeclaratorList', ';')


class Declaration(metaclass=LHS):
    key = 2
    relativeOrder = 2
    rhs = ('DeclarationSpecifiers', ';')


class DeclarationSpecifiers(metaclass=LHS):
    key = 3
    relativeOrder = 1
    rhs = ('StorageClassSpecifier', 'DeclarationSpecifiers')


class DeclarationSpecifiers(metaclass=LHS):
    key = 4
    relativeOrder = 2
    rhs = ('StorageClassSpecifier',)


class DeclarationSpecifiers(metaclass=LHS):
    key = 5
    relativeOrder = 3
    rhs = ('TypeSpecifier', 'DeclarationSpecifiers')


class DeclarationSpecifiers(metaclass=LHS):
    key = 6
    relativeOrder = 4
    rhs = ('TypeSpecifier',)


class DeclarationSpecifiers(metaclass=LHS):
    key = 7
    relativeOrder = 5
    rhs = ('TypeQualifier', 'DeclarationSpecifiers')


class DeclarationSpecifiers(metaclass=LHS):
    key = 8
    relativeOrder = 6
    rhs = ('TypeQualifier',)


class DeclarationSpecifiers(metaclass=LHS):
    key = 9
    relativeOrder = 7
    rhs = ('FunctionSpecifier', 'DeclarationSpecifiers')


class DeclarationSpecifiers(metaclass=LHS):
    key = 10
    relativeOrder = 8
    rhs = ('FunctionSpecifier',)


class InitDeclaratorList(metaclass=LHS):
    key = 11
    relativeOrder = 1
    rhs = ('InitDeclarator',)


class InitDeclaratorList(metaclass=LHS):
    key = 12
    relativeOrder = 2
    rhs = ('InitDeclarator', ',', 'InitDeclaratorList')


class InitDeclarator(metaclass=LHS):
    key = 13
    relativeOrder = 1
    rhs = ('Declarator',)


class InitDeclarator(metaclass=LHS):
    key = 14
    relativeOrder = 2
    rhs = ('Declarator', '=', 'Initializer')


class StorageClassSpecifier(metaclass=LHS):
    key = 15
    relativeOrder = 1
    rhs = ('typedef',)


class StorageClassSpecifier(metaclass=LHS):
    key = 16
    relativeOrder = 2
    rhs = ('extern',)


class StorageClassSpecifier(metaclass=LHS):
    key = 17
    relativeOrder = 3
    rhs = ('static',)


class StorageClassSpecifier(metaclass=LHS):
    key = 18
    relativeOrder = 4
    rhs = ('auto',)


class StorageClassSpecifier(metaclass=LHS):
    key = 19
    relativeOrder = 5
    rhs = ('register',)


class TypeSpecifier(metaclass=LHS):
    key = 20
    relativeOrder = 1
    rhs = ('void',)


class TypeSpecifier(metaclass=LHS):
    key = 21
    relativeOrder = 2
    rhs = ('char',)


class TypeSpecifier(metaclass=LHS):
    key = 22
    relativeOrder = 3
    rhs = ('short',)


class TypeSpecifier(metaclass=LHS):
    key = 23
    relativeOrder = 4
    rhs = ('int',)


class TypeSpecifier(metaclass=LHS):
    key = 24
    relativeOrder = 5
    rhs = ('long',)


class TypeSpecifier(metaclass=LHS):
    key = 25
    relativeOrder = 6
    rhs = ('float',)


class TypeSpecifier(metaclass=LHS):
    key = 26
    relativeOrder = 7
    rhs = ('double',)


class TypeSpecifier(metaclass=LHS):
    key = 27
    relativeOrder = 8
    rhs = ('signed',)


class TypeSpecifier(metaclass=LHS):
    key = 28
    relativeOrder = 9
    rhs = ('unsigned',)


class TypeSpecifier(metaclass=LHS):
    key = 29
    relativeOrder = 10
    rhs = ('_Bool',)


class TypeSpecifier(metaclass=LHS):
    key = 30
    relativeOrder = 11
    rhs = ('_Complex',)


class TypeSpecifier(metaclass=LHS):
    key = 31
    relativeOrder = 12
    rhs = ('StructOrUnionSpecifier',)


class TypeSpecifier(metaclass=LHS):
    key = 32
    relativeOrder = 13
    rhs = ('EnumSpecifier',)


class TypeSpecifier(metaclass=LHS):
    key = 33
    relativeOrder = 14
    rhs = ('TypedefName',)


class TypeQualifier(metaclass=LHS):
    key = 34
    relativeOrder = 1
    rhs = ('const',)


class TypeQualifier(metaclass=LHS):
    key = 35
    relativeOrder = 2
    rhs = ('restrict',)


class TypeQualifier(metaclass=LHS):
    key = 36
    relativeOrder = 3
    rhs = ('volatile',)


class StructOrUnionSpecifier(metaclass=LHS):
    key = 37
    relativeOrder = 1
    rhs = ('StructOrUnion', 'identifier', '{', 'StructDeclarationList', '}')


class StructOrUnionSpecifier(metaclass=LHS):
    key = 38
    relativeOrder = 2
    rhs = ('StructOrUnion', '{', 'StructDeclarationList', '}')


class StructOrUnionSpecifier(metaclass=LHS):
    key = 39
    relativeOrder = 3
    rhs = ('StructOrUnion', 'identifier')


class StructOrUnion(metaclass=LHS):
    key = 40
    relativeOrder = 1
    rhs = ('struct',)


class StructOrUnion(metaclass=LHS):
    key = 41
    relativeOrder = 2
    rhs = ('union',)


class StructDeclarationList(metaclass=LHS):
    key = 42
    relativeOrder = 1
    rhs = ('StructDeclaration',)


class StructDeclarationList(metaclass=LHS):
    key = 43
    relativeOrder = 2
    rhs = ('StructDeclaration', 'StructDeclarationList')


class StructDeclaration(metaclass=LHS):
    key = 44
    relativeOrder = 1
    rhs = ('SpecifierQualifierList', 'StructDeclaratorList', ';')


class SpecifierQualifierList(metaclass=LHS):
    key = 45
    relativeOrder = 1
    rhs = ('TypeSpecifier', 'SpecifierQualifierList')


class SpecifierQualifierList(metaclass=LHS):
    key = 46
    relativeOrder = 2
    rhs = ('TypeSpecifier',)


class SpecifierQualifierList(metaclass=LHS):
    key = 47
    relativeOrder = 3
    rhs = ('TypeQualifier', 'SpecifierQualifierList')


class SpecifierQualifierList(metaclass=LHS):
    key = 48
    relativeOrder = 4
    rhs = ('TypeQualifier',)


class StructDeclaratorList(metaclass=LHS):
    key = 49
    relativeOrder = 1
    rhs = ('StructDeclarator',)


class StructDeclaratorList(metaclass=LHS):
    key = 50
    relativeOrder = 2
    rhs = ('StructDeclarator', ',', 'StructDeclaratorList')


class StructDeclarator(metaclass=LHS):
    key = 51
    relativeOrder = 1
    rhs = ('Declarator',)


class StructDeclarator(metaclass=LHS):
    key = 52
    relativeOrder = 2
    rhs = ('Declarator', ':', 'ConstantExpression')


class StructDeclarator(metaclass=LHS):
    key = 53
    relativeOrder = 3
    rhs = (':', 'ConstantExpression')


class EnumSpecifier(metaclass=LHS):
    key = 54
    relativeOrder = 1
    rhs = ('enum', 'identifier', '{', 'EnumeratorList', '}')


class EnumSpecifier(metaclass=LHS):
    key = 55
    relativeOrder = 2
    rhs = ('enum', '{', 'EnumeratorList', '}')


class EnumSpecifier(metaclass=LHS):
    key = 56
    relativeOrder = 3
    rhs = ('enum', 'identifier', '{', 'EnumeratorList', ',', '}')


class EnumSpecifier(metaclass=LHS):
    key = 57
    relativeOrder = 4
    rhs = ('enum', '{', 'EnumeratorList', ',', '}')


class EnumSpecifier(metaclass=LHS):
    key = 58
    relativeOrder = 5
    rhs = ('enum', 'identifier')


class EnumeratorList(metaclass=LHS):
    key = 59
    relativeOrder = 1
    rhs = ('Enumerator',)


class EnumeratorList(metaclass=LHS):
    key = 60
    relativeOrder = 2
    rhs = ('EnumeratorList', ',', 'Enumerator')


class Enumerator(metaclass=LHS):
    key = 61
    relativeOrder = 1
    rhs = ('EnumerationConstant',)


class Enumerator(metaclass=LHS):
    key = 62
    relativeOrder = 2
    rhs = ('EnumerationConstant', '=', 'ConstantExpression')


class Declarator(metaclass=LHS):
    key = 63
    relativeOrder = 1
    rhs = ('Pointer', 'DirectDeclarator')


class Declarator(metaclass=LHS):
    key = 64
    relativeOrder = 2
    rhs = ('DirectDeclarator',)


class DirectDeclarator(metaclass=LHS):
    key = 65
    relativeOrder = 1
    rhs = ('identifier',)


class DirectDeclarator(metaclass=LHS):
    key = 66
    relativeOrder = 2
    rhs = ('(', 'Declarator', ')')


class DirectDeclarator(metaclass=LHS):
    key = 67
    relativeOrder = 3
    rhs = ('DirectDeclarator', '[', ']')


class DirectDeclarator(metaclass=LHS):
    key = 68
    relativeOrder = 4
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectDeclarator(metaclass=LHS):
    key = 69
    relativeOrder = 5
    rhs = ('DirectDeclarator', '[', 'AssignmentExpression', ']')


class DirectDeclarator(metaclass=LHS):
    key = 70
    relativeOrder = 6
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', ']')


class DirectDeclarator(metaclass=LHS):
    key = 71
    relativeOrder = 7
    rhs = ('DirectDeclarator', '[', 'static', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectDeclarator(metaclass=LHS):
    key = 72
    relativeOrder = 8
    rhs = ('DirectDeclarator', '[', 'static', 'AssignmentExpression', ']')


class DirectDeclarator(metaclass=LHS):
    key = 73
    relativeOrder = 9
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', 'static', 'AssignmentExpression', ']')


class DirectDeclarator(metaclass=LHS):
    key = 74
    relativeOrder = 10
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', '*', ']')


class DirectDeclarator(metaclass=LHS):
    key = 75
    relativeOrder = 11
    rhs = ('DirectDeclarator', '[', '*', ']')


class DirectDeclarator(metaclass=LHS):
    key = 76
    relativeOrder = 12
    rhs = ('DirectDeclarator', '(', 'ParameterTypeList', ')')


class DirectDeclarator(metaclass=LHS):
    key = 77
    relativeOrder = 13
    rhs = ('DirectDeclarator', '(', 'IdentifierList', ')')


class DirectDeclarator(metaclass=LHS):
    key = 78
    relativeOrder = 14
    rhs = ('DirectDeclarator', '(', ')')


class Pointer(metaclass=LHS):
    key = 79
    relativeOrder = 1
    rhs = ('*',)


class Pointer(metaclass=LHS):
    key = 80
    relativeOrder = 2
    rhs = ('*', 'TypeQualifierList')


class Pointer(metaclass=LHS):
    key = 81
    relativeOrder = 3
    rhs = ('*', 'TypeQualifierList', 'Pointer')


class Pointer(metaclass=LHS):
    key = 82
    relativeOrder = 4
    rhs = ('*', 'Pointer')


class TypeQualifierList(metaclass=LHS):
    key = 83
    relativeOrder = 1
    rhs = ('TypeQualifier',)


class TypeQualifierList(metaclass=LHS):
    key = 84
    relativeOrder = 2
    rhs = ('TypeQualifier', 'TypeQualifierList')


class ParameterTypeList(metaclass=LHS):
    key = 85
    relativeOrder = 1
    rhs = ('ParameterList',)


class ParameterTypeList(metaclass=LHS):
    key = 86
    relativeOrder = 2
    rhs = ('ParameterList', ',', '...')


class ParameterList(metaclass=LHS):
    key = 87
    relativeOrder = 1
    rhs = ('ParameterDeclaration',)


class ParameterList(metaclass=LHS):
    key = 88
    relativeOrder = 2
    rhs = ('ParameterDeclaration', ',', 'ParameterList')


class ParameterDeclaration(metaclass=LHS):
    key = 89
    relativeOrder = 1
    rhs = ('DeclarationSpecifiers', 'Declarator')


class ParameterDeclaration(metaclass=LHS):
    key = 90
    relativeOrder = 2
    rhs = ('DeclarationSpecifiers', 'AbstractDeclarator')


class ParameterDeclaration(metaclass=LHS):
    key = 91
    relativeOrder = 3
    rhs = ('DeclarationSpecifiers',)


class IdentifierList(metaclass=LHS):
    key = 92
    relativeOrder = 1
    rhs = ('identifier',)


class IdentifierList(metaclass=LHS):
    key = 93
    relativeOrder = 2
    rhs = ('identifier', ',', 'IdentifierList')


class Typename(metaclass=LHS):
    key = 94
    relativeOrder = 1
    rhs = ('SpecifierQualifierList', 'AbstractDeclarator')


class Typename(metaclass=LHS):
    key = 95
    relativeOrder = 2
    rhs = ('SpecifierQualifierList',)


class AbstractDeclarator(metaclass=LHS):
    key = 96
    relativeOrder = 1
    rhs = ('Pointer',)


class AbstractDeclarator(metaclass=LHS):
    key = 97
    relativeOrder = 2
    rhs = ('Pointer', 'DirectAbstractDeclarator')


class AbstractDeclarator(metaclass=LHS):
    key = 98
    relativeOrder = 3
    rhs = ('DirectAbstractDeclarator',)


class DirectAbstractDeclarator(metaclass=LHS):
    key = 99
    relativeOrder = 1
    rhs = ('(', 'AbstractDeclarator', ')')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 100
    relativeOrder = 2
    rhs = ('DirectAbstractDeclarator', '[', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 101
    relativeOrder = 3
    rhs = ('DirectAbstractDeclarator', '[', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 102
    relativeOrder = 4
    rhs = ('DirectAbstractDeclarator', '[', 'TypeQualifierList', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 103
    relativeOrder = 5
    rhs = ('DirectAbstractDeclarator', '[', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 104
    relativeOrder = 6
    rhs = ('DirectAbstractDeclarator', '[', 'static', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 105
    relativeOrder = 7
    rhs = ('DirectAbstractDeclarator', '[', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 106
    relativeOrder = 8
    rhs = ('DirectAbstractDeclarator', '[', 'TypeQualifierList', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 107
    relativeOrder = 9
    rhs = ('DirectAbstractDeclarator', '[', '*', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 108
    relativeOrder = 10
    rhs = ('DirectAbstractDeclarator', '(', 'ParameterTypeList', ')')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 109
    relativeOrder = 11
    rhs = ('DirectAbstractDeclarator', '(', ')')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 110
    relativeOrder = 12
    rhs = ('[', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 111
    relativeOrder = 13
    rhs = ('[', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 112
    relativeOrder = 14
    rhs = ('[', 'TypeQualifierList', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 113
    relativeOrder = 15
    rhs = ('[', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 114
    relativeOrder = 16
    rhs = ('[', 'static', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 115
    relativeOrder = 17
    rhs = ('[', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 116
    relativeOrder = 18
    rhs = ('[', 'TypeQualifierList', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 117
    relativeOrder = 19
    rhs = ('[', '*', ']')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 118
    relativeOrder = 20
    rhs = ('(', 'ParameterTypeList', ')')


class DirectAbstractDeclarator(metaclass=LHS):
    key = 119
    relativeOrder = 21
    rhs = ('(', ')')


class TypedefName(metaclass=LHS):
    key = 120
    relativeOrder = 1
    rhs = ('identifier',)


class FunctionSpecifier(metaclass=LHS):
    key = 121
    relativeOrder = 1
    rhs = ('inline',)


class Initializer(metaclass=LHS):
    key = 122
    relativeOrder = 1
    rhs = ('AssignmentExpression',)


class Initializer(metaclass=LHS):
    key = 123
    relativeOrder = 2
    rhs = ('{', 'InitializerList', '}')


class Initializer(metaclass=LHS):
    key = 124
    relativeOrder = 3
    rhs = ('{', 'InitializerList', ',', '}')


class InitializerList(metaclass=LHS):
    key = 125
    relativeOrder = 1
    rhs = ('Designation', 'Initializer')


class InitializerList(metaclass=LHS):
    key = 126
    relativeOrder = 2
    rhs = ('Initializer',)


class InitializerList(metaclass=LHS):
    key = 127
    relativeOrder = 3
    rhs = ('InitializerList', ',', 'Designation', 'Initializer')


class InitializerList(metaclass=LHS):
    key = 128
    relativeOrder = 4
    rhs = ('InitializerList', ',', 'Initializer')


class Designation(metaclass=LHS):
    key = 129
    relativeOrder = 1
    rhs = ('DesignatorList', '=')


class DesignatorList(metaclass=LHS):
    key = 130
    relativeOrder = 1
    rhs = ('Designator',)


class DesignatorList(metaclass=LHS):
    key = 131
    relativeOrder = 2
    rhs = ('Designator', 'DesignatorList')


class Designator(metaclass=LHS):
    key = 132
    relativeOrder = 1
    rhs = ('[', 'ConstantExpression', ']')


class Designator(metaclass=LHS):
    key = 133
    relativeOrder = 2
    rhs = ('.', 'identifier')


class PrimaryExpression(metaclass=LHS):
    key = 134
    relativeOrder = 1
    rhs = ('identifier',)


class PrimaryExpression(metaclass=LHS):
    key = 135
    relativeOrder = 2
    rhs = ('constant',)


class PrimaryExpression(metaclass=LHS):
    key = 136
    relativeOrder = 3
    rhs = ('stringLiteral',)


class PrimaryExpression(metaclass=LHS):
    key = 137
    relativeOrder = 4
    rhs = ('(', 'Expression', ')')


class PostfixExpression(metaclass=LHS):
    key = 138
    relativeOrder = 1
    rhs = ('PrimaryExpression',)


class PostfixExpression(metaclass=LHS):
    key = 139
    relativeOrder = 2
    rhs = ('PostfixExpression', '[', 'Expression', ']')


class PostfixExpression(metaclass=LHS):
    key = 140
    relativeOrder = 3
    rhs = ('PostfixExpression', '(', ')')


class PostfixExpression(metaclass=LHS):
    key = 141
    relativeOrder = 4
    rhs = ('PostfixExpression', '(', 'ArgumentExpressionList', ')')


class PostfixExpression(metaclass=LHS):
    key = 142
    relativeOrder = 5
    rhs = ('PostfixExpression', '.', 'identifier')


class PostfixExpression(metaclass=LHS):
    key = 143
    relativeOrder = 6
    rhs = ('PostfixEpression', '->', 'identifier')


class PostfixExpression(metaclass=LHS):
    key = 144
    relativeOrder = 7
    rhs = ('PostfixExpression', '++')


class PostfixExpression(metaclass=LHS):
    key = 145
    relativeOrder = 8
    rhs = ('PostfixExpression', '--')


class PostfixExpression(metaclass=LHS):
    key = 146
    relativeOrder = 9
    rhs = ('(', 'Typename', ')', '{', 'InitializerList', '}')


class PostfixExpression(metaclass=LHS):
    key = 147
    relativeOrder = 10
    rhs = ('(', 'Typename', ')', '{', 'InitializerList', ',', '}')


class ArgumentExpressionList(metaclass=LHS):
    key = 148
    relativeOrder = 1
    rhs = ('AssignmentExpression',)


class ArgumentExpressionList(metaclass=LHS):
    key = 149
    relativeOrder = 2
    rhs = ('ArgumentExpressionList', ',', 'AssignmentExpression')


class UnaryExpression(metaclass=LHS):
    key = 150
    relativeOrder = 1
    rhs = ('PostfixExpression',)


class UnaryExpression(metaclass=LHS):
    key = 151
    relativeOrder = 2
    rhs = ('++', 'UnaryExpression')


class UnaryExpression(metaclass=LHS):
    key = 152
    relativeOrder = 3
    rhs = ('--', 'UnaryExpression')


class UnaryExpression(metaclass=LHS):
    key = 153
    relativeOrder = 4
    rhs = ('UnaryOp', 'CastExpression')


class UnaryExpression(metaclass=LHS):
    key = 154
    relativeOrder = 5
    rhs = ('sizeof', 'UnaryExpression')


class UnaryExpression(metaclass=LHS):
    key = 155
    relativeOrder = 6
    rhs = ('sizeof', '(', 'Typename', ')')


class UnaryOp(metaclass=LHS):
    key = 156
    relativeOrder = 1
    rhs = ('&',)


class UnaryOp(metaclass=LHS):
    key = 157
    relativeOrder = 2
    rhs = ('*',)


class UnaryOp(metaclass=LHS):
    key = 158
    relativeOrder = 3
    rhs = ('+',)


class UnaryOp(metaclass=LHS):
    key = 159
    relativeOrder = 4
    rhs = ('-',)


class UnaryOp(metaclass=LHS):
    key = 160
    relativeOrder = 5
    rhs = ('~',)


class UnaryOp(metaclass=LHS):
    key = 161
    relativeOrder = 6
    rhs = ('!',)


class CastExpression(metaclass=LHS):
    key = 162
    relativeOrder = 1
    rhs = ('UnaryExpression',)


class CastExpression(metaclass=LHS):
    key = 163
    relativeOrder = 2
    rhs = ('(', 'Typename', ')', 'CastExpression')


class MultiplicativeExpression(metaclass=LHS):
    key = 164
    relativeOrder = 1
    rhs = ('CastExpression',)


class MultiplicativeExpression(metaclass=LHS):
    key = 165
    relativeOrder = 2
    rhs = ('MultiplicativeExpression', '*', 'CastExpression')


class MultiplicativeExpression(metaclass=LHS):
    key = 166
    relativeOrder = 3
    rhs = ('MultiplicativeExpression', '/', 'CastExpression')


class MultiplicativeExpression(metaclass=LHS):
    key = 167
    relativeOrder = 4
    rhs = ('MultiplicativeExpression', '%', 'CastExpression')


class AdditiveExpression(metaclass=LHS):
    key = 168
    relativeOrder = 1
    rhs = ('MultiplicativeExpression',)


class AdditiveExpression(metaclass=LHS):
    key = 169
    relativeOrder = 2
    rhs = ('AdditiveExpression', '+', 'MultiplicativeExpression')


class AdditiveExpression(metaclass=LHS):
    key = 170
    relativeOrder = 3
    rhs = ('AdditiveExpression', '-', 'MultiplicativeExpression')


class ShiftExpression(metaclass=LHS):
    key = 171
    relativeOrder = 1
    rhs = ('AdditiveExpression',)


class ShiftExpression(metaclass=LHS):
    key = 172
    relativeOrder = 2
    rhs = ('ShiftExpression', '<<', 'AdditiveExpression')


class ShiftExpression(metaclass=LHS):
    key = 173
    relativeOrder = 3
    rhs = ('ShiftExpression', '>>', 'AdditiveExpression')


class RelationalExpression(metaclass=LHS):
    key = 174
    relativeOrder = 1
    rhs = ('ShiftExpression',)


class RelationalExpression(metaclass=LHS):
    key = 175
    relativeOrder = 2
    rhs = ('RelationalExpression', '<', 'ShiftExpression')


class RelationalExpression(metaclass=LHS):
    key = 176
    relativeOrder = 3
    rhs = ('RelationalExpression', '>', 'ShiftExpression')


class RelationalExpression(metaclass=LHS):
    key = 177
    relativeOrder = 4
    rhs = ('RelationalExpression', '<=', 'ShiftExpression')


class RelationalExpression(metaclass=LHS):
    key = 178
    relativeOrder = 5
    rhs = ('RelationalExpression', '>=', 'ShiftExpression')


class EqualityExpression(metaclass=LHS):
    key = 179
    relativeOrder = 1
    rhs = ('RelationalExpression',)


class EqualityExpression(metaclass=LHS):
    key = 180
    relativeOrder = 2
    rhs = ('EqualityExpression', '==', 'RelationalExpression')


class EqualityExpression(metaclass=LHS):
    key = 181
    relativeOrder = 3
    rhs = ('EqualityExpression', '!=', 'RelationalExpression')


class ANDExpression(metaclass=LHS):
    key = 182
    relativeOrder = 1
    rhs = ('EqualityExpression',)


class ANDExpression(metaclass=LHS):
    key = 183
    relativeOrder = 2
    rhs = ('ANDExpression', '&', 'EqualityExpression')


class ExclusiveORExpression(metaclass=LHS):
    key = 184
    relativeOrder = 1
    rhs = ('ANDExpression',)


class ExclusiveORExpression(metaclass=LHS):
    key = 185
    relativeOrder = 2
    rhs = ('ExclusiveORExpression', '^', 'ANDExpression')


class InclusiveORExpression(metaclass=LHS):
    key = 186
    relativeOrder = 1
    rhs = ('ExclusiveORExpression',)


class InclusiveORExpression(metaclass=LHS):
    key = 187
    relativeOrder = 2
    rhs = ('InclusiveORExpression', '|', 'ExclusiveORExpression')


class LogicalANDExpression(metaclass=LHS):
    key = 188
    relativeOrder = 1
    rhs = ('InclusiveORExpression',)


class LogicalANDExpression(metaclass=LHS):
    key = 189
    relativeOrder = 2
    rhs = ('LogicalANDExpression', '&&', 'InclusiveORExpression')


class LogicalORExpression(metaclass=LHS):
    key = 190
    relativeOrder = 1
    rhs = ('LogicalANDExpression',)


class LogicalORExpression(metaclass=LHS):
    key = 191
    relativeOrder = 2
    rhs = ('LogicalORExpression', '||', 'LogicalANDExpression')


class ConditionalExpression(metaclass=LHS):
    key = 192
    relativeOrder = 1
    rhs = ('LogicalORExpression',)


class ConditionalExpression(metaclass=LHS):
    key = 193
    relativeOrder = 2
    rhs = ('LogicalORExpression', '?', 'Expression', ':', 'ConditionalExpression')


class AssignmentExpression(metaclass=LHS):
    key = 194
    relativeOrder = 1
    rhs = ('ConditionalExpression',)


class AssignmentExpression(metaclass=LHS):
    key = 195
    relativeOrder = 2
    rhs = ('UnaryExpression', 'AssignmentOp', 'AssignmentExpression')


class AssignmentOp(metaclass=LHS):
    key = 196
    relativeOrder = 1
    rhs = ('=',)


class AssignmentOp(metaclass=LHS):
    key = 197
    relativeOrder = 2
    rhs = ('*=',)


class AssignmentOp(metaclass=LHS):
    key = 198
    relativeOrder = 3
    rhs = ('/=',)


class AssignmentOp(metaclass=LHS):
    key = 199
    relativeOrder = 4
    rhs = ('%=',)


class AssignmentOp(metaclass=LHS):
    key = 200
    relativeOrder = 5
    rhs = ('+=',)


class AssignmentOp(metaclass=LHS):
    key = 201
    relativeOrder = 6
    rhs = ('-=',)


class AssignmentOp(metaclass=LHS):
    key = 202
    relativeOrder = 7
    rhs = ('<<=',)


class AssignmentOp(metaclass=LHS):
    key = 203
    relativeOrder = 8
    rhs = ('>>=',)


class AssignmentOp(metaclass=LHS):
    key = 204
    relativeOrder = 9
    rhs = ('&=',)


class AssignmentOp(metaclass=LHS):
    key = 205
    relativeOrder = 10
    rhs = ('^=',)


class AssignmentOp(metaclass=LHS):
    key = 206
    relativeOrder = 11
    rhs = ('|=',)


class Expression(metaclass=LHS):
    key = 207
    relativeOrder = 1
    rhs = ('AssignmentExpression',)


class Expression(metaclass=LHS):
    key = 208
    relativeOrder = 2
    rhs = ('Expression', ',', 'AssignmentExpression')


class ConstantExpression(metaclass=LHS):
    key = 209
    relativeOrder = 1
    rhs = ('ConditionalExpression',)


class Statement(metaclass=LHS):
    key = 210
    relativeOrder = 1
    rhs = ('LabeledStatement',)


class Statement(metaclass=LHS):
    key = 211
    relativeOrder = 2
    rhs = ('CompoundStatement',)


class Statement(metaclass=LHS):
    key = 212
    relativeOrder = 3
    rhs = ('ExpressionStatement',)


class Statement(metaclass=LHS):
    key = 213
    relativeOrder = 4
    rhs = ('SelectionStatement',)


class Statement(metaclass=LHS):
    key = 214
    relativeOrder = 5
    rhs = ('IterationStatement',)


class Statement(metaclass=LHS):
    key = 215
    relativeOrder = 6
    rhs = ('JumpStatement',)


class LabeledStatement(metaclass=LHS):
    key = 216
    relativeOrder = 1
    rhs = ('identifier', ':', 'Statement')


class LabeledStatement(metaclass=LHS):
    key = 217
    relativeOrder = 2
    rhs = ('case', 'constantExpression', ':', 'Statement')


class LabeledStatement(metaclass=LHS):
    key = 218
    relativeOrder = 3
    rhs = ('default', ':', 'Statement')


class CompoundStatement(metaclass=LHS):
    key = 219
    relativeOrder = 1
    rhs = ('{', 'BlockItemList', '}')


class CompoundStatement(metaclass=LHS):
    key = 220
    relativeOrder = 2
    rhs = ('{', '}')


class BlockItemList(metaclass=LHS):
    key = 221
    relativeOrder = 1
    rhs = ('BlockItem',)


class BlockItemList(metaclass=LHS):
    key = 222
    relativeOrder = 2
    rhs = ('BlockItem', 'BlockItemList')


class BlockItem(metaclass=LHS):
    key = 223
    relativeOrder = 1
    rhs = ('Declaration',)


class BlockItem(metaclass=LHS):
    key = 224
    relativeOrder = 2
    rhs = ('Statement',)


class ExpressionStatement(metaclass=LHS):
    key = 225
    relativeOrder = 1
    rhs = ('Expression', ';')


class ExpressionStatement(metaclass=LHS):
    key = 226
    relativeOrder = 2
    rhs = (';',)


class SelectionStatement(metaclass=LHS):
    key = 227
    relativeOrder = 1
    rhs = ('if', '(', 'Expression', ')', 'Statement')


class SelectionStatement(metaclass=LHS):
    key = 228
    relativeOrder = 2
    rhs = ('if', '(', 'Expression', ')', 'Statement', 'else', 'Statement')


class SelectionStatement(metaclass=LHS):
    key = 229
    relativeOrder = 3
    rhs = ('switch', '(', 'Expression', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 230
    relativeOrder = 1
    rhs = ('while', '(', 'Expression', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 231
    relativeOrder = 2
    rhs = ('do', 'Statement', 'while', '(', 'Expression', ')', ';')


class IterationStatement(metaclass=LHS):
    key = 232
    relativeOrder = 3
    rhs = ('for', '(', 'Expression', ';', 'Expression', ';', 'Expression', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 233
    relativeOrder = 4
    rhs = ('for', '(', 'Expression', ';', 'Expression', ';', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 234
    relativeOrder = 5
    rhs = ('for', '(', 'Expression', ';', ';', 'Expression', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 235
    relativeOrder = 6
    rhs = ('for', '(', ';', 'Expression', ';', 'Expression', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 236
    relativeOrder = 7
    rhs = ('for', '(', 'Expression', ';', ';', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 237
    relativeOrder = 8
    rhs = ('for', '(', ';', 'Expression', ';', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 238
    relativeOrder = 9
    rhs = ('for', '(', ';', ';', 'Expression', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 239
    relativeOrder = 10
    rhs = ('for', '(', ';', ';', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 240
    relativeOrder = 11
    rhs = ('for', '(', 'Declaration', 'Expression', ';', 'Expression', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 241
    relativeOrder = 12
    rhs = ('for', '(', 'Declaration', 'Expression', ';', ')', 'Statement')


class IterationStatement(metaclass=LHS):
    key = 242
    relativeOrder = 13
    rhs = ('for', '(', 'Declaration', ';', ')', 'Statement')


class JumpStatement(metaclass=LHS):
    key = 243
    relativeOrder = 1
    rhs = ('goto', 'identifier', ';')


class JumpStatement(metaclass=LHS):
    key = 244
    relativeOrder = 2
    rhs = ('continue', ';')


class JumpStatement(metaclass=LHS):
    key = 245
    relativeOrder = 3
    rhs = ('break', ';')


class JumpStatement(metaclass=LHS):
    key = 246
    relativeOrder = 4
    rhs = ('return', 'Expression', ';')


class JumpStatement(metaclass=LHS):
    key = 247
    relativeOrder = 5
    rhs = ('return', ';')


class FunctionDefinition(metaclass=LHS):
    key = 248
    relativeOrder = 1
    rhs = ('DeclarationSpecifiers', 'Declarator', 'CompoundStatement')


class DeclarationList(metaclass=LHS):
    key = 249
    relativeOrder = 1
    rhs = ('Declaration',)


class DeclarationList(metaclass=LHS):
    key = 250
    relativeOrder = 2
    rhs = ('Declaration', 'DeclarationList')


class TranslationUnit(metaclass=LHS):
    key = 251
    relativeOrder = 1
    rhs = ('ExternalDeclaration',)


class TranslationUnit(metaclass=LHS):
    key = 252
    relativeOrder = 2
    rhs = ('ExternalDeclaration', 'TranslationUnit')


class ExternalDeclaration(metaclass=LHS):
    key = 253
    relativeOrder = 1
    rhs = ('FunctionDefinition',)


class ExternalDeclaration(metaclass=LHS):
    key = 254
    relativeOrder = 2
    rhs = ('Declaration',)

