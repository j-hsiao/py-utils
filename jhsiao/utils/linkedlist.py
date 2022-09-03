"""Linked List-like structures."""
__all__ = ['Link', 'Links']
class Link(list):
    def __init__(self, *args):
        """Expect 3 arguments: prelink, postlink, item."""
        list.__init__(self, args)

    def __call__(self, *item):
        """Set the item if given else return current item."""
        if item:
            self[2] = item[0]
            return None
        else:
            return self[2]

    def __rshift__(self, amount):
        """Step to next link in given direction/amount.

        Return None if reached end.
        """
        idx = int(amount > 0)
        try:
            for _ in range(abs(amount)):
                self = self[idx]
        except TypeError:
            return None
        return self

    def __lshift__(self, amount):
        """Step to previous link in given direction/amount.

        Return None if reached beginning.
        """
        return self >> -amount


class Links(object):
    """A collection of links.

    A link is represented by a length-3 list:
    [pre, post, item] where pre and post refer to the
    link before/after the current one or None if none.

    When slicing, if start is a Link, then what is normally
    'stop' will be interpreted as a relative offset.
    """
    def __init__(self, it=None):
        self.first = None
        self.last = None
        self._length = 0
        if it is not None:
            self.extend(it)

    def __bool__(self):
        """non-empty."""
        return self.first is not None
    __nonzero__ = __bool__

    def __len__(self):
        """Length of the list."""
        return self._length

    def __repr__(self, recursing=[False]):
        """Not threadsafe."""
        if recursing[0]:
            return '[...]'
        else:
            recursing[0] = True
            ret = repr(list(self))
            recursing[0] = False
            return ret

    def __iter__(self):
        """Iterate on items."""
        link = self.first
        while link is not None:
            yield link[2]
            link = link[1]


    def link_islice(self, link, target=None, step=None):
        """Iterate on links from link in step direction by target.

        target is a relative count and excluded.
        (basically, link>>i for i in range(0, target, step))
        target defaults to end of the list.
        If step is 0 or None, use 1.
        """
        if target == 0:
            return
        elif target is None:
            target = self._length
        if not step:
            step = 1 if target > 0 else -1
        ispos = step>0
        if (ispos) != (target>0):
            return
        yield link
        cur = step
        if ispos:
            while target > cur:
                try:
                    for _ in range(step):
                        link = link[1]
                except TypeError:
                    return
                cur += step
                yield link
        else:
            step = -step
            while target < cur:
                try:
                    for _ in range(step):
                        link = link[0]
                except TypeError:
                    return
                cur -= step
                yield link


    def __call__(self, idx):
        """Return corresponding link."""
        try:
            if idx >= 0:
                ret = self.first >> idx
            else:
                ret = self.last >> (idx+1)
            if ret:
                return ret
            raise IndexError(str(idx))
        except TypeError:
            raise IndexError(str(idx))

    def __getitem__(self, idx):
        """Return the corresponding item(s)."""
        if isinstance(idx, int):
            return self(idx)[2]
        elif isinstance(idx.start, Link):
            link, target, step = idx.start, idx.stop, idx.step
        else:
            start, stop, step = idx.indices(self._length)
            fromback = (self._length-1)-start
            if start < fromback:
                link = self.first >> start
            else:
                link = self.last << fromback
            target = stop-start
        ret = Links()
        if link is None:
            return ret
        it = iter(self.link_islice(link, target, step))
        try:
            ret.first = pre = Link(None, None, next(it)[2])
        except StopIteration:
            return ret
        nitems = 1
        for link in it:
            nitems += 1
            post = Link(pre, None, link[2])
            pre[1] = pre = post
        ret.last = pre
        ret._length = nitems
        return ret

    def __setitem__(self, idx, item):
        """Set the corresponding item(s)."""
        if isinstance(idx, int):
            self(idx)[2] = item
        elif isinstance(idx.start, Link):
            link, target, step = idx.start, idx.stop, idx.step or 1
        else:
            start, stop, step = idx.indices(self._length)
            fromback = (self._length-1)-start
            if start < fromback:
                link = self.first >> start
            else:
                link = self.last << fromback
            target = stop-start
        # TODO: finish implementing slice assignment

        it = self.link_islice(link, target, step)
        items = iter(item)
        if step == 1 or step == -1:
            try:
                link = next(it)
            except StopIteration:
                if step == 1:
                    if link[0] is None:
                        tmp = Links(items)
                        if len(tmp):
                            self.first = tmp.first
                    else:
                        self.extend(items, link)


            for link, thing in zip(it, items):
                link[2] = thing
            try:
                extralink = next(it)
            except StopIteration:
                pass
            else:
                pre, post = extralink[0], extralink[1]
                extralink[0] = extralink[1] = extralink[2] = None
                for extralink in it:
                    pre, post = extralink[0], extralink[1]
                    extralink[0] = extralink[1] = extralink[2] = None
        else:
            # don't change anything until verify same lengths
            pairs = list(zip(it, items))
            try:
                next(it)
                raise Exception('extended slice assignment must be equal lengths.')
            except StopIteration:
                pass
            try:
                next(items)
                raise Exception('extended slice assignment must be equal lengths.')
            except StopIteration:
                pass
            for link, item in pairs:
                link[2] = item

    def pop(self, link=None):
        """Remove and return given link.

        If link is None, pop last link.
        Undefined behavior if link is not a part of this list.
        """
        if isinstance(link, int):
            link = self(link)
        elif not link:
            link = self.last
        try:
            pre = link[0]
        except TypeError:
            raise IndexError('pop from empty list.')
        post = link[1]
        link[0] = link[1] = None
        self._length -= 1
        if pre:
            pre[1] = post
        else:
            self.first = post
        if post:
            post[0] = pre
        else:
            self.last = pre
        return link

    def clear(self):
        """Clear the list."""
        #break cyclic references
        for link in self.links():
            link[0] = link[1] = link[2] = None
        self.first = self.last = None
        self._length = 0

    def links(self):
        """Iterate on links."""
        link = self.first
        while link:
            yield link
            link = link[1]

    def append(self, item, link=None, newlink=None):
        """Add an item after link.  Return the newly added link.

        If link is None, add to end of list.
        item: item to add
        link: append relative to link.
        newlink: reuse a link, should have been popped.
        """
        if link is None:
            link = self.last
        try:
            post = link[1]
        except TypeError:
            self.first = self.last = self._link(item, None, None, newlink)
        else:
            link[1] = newlink = self._link(item, link, post, newlink)
            if post:
                post[0] = newlink
            else:
                self.last = newlink
        self._length += 1
        return newlink

    def appendleft(self, item, link=None, newlink=None):
        """Prepend an item.

        item: item to add
        link: append relative to link.
        newlink: reuse a link, should have been popped.
        """
        if link is None:
            link = self.first
        try:
            pre = link[0]
        except TypeError:
            self.first = self.last = self._link(item, None, None, newlink)
        else:
            link[0] = newlink = self._link(item, pre, link, newlink)
            if pre:
                pre[1] = newlink
            else:
                self.first = newlink
        self._length += 1
        return newlink

    def extend(self, items, link=(None,None)):
        """Add items in order after link.

        If link is None, add to end of list.
        """
        self.insert(link[1], items)

    def insert(self, linkOrIdx, items):
        """Insert items in order at link position.

        If link is None, then end of list is used.
        """
        if isinstance(linkOrIdx, int):
            if linkOrIdx < 0:
                linkOrIdx += self._length
            if linkOrIdx >= self._length:
                link = None
            elif linkOrIdx <= 0:
                link = self.first
            else:
                link = self(linkOrIdx)
        else:
            link = linkOrIdx
        it = iter(items)
        try:
            first = pre = Link(None, None, next(it))
        except StopIteration:
            return
        nitems = 1
        for item in it:
            nitems += 1
            post = Link(pre, None, item)
            pre[1] = pre = post
        if link is None:
            first[0] = self.last
            try:
                self.last[1] = first
            except TypeError:
                self.first = first
            self.last = pre
            self._length += nitems
        try:
            post = link[1]
        except TypeError:
            self.first = first
            self.last = pre
            self._length = nitems
        else:
            self._length += nitems
            link[1] = first
            first[0] = link
            pre[1] = post
            try:
                post[0] = pre
            except TypeError:
                self.last = pre

    def extendleft(self, items, link=None):
        """Note that items will end up in reverse order."""
        it = iter(items)
        try:
            last = post = Link(None, None, next(it))
        except StopIteration:
            return
        nitems = 1
        for item in it:
            nitems += 1
            pre = Link(None, post, item)
            post[0] = post = pre
        if link is None:
            link = self.first
        try:
            pre = link[0]
        except TypeError:
            self.last = last
            self.first = post
            self._length = nitems
        else:
            self._length += nitems
            link[0] = last
            last[1] = link
            post[0] = pre
            try:
                pre[1] = post
            except TypeError:
                self.first = post


    @staticmethod
    def _link(item, before, after, newlink=None):
        """Make a disconnected link between before and after.

        item: Item for the new link.
        before, after: links before and after new link.
        newlink: Reuse this link if given.
        """
        if newlink is None:
            return Link(before, after, item)
        else:
            newlink[0] = before
            newlink[1] = after
            newlink[2] = item
            return newlink

    @staticmethod
    def _chain(items, before=None, after=None, reverse=False):
        """Make a disconnected chain of links.

        items: iterable of items.
        before, after: links that are before and after the chain
        reverse: resulting chain should have items in reverse.

        Return (num_items, firstlink, lastlink)
        """
        it = iter(items)
        try:
            item = next(it)
        except StopIteration:
            return 0, None, None
        firstlink = lastlink = Link(before, after, item)
        nitems = 1
        if reverse:
            for item in it:
                nitems += 1
                curlink = Link(before, lastlink, item)
                lastlink[0] = lastlink = curlink
            firstlink, lastlink = lastlink, firstlink
        else:
            for item in it:
                nitems += 1
                curlink = Link(lastlink, after, item)
                lastlink[1] = lastlink = curlink
        return nitems, firstlink, lastlink




