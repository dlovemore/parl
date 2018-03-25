"""
Like unix pipes, but with python iterators -- experimental
functions, machines etc take as rhs op of |
"""
import readline
import itertools
import sys
import ast
import re
from parl.fn import fn

# Perhaps call Machine something better?
class Machine:
    """
A machine is a callable that takes an iterable input and returns an iterable output.
"""
    def __init__(self, *args, **kwargs):
        """These arguments are usually passed to run"""
        self.args = args
        self.kwargs = kwargs
    def go(self, inputIterable):
        """Returns an iterable, by default calls run."""
        return self.run(inputIterable, *self.args, **self.kwargs)
    def run(self, input, *args, **kwargs):
        """
Implement in subclasses, if go 
Input is an iterable, args and kwargs are constructor arguments.
Returns an iterable, such as a list. This method can be a generator, yielding results.
"""
        raise NotImplementedError("Abstract method")
    def __call__(self, input=None):
        """input is an iterable."""
        # Not sure if this is good. It would be simpler not to have Stdin here.
        if input is None: input = Stdin()
        """May return more complex object such as indexable or list"""
        return self.go(input)
    def __iter__(self):
        return self.go(Stdin())
    def __or__(self, f):
        machine = toMachine(f)
        return machine.reverse_or(self)
    def reverse_or(self, lhs):
        return Pipe(lhs, self)
    def __add__(self, machine):
        machine = toMachine(f)
        return "TODO trying to implement a machine chain, but how?"
        return Chain(self, machine)
    def __repr__(self):
        return str(self)
    def __str__(self):
        # TODO there's probably a much better way of doing this.
        s=self.__class__.__name__
        args = hasattr(self, 'args') and self.args
        kwargs = hasattr(self, 'kwargs') and self.kwargs
        if args or kwargs:
            s+='('
            if args:
                s+=",".join([repr(a) for a in self.args])
            if kwargs:
                if args:
                    s+=", "
                s+=",".join([str(k)+"="+str(v) for k,v in self.kwargs.items()])
            s+=')'
        return s

def toMachine(f):
    """Takes string, fun or machine and returns machine.
If string, convert to function see fn.py.
If callable type, then call to instantiate.
If instance of Machine use that otherwise if callable apply using Map."""
    if isinstance(f, Machine):
        return f
    if type(f) == str:
        f = fn(f)
    # TODO probably not the best way to do this, use inspect.isclass?
    #if type(f).__name__ in {'classobj', 'type'}: 
    #    f = f()
    if not isinstance(f, Machine) and (hasattr(f, '__call__') or hasattr(f, '__new__')):
        f = Apply(f)
    return f

class Input(Machine):
    def run(self, inp):
        while True:
            try:
                yield input()
            except EOFError:
                raise StopIteration
    def __str__(self): return "Input()"

class Stdin(Machine):
    def run(self, inputIterable, raw=False):
        while True:
            l = sys.stdin.readline()
            if not l:
                break
            if raw: yield l
            else: yield l.rstrip()
    def __str__(self): return "Stdin()"

def forceArgs(*args): return args
def forceIterable(iterable): return forceArgs(*iterable)

class Go(Machine):
    def reverse_or(self, machine):
        return forceIterable(machine.go(Stdin()))
Go=Go()

class List(Machine):
    def run(self, input):
        return list(input)

class oD(Machine):
    def reverse_or(self, machine):
        return machine.go(None)

class Do(Machine):
    def run(self, inputIterable, iterable):
        return iter(iterable)

class Items(Machine):
    def run(self, inputIterable, *items):
        return items.__iter__()
Item = Items

class Cat(Machine):
    def run(self, input, raw=False):
        for n in input:
            with open(n, 'r') as f:
                while True:
                    l = f.readline()
                    if not l:
                        break
                    if raw: yield l
                    else: yield l.rstrip()

class Cat(Machine):
    def run(self, input, *filenames, raw=False):
        for n in filenames:
            with open(n, 'r') as f:
                while True:
                    l = f.readline()
                    if not l:
                        break
                    if raw: yield l
                    else: yield l.rstrip()

class Show(Machine):
    def run(self, inputIterable):
        for x in inputIterable:
            print("Show:", x)
            yield x

class Print(Machine):
    def run(self, inputIterable):
        for x in inputIterable:
            print(x)
        return
        yield

class Apply(Machine):
    def run(self, input, *fns):
        arg = input
        for f in fns:
            arg = f(arg)
        return arg

class Arg(Machine):
    def run(self, input, f):
        return f(input)

class Map(Machine):
    def run(self, input, f):
        if type(f)==str:
            f = fn(f)
        for x in input:
            # yield args[0](ast.literal_eval(x))
            r = f(x)
            #print(self,r,x)
            yield r

