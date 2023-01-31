"""Find submodules given a modulename in commandline

Uses pkgutil.walk_packages
"""
import pkgutil
import importlib

def findmodules(name):
    results = []
    try:
        paths = importlib.import_module(name).__path__
    except (AttributeError, ImportError):
        return
    else:
        results.append(name)
        for item in pkgutil.walk_packages(paths, name+'.'):
            results.append(item.name)
    return results
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('module', help='module to search for submodules')
    print('\n'.join(findmodules(p.parse_args().module)))
