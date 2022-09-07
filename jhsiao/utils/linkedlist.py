"""Linked List-like structures."""
__all__ = ['Link', 'Links']
class Link(list):
    def __init__(self, *args):
        """Expect 3 arguments: prelink, postlink, item."""
        list.__init__(self, args)

    def __repr__(self):
        return repr(self[2]).join(('Link(', ')'))

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

    Links lists have an alternative slicing notation where the start
    is a link in the list.  In this case, the notation is
    [link:target:step] where link is the link to start at, target is
    the target offset to traverse to, and step is the stepsize to take.
    Positive targets will move towards the end of the list while
    negative offsets will move towards the beginning.  Because the links
    do not track their position in the list, this type of slicing cannot
    have its length be calculated.
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
    def __reversed__(self):
        """Iterate in reverse."""
        link = self.last
        while link is not None:
            yield link[2]
            link = link[0]

    def __eq__(self, other):
        return len(self) == len(other) and all(a==b for a,b in zip(self, other))
    def __neq__(self, other):
        return not self == other

    def _normalize_slice(self, slc):
        """Normalize slice a slice.

        Return a link, distance to travel, stepsize, and count if
        applicable.  Count is only calculable if link is None or an
        index.  Otherwise, it will be None.
        """
        if isinstance(slc.start, Link):
            link = slc.start
            target = slc.stop
            step = slc.step
            if step is None:
                if target is None:
                    target = self._length
                    step = 1
                else:
                    step = 1 if target>0 else -1
            elif target is None:
                target = self._length if step>0 else -self._length
            return link, target, step, None
        else:
            start, stop, step = slc.indices(self._length)
            target = stop-start
            count = max(0, (target + step - (1 if step>0 else -1))//step)
            if start == self._length:
                return None, target, step, count
            else:
                return self(start), target, step, count

    def _links(self, link, target, step):
        """Do the actual iteration on links."""
        if step>0:
            idx = 1
        else:
            idx = 0
            target = -target
            step = -step
        if target <= 0:
            return
        yield link
        cur = step
        while target > cur:
            try:
                for _ in range(step):
                    link = link[idx]
            except TypeError:
                return
            if link:
                yield link
                cur += step
            else:
                return

    def links(self, link=None, target=None, step=None):
        """Iterate on links with similar args to slice().

        link: A link to start at.
        target: A distance to travel
        step: The stepsize to use.
        """
        link, target, step, _ = self._normalize_slice(
            slice(link, target, step))
        return self._links(link, target, step)

    def __call__(self, idx):
        """Return corresponding link."""
        if idx < 0:
            idx += self._length
        if 0 <= idx < self._length:
            fromend = self._length - idx
            if idx < fromend:
                link = self.first
                for i in range(idx):
                    link = link[1]
            else:
                link = self.last
                for i in range(fromend - 1):
                    link = link[0]
            return link
        else:
            raise IndexError(
                'index {} out of range'.format(
                    idx-self._length if idx<0 else idx))

    def __getitem__(self, idx):
        """Return the corresponding item(s)."""
        if isinstance(idx, int):
            return self(idx)[2]
        ret = Links()
        it = iter(self._links(*self._normalize_slice(idx)[:-1]))
        try:
            item = next(it)[2]
        except StopIteration:
            return ret
        nitems = 1
        ret.first = pre = Link(None,None,item)
        for lnk in it:
            nitems += 1
            post = Link(pre, None, lnk[2])
            pre[1] = pre = post
        ret.last = pre
        ret._length = nitems
        return ret

    def __setitem__(self, idx, item):
        """Set the corresponding item(s).

        When slicing, step of 0 is changed to 1.  (step of 0 makes no
        sense).
        """
        # TODO finish this
        if isinstance(idx, int):
            self(idx)[2] = item
        link, target, step, count = self._normalize_slice(idx)
        if step == 1:
            if target:
                self._assign_basic(self._links(link, target, step), item, link)
            else:
                self.insert(link, item)
        else:
            linkit = self._links(link, target, step)
            if count is None:
                linkit = tuple(linkit)
                count = len(linkit)
            self._assign_extended(linkit, item, count)

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
        """Clear the list.

        Also break the circular references.
        Leave the items in the links alone though.
        """
        link = self.first
        while link:
            nxt = link[1]
            link[0] = link[1] = None
            link = nxt
        self.first = self.last = None
        self._length = 0

    def __del__(self):
        self.clear()

    def append(self, item, link=None, newlink=None):
        """Add an item after link.  Return the newly added link.

        If link is None, add to end of list.
        item: item to add
        link: append relative to link.
        newlink: reuse a link, should have been popped.
        """
        if not link:
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
        if not link:
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

    def extend(self, items, link=None):
        """Add items in order after link.

        If link is None, add to end of list.
        """
        self.insert(link[1] if link else None, items)

    def insert(self, link, items, reverse=False):
        """Insert items in order at link position.

        If link is None, then end of list is used.
        NOTE: this is different from list.insert.  It takes an iterable
            of items.  If you only want to add a single item, just use
            appendleft instead.
        """
        if isinstance(link, int):
            link = self(link)
            if link < 0:
                link += self._length
            if link >= self._length:
                link = None
            elif link <= 0:
                link = self.first
            else:
                link = self(link)
        else:
            link = link
        if link:
            pre = link[0]
            if pre:
                n, pre[1], link[0] = self._chain(items, pre, link, reverse)
            else:
                n, self.first, link[0] = self._chain(items, pre, link, reverse)
            self._length += n
        else:
            link = self.last
            if link:
                n, link[1], self.last = self._chain(
                    items, link, None, reverse)
                self._length += n
            else:
                self._length, self.first, self.last = self._chain(
                    items, reverse=reverse)

    def extendleft(self, items, link=None):
        """Note that items will end up in reverse order.

        If link is None, then extend to beginning of list.
        """
        self.insert(link or self.first, items, reverse=True)

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
        firstlink will point to before and lastlink will point to after.
        However, before/after are left unchanged.
        """
        it = iter(items)
        try:
            item = next(it)
        except StopIteration:
            return 0, after, before
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

    def _assign_basic(self, links, items, link):
        try:
            link = next(links)
        except StopIteration:
            self.insert(link, items)
            return
        it = iter(items)
        try:
            # no zip because an extra link would be consumed.
            link[2] = next(it)
            for link in links:
                link[2] = next(it)
        except StopIteration:
            # more links than items
            before = link[0]
            link[0] = link[2] = None
            removed = 1
            pre = link
            for link in links:
                removed += 1
                pre[1] = None
                link[0] = link[2] = None
                pre = link
            self._length -= removed
            after = pre[1]
            pre[1] = None
            if before:
                before[1] = after
            else:
                self.first = after
            if after:
                after[0] = before
            else:
                self.last = before
        else:
            self.insert(link[1], it)

    @staticmethod
    def _assign_extended(links, items, count):
        """Assign to slice with step!=1.

        This requires links and items to have the same length.
        links: Iterable of links.
        items: Items to assign, may be generator
        count: Number of links.
        """
        try:
            nitems = len(items)
        except TypeError:
            items = tuple(items)
            nitems = len(items)
        if nitems != count:
            raise ValueError(
                ('attempt to assign sequence of size {}'
                ' to slice of size {}'.format(nitems, count)))
        for link, item in zip(links, items):
            link[2] = item
