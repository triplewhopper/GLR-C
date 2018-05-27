from typing import *

import normalize
from AST import nodes as ast
from AST.playground import *


class Declaration(Base):
    def __init__(self, relativeOrder, declarationSpecifiers, initDeclaratorList=None, semicolon: str = ';'):
        assert isinstance(declarationSpecifiers, DeclarationSpecifiers)
        assert 1 <= relativeOrder <= 2
        self.declarationSpecifiers: DeclarationSpecifiers = declarationSpecifiers
        if relativeOrder == 1:
            assert isinstance(initDeclaratorList, InitDeclaratorList)

            self.initDeclaratorList: List[InitDeclarator] = initDeclaratorList.initDeclaratorList
        else:
            self.initDeclaratorList: List[InitDeclarator] = []

    def __str__(self):
        if self.initDeclaratorList is not None:
            return span(self.__class__.__name__) + \
                   ul(self.declarationSpecifiers, self.initDeclaratorList)

        return span(self.__class__.__name__) + ul(self.declarationSpecifiers)

    def visit(self, env: Scope):
        category, type0, nodes = self.declarationSpecifiers.visit(env)
        for declarator in self.initDeclaratorList:
            name, type1 = declarator.visit(env, type0)
            # if isinstance(type1, c_type.CompleteMixin) and not type1.isComplete:
            #     raise SystemError(f'类型{type0}不完整。')

            if category == 'var':
                # env.insertVar(name, type1)
                res.append(ast.VarDecl(name, type1))
            elif category == 'typedef':
            # env.insertType(name, type1)
            else:
                raise NotImplementedError()
            res.append(ast.Decl().linkWith(env))
        return res


class DeclarationSpecifiers(Base):
    def __init__(self, relativeOrder, specifierOrQualifier, declarationSpecifiers=None):
        assert declarationSpecifiers is None or isinstance(declarationSpecifiers, DeclarationSpecifiers)
        key: str = {1: 'storageClassSpecifierList',
                    2: 'storageClassSpecifierList',
                    3: 'typeSpecifierList',
                    4: 'typeSpecifierList',
                    5: 'typeQualifierList',
                    6: 'typeQualifierList',
                    7: 'functionSpecifierList'}[relativeOrder]
        self.storageClassSpecifierList: List[StorageClassSpecifier] = []
        self.typeSpecifierList: List[TypeSpecifier] = []
        self.typeQualifierList: List[TypeQualifier] = []
        self.functionSpecifierList: List[FunctionSpecifier] = []
        self.__dict__[key].append(specifierOrQualifier)

        if declarationSpecifiers is not None:
            self.storageClassSpecifierList.extend(declarationSpecifiers.storageClassSpecifierList)
            self.typeSpecifierList.extend(declarationSpecifiers.typeSpecifierList)
            self.typeQualifierList.extend(declarationSpecifiers.typeQualifierList)
            self.functionSpecifierList.extend(declarationSpecifiers.functionSpecifierList)

    def visit(self, env: Scope):
        storageClassSpecifiers = list(frozenset(x.visit() for x in self.storageClassSpecifierList))
        assert len(storageClassSpecifiers) <= 1
        if not storageClassSpecifiers:
            category = 'var'
        else:
            category = storageClassSpecifiers[0]
        qualifiers = [x.visit() for x in self.typeQualifierList]
        nodes: List[ast.ASTNode] = []
        specifiers: List[Union[c_type.CType, str]] = []

        for x in self.typeSpecifierList:
            t = x.visit(env)
            if isinstance(t, str):
                specifiers.append(t)
            else:
                assert isinstance(t[0], c_type.CType)
                assert isinstance(t[1], ast.ASTNode)
                nodes.append(t[1])
                specifiers.append(t[0])

        type0 = normalize.normalize(specifiers, env) \
            .addQualifier(qualifiers)
        return category, type0, nodes

    def __str__(self):
        return span(self.__class__.__name__) + \
               ul(*[x if x else 'None' for x in (
                   self.storageClassSpecifierList,
                   self.typeQualifierList,
                   self.typeSpecifierList,
                   self.functionSpecifierList)])

    __repr__ = __str__


class InitDeclaratorList(Base):
    # key = 12
    # relativeOrder = 2
    # rhs = ('InitDeclarator', ',', 'InitDeclaratorList')
    #
    def __init__(self, relativeOrder, initDeclarator, placeHolder=',', initDeclaratorList=None):
        assert 1 <= relativeOrder <= 2
        assert isinstance(initDeclarator, InitDeclarator)
        assert placeHolder == ','
        assert initDeclaratorList is None or isinstance(initDeclaratorList, InitDeclaratorList)
        if relativeOrder == 1:
            assert initDeclaratorList is None
            self.initDeclaratorList: List[InitDeclarator] = [initDeclarator]
        else:
            assert initDeclaratorList is not None
            self.initDeclaratorList: List[InitDeclarator] = [initDeclarator] + initDeclaratorList.initDeclaratorList

    def __str__(self):
        return span(self.__class__.__name__) + \
               ul(*self.initDeclaratorList)

    __repr__ = __str__


