import argparse

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('formatter_class', argparse.ArgumentDefaultsHelpFormatter)
        super(ArgumentParser, self).__init__(*args, **kwargs)
