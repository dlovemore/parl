# simple ways of defining functions
# So "_1-_2" is just f(x,y) = x - y
# But this doesn't work for reduce because f(1,2) is not f applied to a tuple.
import re
def fn(s):
    if hasattr(s, "__call__"): return s
    if s[0]=='.': s = "_"+s
    s = re.sub('_([0-9])',r'_[\1]',s)
    s = "(lambda _: "+s+")"
    return eval(s)