class InitDeclarator(Base):
    def __init__(self, relativeOrder, declarator, placeHolder: str = '=', initializer=None):
        assert 1 <= relativeOrder <= 2
        assert placeHolder == '='
        self.declarator: Declarator = declarator
        self.initializer: Optional[Initializer] = initializer

    def visit(self, env, type0) -> Tuple[str, Any]:
        name, type1 = self.declarator.visit(env, type0)
        if self.initializer:
            self.initializer.visit(env)

    def __str__(self):
        if self.initializer is None:
            return span(self.__class__.__name__) + ul(self.declarator)
        return span(self.__class__.__name__) + ul(self.declarator, self.initializer)


#
class StorageClassSpecifier(Base, metaclass=LHS):
    # key = 15
    # relativeOrder = 1
    # rhs = ('typedef',)
    def __init__(self, relativeOrder, s):
        assert 1 <= relativeOrder <= 5
        assert isinstance(s, str)
        self.storageClassSpecifier: str = s

    def visit(self):
        return self.storageClassSpecifier
    # def run(self, env, *args, **kwargs):
    #     assert isinstance(self.rhs[0], str)
    #     return self.rhs[0]


#
#
# class StorageClassSpecifier(Base, metaclass=LHS):
#     key = 16
#     relativeOrder = 2
#     rhs = ('extern',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
# class StorageClassSpecifier(Base, metaclass=LHS):
#     key = 17
#     relativeOrder = 3
#     rhs = ('static',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
# class StorageClassSpecifier(Base, metaclass=LHS):
#     key = 18
#     relativeOrder = 4
#     rhs = ('auto',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
# class StorageClassSpecifier(Base, metaclass=LHS):
#     key = 19
#     relativeOrder = 5
#     rhs = ('register',)
#
#     def run(self, env, *args, **kwargs):
#         assert isinstance(self.rhs[0], str)
#         return self.rhs[0]
#
#
class TypeSpecifier(Base, metaclass=LHS):
    def __init__(self, relativeOrder, s):
        assert 1 <= relativeOrder <= 14
        assert isinstance(s, (str, StructOrUnionSpecifier, TypedefName))
        self.typeSpecifier: Union[str, StructOrUnionSpecifier, TypedefName] = s

    def __str__(self):
        return str(self.typeSpecifier)

    def visit(self, env) -> Union[str, Tuple[c_type.CType, ast.ASTNode]]:
        if isinstance(self.typeSpecifier, str):
            return self.typeSpecifier
        else:
            return self.typeSpecifier.visit(env)


#
# class TypeSpecifier(Base, metaclass=LHS):
#     key = 31
#     relativeOrder = 12
#     rhs = ('StructOrUnionSpecifier',)
#
#
# class TypeSpecifier(Base, metaclass=LHS):
#     key = 32
#     relativeOrder = 13
#     rhs = ('EnumSpecifier',)
#
#


#
class TypeQualifier(Base, metaclass=LHS):
    # key = 34
    # relativeOrder = 1
    # rhs = ('const',)
    #
    def __init__(self, relativeOrder, typeQualifier):
        assert isinstance(typeQualifier, str)
        self.typeQualifier = typeQualifier

    def __str__(self):
        return str(self.typeQualifier)

    def visit(self) -> str:
        return self.typeQualifier

    __repr__ = __str__
    # def run(self, env, *args, **kwargs):
    #     assert isinstance(self.rhs[0], str)
    #     return self.rhs[0]


class StructOrUnionSpecifier(Base, metaclass=LHS):
    # key = 37
    # relativeOrder = 1
    # rhs = ('StructOrUnion', 'identifier', '{', 'StructDeclarationList', '}')
    #
    def __init__(self, relativieOrder: int, *args):
        assert 1 <= relativieOrder <= 3
        self.structOrUnion: str = args[0].structOrUnion
        self.tag: str = ''
        self.structDeclarationList: Optional[List[StructDeclaration]] = None
        if relativieOrder == 1:
            assert isinstance(args[1], str)
            self.tag = args[1]
            s: StructDeclarationList = args[3]
        else:
            s: StructDeclarationList = args[2]
        self.structDeclarationList = s.structDeclarationList
        assert self.structOrUnion in ('union', 'struct')

    def visit(self, env: Scope) -> Tuple[c_type.Struct, ast.ASTNode]:
        type0 = env.getTypeByTag(self.tag)
        node = ast.Nop()
        if type0 is None:
            if self.structOrUnion == 'struct':
                type0 = c_type.Struct(self.tag)
            else:
                raise NotImplementedError()
        if self.structDeclarationList is not None:
            if type0.isComplete:
                raise SystemError(f'{type0}重定义！')

            block = BlockScope(env).insertVar(self.tag, type0)
            declarations = []
            for s in self.structDeclarationList:
                declarations.extend(s.visit(block))

            type0.complete(*block.variables.values())

            if type0.tag in env:
                if env.getTypeByTag(type0.tag):
                    if not type0.isComplete:
                        pass
                    else:
                        env.insertType(type0.tag, type0)  # 进去就会抛异常
                else:
                    env.insertType(type0.tag, type0)  # 进去也会抛异常
            else:
                env.insertType(type0.tag, type0)  # 正常插入
            node = ast.RecordDecl(declarations).linkWith(block)
        return type0, node

    def __str__(self):
        return span(self.__class__.__name__) + \
               ul(self.structOrUnion, self.tag, self.structDeclarationList)