class Remove(Machine):
    def run(self, input, omit):
        for x in input:
            if x != self.omit:
                yield x

class Sort(Machine):
    def run(self, input):
        l=list(input)
        l.sort()
        return l

class Uniq(Machine):
    def run(self, input):
        last = None
        for x in input:
            if x != last:
                yield x
                last = x

class Filter(Machine):
    def run(self, input, f):
        f = fn(f)
        for x in input:
            if f(x):
                yield x

class Grep(Machine):
    def run(self, input, pattern, flags='p'):
        n = 'n' in flags # number lines
        one = '1' in flags # printed line numbers start at one
        p = 'p' in flags # print
        i = 'i' in flags # yield index
        v = 'y' in flags # yield value
        for i, value in enumerate(input):
            s = str(value)
            if re.search(pattern, s):
                if p:
                    if n: print(i+one, end=' ')
                    print(value)
                if 'y' in flags:
                    if i and v:
                        yield (i, value)
                    elif v:
                        yield value
                    elif i:
                        yield i

class RemoveDuplicates(Machine):
    def run(self, inputIterable):
        seen = set()
        for x in inputIterable:
            if not x in seen:
                seen.add(x)
                yield x

class Between(Machine):
    def run(self, inputIterable, xfrom, before):
        between = False
        for x in inputIterable:
            if between:
                if x == before:
                    between = False
            else:
                if x == xfrom:
                    between = True
            if between:
                yield x

class Rest(Machine):
    def run(self, inputIterable, itr):
        yield from itr

class Fold(Machine):
    def run(self, inputIterable, f, **kwargs):
        if type(f)==str:
            g = fn(f)
            f = (lambda g: (lambda x,y: g((x,y))))(g)
        if 'initial' in kwargs:
            r = kwargs['initial']
            for xx in inputIterable:
                #print(xx)
                r=f(r,xx)
            yield r
        else:
            itr = iter(inputIterable)
            r = next(itr)
            for x in Rest(itr):
                r=f(r,x)
            yield r

class IndexableOutput:
    def __init__(self, iterable):
        self.iterable = iterable
        self.buf = []
        self.started = False
    def start(self):
        if not self.started:
            self.started = True
            self.itr = iter(self.iterable)
    def __iter__(self):
        self.pos = 0
        while True:
            yield self.get()
    def get(self): # may raise StopIteration
        x = self.pos
        self.pos += 1
        self.ensure(self.pos)
        return self.buf[x]
    def __getitem__(self, item):
        if type(item)==int:
            self.safeEnsure(item+1 if item >=0 else None)
            return self.buf[item]
        start = item.start or 0
        stop = item.stop
        stop = stop and stop >= 0 and start >= 0 and stop
        self.safeEnsure(stop)
        return self.buf[start:stop:item.step]
    def __len__(self):
        self.safeEnsure(None)
        return len(self.buf)
    def safeEnsure(self, stop):
        try:
            self.ensure(stop)
        except StopIteration:
            pass
    def ensure(self, stop): #may raise StopIteration
        # self.start() nothing to do with start or item.start... confusing
        self.start()
        while not stop or len(self.buf) < stop:
            self.buf.append(next(self.itr))
    def seek(self, pos=0):
        self.pos = pos
    def back(self, n=1):
        self.pos -= n
    def skip(self, n=1):
        self.pos += n

# TODO what about __len__?
class Indexable(Machine):
    def go(self, input):
        return indexable(input)

def indexable(iterable):
    if hasattr(iterable, '__getitem__'):
        return iterable
    return IndexableOutput(iterable)

class Chain(Machine):
    def run(self, inputIterable, iterables):
        return iter(itertools.chain(*iterables))

class Pipe(Machine):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right
    def go(self, input):
        return self.right.go(self.left.go(input))
    def __str__(self):
        return f'({self.left!s}|{self.right!s})'

class ChainInput(Machine):
    def run(self, input):
        for i in input:
            for x in i:
                yield x

class Args(Machine):
    def run(self, input, f):
        return iter(f(*input))

# Not really used at present

class Defer:
    def __init__(self, xclass, *args, **kwargs):
        self.xclass=xclass
        self.args=args
        self.kwargs=kwargs
    def __call__(self):
        xclass(*self.args, **self.kwargs)

LiteralEval = Map(ast.literal_eval)
Eval = Map(eval)
Sum = Fold((lambda a,b: a+b), initial=0)
Add = Fold((lambda a,b: a+b))
Words = Map(lambda x: x.split())|ChainInput()
Count = Fold(lambda x,y: x+1, initial=0)
Wc = Map(lambda x: len(x.split()))|Sum
