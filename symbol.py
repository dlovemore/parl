class Symbol:
    symbols = {}
    def __new__(cls, name):
        if name in cls.symbols: return cls.symbols[name]
        return super(Symbol, cls).__new__(cls)
    def __init__(self, name):
        if name in self.__class__.symbols:
            assert(self.name==name)
            return
        self.name = name
        self.__class__.symbols[name] = self
        if name not in globals():
            globals()[name]=self
    def __getattr__(self, attr):
        return Tuple((self, Symbol(attr),))
    def __repr__(self):
        return self.name

class Tuple(tuple):
    def __new__(cls, symbols):
        return super().__new__(cls, symbols)
    def __getattr__(self, attr):
        return Tuple(self + ((Symbol(attr)),))

class MySymbol(Symbol):
    symbols={}