class StructOrUnion(Base, metaclass=LHS):
    # key = 41
    # relativeOrder = 2
    # rhs = ('union',)
    def __init__(self, relativeOrder, s: str):
        self.structOrUnion: str = s


class StructDeclarationList(Base, metaclass=LHS):
    # key = 42
    # relativeOrder = 1
    # rhs = ('StructDeclaration',)

    def __init__(self, relativeOrder, structDeclaration, structDeclarationList=None):
        assert 1 <= relativeOrder <= 2
        assert isinstance(structDeclaration, StructDeclaration)
        assert structDeclarationList is None or isinstance(structDeclarationList, StructDeclarationList)
        self.structDeclarationList: List[StructDeclaration] = [structDeclaration]
        if structDeclarationList:
            self.structDeclarationList.extend(structDeclarationList.structDeclarationList)

    def visit(self, env):
        raise NotImplementedError()

    def __str__(self):
        return span(self.__class__.__name__) + ul(*self.structDeclarationList)


class StructDeclaration(Base, metaclass=LHS):
    # key = 44
    # relativeOrder = 1
    # rhs = ('SpecifierQualifierList', 'StructDeclaratorList', ';')
    def __init__(self, relativeOrder, specifierQualifierList, structDeclaratorList, placeHolder):
        assert placeHolder == ';'
        assert relativeOrder == 1
        assert isinstance(specifierQualifierList, SpecifierQualifierList)
        assert isinstance(structDeclaratorList, StructDeclaratorList)
        self.specifierList: List[TypeSpecifier] = specifierQualifierList.specifierList
        self.qualifierList: List[TypeQualifier] = specifierQualifierList.qualifierList
        self.structDeclaratorList: List[StructDeclarator] = structDeclaratorList.structDeclaratorList

    def __str__(self):
        return span(self.__class__.__name__) + ul(self.qualifierList, self.specifierList, self.structDeclaratorList)

    def visit(self, env: Scope) -> List[ast.Decl]:
        specifiers = [x.visit(env) for x in self.specifierList]
        qualifiers = [x.visit() for x in self.qualifierList]
        type0 = normalize.normalize(specifiers) \
            .addQualifier(qualifiers)
        res = []
        for declarator in self.structDeclaratorList:
            name, type1 = declarator.visit(env, type0)
            if isinstance(type1, c_type.CompleteMixin) and not type1.isComplete:
                raise SystemError(f'类型{type0}不完整。')
            assert isinstance(env, BlockScope)
            env.insertVar(name, type1)
            res.append(ast.Decl().linkWith(env))
        return res


class SpecifierQualifierList(Base, metaclass=LHS):
    # key = 45
    # relativeOrder = 1
    # rhs = ('TypeSpecifier', 'SpecifierQualifierList')

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 4
        self.specifierList: List[TypeSpecifier]
        self.qualifierList: List[TypeQualifier]
        assert isinstance(args[0], (TypeSpecifier, TypeQualifier))
        if len(args) > 1:
            assert isinstance(args[1], SpecifierQualifierList)
        if relativeOrder == 1:
            self.specifierList = [args[0]] + args[1].specifierList
            self.qualifierList = args[1].qualfierList
        elif relativeOrder == 2:
            self.specifierList = [args[0]]
            self.qualifierList = []
        elif relativeOrder == 3:
            self.specifierList = args[1].specifierList
            self.qualifierList = [args[0]] + args[1].qualifierList
        elif relativeOrder == 4:
            self.specifierList = []
            self.qualifierList = [args[0]]


class StructDeclaratorList(Base, metaclass=LHS):
    # key = 49
    # relativeOrder = 1
    # rhs = ('StructDeclarator',)
    #
    def __init__(self, relativeOrder, structDeclarator, placeHolder=',', structDeclaratorList=None):
        assert 1 <= relativeOrder <= 2
        assert placeHolder == ','
        assert isinstance(structDeclarator, StructDeclarator)
        assert structDeclaratorList is None or isinstance(structDeclaratorList, StructDeclaratorList)
        self.structDeclaratorList: List[StructDeclarator] = [structDeclarator]
        if structDeclaratorList:
            self.structDeclaratorList.extend(structDeclaratorList.structDeclaratorList)

    def __str__(self):
        return span(self.__class__.__name__) + ul(*self.structDeclaratorList)


class StructDeclarator(Base, metaclass=LHS):
    key = 51
    relativeOrder = 1
    rhs = ('Declarator',)

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 3
        if relativeOrder == 1:
            self.declarator: Declarator = args[0]
        else:
            raise NotImplementedError()

    def visit(self, env: Scope, type0: c_type.CType) -> Tuple[str, c_type.CType]:
        return self.declarator.visit(env, type0)


