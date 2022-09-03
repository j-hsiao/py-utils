"""xml utils."""
from xml.etree.ElementTree import ElementTree

def indent(item, space='  ', level=0):
    """breadth first, no need for list cache.

    Handles some unhandled situations from ElementTree.indent in 3.9+
    (Though only seen if not short_empty_elements...)
    """
    if level < 0:
        raise ValueError('Bad level, must be >= 0')
    if isinstance(item, ElementTree):
        item = item.getroot()

    tailindent = '\n' + space*level
    if item.tail and not item.tail.strip():
        item.tail=tailindent
    if not len(item):
        if item.text and not item.text.strip():
            item.text = None
        return
    textindent = tailindent+space
    if not item.text or not item.text.strip():
        item.text = textindent
    for child in item:
        change = not child.tail or not child.tail.strip()
        if change:
            child.tail = textindent
    if change:
        child.tail = tailindent
    items = list(item)
    while items:
        tailindent = textindent
        textindent += space
        nitems = []
        for child in items:
            if len(child):
                if not child.text or not child.text.strip():
                    child.text = textindent
                for cchild in child:
                    change = not cchild.tail or not cchild.tail.strip()
                    if change:
                        cchild.tail = textindent
                if change:
                    cchild.tail = tailindent
                nitems.extend(child)
            else:
                if child.text and not child.text.strip():
                    child.text = None
        items = nitems

if __name__ == '__main__':
    import xml.etree.ElementTree as et
    import sys
    import io
    check='''
    <xml>
        <someEmptyItemButSpaced>
        </someEmptyItemButSpaced>
    </xml>'''
    if sys.version_info >= (3,9):
        with io.StringIO(check) as f:
            tree = et.parse(f)
            et.indent(tree)
            print('standard lib')
            tree.write(sys.stdout, short_empty_elements=False, encoding='unicode')

        with io.StringIO(check) as f:
            tree = et.parse(f)
            indent(tree)
            print('mine')
            tree.write(sys.stdout, short_empty_elements=False, encoding='unicode')

