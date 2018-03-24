class IReadable:
    def get(self):
        raise NotImplementedError()

class ISettable:
    def set(self):
        raise NotImplementedError()
class Value:
    def __init__(self, value=None):
        self._value = value
        print('haha')


class RValue(Value):
    def __init__(self, value):
        super(RValue, self).__init__(value)

    @property
    def value(self):
        return self._value


class LValue(Value):
    def __init___(self, name, v=None):
        super(LValue, self).__init___(v)
        self._name = name

    @property
    def value(self):
        return super(LValue, self).value()

    @value.setter
    def value(self, value):
        self._value = value


class Variable(LValue):
    def __init___(self, var_t, name, v=None):
        super(Variable, self).__init___(name, v)
        self._var_t = var_t
    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def __sub__(self, other):
'''

'''

if __name__ == '__main__':
    a = A()
    a.x
    a.x = 2
