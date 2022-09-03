class Base(object):
    def __init__(self):
        print('__init__ recalled')
        type(self).__new__ = lambda cls: self
        type(self).__init__ = lambda self: None
    def __repr__(self):
        return type(self).__name__

if __name__ == '__main__':
    import sentinel
    class whatever(object):
        class MySentinel(sentinel.Base): pass
        sentinel = MySentinel()
        pass
    import pickle
    assert pickle.loads(pickle.dumps(whatever.sentinel)) is whatever.sentinel
    print('pass')
    print(whatever.sentinel)
