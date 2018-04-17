import tokenizer
from collections import UserDict, namedtuple, OrderedDict
from typing import Dict, List, Tuple
import c_parser.c_type as c_type
import c_parser.mem

predeclared = frozenset(tokenizer.keywords) | frozenset(tokenizer.builtinTypes)


class Env:
    offsetTotal = 0
    mem = c_parser.mem.mem
    consts = []

    def __init__(self, prev, description=''):
        self.prev = prev
        self.description = description
        self.typedefs: OrderedDict[str, c_type.CType] = OrderedDict()
        self.varTypes: OrderedDict[str, c_type.CType] = OrderedDict()
        self.funcTypes: OrderedDict[str, c_type.FunctionProtoType] = OrderedDict()
        self._offset: OrderedDict[str, int] = OrderedDict()

    def __getitem__(self, item: str):
        assert isinstance(item, str)
        assert int(item in self.typedefs) + int(item in self.varTypes) + int(item in self.funcTypes) == 1
        if item in self.typedefs:
            return self.typedefs[item]
        return self.varTypes[item]

    def fork(self):
        pass

    def offset(self, item):
        assert isinstance(item, str)
        if item not in self.varTypes:
            raise KeyError(f'{item} has not been declared yet.')
        return self._offset[item]

    def __contains__(self, item: str):
        assert isinstance(item, str)
        return item in predeclared or item in self.typedefs or item in self.varTypes

    def insertType(self, typeName, type):
        assert isinstance(typeName, str)
        assert isinstance(type, c_type.CType)
        if typeName in self:
            raise KeyError(f'{typeName} has already been declared.')
        self.typedefs[typeName] = type
        return self

    def freeze(self):
        self.__dict__['insertType'] = None
        self.__dict__['insertVar'] = None
        self.__dict__['insertFunc'] = None
        self.__dict__['insertConst'] = None
        self.__dict__['modifyVar'] = None
        self.__dict__['updateType'] = None
        self.__dict__['freeze'] = None

    # def removeType(self, typeName):
    #     assert isinstance(typeName, str)
    #     if typeName not in self.typedefs:
    #         raise KeyError(f'{typeName} has not been declared yet.')
    #     del self.typedefs[typeName]
    #     return self

    def insertVar(self, varName, varType):
        assert isinstance(varName, str)
        assert isinstance(varType, c_type.CType)
        if varName in self:
            raise KeyError(f'{varName} has already been declared.')
        self.varTypes[varName] = varType
        self._offset[varName] = Env.offsetTotal
        Env.offsetTotal += varType.width
        return self

    def insertFunc(self, funcName, funcType):
        assert isinstance(funcName, str)
        assert isinstance(funcType, c_type.FunctionProtoType)
        if funcName in self:
            raise KeyError(f'{funcName} has already been declared.')
        self.funcTypes[funcName] = funcType
        return self

    def insertConst(self, value):
        self.consts.append(value)
        return self

    def modifyVar(self, key, value):
        pass

    def updateType(self, key, value):
        if key not in self.typedefs:
            raise KeyError(f'{key} has not been declared yet.')
        self.typedefs[key] = value
        return self

    def __str__(self):
        def fun(x):
            return ''.join('<li>%s => %s</li>' % (k, v) for k, v in x.items())

        return \
            f'''
            <span><br>ST '{self.description}'</span><ul>
                <li>
                    <span>types</span>
                    <ul>{fun(self.typedefs)}</ul>
                </li><li>
                    <span>vars</span>
                    <ul>{fun(self.varTypes)}</ul>
                </li>
            </ul>
            '''


# class SymbolTableStack:
#     def __init__(self):
#         self.stack: List[Env] = []
#
#     def __len__(self):
#         return len(self.stack)
#     def fork(self):
#         res=SymbolTableStack()
#         res.stack=list(self.stack)
#         res.stack[-1]=
#     def insertTypeEntry(self, typeName, type):
#
#         self.stack[-1].insertType(typeName, type)
#         return self
#
#     def insertVarEntry(self, varName, varType):
#         self.stack[-1].insertVar(varName, varType)
#         return self
#
#     def insertFuncEntry(self, funcName, funcType):
#         self.stack[-1].insertFunc(funcName, funcType)
#
#     def push(self, description):
#         self.stack.append(Env(description))
#         return self
#
#     def pop(self):
#         res = self.stack.pop()
#         res.freeze()
#         return res
#
#     def top(self):
#         return self.stack[-1]
#
#     def __getShallowestEntry(self, item):
#         for t in reversed(self.stack):
#             if item in t:
#                 return t
#
#     def __getShallowestTypeEntry(self, item):
#         for t in reversed(self.stack):
#             if item in t.typedefs:
#                 return t
#
#     def __getShallowestVarEntry(self, item):
#         for t in reversed(self.stack):
#             if item in t.varTypes:
#                 return t
#
#     def getType(self, item: str):
#         assert isinstance(item, str)
#         t = self.__getShallowestTypeEntry(item)
#         if t is None:
#             return t
#         return t.typedefs[item]
#
#     def getVar(self, item: str):
#         assert isinstance(item, str)
#         t = self.__getShallowestVarEntry(item)
#         if t is None:
#             return t
#         return t.varTypes[item]
#
#     def __getitem__(self, item: str):
#         assert isinstance(item, str)
#         t = self.__getShallowestEntry(item)
#         if t is not None:
#             return t[item]
#         raise RuntimeError('%s undeclared.' % item)
#
#
# stack = SymbolTableStack()
# stack.push('global')
