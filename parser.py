from parl import itpipe
from parl.itpipe import indexable, IndexableOutput
from parl.util import taggedtuple, dfsVisit
from parl.fn import fn
from copy import copy
import collections

# Initially based on http://www.jayconrod.com/posts/38/a-simple-interpreter-from-scratch-in-python-part-2

# Todo this needs to pass parse stack around rather than just pos.

Result = taggedtuple('Result', ['value', 'pos'])

class ParseError(Exception):
    pass

class Parser(itpipe.Machine):
    """Repeatedly parses grammar until EOF or parsing fails.
"""
    def __init__(self, grammar):
        grammar = toGrammar(grammar)
        grammar = grammar.flatten() # maybe should be compile...
        super().__init__(grammar)
    # TODO Need to think about this class. It's a bit over complicated.
    # TODO Maybe have separate interactive parser.
    # A grammar may explicitly specify a terminating EOF explicitly limiting to
    # a single result.
    def run(self, input, grammar):
        pos = 0
        tokens = indexable(input)
        # this is ugly
        while (pos==0 or tokens[pos-1].tag != 'EOF') and tokens[pos].tag != 'EOF':
            result = grammar.parse(tokens, pos)
            if not result:
                if isinstance(tokens, IndexableOutput):
                    pos = len(tokens.buf) # hack, see IndexableOutput
                token = tokens[pos]
                raise ParseError(f'Syntax error at line={token.line}, column={token.column}', token)
            value, pos = result
            yield value

def toGrammar(g):
    if isinstance(g, Grammar): return g
    if isinstance(g, str): return Match(g)
    raise ValueError(g)
def toGrammars(gs):
    return list(map(toGrammar, gs))

class Grammar:
    """
Use g0+g1 for concatenation. See Concat.
Use g*separator for lists. See List.
Use g0 | g1 for alternation. See Alt.
Use g['name'] to set field name. See Named.
    Default field for repeats is g.field+'s'
Use g[start:stop] (slice notation) for repeats. See Rep. Experimental.
Use g*n for n repeats. See Rep. Experimental.
Use Match(value) to match token.value, or mostly just a string.
Use Tag(tag) to match token.tag.
Use g & validateFn to validate parse result. Experimental.
"""
    # TODO should probably have make on every grammar
    # or maybe add make dict on parser.
    def __add__(self, other):
        return Concat(self, toGrammar(other))
    def __mul__(self, other):
        if isinstance(other, int):
            return Rep(self, start=other, stop=other)
        return List(self, toGrammar(other))
    def __or__(self, other):
        return Alt(self, toGrammar(other))
    def __and__(self, checkFn):
        return Check(self, checkFn)
    def __getitem__(self, item):
        if type(item) == int:
            # will be used for position in constructor
            return Named(self, position=item)
        elif isinstance(item, slice):
            assert(not item.step)
            return Rep(self, item.start, item.stop)
        elif isinstance(item, str):
            return Named(self, field=item)
        else: raise IndexError
    def flatten(self):
        raise NotImplementedError
    def subGrammars(self):
        raise NotImplementedError("Instances should list subgrammars")
    def flattenShallow(self, g, cs):
        """Flatten this grammar so that all binary relations become lists.
This also fixes up grammar fields."""
        assert(not cs)
        return self
    def __repr__(self):
        return str(self.__class__.__name__) + ":" + str(self.__dict__)
    def myreprRecurse(self):
        return None
    def __repr__(self):
        d={}
        def visit(n, cs):
            d[n] = n.myrepr(cs)
            return d[n]
        def children(n):
            return n.subGrammars()
        def recurse(n):
            return self.myreprRecurse() or d[n]
        return dfsVisit(self, visit, children, recurse)

def plural(word):
    return word and word+'s'
# flatten is now doing more than flatten: rename or refactor.

class WithNoSubGrammar(Grammar):
    def subGrammars(self):
        return ()
    def flatten(self): return self
    def myrepr(self, cs):
        return f'{self.__class__.__name__} + ":" + str(self.__dict__)'

class WithSubGrammar(Grammar):
    def subGrammars(self):
        yield self.grammar
    def flatten(self):
        r = copy(self)
        r.grammar = self.grammar.flatten()
        return r
    def myrepr(self, cs):
        cs = ", ".join(cs)
        return f'{self.__class__.__name__}(cs)'

class WithSubGrammars(Grammar):
    def subGrammars(self):
        return self.grammars
    def flatten(self):
        grammars = []
        for grammar in self.grammars:
            grammar = grammar.flatten()
            if isinstance(grammar, type(self)):
                grammars += list(grammar.grammars)
            else:
                grammars.append(grammar)
        r = copy(self)
        r.grammars = grammars
        return r
    def myrepr(self, cs):
        cs = ", ".join(cs)
        return f'{self.__class__.__name__}(cs)'

# match token value (not tag)
class Match(WithNoSubGrammar):
    def __init__(self, value):
        self.value = value
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.value == self.value:
            return Result(token, pos + 1)
    def flatten(self): return self
    def myreprLhs(self, cs):
        return f'{self.__class__.__name__}({self.value})'
    def myreprRhs(self, cs):
        repr(self.value)
    def myrepr(self, cs):
        return repr(self.value)

class Tag(WithNoSubGrammar):
    def __init__(self, tag):
        self.tag = tag
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.tag == self.tag: #optimise == to is?
            return Result(token, pos + 1)
    def myrepr(self, cs):
        return f'{self.__class__.__name__}({self.tag!r})'

