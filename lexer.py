# parl lexer
import itpipe
import collections
import re
#Token = collections.namedtuple('Token', ['tag', 'value', 'line', 'column'])
class Token:
    def __init__(self, tag, value, line, column):
        self.tag = tag
        self.value = value
        self.line = line
        self.column = column
    def __repr__(self):
        return f'Token({self.tag!r},{self.value!r},{self.line!r},{self.column!r})'
    def __str__(self):
        return f'{self.value!s}({self.line}:{self.column})'

class Lexer1(itpipe.Filter):
    def run(self, input):
        keywords = {'IF', 'THEN', 'ENDIF', 'FOR', 'NEXT', 'GOSUB', 'RETURN'}
        sep_chars = r'\][)(}{,;'
        token_specification = [
            ('NUMBER',  r'\d+(\.\d*)?'),       # Integer or decimal number
            ('SELF',    f'[{sep_chars!s}]'),   # always separate token chars
            ('COMMENT', r'#.*'),               # end comment
            ('SKIP',    r'[ \t\f]+'),          # Skip spaces and tabs
            ('STRING',  r'".*"'),              # " anything but " then "
            ('UNMATCHEDQ',r'".*'),             # unmatched "
            ('SYMBOL',  f'[^{sep_chars!s}'+r' \t\f"\#]+'),# Ids
            ('ERROR',   r'.'),                 # Anything else -- syntax error
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        # TODO compile re ?
        line_num = 1 # starting line num at 1 are insane - use 0 internally?
        for line in input:
            line_start = 0
            for mo in re.finditer(tok_regex, line):
                tag = mo.lastgroup
                value = mo.group(tag)
                if tag == 'SKIP':
                    continue
                #elif tag == 'SELF':
                #    tag = value
                elif tag == 'MISMATCH':
                    raise RuntimeError(f'{value!r} unexpected on line {line_num}')
                elif tag == 'ID' and value in keywords:
                    tag = value
                column = mo.start()
                yield Token(tag, value, line_num, column)
            line_num += 1
        yield Token('EOF', '', line_num, 0) # sentinel: simplifies parsing
Lexer=Lexer1()

class Lexer0(itpipe.Filter):
    def run(self, input):
        for i in input.split():
            while len(i) and re.match(i,r'[][\(\){},:]'):
                yield i[0]
                i = i[1:]
            yield i