# class EnumSpecifier(Base, metaclass=LHS):
#     key = 54
#     relativeOrder = 1
#     rhs = ('enum', 'identifier', '{', 'EnumeratorList', '}')
#
#
# class EnumSpecifier(Base, metaclass=LHS):
#     key = 55
#     relativeOrder = 2
#     rhs = ('enum', '{', 'EnumeratorList', '}')
#
#
# class EnumSpecifier(Base, metaclass=LHS):
#     key = 56
#     relativeOrder = 3
#     rhs = ('enum', 'identifier', '{', 'EnumeratorList', ',', '}')
#
#
# class EnumSpecifier(Base, metaclass=LHS):
#     key = 57
#     relativeOrder = 4
#     rhs = ('enum', '{', 'EnumeratorList', ',', '}')
#
#
# class EnumSpecifier(Base, metaclass=LHS):
#     key = 58
#     relativeOrder = 5
#     rhs = ('enum', 'identifier')
#
#
# class EnumeratorList(Base, metaclass=LHS):
#     key = 59
#     relativeOrder = 1
#     rhs = ('Enumerator',)
#
#
# class EnumeratorList(Base, metaclass=LHS):
#     key = 60
#     relativeOrder = 2
#     rhs = ('EnumeratorList', ',', 'Enumerator')
#
#
# class Enumerator(Base, metaclass=LHS):
#     key = 61
#     relativeOrder = 1
#     rhs = ('EnumerationConstant',)
#
#
# class Enumerator(Base, metaclass=LHS):
#     key = 62
#     relativeOrder = 2
#     rhs = ('EnumerationConstant', '=', 'ConstantExpression')


class Declarator(Base, metaclass=LHS):
    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 2
        self.pointer: Optional[Pointer]
        if relativeOrder == 1:
            self.pointer = args[0]
            self.directDeclarator: DirectDeclarator = args[1]
        else:
            self.pointer = None
            self.directDeclarator: DirectDeclarator = args[0]

    def visit(self, env: Scope, type0: c_type.CType) -> Tuple[str, c_type.CType]:
        self.pointer: Optional[Pointer]
        if self.pointer is None:
            return self.directDeclarator.visit(env, type0)
        type0, qualifiers = self.pointer.visit(type0)
        type0.addQualifier(qualifiers)
        return self.directDeclarator.visit(env, type0)

    def __str__(self):
        if self.pointer is not None:
            return span(self.__class__.__name__) + ul(self.pointer, self.directDeclarator)
        return span(self.__class__.__name__) + ul(self.directDeclarator)


class DirectDeclarator(Base, metaclass=LHS):
    # key = 66
    # relativeOrder = 2
    # rhs = ('(', 'Declarator', ')')

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 14
        self.relativeOrder: int = relativeOrder
        if relativeOrder == 1:
            assert isinstance(args[0], str)
            self.identifier: str = args[0]
        elif relativeOrder == 2:
            self.declarator: Declarator = args[1]
        else:
            self.directDeclarator: DirectDeclarator = args[0]
            if relativeOrder == 3:
                self.subscript: Optional[AssignmentExpression] = None
            elif relativeOrder == 4:
                self.typeQualifierList: Optional[TypeQualifierList] = args[2]
                self.subscript: Optional[AssignmentExpression] = args[3]
            elif relativeOrder == 5:
                self.typeQualifierList = None
                self.subscript: Optional[AssignmentExpression] = args[2]
            elif relativeOrder == 6:
                raise NotImplementedError()
            elif relativeOrder == 7:
                raise NotImplementedError()
            elif relativeOrder == 8:
                raise NotImplementedError()
            elif relativeOrder == 9:
                raise NotImplementedError()
            elif relativeOrder == 10:
                raise NotImplementedError()
            elif relativeOrder == 11:
                raise NotImplementedError()
            elif relativeOrder == 12:
                self.parameterTypeList: Optional[ParameterTypeList] = args[2]
            elif relativeOrder == 13:
                raise NotImplementedError()
            elif relativeOrder == 14:
                self.parameterTypeList: Optional[ParameterTypeList] = None
        pass

    def visit(self, env, type0: c_type.CType) -> Tuple[str, c_type.CType]:
        if self.relativeOrder == 1:
            return self.identifier, type0
        elif self.relativeOrder == 2:
            return self.declarator.visit(env, type0)
        elif self.relativeOrder == 3:
            return self.directDeclarator.visit(env, c_type.Array(type0))
        elif self.relativeOrder in (4, 5, 7, 8, 9):
            return self.directDeclarator.visit(env, c_type.Array(type0, self.subscript.visit(env)))
        elif self.relativeOrder == 6:
            return self.directDeclarator.visit(env, c_type.Array(type0))
        elif self.relativeOrder in (10, 11):
            if env.scope != env.Scope.FUNCTION_PROTOTYPE:
                raise SystemError()
            return self.directDeclarator.visit(env, c_type.Array(type0))
        elif self.relativeOrder == 12:
            nodes, types = self.parameterTypeList.visit(FunctionPrototypeScope(env))
            type0 = c_type.ParenType(type0, types)
            return self.directDeclarator.visit(env, type0)
        elif self.relativeOrder == 13:
            raise SystemError()
        elif self.relativeOrder == 14:
            type0 = c_type.ParenType(type0, ())
            return self.directDeclarator.visit(env, type0)

    def __str__(self):
        res = span(self.__class__.__name__) + str(self.relativeOrder)
        tmp = []
        if hasattr(self, 'identifier'):
            tmp.append(self.identifier)
        if hasattr(self, 'directDeclarator'):
            tmp.append(self.directDeclarator)
            if hasattr(self, 'typeQualifierList'):
                tmp.append(self.typeQualifierList)
            if hasattr(self, 'subscript'):
                tmp.append(self.subscript)
            if hasattr(self, 'parameterTypeList'):
                tmp.append(self.parameterTypeList)
            assert tmp
        return res + ul(*tmp)


