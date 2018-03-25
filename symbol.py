class Symbol:
    symbols = {}
    def __new__(cls, name):
        if name in Symbol.symbols: return Symbol.symbols[name]
        return super(Symbol, cls).__new__(cls)
    def __init__(self, name):
        if name in self.symbols:
            assert(self.name==name)
            return
        self.name = name
        self.symbols[name] = self
        if name not in globals():
            globals()[name]=self
    def __repr__(self): return self.name
