"""Forwarding data from stream to stream.

Streams should implement file api, namely
read/readinto and write
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

def _readfunc(f, bufsize, linebuf=False):
    """Return a func to obtain data.

    Order of preference is readinto1, readinto (if binary stream),
    then read1 and lastly read.
    The func may return a memoryview/buffer or bytes if binary else str
    if text.
    """
    if linebuf:
        return f.readline
    if not isinstance(f.read(0), TEXT_TYPE):
        buf = bytearray(bufsize)
        view = memoryview(buf)
        try:
            readinto = getattr(f, 'readinto1', f.readinto)
        except AttributeError:
            pass
        else:
            if sys.version_info.major > 2:
                return lambda : view[:readinto(buf)]
            else:
                return lambda : buffer(buf, 0, readinto(buf))
    read = getattr(f, 'read1', f.read)
    return lambda : read(bufsize)

def _flushed_write(f, flush):
    """Return corresponding write function.

    Auto flush after every write if flush.  Assume f is buffered.
    """
    if flush:
        _write = f.write
        _flush = f.flush
        def write(data):
            ret = _write(data)
            _flush()
            return ret
        return write
    else:
        return f.write

class Forwarder(object):
    """Forward data from one file-like object to another.

    Streams are assumed to be io.BufferedIOBase subclasses.
    In other words, writes should be buffered and auto-repeat if
    fewer bytes were written in a single call.
    """
    def __init__(
        self, istream, ostream,
        blocksize=io.DEFAULT_BUFFER_SIZE,
        flush=False, linebuf=False):
        """Initialize file forwarding.

        istream/ostream: input/output stream, read() is required
            for input but readinto is preferred.  write() and
            flush() are required for output.
        blocksize: reading blocksize.
        flush: flush after every write if True.
        """
        self._e = threading.Event()
        # hold a reference to original so if this is the last
        # reference it doesn't close its buffer if applicable.
        self.orig = istream, ostream
        self.streams = istream, ostream = self._match_streams(
            istream, ostream)
        self.read = _readfunc(istream, blocksize, linebuf)
        self.write = _flushed_write(ostream, flush)
        self.flush = ostream.flush
        # 1 thread per pair is most cross-platform.
        # select/poll/epoll can't be used on files on windows.
        self._thread = None

    def start(self):
        """Start thread and return self."""
        if self._thread is None:
            self._e.set()
            self._thread = threading.Thread(target=self._loop)
            self._thread.start()
        return self

    def _match_streams(self, istream, ostream):
        """Match the [byte/str]ness of the streams.

        Return istream, ostream, possibly wrapped/unwrapped.
        """
        check = istream.read(0)
        try:
            ostream.write(check)
        except TypeError:
            # mismatched read/write types
            if isinstance(check, TEXT_TYPE):
                # reading text, but writing binary
                try:
                    # If istream has binary buffer attr,
                    # write to it
                    ostream.write(istream.buffer.read(0))
                except (AttributeError, TypeError):
                    # must convert text to binary
                    ostream = io.TextIOWrapper(ostream)
                else:
                    istream = istream.buffer
            else:
                # reading binary, writing text
                try:
                    # If outstream has binary buffer attr
                    # write to it
                    ostream.buffer.write(check)
                except (AttributeError, TypeError):
                    # must convert binary to text
                    istream = io.TextIOWrapper(istream)
                else:
                    ostream = ostream.buffer
        return (istream, ostream)

    def _loop(self):
        """Write from istream to ostream and flush."""
        read = self.read
        write = self.write
        data = read()
        e = self._e
        try:
            while data and e.is_set():
                write(data)
                data = read()
            if data:
                write(data)
        except EnvironmentError:
            pass
        try:
            self.flush()
        except EnvironmentError:
            pass

    def is_alive(self):
        if self._thread is not None:
            return self._thread.is_alive()
        return False

    def join(self):
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def stop(self):
        if self._thread is not None:
            self._e.clear()
            self.join()

    def close(self, i=True, o=True):
        """Stop and close the forwarder.

        i,o: if True, close the streams, otherwise, detach them
            if applicable.
        """
        if not self.streams:
            return
        self.stop()
        oi, oo = self.orig
        si, so = self.streams
        if i:
            try:
                si.close()
            except Exception:
                pass
        elif si is not oi and si is not getattr(oi, 'buffer', oi):
            si.detach()
        if o:
            try:
                so.close()
            except Exception:
                pass
        elif so is not oo and so is not getattr(oo, 'buffer', oo):
            so.detach()
        self.streams = None

if __name__ == '__main__':
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
    forwarders = [Forwarder(i, o, flush=True).start() for i, o in pairs]

    inp.write(message)
    inp.flush()
    inp.close()

    closechecks = [(True,True), (True,False), (False,True), (False,False)]
    for i, (forwarder, (i,o), close) in enumerate(zip(forwarders, pairs, closechecks)):
        forwarder.join()
        if o is dst:
            assert o.getvalue() == target
            print('final output success')
        closein, closeout = close
        forwarder.close(closein, closeout)
        # need to close or not joinable
        assert i.closed == closein
        assert o.closed == closeout
        if not closein:
            i.close()
        if not closeout:
            o.close()

    for forwarder in forwarders:
        assert not forwarder.is_alive()
    print('pass')
