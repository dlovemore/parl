from parl import itpipe
import collections
import re
#Token = collections.namedtuple('Token', ['tag', 'value', 'line', 'column'])
class Token:
    def __init__(self, tag, value, line, column):
        self.tag = tag
        self.value = value
        self.line = line
        self.column = column
    # TODO: what is best here?
    def __repr__(self):
        #return f'Token({self.tag!r},{self.value!r},{self.line!r},{self.column!r})'
        return f'{self.tag!s}({self.value!r})'

class Lexer(itpipe.Machine):
    """
Interim Lexer, requires spaces except for sep_chars.
"""
    sep_chars = r'\][)(}{,;\.'
    keywords = {'IF', 'THEN', 'ENDIF', 'FOR', 'NEXT', 'GOSUB', 'RETURN'}
    def run(self, input):
        seps = self.sep_chars
        keywords = self.keywords
        token_specification = [
            ('NUMBER',  r'\d+(\.\d*)?'),       # Integer or decimal number
            ('SELF',    f'[{seps!s}]'),   # always separate token chars
            ('COMMENT', r'#.*'),               # end comment
            ('SKIP',    r'[ \t\f]+'),          # Skip spaces and tabs
            ('STRING',  r'".*"'),              # " anything but " then "
            ('UNMATCHEDQ',r'".*'),             # unmatched "
            ('SYMBOL',  f'[^{seps!s}'+r' \t\f"\#]+'),# Ids
            ('ERROR',   r'.'),                 # Anything else -- syntax error
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        # TODO compile re ?
        # starting line_num at 1 is insane - use 0 internally?
        for line_num, line in enumerate(input, start=1):
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
        yield Token('EOF', '', line_num, 0) # sentinel: simplifies parsing
