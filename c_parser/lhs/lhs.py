from playground import *
from typing import Dict, List


class Declaration(Base, metaclass=LHS):
    key = 1
    relativeOrder = 1
    rhs = ('DeclarationSpecifiers', 'InitDeclaratorList', ';')

    def run(self, env, *args, **kwargs):
        assert len(self.rhs) == 3
        assert strCheck(self, 0)
        assert strCheck(self, 1)
        type0, category, info = self.rhs[0].run(env)
        print(f'category={category}')
        declarators = self.rhs[1].run(env, type0=type0, category=category)
        print(f'定义变量如下：')
        for d in declarators:
            print(d, ':', 'typedef' if d in env.types else '', env[d])
        # specifierQualifierDict: Dict[str, list] = rhs[0]()
        # initType = c_type.normalize(specifierQualifierDict['TypeSpecifier'])
        #
        # if 'TypeQualifier' in specifierQualifierDict:
        #     initType.addQualifier(specifierQualifierDict['TypeQualifier'])
        # print('initType=', initType)
        #
        # Decl = VarDecl \
        #     if 'typedef' not in specifierQualifierDict.get('StorageClassSpecifier', []) \
        #     else TypedefDecl
        # print('Decl=', Decl)
        #
        # if isinstance(specifierQualifierDict['TypeSpecifier'][0], RecordDecl):
        #     return DeclStmt(specifierQualifierDict['TypeSpecifier'][0],
        #                     *rhs[1](inheritType=initType, Decl=Decl))
        # return DeclStmt(*rhs[1](inheritType=initType, Decl=Decl))


class Declaration(Base, metaclass=LHS):
    key = 2
    relativeOrder = 2
    rhs = ('DeclarationSpecifiers', ';')


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 3
    relativeOrder = 1
    rhs = ('StorageClassSpecifier', 'DeclarationSpecifiers')

    def run(self, env, *args, **kwargs):
        print(f'len(self.rhs)={len(self.rhs)}')
        d: defaultdict = defaultdict(list)
        for specifier in self.rhs:
            name = specifier.__class__.__name__
            assert name in ('StorageClassSpecifier', 'TypeSpecifier', 'TypeQualifier')
            d[name].append(specifier.run(env))
        print(f'dict={d}')
        dsc = d['StorageClassSpecifier']
        dts = d['TypeSpecifier']
        dtq = d['TypeQualifier']
        type0 = c_type.normalize(dts)
        type0.addQualifier(dtq)
        dsc = list(set(dsc))
        assert len(dsc) <= 1
        if len(dsc) == 0:
            return type0, 'var', ''
        if dsc[0] == 'typedef':
            return type0, 'typedef', ''
        if dsc[0] == 'static':
            return type0, 'var', 'static'
        raise NotImplementedError()


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 4
    relativeOrder = 2
    rhs = ('StorageClassSpecifier',)


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 5
    relativeOrder = 3
    rhs = ('TypeSpecifier', 'DeclarationSpecifiers')


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 6
    relativeOrder = 4
    rhs = ('TypeSpecifier',)


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 7
    relativeOrder = 5
    rhs = ('TypeQualifier', 'DeclarationSpecifiers')


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 8
    relativeOrder = 6
    rhs = ('TypeQualifier',)


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 9
    relativeOrder = 7
    rhs = ('FunctionSpecifier', 'DeclarationSpecifiers')


class DeclarationSpecifiers(Base, metaclass=LHS):
    key = 10
    relativeOrder = 8
    rhs = ('FunctionSpecifier',)


class InitDeclaratorList(Base, metaclass=LHS):
    key = 11
    relativeOrder = 1
    rhs = ('InitDeclarator',)

    def run(self, env, *args, **kwargs):
        # type0, cotegory
        assert self.rhs[0].__class__.__name__ == self.__class__.rhs[0]
        print(f'len(initDeclaratorlist)={len(self.rhs)}')
        return [a.run(env, *args, **kwargs) for a in self.rhs]


class InitDeclaratorList(Base, metaclass=LHS):
    key = 12
    relativeOrder = 2
    rhs = ('InitDeclarator', ',', 'InitDeclaratorList')

    def run(self, env, *args, **kwargs):
        # type0, category
        print(f'len(initDeclaratorlist)={len(self.rhs)}')
        return [a.run(env, *args, **kwargs) for a in self.rhs]


class InitDeclarator(Base, metaclass=LHS):
    key = 13
    relativeOrder = 1
    rhs = ('Declarator',)

    def run(self, env, *args, **kwargs):
        # type0, category
        return self.rhs[0].run(env, *args, **kwargs)


class InitDeclarator(Base, metaclass=LHS):
    key = 14
    relativeOrder = 2
    rhs = ('Declarator', '=', 'Initializer')


