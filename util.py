def taggedtuple(tag, names=None):
    _n = names and len(names)
    _names = names # to provide access to names if given
    def initial_dict(names):
        d=dict(__new__=_new_, __init__=_init_, __repr__=_repr_, _tag=tag)
        if names:
            for (i, name) in enumerate(names):
                if name in d: raise ValueError(f'Attr {name} already exists')
                if name:
                    d[name] = property((lambda i: lambda self: self[i])(i))
        if 'tag' not in d: d['tag']=tag
        return d
    # should also make accessors from members
    def _new_(cls, *args):
        return tuple.__new__(cls, args)
    def _init_(self, *args):
        if _n and len(args)!=_n:
            raise ValueError(f'{tag} expects {_n} args not {len(args)}.')
    # tuple.__str__ seems just to call repr, so omit
    #def _str_(self):
        #return tag+tuple.__str__(self)
    def _repr_(self):
        return tag+tuple.__repr__(self)
    return type(tag, (tuple,), initial_dict(names))

