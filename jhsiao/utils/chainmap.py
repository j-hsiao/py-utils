"""Wrap dict with default values from other dicts."""

from __future__ import print_function
__all__ = ['ChainMap']

try:
    from collections import ChainMap as ChainMap
except Exception:
    import itertools
    import sys
    if sys.version_info.major > 2:
        from collections.abc import MutableMapping
    else:
        from itertools import imap as map
        from itertools import izip as zip
        from collections import MutableMapping

    def get_newfunc():
        """Factory for function that returns True if passed a new item.

        The item must be hashable
        """
        s = set()
        add = s.add
        slen = s.__len__
        def new(k):
            """Return True if the first time k is passed as arg.

            k must be hashable.
            """
            l = slen()
            add(k)
            return l != slen()
        return new 

    class ChainMap(MutableMapping, object):
        def __init__(self, *maps):
            """Initialize ChainMap.

            maps: Missing keys are drawn from maps in order.  These will
                not be modified
            """
            if maps:
                self.maps = list(maps)
            else:
                self.maps = [{}]

        @property
        def parents(self):
            """Chainmap of latter mappings."""
            return ChainMap(*self.maps[1:])

        def __repr__(self):
            return ', '.join(map(repr, self.maps)).join((
                'ChainMap(', ')'))

        def __getitem__(self, k):
            for mp in self.maps:
                try:
                    return mp[k]
                except KeyError:
                    pass
            return self.__missing__(k)

        def __missing__(self, k):
            raise KeyError('missing key {}'.format(repr(k)))

        def __setitem__(self, k, v):
            self.maps[0][k] = v

        def __delitem__(self, k):
            del self.maps[0][k]

        def __iter__(self):
            for k in filter(get_newfunc(), itertools.chain.from_iterable(self.maps)):
                yield k

        def __len__(self):
            return len(set().union(*self.maps))

        def __contains__(self, k):
            return any(k in m for m in self.maps)

        def setdefault(self, k, v):
            """Add key if absent from all maps."""
            sd = self.setdefault
            for mp in self.maps:
                thing = mp.get(k, sd)
                if thing is not sd:
                    return thing
            return super(ChainMap, self).setdefault(k, v)

        def __bool__(self):
            return any(self.maps)

        def __or__(self, other):
            o = dict(other)
            for m in reversed(self.maps):
                o.update(m)
            return ChainMap(o)

        def __ror__(self, other):
            return self.__or__(self, other)

        def new_child(self, m=None):
            if m is None:
                m = {}
            return ChainMap(m, *self.maps)

        def __ior__(self, other):
            self.maps[0].update(other)
            return self

        @classmethod
        def fromkeys(cls, iterable, val):
            """Keys from iterable, with value val."""
            return ChainMap(dict.fromkeys(iterable, val))

        def __copy__(self):
            return ChainMap(*self.maps)

        def copy(self):
            ret = ChainMap(self.maps[0].copy())
            ret.maps.extend(itertools.islice(self.maps, 1, None))
            return ret

        def keys(self):
            return iter(self)

        def values(self):
            for k, v in self.items():
                yield v

        def items(self):
            isnew = get_newfunc()
            for mp in self.maps:
                for t in mp.items():
                    if isnew(t[0]):
                        yield t

if __name__ == '__main__':
    d1 = dict(a=1, b=2)
    d2 = dict(c=3, d=4)
    c = ChainMap(dict(k='v'), d1, d2)
    for k in 'abcdk':
        assert k in c
    assert c['a'] == 1
    assert c['b'] == 2
    assert c['c'] == 3
    assert c['d'] == 4
    assert c['k'] == 'v'
    assert sorted(c.keys()) == ['a', 'b', 'c', 'd', 'k']
    assert sorted(c.items()) == [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('k', 'v')]
    assert set(list(c.values())) == set([1, 2, 3, 4, 'v'])
    assert c.setdefault('a', 69) == 1
    assert c.setdefault('e', 69) == 69
    assert dict(c) == dict(a=1, b=2,c=3, d=4, e=69, k='v')
    assert len(c) == 6
    cp = c.copy()
    assert isinstance(cp, ChainMap)
    assert cp == c
    d = {}
    d.update(cp)
    assert d == dict(a=1,b=2,c=3,d=4,k='v',e=69)
    out = ChainMap(dict(a=1, b=2)) | ChainMap(dict(c=3, d=4))
    assert dict(out) == dict(a=1,b=2,c=3,d=4)
    cm = ChainMap.fromkeys(range(10), 69)
    assert dict(cm) == dict.fromkeys(range(10), 69)
    cm |= dict(x=25, z=26)
    d = dict.fromkeys(range(10), 69)
    d.update(x=25, z=26)
    assert dict(cm) == d
    print('success')
