"""Make closures"""
__all__ = ['Code']
import itertools

class Code(object):
    def __init__(self, code, indent='    ', raw=True, mindent=None):
        """Initialize a code object.

        code: sequence of lines of code.  The lines could have
            newlines or not.
        indent: the indentation to use.
        raw: code is raw code, not preprocessed by the Code class.
        mindent: lowest indent level.

        Internal code is represented as an indent level and codeline
        tuple.
        """
        self.indentation = indent
        if raw:
            if isinstance(code, str):
                code = code.splitlines()
            strippeds = [l.lstrip() for l in code]
            splits = [
                (l[:len(l) - len(stripped)], stripped)
                for l, stripped in zip(code, strippeds) if stripped]
            self.code = []
            for l, stripped in zip(code, strippeds):
                if not stripped:
                    continue
                pre = l[:len(l) - len(stripped)]
                pos = 0
                ilen = len(indent)
                while pre.startswith(indent, pos):
                    pos += ilen
                if pos != len(pre):
                    raise ValueError('bad indent: {}'.format(repr(l)))
                level = len(pre) // ilen
                self.code.append([level, stripped])
        else:
            self.code = code
        if mindent is None:
            self.mindent = min([lvl for lvl,line in self.code])
        else:
            self.mindent = mindent

    def __iter__(self):
        """Iterate over chunks."""
        ind = self.indentation
        for lvl, line in self.code:
            for i in range(lvl):
                yield ind
            yield line
            if not line.endswith('\n'):
                yield '\n'

    def __str__(self):
        return ''.join(self)

    def indent(self):
        """Increase indentation level."""
        for item in self.code:
            item[0] += 1
        self.mindent += 1

    def dedent(self, force=False):
        """Decrease indentation level."""
        if not self.mindent:
            raise ValueError("Tried to dedent past 0")
        self.mindent -= 1
        for item in self.code:
            item[0] = max(item[0]-1, 0)

    def __add__(self, code):
        """Add new code lines to end."""
        cp = Code(
            list(map(list, self.code)),
            self.indentation, False, self.mindent)
        cp += code
        return code

    def __radd__(self, code):
        if isinstance(code, Code):
            return NotImplemented
        try:
            code = Code(code, indent=self.indentation)
        except Exception:
            return NotImplemented
        else:
            code += self
            return code

    def __iadd__(self, code):
        if isinstance(code, Code):
            if code.indentation != self.indentation:
                raise ValueError((
                    'Tried to concatenate code with different indentations'
                    '{!r} vs {!r}').format(self.indentation, code.indentation))
            self.code.extend(map(list, code.code))
        else:
            code = Code(code, self.indentation)
            self.code.extend(code.code)
        self.mindent = min(self.mindent, code.mindent)
        return self

    def prepend(self, code):
        if isinstance(code, Code):
            ncode = list(map(list, code.code))
            ncode.extend(self.code)
            self.code = ncode
        else:
            code = Code(code)
            code.code.extend(self.code)
            self.code = code.code
        self.mindent = min(self.mindent, code.mindent)

    def append(self, code):
        self += code

    def make_closure(self, variables):
        """Create a closure with the given variables."""
        deflvl, defline = self.code[0]
        if deflvl or not defline.startswith('def'):
            raise ValueError(
                'closure expects code to start with "def", but got {!r}'.format(
                    self.indentation*deflvl + defline))
        funcname = defline[4:defline.index('(')]
        code = Code([[0, 'def maker():']], self.indentation, False, 0)
        code.code.extend(
            [[1, '{0} = variables["{0}"]'.format(v)] for v in variables])
        code.code.extend([[lvl+1, line] for lvl, line in self.code])
        code.code.extend((
            [1, 'return {}'.format(funcname)],
            [0, 'func = maker()']))
        globs = {'variables': variables}
        exec(str(code), globs)
        return globs['func']

if __name__ == '__main__':
    func = '''
def closure1():
    return a
'''
    f1 = Code(func.strip().splitlines()).make_closure(dict(a=5))
    f2 = Code(func).make_closure(dict(a=69))
    f3 = Code(func.strip().splitlines(keepends=True)).make_closure(dict(a=42))
    print(f1, f1())
    print(f2, f2())
    print(f3, f3())
