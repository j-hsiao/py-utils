"""Forward binary streams.

Regarding text streams, they are usually buffered because characters
could be multiple bytes.  As a result, accessing the underlying
binary stream will lose the buffered data.
"""
from __future__ import print_function
__all__ = ['Forwarder']

import io
import threading
import traceback
import sys

if sys.version_info.major > 2:
    TEXT_TYPE = str
else:
    TEXT_TYPE = unicode

class Wrapper(object):
    """Wrap a stream to handle proper close/detach."""
    def __init__(self, stream, orig, wrapped):
        """Initialize wrapper.

        stream: file like object
            The stream to use.
        orig: file like object
            The original stream.
        wrapped: bool
            If wrapped, stream.detach() will be called in detach() and
            close().  Otherwise, do nothing.
        """
        self.stream = stream
        self.orig = orig
        self.wrapped = wrapped

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def detach(self):
        """Detach stream if applicable.  Return the original stream."""
        if self.wrapped:
            self.stream.detach()
            self.wrapped = False
        return self.orig

    def close(self):
        """Detach stream if applicable.  Close the original stream."""
        self.detach().close()

def rwpair(istream, ostream):
    """Helper function to wrap istream/ostream to be compatible.

    This takes the safer approach to creating compatible pairs.
    On mismatch, if istream returns strs, then ostream will be
    wrapped with TextIOWrapper.  Even if istream has a buffer attr
    that can be used for binary io which would be more efficient,
    because istream returns strs, it may have buffered data that has
    already left the binary stream.  Streams aren't assumed to be
    seekable, so to avoid data loss, use text.
    On the other hand, if output is text, then it can just be flushed
    before using the underlying binary buffer.
    """
    itype = istream.read(0)
    try:
        ostream.write(itype)
        istream = Wrapper(istream, istream, False)
        ostream = Wrapper(ostream, ostream, False)
    except TypeError:
        if isinstance(itype, TEXT_TYPE):
            istream = Wrapper(istream, istream, False)
            ostream = Wrapper(io.TextIOWrapper(ostream), ostream, True)
        else:
            try:
                ostream.buffer.write(b'')
            except AttributeError:
                istream = Wrapper(io.TextIOWrapper(istream), istream, True)
                ostream = Wrapper(ostream, ostream, False)
            else:
                try:
                    ostream.flush()
                except AttributeError():
                    pass
                istream = Wrapper(istream, istream, False)
                ostream = Wrapper(ostream.buffer, ostream, False)
    ostream.write(istream.read(0))
    return istream, ostream

class Forwarder(object):
    """Forward binary stream to another.

    Data is read and written as chunks in single reads in a separate
    thread.
    """
    def __init__(
        self, istream, ostream, iclose=True, oclose=True,
        flush=False, blocksize=io.DEFAULT_BUFFER_SIZE):
        """Initialize a forwarder.

        istream: file-like object.
            Binary input stream.
        ostream: file-like object.
            Binary output stream.
        blocksize: int
            Size of blocks to transfer between the two streams.
        flush: bool
            Flush after each write?
        iclose: bool
            Close input after end?
        oclose: bool
            Close output after end?
        """
        self.streams = istream, ostream
        self.blocksize = blocksize
        self.doflush = flush
        self.iclose = iclose
        self.oclose = oclose
        self.running = threading.Event()
        self.running.set()
        self.thread = threading.Thread(target=self._loop)
        self.thread.start()

    def _loop(self):
        """Forward data between streams."""
        istream, ostream = rwpair(*self.streams)
        if self.doflush:
            flush = getattr(ostream, 'flush', None)
        else:
            flush = None
        try:
            try:
                readinto = getattr(istream, 'readinto1', istream.readinto)
            except AttributeError:
                self._forward_text(istream.read, ostream.write, flush)
            else:
                self._forward_binary(readinto, ostream.write, flush)
        except Exception:
            pass
        try:
            ostream.flush()
        except AttributeError:
            pass
        if self.iclose:
            istream.close()
        else:
            istream.detach()
        if self.oclose:
            ostream.close()
        else:
            ostream.detach()

    def _forward_binary(self, read, write, flush):
        buf = bytearray(self.blocksize)
        view = memoryview(buf)
        amt = read(view)
        running = self.running.is_set
        while amt and running():
            write(view[:amt])
            if flush is not None:
                flush()
            amt = read(view)

    def _forward_text(self, read, write, flush):
        size = self.blocksize
        data = read(size)
        running = self.running.is_set
        while data and running():
            write(data)
            if flush is not None:
                flush()
            data = read(size)

    def is_alive(self):
        return self.thread.is_alive()

    def join(self):
        """Wait until forwarding is done."""
        self.thread.join()

    def close(self):
        """Set stop flag.

        Does not join thread because it could be stuck on a read.
        """
        self.running.clear()

if __name__ == '__main__':
    i = io.BytesIO(b'secret message')
    o = io.BytesIO()

    def check(istream, ostream):
        wi, wo = rwpair(istream, ostream)
        wo.write(wi.read())
        wo.flush()
        assert o.getvalue() == b'secret message'
        assert wi.detach() is istream
        assert wo.detach() is ostream
        i.seek(0)
        o.seek(0)
        o.truncate()

        f = Forwarder(istream, ostream, False, False)
        f.join()
        assert o.getvalue() == b'secret message'
        i.seek(0)
        o.seek(0)
        o.truncate()

        return istream, ostream

    check(i, o)
    assert check(io.TextIOWrapper(i), o)[0].detach() is i
    assert check(i, io.TextIOWrapper(o))[1].detach() is o
    ti, to = check(io.TextIOWrapper(i), io.TextIOWrapper(o))
    assert ti.detach() is i
    assert to.detach() is o

    import os
    message = '\n'.join(
        ('hello world!', 'goodbye world!', 'whatever')*io.DEFAULT_BUFFER_SIZE)

    check = io.TextIOWrapper(io.BytesIO())
    check.write(message)
    check = check.detach()
    target = check.getvalue()
    check.close()

    rb0, wt0 = os.pipe()
    rt1, wb1 = os.pipe()
    rb2, wt2 = os.pipe()
    rt3, wt3 = os.pipe()
    dst = io.BytesIO()

    inp = os.fdopen(wt0, 'w')
    pairs = [
        (os.fdopen(rb0, 'rb'), os.fdopen(wb1, 'wb')), # binary to binary
        (os.fdopen(rt1, 'r'), os.fdopen(wt2, 'w')), # text to text
        (os.fdopen(rb2, 'rb'), os.fdopen(wt3, 'w')), # binary to text
        (os.fdopen(rt3, 'r'), dst), # text to binary
    ]
    forwarders = [Forwarder(i, o, oclose=o is not dst) for i, o in pairs]

    inp.write(message)
    inp.flush()
    inp.close()

    for forwarder, (i,o) in zip(forwarders, pairs):
        forwarder.join()
        assert i.closed
        if o is dst:
            assert o.getvalue() == target
            o.close()
        else:
            assert o.closed
    print('pass')
