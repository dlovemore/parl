import itpipe
from itpipe import Machine
from operator import itemgetter

class Cut(Machine):
    def run(self, input, item):
        if isinstance(item, int):
            for x in input:
                yield x[item]
        else:
            getter = itemgetter(*item)
            for x in input:
                yield getter(x)


