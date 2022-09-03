"""File-like io."""
__all__ = ['SeqWriter', 'BytesReader']
import io

class SeqWriter(io.RawIOBase):
    """Wrap a sequence as a write-only file-like object.

    Write calls append() of the sequence.
    """
    def __init__(self, cls=list):
        """Initialize SeqWriter.

        cls: If a type, then use cls(), otherwise
            cls should be a an instance with an append() method.
        Unseekable, and position = total amount written, not necessarily
        total data in sequence. (For example, if cls is
        deque(maxlen!=None))
        """
        if isinstance(cls, type):
            self.data = cls()
        else:
            self.data = cls
        self.pos = 0

    def writable(self):
        return True
    def readable(self):
        return False
    def seekable(self):
        return False

    def write(self, data):
        self.data.append(data)
        dlen = len(data)
        self.pos += dlen
        return dlen
    def seek(self, pos, whence=None):
        raise io.UnsupportedOperation
    def tell(self):
        return self.pos

    def isatty(self):
        return False
    def close(self):
        self.data = None
        super(SeqWriter, self).close()
    def fileno(self):
        raise OSError("SeqWriter has no fileno.")
    def flush(self):
        pass

class BytesReader(io.RawIOBase):
    """Use a bytes as contents of a file (readonly).

    Basically an io.BytesIO() except it does not copy
    data and is not writable.
    """
    def __init__(self, data):
        """Initialize BytesReader

        data: the data to wrap.
        memviews: Return memoryviews when reading to reduce copies.
        """
        self.data = memoryview(data)
        self.pos = 0

    def writable(self):
        return False
    def readable(self):
        return True
    def seekable(self):
        return True

    def read(self, size=-1):
        return self.readview(size).tobytes()
    def readview(self, size=-1):
        data = self.data
        pos = self.pos
        dlen = len(data)
        if size is None or size < 0:
            ret = data[pos:]
            self.pos = dlen
            return ret
        end = min(pos+size, dlen)
        ret = data[pos:end]
        self.pos = end
        return ret

    def readinto(self, buf):
        pos = self.pos
        data = self.data
        size = min(len(buf), len(data)-pos)
        buf[:size] = data[pos:pos+size]
        self.pos += size
        return size

    def readall(self):
        return self.read()

    def truncate(self, size):
        """Just slice data and make another fobj."""
        raise NotImplementedError
    def seek(self, pos, whence=io.SEEK_SET):
        dlen = len(self.data)
        if whence == io.SEEK_CUR:
            pos += self.pos
        elif whence == io.SEEK_END:
            pos += dlen
        self.pos = max(min(dlen, pos), 0)
        return self.pos
    def tell(self):
        return self.pos

    def isatty(self):
        return False
    def close(self):
        self.data = None
        super(BytesReader, self).close()
    def fileno(self):
        raise OSError("BytesReader has no fileno.")
    def flush(self):
        pass

if __name__ == '__main__':
    msg = b'hello world!\ngoodbye world!'
    with BytesReader(msg) as f:
        assert list(f) == msg.splitlines(True)
        f.seek(0)
        assert list(f) == msg.splitlines(True)
        f.seek(0, io.SEEK_END)
        assert list(f) == []
        f.seek(-2, io.SEEK_END)
        assert list(f) == [b'd!']

    with SeqWriter() as f:
        f.write(b'hello')
        f.write(b'world')
        f.writelines([b'hello world!', b'goodbye world!'])
        assert f.data == [b'hello', b'world', b'hello world!', b'goodbye world!']

    import collections
    with SeqWriter(collections.deque(maxlen=2)) as f:
        f.writelines('hello world')
        assert list(f.data) == ['l', 'd']
    import pickle
    item = [1, 3.14, ('a', b'b'), dict(a=1, b=2, c=3.14, d=None)]
    with SeqWriter() as f:
        pickle.dump(item, f)
        assert pickle.loads(b''.join(f.data)) == item
    print('pass')
