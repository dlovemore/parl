import attr
import itpipe
from itpipe import Do, indexable
from copy import copy
import collections

# Initially based on http://www.jayconrod.com/posts/38/a-simple-interpreter-from-scratch-in-python-part-2

Result = collections.namedtuple('Result', ['value', 'pos'])

class Parser(itpipe.Filter):
    def run(self, input, grammar):
        grammar = toGrammar(grammar)
        yield grammar.parse(indexable(input), 0)

def toGrammar(g):
    if isinstance(g, Grammar): return g
    if isinstance(g, str): return Match(g)
    if hasattr(g, '__iter__'): return Concat(*g)
    raise ValueError(g)

class Grammar:
    def __add__(self, other):
        return Concat(self, toGrammar(other))
    def __mul__(self, other):
        return Exp(self, toGrammar(other))
    def __or__(self, other):
        return Alt(self, toGrammar(other))
    def __getitem__(self, item):
        if type(item) == int:
            return Rep(self, item, item)
        assert(not item.step)
        return Rep(self, item.start, item.stop)
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return str(self.__class__.__name__) + ":" + str(self.__dict__)
def flattenGrammar(self):
    r = copy(self)
    r.grammar = self.grammar.flatten()
    return r
def flattenGrammars(self):
    grammars = []
    for grammar in self.grammars:
        grammar = grammar.flatten()
        if isinstance(grammar, type(self)):
            grammars += list(self.grammars)
        else: grammars.append(grammar)
    r = copy(self)
    r.grammars = grammars
    return self

# match token value and tag
# -- don't really need this since reserved words/ops have value==tag
@attr.s
class Match(Grammar):
    value = attr.ib()
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.value == self.value:
            return Result(token, pos + 1)
    def flatten(self): return self

class Tag(Grammar):
    def __init__(self, tag):
        self.tag = tag
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.tag == self.tag: #optimise == to is?
            return Result(token, pos + 1)
    def flatten(self): return self
    def __str__(self):
        return f'{self.__class__.__name__}({self.tag!r})'

class Concat(Grammar):
    def __init__(self, *gs):
        self.grammars = list(map(toGrammar, gs))
    def parse(self, tokens, pos):
        value_list = []
        for grammar in self.grammars:
            result = grammar.parse(tokens, pos)
            if not result:
                return None
            value, pos = result
            value_list.append(value)
        if value_list:
            return Result(value_list, pos)
    flatten = flattenGrammars
    def __str__(self):
        return f'{self.__class__.__name__}({self.grammars})'

class Alt(Grammar):
    def __init__(self, *gs):
        self.grammars = list(map(toGrammar, gs))
    def parse(self, tokens, pos):
        for grammar in self.grammars:
            result = grammar.parse(tokens, pos)
            if result:
                return result
    flatten = flattenGrammars
    def __str__(self):
        return f'{self.__class__.__name__}({self.grammars})'

class Opt(Grammar):
    def __init__(self, grammar):
        self.grammar = grammar
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        if result:
            return Result([result.value], result.pos)
        return Result(None, pos)
    flatten = flattenGrammar
    def __str__(self):
        return f'{self.__class__.__name__}({self.grammar})'

class Rep(Grammar):
    def __init__(self, grammar, start=None, stop=None):
        self.grammar = grammar
        self.start = start or 0
        self.stop = stop
    def parse(self, tokens, pos):
        value_list = []
        i = 0
        while i < self.start:
            result = self.grammar.parse(tokens, pos)
            if not result:
                return None
            value, pos = result
            value_list.append(value)
            i+=1
        while not self.stop or i < self.stop:
            result = self.grammar.parse(tokens, pos)
            if not result:
                break
            value, pos = result
            value_list.append(value)
            i+=1
        return Result(value_list, pos)
    def __getitem__(self, item):
        # a bit unnecessary, but avoiding confusion when
        # writing Rep(G)[:3] instead of G[:3]
        # should probably remove.
        assert(self.start == 0 and not self.stop)
        if type(item) == int:
            item = slice(item,item)
        assert(not item.step)
        return Rep(self.grammar, item.start, item.stop)
    flatten = flattenGrammar
    def __str__(self):
        return f'{self.__class__.__name__}({self.grammar})[{self.start}:{self.stop}]'

class List(Grammar):
    def __init__(self, g, sep):
        self.grammar = toGrammar(g)
        self.sep = toGrammar(sep)
    def parse(self, tokens, pos):
        value_list = []
        sep_list = []
        while True:
            result = grammar.parse(tokens, pos)
            if not result:
                return None
            value, pos = result
            value_list.append(value)
            sep_result = sep.parse(tokens, pos)
            if not sep_result:
                break
            sep_value, pos = sep_result
            sep_list.append(value)
        return Result(value_list, pos)
    flatten = flattenGrammar
    def __str__(self):
        return f'{self.__class__.__name__}({self.grammar},{self.sep})'

class Forward(Grammar):
    def __init__(self):
        self.grammar = None
    def parse(self, tokens, pos):
        return self.grammar(tokens, pos)
    def flatten(self): return self.grammar
    def __str__(self):
        return f'{self.__class__.__name__}({self.grammar})'

class Rule(Grammar):
    def __init__(self, name, g=None, make=None):
        self.flattened = False
        self.name = name
        if g: self.grammar = toGrammar(g)
        if not make: self.make = collections.namedtuple(name, ['value'])
    #def make(self, value):
        #print(self.name,":",value)
    def __call__(self, *gs, make=None):
        self.grammar = toGrammar(gs)
        return self
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        if result:
            return Result(self.make(result.value), result.pos)
    def flatten(self):
        # TODO not sure how to do this properly
        # I think flatten needs to pass extra dict around
        if not self.flattened:  # use decorator?
            self.flattened = True
            self.grammar = self.grammar.flatten()
        return self
    def __str__(self):
        return f'{self.__class__.__name__}({self.name!r},{self.grammar})'
