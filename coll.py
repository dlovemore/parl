class At:
    def __rmatmul__(self, other): return self.rhs(other, self)
    def __matmul__(self, other): return self.lhs(self, other)
    def lhs(self, lhs, rhs): return self.rhs(lhs, rhs)
    def rhs(self, lhs, rhs): return self.lhs(lhs, rhs)

class AsList(list, At):
    def __call__(self, *args):
        return AsList(*args)
    def lhs(self, lhs, rhs):
        return AsList(AsList(lhs)+AsList(rhs))

aslist = AsList()

class Chain(list, At):
    def __call__(self, *args):
        return self@args
    def __getitem__(self, *args):
        return self@(args,)
    def lhs(self, lhs, rhs):
        return Chain(((lhs,) if lhs else () + ((rhs,) if rhs else ()))
    def __iter__(self):
        for i in range(len(self)):
            yield from super().__getitem__(i)
    def __repr__(self):
        return 'chain'+super().__repr__()

chain = Chain()
from itertools import chain as iterchain