if __name__ == '__main__':
    l = Links()
    l.append(1)
    assert list(l) == [1]
    mid = l.append(2)
    assert list(l) == [1,2]
    l.append(3)
    assert list(l) == [1,2,3]
    l.appendleft(4)
    assert list(l) == [4,1,2,3]
    l.append(5, mid)
    assert list(l) == [4,1,2,5,3]
    l.appendleft(6, mid)
    expect = [4, 1, 6, 2, 5, 3]
    assert list(l) == expect
    assert (mid << 4) is None
    assert (mid >>-3)() == 4
    assert (mid << 2)() == 1
    assert (mid << 1)() == 6
    assert (mid >> 0) is mid
    assert (mid >> 1)() == 5
    assert (mid <<-2)() == 3
    assert (mid >> 3) is None
    for i, v in enumerate(expect):
        assert l[i] == v
    thing = l.first
    thing>>=1
    assert thing is l.first[1]
    assert thing() == 1
    assert thing[0] is l.first
    assert l.first() == 4
    assert len(l) == 6
    assert l.pop(l.last)() == 3
    assert list(l) == expect[:-1]
    assert len(l) == 5
    assert l.pop(0)() == 4
    assert list(l) == expect[1:-1]
    assert len(l) == 4
    assert l.pop(l.first)() == 1
    assert list(l) == expect[2:-1]
    assert len(l) == 3
    assert l.pop(-1)() == 5
    assert list(l) == [6,2]
    assert len(l) == 2
    assert mid is l.last
    assert l.pop(mid)() == 2
    assert list(l) == [6]
    assert len(l) == 1
    assert l.first is l.last
    assert l.pop(l.last)() == 6
    assert list(l) == []
    assert len(l) == 0
    assert l.first == l.last == None
    l.extend(expect)
    assert list(l) == expect
    mid = l(3)
    assert mid() == 2
    assert l.pop()() == expect[-1]
    assert list(l) == expect[:-1]
    assert len(l) == 5
    assert l.pop(mid)() == 2
    assert list(l) == [4,1,6,5]
    assert len(l) == 4

    l.clear()
    from collections import deque
    l.extend('hello')
    expect = deque('hello')
    assert len(l) == len(expect)
    assert deque(l) == expect
    l.extendleft('hello')
    expect.extendleft('hello')
    assert len(l) == len(expect)
    assert deque(l) == expect

    expect = list(l)
    for start in range(len(expect)):
        for stop in range(len(expect)):
            for step in range(-3, 4):
                slc = slice(start, stop, step or None)
                sliced = list(l[slc])
                expectslice = expect[slc]
                if sliced != expectslice:
                    print('slice:', start, stop, step)
                    print('result:', sliced)
                    print('expected:', expectslice)
                    assert 0
    print('pass')

    l = Links()
    l._length, l.first, l.last = Links._chain('hello world!')
    assert list(l) == list('hello world!')
    l._length, l.first, l.last = Links._chain('hello world!', reverse=True)
    assert list(l) == list(reversed('hello world!'))
