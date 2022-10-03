"""Make closures"""
import itertools

def make_closure(definition, variables, stripped=False):
    """Make a closure dynamically.

    definition: list of lines or a single str.  Code that would define
        a function.
    variables: dict of variables to close over.
    stripped: If definition is a list of lines, True if line endings are
        stripped/removed.
    """

    if isinstance(definition, str):
        definition = definition.lstrip()
        defline = definition[:definition.index('(')+1]
        definition = ['\n    ', definition.replace('\n', '\n    ')]
    else:
        if stripped:
            sep = '\n    '
        else:
            sep = '    '
        definition = list(
            itertools.chain.from_iterable(
                zip(
                    itertools.chain(('\n    ',), itertools.repeat(sep)),
                    filter(None, definition))))
        defline = definition[1]
    if not defline.startswith('def '):
        raise Exception('lines should start with def')
    funcname = defline[4:defline.index('(')]
    code = ['def maker():']
    for var in variables:
        code.append("\n    {0} = variables['{0}']".format(var))

    code.extend(definition)
    if not code[-1].endswith('\n'):
        code.append('\n')
    code.append((
        '    return {}\n'
        'func = maker()\n').format(funcname))
    globs = dict(variables=variables)
    print(''.join(code))
    exec(''.join(code), globs)
    return globs['func']


if __name__ == '__main__':
    func = '''
def closure1():
    return a
'''
    f1 = make_closure(func.strip().splitlines(), dict(a=5), stripped=True)
    f2 = make_closure(func, dict(a=42))
    f3 = make_closure(func.lstrip().splitlines(keepends=True), dict(a=243))
    print(f1, f1())
    print(f2, f2())
    print(f3, f3())
