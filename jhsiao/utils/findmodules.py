"""Find submodules given a modulename in commandline

Uses pkgutil.walk_packages
"""
import pkgutil
import importlib

def findmodules(name):
    results = []
    try:
        md = importlib.import_module(name)
    except ImportError:
        return results
    results.append(name)
    try:
        paths = md.__path__
    except AttributeError:
        return results
    else:
        for loader, name, ispkg in pkgutil.walk_packages(paths, name+'.'):
            results.append(name)
    return results
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('module', help='module to search for submodules')
    print('\n'.join(findmodules(p.parse_args().module)))