class Pointer(Base, metaclass=LHS):

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 4
        self.typeQualifierList: List[TypeQualifier] = []
        self.pointer: Optional[Pointer] = None
        if relativeOrder == 1:
            pass
        elif relativeOrder == 2:
            t = args[1]
            assert isinstance(t, TypeQualifierList)
            self.typeQualifierList = t.typeQualifierList
        elif relativeOrder == 3:
            t = args[1]
            p = args[2]
            assert isinstance(t, TypeQualifierList)
            assert isinstance(p, Pointer)
            self.typeQualifierList = t.typeQualifierList
            self.pointer = p
        elif relativeOrder == 4:
            assert isinstance(args[1], Pointer)
            self.pointer = args[1]

    def visit(self, type0: c_type.CType) -> Tuple[c_type.CType, List[TypeQualifier]]:
        self.pointer: Optional[Pointer]
        type0 = c_type.Pointer(type0)
        if self.pointer is None:
            return type0, self.typeQualifierList
        type0.addQualifier(self.typeQualifierList)
        return self.pointer.visit(type0)

    def __str__(self):
        if self.typeQualifierList is not None:
            return span(self.__class__.__name__) + ul(self.pointer, self.typeQualifierList)

        return span(self.__class__.__name__) + ul(self.pointer)


class TypeQualifierList(Base, metaclass=LHS):

    def __init__(self, relativeOrder, typeQualifier, typeQualifierList=None):
        assert isinstance(typeQualifier, TypeQualifier)
        if typeQualifierList is None:
            self.typeQualifierList: List[TypeQualifier] = [typeQualifier]
        else:
            assert isinstance(typeQualifierList, TypeQualifierList)
            self.typeQualifierList: List[TypeQualifier] = [typeQualifier] + typeQualifierList.typeQualifierList


class ParameterTypeList(Base, metaclass=LHS):

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 2:
            raise NotImplementedError()
        p = args[0]
        assert isinstance(p, ParameterList)
        self.parameterTypeList: List[ParameterDeclaration] = p.parameterList

    def visit(self, env):
        types: List[c_type.CType] = []
        nodes: List[ast.Decl] = []
        for p in self.parameterTypeList:
            node, t = p.visit(env)
            if not isinstance(node, ast.Nop):
                nodes.append(node)
            types.append(t)
        return nodes, types


class ParameterList(Base, metaclass=LHS):
    # key = 87
    # relativeOrder = 1
    # rhs = ('ParameterDeclaration',)
    #
    def __init__(self, relativeOrder, parameterDeclaration, placeHolder=',', parameterList=None):
        assert placeHolder == ','
        assert parameterList is None or isinstance(parameterList, ParameterList)
        assert 1 <= relativeOrder <= 2
        assert isinstance(parameterDeclaration, ParameterDeclaration)
        self.parameterList: List[ParameterDeclaration] = [parameterDeclaration]
        if parameterList is not None:
            self.parameterList.extend(parameterList.parameterList)


class ParameterDeclaration(Base, metaclass=LHS):
    # key = 90
    # relativeOrder = 2
    # rhs = ('DeclarationSpecifiers', 'AbstractDeclarator')
    #
    def __init__(self, relativeOrder, declarationSpecifiers, declarator=None):
        assert 1 <= relativeOrder <= 3
        assert isinstance(declarationSpecifiers, DeclarationSpecifiers)
        self.declarationSpecifiers = declarationSpecifiers
        self.declarator: Optional[Declarator] = None
        self.abstractDeclarator: Optional[Declarator] = None
        if declarator is not None:
            if isinstance(declarator, Declarator):
                self.declarator = declarator
            elif isinstance(declarator, AbstractDeclarator):
                self.abstractDeclarator = declarator
            else:
                assert 0

    def visit(self, env) -> Tuple[Union[ast.Nop, ast.Decl], c_type.CType]:
        category, type0, nodes = self.declarationSpecifiers.visit(env)
        if category == 'typedef':
            raise SystemError('typedef are not allow in the scope of function prototype!')
        assert category == 'var'
        if self.declarator:
            identifier, type1 = self.declarator.visit(env, type0)
            env.insertVar(identifier, type1)
            return ast.Decl().linkWith(env), type1
        else:
            type0 = self.abstractDeclarator.visit(env, type0)
            return ast.Nop(), type0

    def __str__(self):
        if (self.declarator or self.abstractDeclarator) is not None:
            return span(self.__class__.__name__) + ul(self.declarationSpecifiers,
                                                      self.declarator or self.abstractDeclarator)
        return span(self.__class__.__name__) + ul(self.declarationSpecifiers)

    __repr__ = __str__