class AnyToken(WithNoSubGrammar):
    """For error handling, doesn't match EOF"""
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.tag != 'EOF':
            return Result(token, pos + 1)
    def flatten(self): return self
    def myrepr(self, cs):
        return f'{self.__class__.__name__}()'

class Check(WithSubGrammar):
    def __init__(self, grammar, f):
        self.grammar = grammar
        self.f = f
        self.fn = fn(f)
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        return result and self.fn(result.value) and result
    def myrepr(self, cs):
        return f'{self.f!r}&{f}'

class Concat(WithSubGrammars):
    def __init__(self, *gs):
        self.grammars = toGrammars(gs)
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
    def myrepr(self, cs):
        return "+".join(cs)

class Alt(WithSubGrammars):
    def __init__(self, *gs):
        self.grammars = toGrammars(gs)
    def parse(self, tokens, pos):
        for grammar in self.grammars:
            result = grammar.parse(tokens, pos)
            if result:
                return result
    def myrepr(self, cs):
        return "|".join(cs)

class Named(WithSubGrammar):
    """Tags grammar with name used as attribute name for parent grammar."""
    # field is still not a good name, attr maybe, cons maybe, tag, field?
    def __init__(self, grammar, field=None, plural=None, position=None):
        self.grammar = grammar
        self.field = field
        self.plural = plural
        if position: raise NotImplementedError
    def parse(self, tokens, pos):
        return self.grammar.parse(tokens, pos)
    def myrepr(self, cs):
        return f'{self.grammar!r}[{self.field!r}]'

class Opt(WithSubGrammar):
    def __init__(self, grammar):
        self.grammar = grammar
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        if result:
            return Result([result.value], result.pos)
        return Result(None, pos)
    def myrepr(self, cs):
        return f'{self.__class__.__name__}({", ".join(cs)})'

class Not(WithSubGrammar):
    def __init__(self, grammar):
        self.grammar = grammar
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        if not result:
            return Result(None, pos)
    def myrepr(self, cs):
        return f'{self.__class__.__name__}({", ".join(cs)})'

class Rep(WithSubGrammar):
    """Allows between start and stop repetitions."""
    # Is stop really needed?
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
    def flatten(self):
        r = copy(self)
        r = super().flatten()
        if not getattr(r, 'field', None):
            field = getattr(r.grammar, 'field', None)
            r.field = plural(field)
        return r
    def myrepr(self, cs):
        post = f'[{self.start}:{self.stop}]' if self.start or self.stop else '' 
        return f'{self.__class__.__name__}({", ".join(cs)}){post}'

class List(WithSubGrammars):
    # Not pure: doesn't keep sep. TODO fix?
    def __init__(self, g, sep):
        self.grammars = toGrammars([g, sep])
    def parse(self, tokens, pos):
        value_list = []
        sep_list = []
        grammar , sep = self.grammars
        while True:
            # work out exact semantics... currently allows trailing sep
            result = grammar.parse(tokens, pos)
            if not result:
                break
            value, pos = result
            value_list.append(value)
            sep_result = sep.parse(tokens, pos)
            if not sep_result:
                break
            sep_value, pos = sep_result
            sep_list.append(sep_value)
        return Result(value_list, pos)
    def flatten(self):
        r = copy(self)
        r = super().flatten()
        if not getattr(r, 'field', None):
            field = getattr(r.grammars[0], 'field', None)
            r.field = plural(field)
        return r
    def myrepr(self, cs):
        return '*'.join(cs)

class Forward(WithSubGrammar):
    def __init__(self):
        self.grammar = None
    def __call__(self, *gs):
        if len(gs)==1:
            self.grammar = toGrammar(*gs)
        else:
            self.grammar = Concat(*gs)
    def parse(self, tokens, pos):
        return self.grammar(tokens, pos)
    def flatten(self): return self.grammar
    def myrepr(self, cs):
        return f'{self.__class__.__name__}({", ".join(cs)})'

class Rule(WithSubGrammar):
    def __init__(self, name, g=None, make=None):
        """
A Rule achieves multiple things. It names a grammar; creates a make method;
allows recursion, and prevents flattening happening through the Rule.
make if specified is used to construct return value.
"""
# Should separarte various uses into seperate classes.
# TODO should probably have make on every grammar
        self.flattened = False
        self.name = name
        self.field = name
        if g:
            self.grammar = toGrammar(g)
        self.make = make
    def __call__(self, *gs, make=None):
        gs = list(gs)
        self.grammar = Concat(*gs)
        if make: self.make = make
        return self
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        if result:
            return Result(self.make(result.value), result.pos)
    def flatten(self):
        if not self.flattened:  # use decorator?
            self.flattened = True
            self.grammar = self.grammar.flatten()
            # Why is this so ugly?
            if not self.make:
                if isinstance(self.grammar, Concat):
                    gs = self.grammar.grammars
                else:
                    gs = list(self.grammar)
                names = [getattr(g, 'field', None) for g in gs]
                if len(gs)==1 and not names[0]:
                    names=['value']
                    # Allow invisible grammar.
                    # The problem here is Rule is trying to do too many things
                    # including preventing recursion and naming a grammar.
                    # sometimes we only want to prevent recursion.
                    # Of course the user could specify this, but then we lose
                    # information about intent.
                    if not self.field: make = lambda value: value
                #names = [name or f'_{i}' for i, name in enumerate(names)]
                tt = taggedtuple(self.name, names)
                self.make = lambda value: tt(*value)
        return self
    def myreprRecurse(self):
        return f'{self.name}'
    def myrepr(self, cs):
        return f'\n{self.name} = {self.__class__.__name__}({self.name!r})({", ".join(cs)})'