class StorageClassSpecifier(Base, metaclass=LHS):
    key = 15
    relativeOrder = 1
    rhs = ('typedef',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class StorageClassSpecifier(Base, metaclass=LHS):
    key = 16
    relativeOrder = 2
    rhs = ('extern',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class StorageClassSpecifier(Base, metaclass=LHS):
    key = 17
    relativeOrder = 3
    rhs = ('static',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class StorageClassSpecifier(Base, metaclass=LHS):
    key = 18
    relativeOrder = 4
    rhs = ('auto',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class StorageClassSpecifier(Base, metaclass=LHS):
    key = 19
    relativeOrder = 5
    rhs = ('register',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 20
    relativeOrder = 1
    rhs = ('void',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 21
    relativeOrder = 2
    rhs = ('char',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 22
    relativeOrder = 3
    rhs = ('short',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 23
    relativeOrder = 4
    rhs = ('int',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 24
    relativeOrder = 5
    rhs = ('long',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 25
    relativeOrder = 6
    rhs = ('float',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 26
    relativeOrder = 7
    rhs = ('double',)


class TypeSpecifier(Base, metaclass=LHS):
    key = 27
    relativeOrder = 8
    rhs = ('signed',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 28
    relativeOrder = 9
    rhs = ('unsigned',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 29
    relativeOrder = 10
    rhs = ('_Bool',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 30
    relativeOrder = 11
    rhs = ('_Complex',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeSpecifier(Base, metaclass=LHS):
    key = 31
    relativeOrder = 12
    rhs = ('StructOrUnionSpecifier',)


class TypeSpecifier(Base, metaclass=LHS):
    key = 32
    relativeOrder = 13
    rhs = ('EnumSpecifier',)


class TypeSpecifier(Base, metaclass=LHS):
    key = 33
    relativeOrder = 14
    rhs = ('TypedefName',)


class TypeQualifier(Base, metaclass=LHS):
    key = 34
    relativeOrder = 1
    rhs = ('const',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeQualifier(Base, metaclass=LHS):
    key = 35
    relativeOrder = 2
    rhs = ('restrict',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class TypeQualifier(Base, metaclass=LHS):
    key = 36
    relativeOrder = 3
    rhs = ('volatile',)

    def run(self, env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        return self.rhs[0]


class StructOrUnionSpecifier(Base, metaclass=LHS):
    key = 37
    relativeOrder = 1
    rhs = ('StructOrUnion', 'identifier', '{', 'StructDeclarationList', '}')


class StructOrUnionSpecifier(Base, metaclass=LHS):
    key = 38
    relativeOrder = 2
    rhs = ('StructOrUnion', '{', 'StructDeclarationList', '}')


class StructOrUnionSpecifier(Base, metaclass=LHS):
    key = 39
    relativeOrder = 3
    rhs = ('StructOrUnion', 'identifier')


class StructOrUnion(Base, metaclass=LHS):
    key = 40
    relativeOrder = 1
    rhs = ('struct',)


class StructOrUnion(Base, metaclass=LHS):
    key = 41
    relativeOrder = 2
    rhs = ('union',)


class StructDeclarationList(Base, metaclass=LHS):
    key = 42
    relativeOrder = 1
    rhs = ('StructDeclaration',)


class StructDeclarationList(Base, metaclass=LHS):
    key = 43
    relativeOrder = 2
    rhs = ('StructDeclaration', 'StructDeclarationList')


class StructDeclaration(Base, metaclass=LHS):
    key = 44
    relativeOrder = 1
    rhs = ('SpecifierQualifierList', 'StructDeclaratorList', ';')


class SpecifierQualifierList(Base, metaclass=LHS):
    key = 45
    relativeOrder = 1
    rhs = ('TypeSpecifier', 'SpecifierQualifierList')


class SpecifierQualifierList(Base, metaclass=LHS):
    key = 46
    relativeOrder = 2
    rhs = ('TypeSpecifier',)


class SpecifierQualifierList(Base, metaclass=LHS):
    key = 47
    relativeOrder = 3
    rhs = ('TypeQualifier', 'SpecifierQualifierList')


class SpecifierQualifierList(Base, metaclass=LHS):
    key = 48
    relativeOrder = 4
    rhs = ('TypeQualifier',)


class StructDeclaratorList(Base, metaclass=LHS):
    key = 49
    relativeOrder = 1
    rhs = ('StructDeclarator',)


class StructDeclaratorList(Base, metaclass=LHS):
    key = 50
    relativeOrder = 2
    rhs = ('StructDeclarator', ',', 'StructDeclaratorList')


class StructDeclarator(Base, metaclass=LHS):
    key = 51
    relativeOrder = 1
    rhs = ('Declarator',)


class StructDeclarator(Base, metaclass=LHS):
    key = 52
    relativeOrder = 2
    rhs = ('Declarator', ':', 'ConstantExpression')


class StructDeclarator(Base, metaclass=LHS):
    key = 53
    relativeOrder = 3
    rhs = (':', 'ConstantExpression')


class EnumSpecifier(Base, metaclass=LHS):
    key = 54
    relativeOrder = 1
    rhs = ('enum', 'identifier', '{', 'EnumeratorList', '}')


class EnumSpecifier(Base, metaclass=LHS):
    key = 55
    relativeOrder = 2
    rhs = ('enum', '{', 'EnumeratorList', '}')


class EnumSpecifier(Base, metaclass=LHS):
    key = 56
    relativeOrder = 3
    rhs = ('enum', 'identifier', '{', 'EnumeratorList', ',', '}')


class EnumSpecifier(Base, metaclass=LHS):
    key = 57
    relativeOrder = 4
    rhs = ('enum', '{', 'EnumeratorList', ',', '}')


class EnumSpecifier(Base, metaclass=LHS):
    key = 58
    relativeOrder = 5
    rhs = ('enum', 'identifier')


class EnumeratorList(Base, metaclass=LHS):
    key = 59
    relativeOrder = 1
    rhs = ('Enumerator',)


class EnumeratorList(Base, metaclass=LHS):
    key = 60
    relativeOrder = 2
    rhs = ('EnumeratorList', ',', 'Enumerator')


class Enumerator(Base, metaclass=LHS):
    key = 61
    relativeOrder = 1
    rhs = ('EnumerationConstant',)


class Enumerator(Base, metaclass=LHS):
    key = 62
    relativeOrder = 2
    rhs = ('EnumerationConstant', '=', 'ConstantExpression')


class Declarator(Base, metaclass=LHS):
    key = 63
    relativeOrder = 1
    rhs = ('Pointer', 'DirectDeclarator')

    def run(self, env, *args, **kwargs):
        # type0, category
        assert strCheck(self, 0)
        assert strCheck(self, 1)
        type0 = kwargs['type0']
        category = kwargs['category']
        # Decl = kwargs['Decl']
        type0, qualifiers = self.rhs[0].run(env, type0=type0)
        # res = self.rhs[1].run(type0=type0, Decl=Decl)
        varName = self.rhs[1].run(env, type0=type0, category=category)
        env[varName].addQualifier(qualifiers)
        return varName


class Declarator(Base, metaclass=LHS):
    key = 64
    relativeOrder = 2
    rhs = ('DirectDeclarator',)

    def run(self, env, *args, **kwargs):
        # type0, category
        assert strCheck(self, 0)
        return self.rhs[0].run(env, *args, **kwargs)


class DirectDeclarator(Base, metaclass=LHS):
    key = 65
    relativeOrder = 1
    rhs = ('identifier',)

    def run(self, env: Env, *args, **kwargs):
        assert isinstance(self.rhs[0], str)
        identifier = self.rhs[0]
        type0 = kwargs['type0']
        category = kwargs['category']
        if category == 'var':
            env.insertVar(identifier, type0)
        elif category == 'typedef':
            env.insertType(identifier, type0)
        return identifier


class DirectDeclarator(Base, metaclass=LHS):
    key = 66
    relativeOrder = 2
    rhs = ('(', 'Declarator', ')')

    def run(self, env, *args, **kwargs):
        return self.rhs[1].run(env, *args, **args)


class DirectDeclarator(Base, metaclass=LHS):
    key = 67
    relativeOrder = 3
    rhs = ('DirectDeclarator', '[', ']')

    def run(self, env, *args, **kwargs):
        # type0, category
        assert strCheck(self, 0)
        type0 = kwargs['type0']
        category = kwargs['category']
        type0 = c_type.Array(type0)
        return self.rhs[0].run(env, *args, type0=type0, category=category)


class DirectDeclarator(Base, metaclass=LHS):
    key = 68
    relativeOrder = 4
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', 'AssignmentExpression', ']')

    def run(self, env, *args, **kwargs):
        # type0, category
        assert strCheck(self, 0)
        assert strCheck(self, 1)
        assert strCheck(self, 2)
        raise NotImplementedError()
        type0 = kwargs['type0']
        category = kwargs['category']
        type0 = c_type.Array(type0)
        return self.rhs[0].run(env, *args, type0=type0, category=category)


class DirectDeclarator(Base, metaclass=LHS):
    key = 69
    relativeOrder = 5
    rhs = ('DirectDeclarator', '[', 'AssignmentExpression', ']')


class DirectDeclarator(Base, metaclass=LHS):
    key = 70
    relativeOrder = 6
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', ']')


class DirectDeclarator(Base, metaclass=LHS):
    key = 71
    relativeOrder = 7
    rhs = ('DirectDeclarator', '[', 'static', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectDeclarator(Base, metaclass=LHS):
    key = 72
    relativeOrder = 8
    rhs = ('DirectDeclarator', '[', 'static', 'AssignmentExpression', ']')


class DirectDeclarator(Base, metaclass=LHS):
    key = 73
    relativeOrder = 9
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', 'static', 'AssignmentExpression', ']')


class DirectDeclarator(Base, metaclass=LHS):
    key = 74
    relativeOrder = 10
    rhs = ('DirectDeclarator', '[', 'TypeQualifierList', '*', ']')


class DirectDeclarator(Base, metaclass=LHS):
    key = 75
    relativeOrder = 11
    rhs = ('DirectDeclarator', '[', '*', ']')

    def run(self, env, *args, **kwargs):
        # type0, category
        if env.scope != env.Scope.FUNCTION_PROTOTYPE:
            raise RuntimeError()
        type0 = kwargs['type0']
        category = kwargs['category']
        type0 = c_type.Array(type0)
        return self.rhs[0].run(env, *args, type0=type0, category=category)


class DirectDeclarator(Base, metaclass=LHS):
    key = 76
    relativeOrder = 12
    rhs = ('DirectDeclarator', '(', 'ParameterTypeList', ')')

    def run(self, env, *args, **kwargs):
        # type0, category
        type0 = kwargs['type0']
        category = kwargs['category']
        type0 = c_type.ParenType(type0,
                                 self.rhs[2].run(
                                     Env(
                                         Env.Scope.FUNCTION_PROTOTYPE,
                                         env
                                     )
                                 )
                                 )
        return self.rhs[0].run(env, *args, type0=type0, category=category)


class DirectDeclarator(Base, metaclass=LHS):
    key = 77
    relativeOrder = 13
    rhs = ('DirectDeclarator', '(', 'IdentifierList', ')')


class DirectDeclarator(Base, metaclass=LHS):
    key = 78
    relativeOrder = 14
    rhs = ('DirectDeclarator', '(', ')')

    def run(self, env, *args, **kwargs):
        # type0, category
        type0 = kwargs['type0']
        category = kwargs['category']
        type0 = c_type.ParenType(type0, ())
        return self.rhs[0].run(env, *args, type0=type0, category=category)


class Pointer(Base, metaclass=LHS):
    key = 79
    relativeOrder = 1
    rhs = ('*',)

    def run(self, env, *args, **kwargs) -> (c_type.CType, list):
        # type0
        type0 = kwargs['type0']
        type0 = c_type.Pointer(type0)
        return type0, []


class Pointer(Base, metaclass=LHS):
    key = 80
    relativeOrder = 2
    rhs = ('*', 'TypeQualifierList')

    def run(self, env, *args, **kwargs) -> (c_type.CType, list):
        # type0
        assert strCheck(self, 1)
        type0 = kwargs['type0']
        type0 = c_type.Pointer(type0)
        qualifiers = self.rhs[1].run(env, *args, type0=type0)
        assert isinstance(qualifiers, list)
        return type0, qualifiers


class Pointer(Base, metaclass=LHS):
    key = 81
    relativeOrder = 3
    rhs = ('*', 'TypeQualifierList', 'Pointer')

    def run(self, env, *args, **kwargs) -> (c_type.CType, list):
        # type0
        assert strCheck(self, 1)
        assert strCheck(self, 2)
        type0 = c_type.Pointer(kwargs['type0'])

        qualifiers = self.rhs[1].run(env, *args, type0=type0)
        assert isinstance(qualifiers, list)

        type0.addQualifier(qualifiers)

        return self.rhs[2].run(env, *args, type0=type0)


class Pointer(Base, metaclass=LHS):
    key = 82
    relativeOrder = 4
    rhs = ('*', 'Pointer')

    def run(self, env, *args, **kwargs) -> (c_type.CType, list):
        # type0
        assert strCheck(self, 1)
        type0 = c_type.Pointer(kwargs['type0'])

        return self.rhs[1].run(env, *args, type0=type0)


class TypeQualifierList(Base, metaclass=LHS):
    key = 83
    relativeOrder = 1
    rhs = ('TypeQualifier',)

    def run(self, env, *args, **kwargs):
        assert strCheck(self, 0)
        assert isinstance(self.rhs[0].run(env), str)
        return [self.rhs[0].run(env)]


class TypeQualifierList(Base, metaclass=LHS):
    key = 84
    relativeOrder = 2
    rhs = ('TypeQualifier', 'TypeQualifierList')

    def run(self, env, *args, **kwargs):
        res = [qualifier.run(env) for qualifier in self.rhs]
        return res


class ParameterTypeList(Base, metaclass=LHS):
    key = 85
    relativeOrder = 1
    rhs = ('ParameterList',)


class ParameterTypeList(Base, metaclass=LHS):
    key = 86
    relativeOrder = 2
    rhs = ('ParameterList', ',', '...')


class ParameterList(Base, metaclass=LHS):
    key = 87
    relativeOrder = 1
    rhs = ('ParameterDeclaration',)


class ParameterList(Base, metaclass=LHS):
    key = 88
    relativeOrder = 2
    rhs = ('ParameterDeclaration', ',', 'ParameterList')


class ParameterDeclaration(Base, metaclass=LHS):
    key = 89
    relativeOrder = 1
    rhs = ('DeclarationSpecifiers', 'Declarator')


class ParameterDeclaration(Base, metaclass=LHS):
    key = 90
    relativeOrder = 2
    rhs = ('DeclarationSpecifiers', 'AbstractDeclarator')


class ParameterDeclaration(Base, metaclass=LHS):
    key = 91
    relativeOrder = 3
    rhs = ('DeclarationSpecifiers',)


class IdentifierList(Base, metaclass=LHS):
    key = 92
    relativeOrder = 1
    rhs = ('identifier',)


class IdentifierList(Base, metaclass=LHS):
    key = 93
    relativeOrder = 2
    rhs = ('identifier', ',', 'IdentifierList')


class Typename(Base, metaclass=LHS):
    key = 94
    relativeOrder = 1
    rhs = ('SpecifierQualifierList', 'AbstractDeclarator')


class Typename(Base, metaclass=LHS):
    key = 95
    relativeOrder = 2
    rhs = ('SpecifierQualifierList',)


class AbstractDeclarator(Base, metaclass=LHS):
    key = 96
    relativeOrder = 1
    rhs = ('Pointer',)


class AbstractDeclarator(Base, metaclass=LHS):
    key = 97
    relativeOrder = 2
    rhs = ('Pointer', 'DirectAbstractDeclarator')


class AbstractDeclarator(Base, metaclass=LHS):
    key = 98
    relativeOrder = 3
    rhs = ('DirectAbstractDeclarator',)


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 99
    relativeOrder = 1
    rhs = ('(', 'AbstractDeclarator', ')')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 100
    relativeOrder = 2
    rhs = ('DirectAbstractDeclarator', '[', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 101
    relativeOrder = 3
    rhs = ('DirectAbstractDeclarator', '[', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 102
    relativeOrder = 4
    rhs = ('DirectAbstractDeclarator', '[', 'TypeQualifierList', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 103
    relativeOrder = 5
    rhs = ('DirectAbstractDeclarator', '[', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 104
    relativeOrder = 6
    rhs = ('DirectAbstractDeclarator', '[', 'static', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 105
    relativeOrder = 7
    rhs = ('DirectAbstractDeclarator', '[', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 106
    relativeOrder = 8
    rhs = ('DirectAbstractDeclarator', '[', 'TypeQualifierList', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 107
    relativeOrder = 9
    rhs = ('DirectAbstractDeclarator', '[', '*', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 108
    relativeOrder = 10
    rhs = ('DirectAbstractDeclarator', '(', 'ParameterTypeList', ')')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 109
    relativeOrder = 11
    rhs = ('DirectAbstractDeclarator', '(', ')')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 110
    relativeOrder = 12
    rhs = ('[', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 111
    relativeOrder = 13
    rhs = ('[', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 112
    relativeOrder = 14
    rhs = ('[', 'TypeQualifierList', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 113
    relativeOrder = 15
    rhs = ('[', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 114
    relativeOrder = 16
    rhs = ('[', 'static', 'TypeQualifierList', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 115
    relativeOrder = 17
    rhs = ('[', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 116
    relativeOrder = 18
    rhs = ('[', 'TypeQualifierList', 'static', 'AssignmentExpression', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 117
    relativeOrder = 19
    rhs = ('[', '*', ']')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 118
    relativeOrder = 20
    rhs = ('(', 'ParameterTypeList', ')')


class DirectAbstractDeclarator(Base, metaclass=LHS):
    key = 119
    relativeOrder = 21
    rhs = ('(', ')')


class TypedefName(Base, metaclass=LHS):
    key = 120
    relativeOrder = 1
    rhs = ('identifier',)


class FunctionSpecifier(Base, metaclass=LHS):
    key = 121
    relativeOrder = 1
    rhs = ('inline',)


class Initializer(Base, metaclass=LHS):
    key = 122
    relativeOrder = 1
    rhs = ('AssignmentExpression',)


class Initializer(Base, metaclass=LHS):
    key = 123
    relativeOrder = 2
    rhs = ('{', 'InitializerList', '}')


class Initializer(Base, metaclass=LHS):
    key = 124
    relativeOrder = 3
    rhs = ('{', 'InitializerList', ',', '}')


class InitializerList(Base, metaclass=LHS):
    key = 125
    relativeOrder = 1
    rhs = ('Designation', 'Initializer')


class InitializerList(Base, metaclass=LHS):
    key = 126
    relativeOrder = 2
    rhs = ('Initializer',)


class InitializerList(Base, metaclass=LHS):
    key = 127
    relativeOrder = 3
    rhs = ('InitializerList', ',', 'Designation', 'Initializer')


class InitializerList(Base, metaclass=LHS):
    key = 128
    relativeOrder = 4
    rhs = ('InitializerList', ',', 'Initializer')


class Designation(Base, metaclass=LHS):
    key = 129
    relativeOrder = 1
    rhs = ('DesignatorList', '=')


class DesignatorList(Base, metaclass=LHS):
    key = 130
    relativeOrder = 1
    rhs = ('Designator',)


class DesignatorList(Base, metaclass=LHS):
    key = 131
    relativeOrder = 2
    rhs = ('Designator', 'DesignatorList')


class Designator(Base, metaclass=LHS):
    key = 132
    relativeOrder = 1
    rhs = ('[', 'ConstantExpression', ']')


class Designator(Base, metaclass=LHS):
    key = 133
    relativeOrder = 2
    rhs = ('.', 'identifier')


class PrimaryExpression(Base, metaclass=LHS):
    key = 134
    relativeOrder = 1
    rhs = ('identifier',)


class PrimaryExpression(Base, metaclass=LHS):
    key = 135
    relativeOrder = 2
    rhs = ('constant',)


class PrimaryExpression(Base, metaclass=LHS):
    key = 136
    relativeOrder = 3
    rhs = ('stringLiteral',)


class PrimaryExpression(Base, metaclass=LHS):
    key = 137
    relativeOrder = 4
    rhs = ('(', 'Expression', ')')


class PostfixExpression(Base, metaclass=LHS):
    key = 138
    relativeOrder = 1
    rhs = ('PrimaryExpression',)


class PostfixExpression(Base, metaclass=LHS):
    key = 139
    relativeOrder = 2
    rhs = ('PostfixExpression', '[', 'Expression', ']')


class PostfixExpression(Base, metaclass=LHS):
    key = 140
    relativeOrder = 3
    rhs = ('PostfixExpression', '(', ')')


class PostfixExpression(Base, metaclass=LHS):
    key = 141
    relativeOrder = 4
    rhs = ('PostfixExpression', '(', 'ArgumentExpressionList', ')')


class PostfixExpression(Base, metaclass=LHS):
    key = 142
    relativeOrder = 5
    rhs = ('PostfixExpression', '.', 'identifier')


class PostfixExpression(Base, metaclass=LHS):
    key = 143
    relativeOrder = 6
    rhs = ('PostfixExpression', '->', 'identifier')


class PostfixExpression(Base, metaclass=LHS):
    key = 144
    relativeOrder = 7
    rhs = ('PostfixExpression', '++')


class PostfixExpression(Base, metaclass=LHS):
    key = 145
    relativeOrder = 8
    rhs = ('PostfixExpression', '--')


class PostfixExpression(Base, metaclass=LHS):
    key = 146
    relativeOrder = 9
    rhs = ('(', 'Typename', ')', '{', 'InitializerList', '}')


class PostfixExpression(Base, metaclass=LHS):
    key = 147
    relativeOrder = 10
    rhs = ('(', 'Typename', ')', '{', 'InitializerList', ',', '}')


class ArgumentExpressionList(Base, metaclass=LHS):
    key = 148
    relativeOrder = 1
    rhs = ('AssignmentExpression',)


class ArgumentExpressionList(Base, metaclass=LHS):
    key = 149
    relativeOrder = 2
    rhs = ('ArgumentExpressionList', ',', 'AssignmentExpression')


class UnaryExpression(Base, metaclass=LHS):
    key = 150
    relativeOrder = 1
    rhs = ('PostfixExpression',)


class UnaryExpression(Base, metaclass=LHS):
    key = 151
    relativeOrder = 2
    rhs = ('++', 'UnaryExpression')


class UnaryExpression(Base, metaclass=LHS):
    key = 152
    relativeOrder = 3
    rhs = ('--', 'UnaryExpression')


class UnaryExpression(Base, metaclass=LHS):
    key = 153
    relativeOrder = 4
    rhs = ('UnaryOp', 'CastExpression')


class UnaryExpression(Base, metaclass=LHS):
    key = 154
    relativeOrder = 5
    rhs = ('sizeof', 'UnaryExpression')


class UnaryExpression(Base, metaclass=LHS):
    key = 155
    relativeOrder = 6
    rhs = ('sizeof', '(', 'Typename', ')')


class UnaryOp(Base, metaclass=LHS):
    key = 156
    relativeOrder = 1
    rhs = ('&',)


class UnaryOp(Base, metaclass=LHS):
    key = 157
    relativeOrder = 2
    rhs = ('*',)


class UnaryOp(Base, metaclass=LHS):
    key = 158
    relativeOrder = 3
    rhs = ('+',)


class UnaryOp(Base, metaclass=LHS):
    key = 159
    relativeOrder = 4
    rhs = ('-',)


class UnaryOp(Base, metaclass=LHS):
    key = 160
    relativeOrder = 5
    rhs = ('~',)


class UnaryOp(Base, metaclass=LHS):
    key = 161
    relativeOrder = 6
    rhs = ('!',)


class CastExpression(Base, metaclass=LHS):
    key = 162
    relativeOrder = 1
    rhs = ('UnaryExpression',)


class CastExpression(Base, metaclass=LHS):
    key = 163
    relativeOrder = 2
    rhs = ('(', 'Typename', ')', 'CastExpression')


class MultiplicativeExpression(Base, metaclass=LHS):
    key = 164
    relativeOrder = 1
    rhs = ('CastExpression',)


class MultiplicativeExpression(Base, metaclass=LHS):
    key = 165
    relativeOrder = 2
    rhs = ('MultiplicativeExpression', '*', 'CastExpression')


class MultiplicativeExpression(Base, metaclass=LHS):
    key = 166
    relativeOrder = 3
    rhs = ('MultiplicativeExpression', '/', 'CastExpression')


class MultiplicativeExpression(Base, metaclass=LHS):
    key = 167
    relativeOrder = 4
    rhs = ('MultiplicativeExpression', '%', 'CastExpression')


class AdditiveExpression(Base, metaclass=LHS):
    key = 168
    relativeOrder = 1
    rhs = ('MultiplicativeExpression',)


class AdditiveExpression(Base, metaclass=LHS):
    key = 169
    relativeOrder = 2
    rhs = ('AdditiveExpression', '+', 'MultiplicativeExpression')


class AdditiveExpression(Base, metaclass=LHS):
    key = 170
    relativeOrder = 3
    rhs = ('AdditiveExpression', '-', 'MultiplicativeExpression')


class ShiftExpression(Base, metaclass=LHS):
    key = 171
    relativeOrder = 1
    rhs = ('AdditiveExpression',)


class ShiftExpression(Base, metaclass=LHS):
    key = 172
    relativeOrder = 2
    rhs = ('ShiftExpression', '<<', 'AdditiveExpression')


class ShiftExpression(Base, metaclass=LHS):
    key = 173
    relativeOrder = 3
    rhs = ('ShiftExpression', '>>', 'AdditiveExpression')


class RelationalExpression(Base, metaclass=LHS):
    key = 174
    relativeOrder = 1
    rhs = ('ShiftExpression',)


class RelationalExpression(Base, metaclass=LHS):
    key = 175
    relativeOrder = 2
    rhs = ('RelationalExpression', '<', 'ShiftExpression')


class RelationalExpression(Base, metaclass=LHS):
    key = 176
    relativeOrder = 3
    rhs = ('RelationalExpression', '>', 'ShiftExpression')


class RelationalExpression(Base, metaclass=LHS):
    key = 177
    relativeOrder = 4
    rhs = ('RelationalExpression', '<=', 'ShiftExpression')


class RelationalExpression(Base, metaclass=LHS):
    key = 178
    relativeOrder = 5
    rhs = ('RelationalExpression', '>=', 'ShiftExpression')


class EqualityExpression(Base, metaclass=LHS):
    key = 179
    relativeOrder = 1
    rhs = ('RelationalExpression',)


class EqualityExpression(Base, metaclass=LHS):
    key = 180
    relativeOrder = 2
    rhs = ('EqualityExpression', '==', 'RelationalExpression')


class EqualityExpression(Base, metaclass=LHS):
    key = 181
    relativeOrder = 3
    rhs = ('EqualityExpression', '!=', 'RelationalExpression')


class ANDExpression(Base, metaclass=LHS):
    key = 182
    relativeOrder = 1
    rhs = ('EqualityExpression',)


class ANDExpression(Base, metaclass=LHS):
    key = 183
    relativeOrder = 2
    rhs = ('ANDExpression', '&', 'EqualityExpression')


class ExclusiveORExpression(Base, metaclass=LHS):
    key = 184
    relativeOrder = 1
    rhs = ('ANDExpression',)


class ExclusiveORExpression(Base, metaclass=LHS):
    key = 185
    relativeOrder = 2
    rhs = ('ExclusiveORExpression', '^', 'ANDExpression')


class InclusiveORExpression(Base, metaclass=LHS):
    key = 186
    relativeOrder = 1
    rhs = ('ExclusiveORExpression',)


class InclusiveORExpression(Base, metaclass=LHS):
    key = 187
    relativeOrder = 2
    rhs = ('InclusiveORExpression', '|', 'ExclusiveORExpression')


class LogicalANDExpression(Base, metaclass=LHS):
    key = 188
    relativeOrder = 1
    rhs = ('InclusiveORExpression',)


class LogicalANDExpression(Base, metaclass=LHS):
    key = 189
    relativeOrder = 2
    rhs = ('LogicalANDExpression', '&&', 'InclusiveORExpression')


class LogicalORExpression(Base, metaclass=LHS):
    key = 190
    relativeOrder = 1
    rhs = ('LogicalANDExpression',)


class LogicalORExpression(Base, metaclass=LHS):
    key = 191
    relativeOrder = 2
    rhs = ('LogicalORExpression', '||', 'LogicalANDExpression')


class ConditionalExpression(Base, metaclass=LHS):
    key = 192
    relativeOrder = 1
    rhs = ('LogicalORExpression',)


class ConditionalExpression(Base, metaclass=LHS):
    key = 193
    relativeOrder = 2
    rhs = ('LogicalORExpression', '?', 'Expression', ':', 'ConditionalExpression')


class AssignmentExpression(Base, metaclass=LHS):
    key = 194
    relativeOrder = 1
    rhs = ('ConditionalExpression',)


class AssignmentExpression(Base, metaclass=LHS):
    key = 195
    relativeOrder = 2
    rhs = ('UnaryExpression', 'AssignmentOp', 'AssignmentExpression')


class AssignmentOp(Base, metaclass=LHS):
    key = 196
    relativeOrder = 1
    rhs = ('=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 197
    relativeOrder = 2
    rhs = ('*=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 198
    relativeOrder = 3
    rhs = ('/=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 199
    relativeOrder = 4
    rhs = ('%=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 200
    relativeOrder = 5
    rhs = ('+=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 201
    relativeOrder = 6
    rhs = ('-=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 202
    relativeOrder = 7
    rhs = ('<<=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 203
    relativeOrder = 8
    rhs = ('>>=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 204
    relativeOrder = 9
    rhs = ('&=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 205
    relativeOrder = 10
    rhs = ('^=',)


class AssignmentOp(Base, metaclass=LHS):
    key = 206
    relativeOrder = 11
    rhs = ('|=',)


class Expression(Base, metaclass=LHS):
    key = 207
    relativeOrder = 1
    rhs = ('AssignmentExpression',)


class Expression(Base, metaclass=LHS):
    key = 208
    relativeOrder = 2
    rhs = ('Expression', ',', 'AssignmentExpression')


class ConstantExpression(Base, metaclass=LHS):
    key = 209
    relativeOrder = 1
    rhs = ('ConditionalExpression',)


class Statement(Base, metaclass=LHS):
    key = 210
    relativeOrder = 1
    rhs = ('LabeledStatement',)


class Statement(Base, metaclass=LHS):
    key = 211
    relativeOrder = 2
    rhs = ('CompoundStatement',)


class Statement(Base, metaclass=LHS):
    key = 212
    relativeOrder = 3
    rhs = ('ExpressionStatement',)


class Statement(Base, metaclass=LHS):
    key = 213
    relativeOrder = 4
    rhs = ('SelectionStatement',)


class Statement(Base, metaclass=LHS):
    key = 214
    relativeOrder = 5
    rhs = ('IterationStatement',)


class Statement(Base, metaclass=LHS):
    key = 215
    relativeOrder = 6
    rhs = ('JumpStatement',)


class LabeledStatement(Base, metaclass=LHS):
    key = 216
    relativeOrder = 1
    rhs = ('identifier', ':', 'Statement')


class LabeledStatement(Base, metaclass=LHS):
    key = 217
    relativeOrder = 2
    rhs = ('case', 'constantExpression', ':', 'Statement')


class LabeledStatement(Base, metaclass=LHS):
    key = 218
    relativeOrder = 3
    rhs = ('default', ':', 'Statement')


class CompoundStatement(Base, metaclass=LHS):
    key = 219
    relativeOrder = 1
    rhs = ('{', 'BlockItemList', '}')


class CompoundStatement(Base, metaclass=LHS):
    key = 220
    relativeOrder = 2
    rhs = ('{', '}')


class BlockItemList(Base, metaclass=LHS):
    key = 221
    relativeOrder = 1
    rhs = ('BlockItem',)


class BlockItemList(Base, metaclass=LHS):
    key = 222
    relativeOrder = 2
    rhs = ('BlockItem', 'BlockItemList')


class BlockItem(Base, metaclass=LHS):
    key = 223
    relativeOrder = 1
    rhs = ('Declaration',)


class BlockItem(Base, metaclass=LHS):
    key = 224
    relativeOrder = 2
    rhs = ('Statement',)


class ExpressionStatement(Base, metaclass=LHS):
    key = 225
    relativeOrder = 1
    rhs = ('Expression', ';')


class ExpressionStatement(Base, metaclass=LHS):
    key = 226
    relativeOrder = 2
    rhs = (';',)


class SelectionStatement(Base, metaclass=LHS):
    key = 227
    relativeOrder = 1
    rhs = ('if', '(', 'Expression', ')', 'Statement')


class SelectionStatement(Base, metaclass=LHS):
    key = 228
    relativeOrder = 2
    rhs = ('if', '(', 'Expression', ')', 'Statement', 'else', 'Statement')


class SelectionStatement(Base, metaclass=LHS):
    key = 229
    relativeOrder = 3
    rhs = ('switch', '(', 'Expression', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 230
    relativeOrder = 1
    rhs = ('while', '(', 'Expression', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 231
    relativeOrder = 2
    rhs = ('do', 'Statement', 'while', '(', 'Expression', ')', ';')


class IterationStatement(Base, metaclass=LHS):
    key = 232
    relativeOrder = 3
    rhs = ('for', '(', 'Expression', ';', 'Expression', ';', 'Expression', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 233
    relativeOrder = 4
    rhs = ('for', '(', 'Expression', ';', 'Expression', ';', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 234
    relativeOrder = 5
    rhs = ('for', '(', 'Expression', ';', ';', 'Expression', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 235
    relativeOrder = 6
    rhs = ('for', '(', ';', 'Expression', ';', 'Expression', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 236
    relativeOrder = 7
    rhs = ('for', '(', 'Expression', ';', ';', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 237
    relativeOrder = 8
    rhs = ('for', '(', ';', 'Expression', ';', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 238
    relativeOrder = 9
    rhs = ('for', '(', ';', ';', 'Expression', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 239
    relativeOrder = 10
    rhs = ('for', '(', ';', ';', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 240
    relativeOrder = 11
    rhs = ('for', '(', 'Declaration', 'Expression', ';', 'Expression', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 241
    relativeOrder = 12
    rhs = ('for', '(', 'Declaration', 'Expression', ';', ')', 'Statement')


class IterationStatement(Base, metaclass=LHS):
    key = 242
    relativeOrder = 13
    rhs = ('for', '(', 'Declaration', ';', ')', 'Statement')


class JumpStatement(Base, metaclass=LHS):
    key = 243
    relativeOrder = 1
    rhs = ('goto', 'identifier', ';')


class JumpStatement(Base, metaclass=LHS):
    key = 244
    relativeOrder = 2
    rhs = ('continue', ';')


class JumpStatement(Base, metaclass=LHS):
    key = 245
    relativeOrder = 3
    rhs = ('break', ';')


class JumpStatement(Base, metaclass=LHS):
    key = 246
    relativeOrder = 4
    rhs = ('return', 'Expression', ';')


class JumpStatement(Base, metaclass=LHS):
    key = 247
    relativeOrder = 5
    rhs = ('return', ';')


class FunctionDefinition(Base, metaclass=LHS):
    key = 248
    relativeOrder = 1
    rhs = ('DeclarationSpecifiers', 'Declarator', 'CompoundStatement')


class DeclarationList(Base, metaclass=LHS):
    key = 249
    relativeOrder = 1
    rhs = ('Declaration',)


class DeclarationList(Base, metaclass=LHS):
    key = 250
    relativeOrder = 2
    rhs = ('Declaration', 'DeclarationList')


class TranslationUnit(Base, metaclass=LHS):
    key = 251
    relativeOrder = 1
    rhs = ('ExternalDeclaration',)


class TranslationUnit(Base, metaclass=LHS):
    key = 252
    relativeOrder = 2
    rhs = ('ExternalDeclaration', 'TranslationUnit')


class ExternalDeclaration(Base, metaclass=LHS):
    key = 253
    relativeOrder = 1
    rhs = ('FunctionDefinition',)


class ExternalDeclaration(Base, metaclass=LHS):
    key = 254
    relativeOrder = 2
    rhs = ('Declaration',)