# class IdentifierList(Base, metaclass=LHS):
#     key = 93
#     relativeOrder = 2
#     rhs = ('identifier', ',', 'IdentifierList')
#

class Typename(Base, metaclass=LHS):
    # key = 94
    # relativeOrder = 1
    # rhs = ('SpecifierQualifierList', 'AbstractDeclarator')

    def __init__(self, relativeOrder, specifierQualifierList, abstractDeclarator=None):
        assert isinstance(specifierQualifierList, SpecifierQualifierList)
        assert 1 <= relativeOrder <= 2
        self.specifierList: List[TypeSpecifier] = specifierQualifierList.specifierList
        self.qualifierList: List[TypeQualifier] = specifierQualifierList.qualifierList
        self.abstractDeclarator: Optional[AbstractDeclarator] = None
        if abstractDeclarator is not None:
            assert isinstance(abstractDeclarator, AbstractDeclarator)
            self.abstractDeclarator = abstractDeclarator


class AbstractDeclarator(Base, metaclass=LHS):
    # key = 96
    # relativeOrder = 1
    # rhs = ('Pointer',)
    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 3
        self.pointer: Optional[Pointer] = None
        self.directAbstractDeclarator: Optional[Pointer] = None
        if relativeOrder == 1:
            p = args[0]
            assert isinstance(p, Pointer)
            self.pointer = p
        elif relativeOrder == 2:
            p = args[0]
            d = args[1]
            assert isinstance(p, Pointer)
            assert isinstance(d, DirectAbstractDeclarator)
            self.pointer = p
            self.directAbstractDeclarator = d
        else:
            d = args[0]
            assert isinstance(d, DirectAbstractDeclarator)
            self.directAbstractDeclarator = d

    def visit(self, env: Scope, type0: c_type.CType) -> c_type.CType:
        if self.pointer is None:
            return self.directAbstractDeclarator.visit(env, type0)
        type0, _ = self.pointer.visit(type0)
        if self.directAbstractDeclarator is None:
            return type0
        return self.directAbstractDeclarator.visit(env, type0)


#
# class AbstractDeclarator(Base, metaclass=LHS):
#     key = 97
#     relativeOrder = 2
#     rhs = ('Pointer', 'DirectAbstractDeclarator')
#
#
# class AbstractDeclarator(Base, metaclass=LHS):
#     key = 98
#     relativeOrder = 3
#     rhs = ('DirectAbstractDeclarator',)
#

