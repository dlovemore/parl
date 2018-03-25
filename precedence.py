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
        assert(prec[checkOp] == prec[leftOp])
        lhs = parseK.pop()
        lhs = (lhs, leftOp, rhs)    # or (leftOp, lhs, rhs)
        leftOp = parseK[-1]
        assert(leftOp == parseK[-1])
    def shift():
        nonlocal leftOp, lhs, op
        parseK.append(lhs);
        parseK.append(op);
        leftOp = op
    for s in chain(symbols, ''):
        assert(leftOp == parseK[-1])
        print(parseK, lhs, op, s)
        if lhs is None:
            lhs = s
            # if s is postfix then 
            assert(s not in prec)
            continue
        elif op is None:
            op = s

        while prec[leftOp] >= prec[op]:
            # = handled same as > implies left associative behaviour
            if prec[leftOp] == 0:
                break
            reduce()
            assert(leftOp == parseK[-1])
        if prec[leftOp] < prec[op]:
            shift()
            lhs = None
            op = None
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
if False:
    from itpipe import Items, Map, Go, Input, Print, Apply
    from functools import partial
    tokens = Input()|Map(Apply(lambda x: [x])|Lexer()|Map("_.value")|partial(precedenceParse, prec=prec))|Print()|Go
    print(tokens)

while True:
    l = input("expr:")
    toks = Lexer()([l])
    strs = [tok.value for tok in toks]
    parse = precedenceParse(strs, prec)
    print (parse)
