from parl import itpipe
from parl.itpipe import indexable, IndexableOutput
from parl.util import taggedtuple
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

class Grammar:
    """
Use g0+g1 for concatenation. See Concat.
Use g*separator for lists. See List.
Use g0 | g1 for alternation. See Alt.
Use g['name'] to set node name. See Named.
    Default node for repeats is g.node+'s'
Use g[start:stop] (slice notation) for repeats. See Rep. Experimental.
Use g*n for n repeats. See Rep. Experimental.
Use Match(value) to match token.value, or mostly just a string.
Use Tag(tag) to match token.tag.
Use g & validateFn to validate parse result. Experimental.
"""
    # TODO should probably have make on every node
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
            return Named(self, node=item)
        else: raise IndexError
    def fixUpPlural(g): pass
    def flatten(self):
        raise NotImplementedError
    def map(self, f, context):
        self.flatten()
        self.flattenProperly()
        pass
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return str(self.__class__.__name__) + ":" + str(self.__dict__)

def plural(word):
    return word and word+'s'
def fixUpPlural(g):
    print("fixUp", g, g.grammar)
    if not getattr(g, 'node', None):
        node = getattr(g.grammar, 'node', None)
        print("fixUp node=", node)
        g.node = plural(node)
# flatten is now doing more than flatten: rename or refactor.
def flattenGrammar(self):
    r = copy(self)
    r.grammar = self.grammar.flatten()
    return r
def flattenGrammars(self):
    grammars = []
    for grammar in self.grammars:
        grammar = grammar.flatten()
        if isinstance(grammar, type(self)):
            grammars += list(grammar.grammars)
        else: grammars.append(grammar)
    r = copy(self)
    r.grammars = grammars
    return r

# match token value (not tag)
class Match(Grammar):
    def __init__(self, value):
        self.value = value
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.value == self.value:
            return Result(token, pos + 1)
    def flatten(self): return self
    def __str__(self):
        return f'{self.__class__.__name__}({self.value})'

class Tag(Grammar):
    def __init__(self, tag):
        self.tag = tag
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.tag == self.tag: #optimise == to is?
            return Result(token, pos + 1)
    def flatten(self): return self
    def __str__(self):
        return f'{self.__class__.__name__}({self.tag})'

class AnyToken(Grammar):
    """For error handling, doesn't match EOF"""
    def parse(self, tokens, pos):
        token = tokens[pos]
        if token.tag != 'EOF':
            return Result(token, pos + 1)
    def flatten(self): return self
    def __str__(self):
        return f'{self.__class__.__name__}()'

class Check(Grammar):
    def __init__(self, grammar, s):
        self.grammar = grammar
        self.s = s
        self.fn = fn(s)
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        return result and self.fn(result.value) and result
    def flatten(self): return self
    def __str__(self):
        return f'{self.__class__.__name__}({self.s})'

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

class Named(Grammar):
    """Tags grammar with name used as attribute name for parent parse node."""
    # node is still not a good name, attr maybe, cons maybe, tag, field?
    def __init__(self, grammar, node=None, plural=None, position=None):
        self.grammar = grammar
        self.node = node
        self.plural = plural
        if position: raise NotImplementedError
    def parse(self, tokens, pos):
        return self.grammar.parse(tokens, pos)
    flatten = flattenGrammar
    def __str__(self):
        return f'{self.grammar}[{self.node!r}]'

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

class Not(Grammar):
    def __init__(self, grammar):
        self.grammar = grammar
    def parse(self, tokens, pos):
        result = self.grammar.parse(tokens, pos)
        if not result:
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
    fixUpPlural = fixUpPlural
    def flatten(self):
        r = flattenGrammar(self)
        r.fixUpPlural()
        return r
    def __str__(self):
        return f'{self.__class__.__name__}({self.grammar})[{self.start}:{self.stop}]'

class List(Grammar):
    # Not pure: doesn't keep sep. TODO fix?
    def __init__(self, g, sep):
        self.grammar = toGrammar(g)
        self.sep = toGrammar(sep)
    def parse(self, tokens, pos):
        value_list = []
        sep_list = []
        while True:
            # work out exact semantics... currently allows trailing sep
            result = self.grammar.parse(tokens, pos)
            if not result:
                break
            value, pos = result
            value_list.append(value)
            sep_result = self.sep.parse(tokens, pos)
            if not sep_result:
                break
            sep_value, pos = sep_result
            sep_list.append(sep_value)
        return Result(value_list, pos)
    fixUpPlural = fixUpPlural
    def flatten(self):
        r = flattenGrammar(self)
        r.fixUpPlural()
        print("flatten", r.node)
        return r
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
        """
A Rule achieves multiple things. It names a grammar; creates a make method;
allows recursion, and prevents flattening happening through the Rule.
make if specified is used to construct return value.
"""
# Should separarte various uses into seperate classes.
# TODO should probably have make on every grammar
        self.flattened = False
        self.name = name
        self.node = name
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
    def flattenProperly(self, rewriteDict):
        pass
    def flatten(self):
        print("Rule.flatten",self.node, getattr(self, 'flattened', None), self.make)
        # TODO not sure how to do this properly
        # I mean this should copy, but if it copies, then link with original
        # variable lost. Maybe that is OK.
        # I think flatten needs to pass extra dict around
        if not self.flattened:  # use decorator?
            self.flattened = True
            self.grammar = self.grammar.flatten()
            # Why is this so ugly?
            if not self.make:
                if isinstance(self.grammar, Concat):
                    gs = self.grammar.grammars
                else:
                    gs = list(self.grammar)
                names = [getattr(g, 'node', None) for g in gs]
                print("Rule.flatten",self.node, names)
                if len(gs)==1 and not names[0]:
                    names=['value']
                    # Allow invisible grammar.
                    # The problem here is Rule is trying to do too many things
                    # including preventing recursion and naming a grammar.
                    # sometimes we only want to prevent recursion.
                    # Of course the user could specify this, but then we lose
                    # information about intent.
                    if not self.node: make = lambda value: value
                names = [name or f'_{i}' for i, name in enumerate(names)]
                tt = taggedtuple(self.name, names)
                self.make = lambda value: tt(*value)
        return self
    def __str__(self):
        return f'{self.__class__.__name__}({self.name!r},{self.grammar})'