class DirectAbstractDeclarator(Base, metaclass=LHS):
    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 21
        self.abstractDeclarator: Optional[AbstractDeclarator] = None
        self.directAbstractDeclarator: Optional[DirectAbstractDeclarator] = None
        self.typeQualifierList: Optional[List[TypeQualifier]] = None
        self.subscript: Optional[AssignmentExpression] = None
        self.parameterTypeList: Optional[ParameterDeclaration] = None
        self.relativeOrder: int = relativeOrder

        def ab(x):
            tmp = args[x]
            assert isinstance(tmp, AbstractDeclarator)
            self.abstractDeclarator = tmp

        def d(x):
            tmp = args[x]
            assert isinstance(tmp, DirectAbstractDeclarator)
            self.directAbstractDeclarator = tmp

        def t(x):
            tmp = args[x]
            assert isinstance(tmp, TypeQualifierList)
            self.typeQualifierList = tmp.typeQualifierList

        def a(x):
            tmp = args[x]
            assert isinstance(tmp, AssignmentExpression)
            self.subscript = tmp

        def p(x):
            tmp = args[x]
            assert isinstance(tmp, ParameterTypeList)
            self.parameterTypeList = tmp

        if relativeOrder == 1:
            ab(1)
        elif 2 <= relativeOrder <= 11:
            d(0)
            if relativeOrder == 2:
                t(2)
                a(3)
            elif relativeOrder == 3:
                a(2)
            elif relativeOrder == 4:
                t(2)
            elif relativeOrder == 5:
                pass
            elif relativeOrder == 6:
                t(3)
                a(4)
            elif relativeOrder == 7:
                a(3)
            elif relativeOrder == 8:
                d(0)
                t(2)
                a(4)
            elif relativeOrder == 9:
                pass
            elif relativeOrder == 10:
                p(2)
            elif relativeOrder == 11:
                pass
        elif relativeOrder == 12:
            t(1)
            a(2)
        elif relativeOrder == 13:
            a(1)
        elif relativeOrder == 14:
            t(1)
        elif relativeOrder == 15:
            pass
        elif relativeOrder == 16:
            t(2)
            a(3)
        elif relativeOrder == 17:
            a(2)
        elif relativeOrder == 18:
            t(1)
            a(3)
        elif relativeOrder == 19:
            pass
        elif relativeOrder == 20:
            p(1)
        elif relativeOrder == 21:
            pass

    def visit(self, env, type0: c_type.CType):
        if self.relativeOrder == 1:
            # "(" AbstractDeclarator ")"
            return self.abstractDeclarator.visit(env, type0)
        elif self.relativeOrder in (2, 3):
            # DirectAbstractDeclarator "[" TypeQualifierList AssignmentExpression "]"
            # DirectAbstractDeclarator "[" AssignmentExpression "]"

            length = self.subscript.visit(env)
            type0 = c_type.Array(type0, length)
            raise NotImplementedError()
            # incomplete!
            return self.directAbstractDeclarator.visit(env, type0)

        elif self.relativeOrder in (4, 5):
            # DirectAbstractDeclarator "[" TypeQualifierList "]"
            # DirectAbstractDeclarator "["  "]"

            return self.directAbstractDeclarator.visit(env, c_type.Array(type0))

        elif self.relativeOrder in (6, 7, 8):
            # DirectAbstractDeclarator "[" static TypeQualifierList AssignmentExpression "]"
            # DirectAbstractDeclarator "[" static AssignmentExpression "]"
            # DirectAbstractDeclarator "[" TypeQualifierList static AssignmentExpression "]"

            length = self.subscript.visit(env)
            type0 = c_type.Array(type0, length)
            raise NotImplementedError()
            # incomplete!
            return self.directAbstractDeclarator.visit(env, type0)

        elif self.relativeOrder == 9:
            # DirectAbstractDeclarator "[" "*" "]"
            if env.scope != env.Scope.FUNCTION_PROTOTYPE:
                raise SystemError()
            return self.directAbstractDeclarator.visit(env, c_type.Array(type0))

        elif self.relativeOrder == 10:
            # DirectAbstractDeclarator "(" ParameterTypeList ")"
            type0 = c_type.ParenType(type0, self.parameterTypeList.visit(Scope(Scope.Scope.FUNCTION_PROTOTYPE, env)))
            return self.directAbstractDeclarator.visit(env, type0)

        elif self.relativeOrder == 11:
            # DirectAbstractDeclarator "("  ")"
            type0 = c_type.ParenType(type0, ())
            return self.directAbstractDeclarator.visit(env, type0)

        elif self.relativeOrder in (12, 13, 16, 17, 18):
            # "[" AssignmentExpression "]"
            raise NotImplementedError()
            length = self.subscript.visit(env)

            return c_type.Array(type0, length)

        elif self.relativeOrder in (14, 15):
            # "["  "]"
            return c_type.Array(type0)

        elif self.relativeOrder == 19:
            # "[" "*" "]"
            if env.scope != env.Scope.FUNCTION_PROTOTYPE:
                raise SystemError()
            return c_type.Array(type0)
        elif self.relativeOrder == 20:
            # "(" ParameterTypeList ")"
            type0 = c_type.ParenType(type0, self.parameterTypeList.visit(Scope(Scope.Scope.FUNCTION_PROTOTYPE, env)))
            return type0
        elif self.relativeOrder == 21:
            # "("  ")"
            return c_type.ParenType(type0, ())


class TypedefName(Base, metaclass=LHS):
    # key = 120
    # relativeOrder = 1
    # rhs = ('identifier',)
    def __init__(self, relativeOrder: int, s: str):
        assert relativeOrder == 1
        assert isinstance(s, str)
        self.typedefName: str = s

    def visit(self, env: Scope):
        # res=env[self.typedefName]
        raise NotImplementedError()


class FunctionSpecifier(Base, metaclass=LHS):
    key = 121
    relativeOrder = 1
    rhs = ('inline',)


class Initializer(Base, metaclass=LHS):
    key = 124
    relativeOrder = 3
    rhs = ('{', 'InitializerList', ',', '}')

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 3
        self.expr = None
        self.initializerList = None
        if relativeOrder == 1:
            self.expr: Expression = args[0]
        else:
            self.initializerList: InitializerList = args[1]


class InitializerList(Base, metaclass=LHS):
    # InitializerList->
    #      Designation Initializer
    #     |Initializer
    #     |InitializerList "," Designation Initializer
    #     |InitializerList ","             Initializer

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 4
        self.initializerList: List[Union[Initializer, Tuple[Designation, Initializer]]]
        if relativeOrder == 1:
            assert len(args) == 2
            self.initializerList = [(args[0], args[1])]
        elif relativeOrder == 2:
            assert len(args) == 1
            self.initializerList = [args[0]]
        elif relativeOrder == 3:
            assert len(args) == 4
            initializerList: InitializerList = args[0]
            assert isinstance(initializerList, InitializerList)
            self.initializerList = initializerList.initializerList + [(args[-2], args[-1])]
        elif relativeOrder == 4:
            assert len(args) == 3
            initializerList: InitializerList = args[0]
            assert isinstance(initializerList, InitializerList)
            self.initializerList = initializerList.initializerList + [args[-1]]


class Designation(Base, metaclass=LHS):
    #
    # Designation->
    #    DesignatorList "="

    def __init__(self, relativeOrder, *args):
        assert relativeOrder == 1
        self.designatorList = args[0]


class DesignatorList(Base, metaclass=LHS):
    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 2
        if relativeOrder == 1:
            self.designatorList: List[Designator] = [args[0]]
        else:
            designatorList = args[1]
            assert isinstance(designatorList, DesignatorList)
            self.designatorList: List[Designator] = [args[0]] + designatorList.designatorList


