class UnaryFunction(object):
    def __init__(self,*args):
        print(args)
        #self.functions=tuple(f for f in 
    def __mul__(self,rhs):
        {'UnaryFunction':
            lambda rhs:UnaryFunction(*(rhs.functions+self.functions)),
        'function':
            lambda rhs:UnaryFunction(*((rhs,)+self.functions))
        }[type(rhs).__name__](rhs)
    def __call__(self,x):
        if len(self.functions)==0:
            raise RuntimeError('this UnaryFunction has an empty function list.')
        for f in self.functions:
             x=f(x)
        return x
class Stream(object):
    def __init__(self,iterable):
        self._it=iterable
        self._manipulation=[]
        self._guard=lambda :None
    def _map(self,func):
        self._manipulation.append(('map',func))
        return self
    def _filter(self,func):
        self._manipulation.append(('filter',func))
        return self
    def _distinct(self):
        self._it=list(set(self._collect(False)))
        return self
    def _peek(self,func):
        self._manipulation.append(('peek',func))
        return self
    def _collect(self,close=True):
        def gen():
            for x in self._it:
                filterOff=False
                for t,f in self._manipulation:
                    if t=='map':
                        x=f(x)
                    elif t=='peek':
                        f(x)
                    elif t=='filter' and not f(x):
                        filterOff=True
                        break
                if not filterOff:
                    yield x
        if(close):
            self._close()
        #print("collected.returning...")
        return gen()
    def _groupBy(self,func):
        res={}
        for x in self._collect():
            res.setdefault(func(x),[]).append(x)
        self._close()
        return res
    def _close(self):
        #print("closing!")
        self._guard=self.__closed
    def __closed(self):
        raise RuntimeError('stream has already been operated upon or closed')
    def __getattr__(self,name):
        #print("get("+name+")")
        self._guard()
        try:
            return {
                'map':self._map,
                'filter':self._filter,
                'collect':self._collect,
                'groupBy':self._groupBy,
                'distinct':self._distinct,
                'peek':self._peek,
                'close':self._close
            }[name]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" %(Stream.__name__,name))
    
