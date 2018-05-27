from collections import defaultdict
from typing import List
import c_parser.c_type as c_type
import c_parser.ast_node as ast
from c_parser.environment import Env

table = {}


class LHS(type):
    # @classmethod
    # def __prepare__(metacls, name, bases):
    #     print(f'name={name},bases={bases}')
    #     return {}

    def __new__(cls, name, bases, classDict, **kwargs):
        # print(f'{name},classdict={classDict}')
        res = super().__new__(cls, name, bases, dict(classDict))
        table[classDict['key']] = res
        return res


class MultipleSol(metaclass=LHS):
    key = 'MultiSol'

    def __init__(self, *args):
        self.sols = args

    def __str__(self):
        return f"""
<span>{self.__class__.__name__}</span><ul>
{''.join(f'''
    <li>
        <span>解{i+1}</span>
        <ul>{j}</ul>
    </li>'''
    for i, j in enumerate(self.sols))}
</ul>"""

    def run(self, env: Env, *args, **kwargs):
        pass


def check(x):
    for e in x:
        if not (isinstance(e, str) or isinstance(e.__class__, LHS)):
            return False
    return True


class Base:
    def __init__(self, *args):
        self.rhs: List[Base] = args
        assert check(args)
        self.__hash = hash(self.rhs)

    def run(self, env, *args, **kwargs):
        raise NotImplementedError()

    def __hash__(self):
        return self.__hash

    def __eq__(self, other):
        return self.__class__.__name__ == other.__class__.__name__

    def __str__(self):
        return """
    <span>{0}</span><ul>
    {1}
    </ul>""".format(self.__class__.__name__, ''.join(f'<li>{r}</li>' for r in self.rhs))


def strCheck(self, i):
    if self.rhs[i].__class__.__name__ == self.__class__.rhs[i]:
        return True
    print(f'oops! self.rhs[{i}].__class__.__name__ = {self.rhs[i].__class__.__name__}, '
          f'self.__class__.rhs[{i}] = {self.__class__.rhs[i]}')
    assert 0