class Designator(Base, metaclass=LHS):
    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 2
        assert isinstance(args[0], (ConstantExpression, str))
        self.designator: Union[ConstantExpression, str] = args[0]

    def visit(self, env):
        raise NotImplementedError()


class PrimaryExpression(Base, metaclass=LHS):
    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 4
        self.target
        if relativeOrder <= 3:
            self.target = args[0]
        else:
            self.target = args[1]

    def visit(self, env):
        pass


class PostfixExpression(Base, metaclass=LHS):
    pass


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
    def __init__(self, relativeOrder, blockItem, blockItemList=None):
        assert 1 <= relativeOrder <= 2
        self.blockItemList: List[BlockItem] = [blockItem]
        if blockItemList is not None:
            assert hasattr(blockItemList, 'blockItemList')
            self.blockItemList.extend(blockItemList.blockItemList)

    def visit(self, env: Scope):
        for blockItem in self.blockItemList:
            blockItem.visit(env)

    def __str__(self):
        return span(self.__class__.__name__) + ul(*self.blockItemList)


class BlockItem(Base, metaclass=LHS):
    def __init__(self, relativeOrder, item: Union[Statement, Declaration]):
        assert 1 <= relativeOrder <= 2
        self.statement: Optional[Statement] = None
        self.declaration: Optional[Declaration] = None
        if relativeOrder == 1:
            self.declaration: Declaration = item
        else:
            self.statement: Statement = item

    def visit(self, env: Scope):
        if self.statement is None:
            self.declaration.visit(env)
        else:
            self.statement.visit(env)

    def __str__(self):
        return span(self.__class__.__name__) + ul(self.statement or self.declaration)


class ExpressionStatement(Base, metaclass=LHS):
    key = 225
    relativeOrder = 1
    rhs = ('Expression', ';')


class ExpressionStatement(Base, metaclass=LHS):
    key = 226
    relativeOrder = 2
    rhs = (';',)

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 2
        self.expression: Optional[Expression] = None
        if relativeOrder == 1:
            self.expression: Expression = args[0]

    def visit(self, env):
        raise NotImplementedError()

    def __str__(self):
        return span(self.__class__.__name__) + ul('NullExpression' if self.expression is None else self.expression)


class SelectionStatement(Base, metaclass=LHS):
    key = 228
    relativeOrder = 2
    rhs = ('if', '(', 'Expression', ')', 'Statement', 'else', 'Statement')

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 3
        self.elseStmt: Optional[Statement] = None
        self.flag = ''
        if relativeOrder <= 2:
            assert len(args) in (5, 7)
            self.flag = 'if'
            self.expression: Expression = args[2]
            self.stmt = args[4]
            if relativeOrder == 2:
                assert len(args) == 7
                self.elseStmt: Statement = args[-1]
        elif relativeOrder == 3:
            assert len(args) == 5
            self.flag = 'switch'
            self.expression: Expression = args[2]
            self.stmt = args[-1]

    def visit(self, env: Scope):
        if self.flag == 'if':
            pass
        elif self.flag == 'switch':
            pass
        else:
            assert 0


class IterationStatement(Base, metaclass=LHS):
    key = 230
    relativeOrder = 1
    rhs = ('while', '(', 'Expression', ')', 'Statement')

    def __init__(self, relativeOrder, *args):
        assert 1 <= relativeOrder <= 13
        if relativeOrder == 1:
            self.flag = 'while'
        elif relativeOrder == 2:
            self.flag = 'do'
        else:
            self.flag = 'for'

        if relativeOrder == 1:
            self.e1: Expression = args[2]
            self.stmt: Statement = args[4]
        elif relativeOrder == 2:
            self.stmt: Statement = args[1]
            self.e1: Expression = args[4]
        else:
            self.stmt = args[-1]
            args = tuple(x for x in args[:-1] if not isinstance(x, str))
            self.e1: Optional[Expression] = None
            self.e2: Optional[Expression] = None
            self.e3: Optional[Expression] = None
            if relativeOrder == 3:
                assert len(args) == 3
                self.e1, self.e2, self.e3 = args
            elif relativeOrder in (4, 5, 6):
                assert len(args) == 2
                if relativeOrder == 4:
                    self.e1, self.e2 = args
                elif relativeOrder == 5:
                    self.e1, self.e3 = args
                else:
                    self.e2, self.e3 = args
            elif relativeOrder in (7, 8, 9):
                assert len(args) == 1
                if relativeOrder == 7:
                    self.e1, = args
                elif relativeOrder == 8:
                    self.e2, = args
                else:
                    self.e3, = args
            for e in (self.e1, self.e2, self.e3):
                if e is not None:
                    assert isinstance(e, Expression)


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
    # key = 250
    # relativeOrder = 2
    # rhs = ('Declaration', 'DeclarationList')
    #
    def __init__(self, relativeOrder: int, declaration: Declaration, declarationList=None):
        assert 1 <= relativeOrder <= 2
        self.declarationList: List[Declaration] = [declaration]
        if relativeOrder == 2:
            if equal(declarationList, DeclarationList):
                self.declarationList.extend(declarationList.declarationList)

    def __str__(self):
        return span(self.__class__.__name__) + ul(*self.declarationList)


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
