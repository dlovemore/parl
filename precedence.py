from itertools import chain
def precedenceParse(symbols, prec):
    """
Parses symbols into tree based on precedence of operators given in prec.
prec is a dict from op to precedence. Higher precedence binds tighter.
So normally + has lower precedence than * meaning a + b * c is parsed as
(+ a (b * c))
"""
    leftOp = ''
    lhs = None
    parseK = [leftOp] # parse stack
    op = None
    def reduce():
        nonlocal leftOp, lhs, op
        rhs=lhs
        checkOp = parseK.pop()
        assert(checkOp == leftOp)
        lhs = parseK.pop()
        lhs = (lhs, leftOp, rhs)    # or (leftOp, lhs, rhs)
        leftOp = parseK[-1]
        assert(leftOp == parseK[-1])
    def shift():
        nonlocal leftOp, lhs, op
        parseK.append(lhs);
        parseK.append(op);
        leftOp = op
        lhs = None
        op = None
        print(parseK, lhs, op)
    for s in chain(symbols, ''):
        assert(leftOp == parseK[-1])
        if lhs is None:
            lhs = s
            print(parseK, lhs, op)
            assert(s not in prec)
            continue
        elif op is None:
            op = s

        while prec[leftOp] >= prec[op]:
            # = handled same as > implies left associative behaviour
            if len(parseK) == 1:
                break
            reduce()
            assert(leftOp == parseK[-1])
        if prec[leftOp] < prec[op]:
            shift()
    print(parseK, lhs, op)
    return lhs
        
        
"""
[a * b + c / d ^ e * f - g]  + - less than * / less than ^
General state
# [ (a * b) + lhs=c op=/ . d ^ e * f - g]  + - less than * / less than ^

. represents position in input
( represents parser stack

# [
leftOp = [
[ . a * b + c / d ^ e * f - g]
lhs = a
[ a * . b + c / d ^ e * f - g]
op = *
[ a * . b + c / d ^ e * f - g]
[ < * so shift {
    push(lhs)
    # [ a
    push(op)
    # [ a *
    lhsOp = op {tos = op = *}
}
lhs = b
[ a * b . + c / d ^ e * f - g]
op = +
[ a * b + . c / d ^ e * f - g]
* > + so reduce {
    # [ a *
    rhs = lhs = b
    leftOp = pop() = *
    # [ a
    lhs = pop()
    # [ 
    lhs = make(lhs leftOp rhs) = (a * b) { or (* a b) }
    # [
leftOp = [
[ a * b + . c / d ^ e * f - g]
lhs = (a * b)
[ a * b + . c / d ^ e * f - g]
op = +
[ < + so shift
[ (a * b) + c . / d ^ e * f - g]
lhs = c
op = /
+ < / so shift
"""

prec = {
'*' : 9,
'/' : 9,
'+' : 8,
'-' : 8,
'<<' : 7,
'>>' : 7,
'<' : 6,
'<=' : 6,
'>' : 6,
'>=' : 6,
'==' : 5,
'!=' : 5,
'&' : 4,
'|' : 3,
'&&' : 2,
'||' : 1,
'' : 0
}

from lexer import Lexer
from itpipe import *
tokens = Items("2 + 3 * 4 - 5")|Lexer()|Map("_.value")|list|Go
print(tokens)
parse = precedenceParse(tokens, prec)

print(parse)
