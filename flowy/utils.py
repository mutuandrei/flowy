import itertools
import logging
import sys

from flowy.result import SuspendTask
from flowy.result import wait

try:
    import repr as r
except ImportError:
    import reprlib as r


__all__ = ['logger', 'sentinel', 'setup_default_logger', 'i_or_args',
           'short_repr', 'scan_args', 'caller_module']


logger = logging.getLogger(__name__.split('.', 1)[0])
sentinel = object()


def setup_default_logger():
    """Configure the default logger for Flowy."""
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s\t%(name)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel('INFO')
    logger.propagate = False


def i_or_args(result, results):
    if len(results) == 0:
        return iter(result)
    return (result, ) + results


class ShortRepr(r.Repr):
    def __init__(self):
        self.maxlevel = 1
        self.maxtuple = 4
        self.maxlist = 4
        self.maxarray = 4
        self.maxdict = 4
        self.maxset = 4
        self.maxfrozenset = 4
        self.maxdeque = 4
        self.maxstring = self.maxlong = self.maxother = 16

    def repr_dict(self, x, level):
        n = len(x)
        if n == 0: return '{}'
        if level <= 0: return '{...}'
        newlevel = level - 1
        repr1 = self.repr1
        pieces = []
        for key in itertools.islice(r._possibly_sorted(x), self.maxdict):
            keyrepr = repr1(key, newlevel)
            valrepr = repr1(x[key], newlevel)
            pieces.append('%s: %s' % (keyrepr, valrepr))
        if n > self.maxdict: pieces.append('...')
        s = ',\n'.join(pieces)
        return '{%s}' % (s, )

    def _repr_iterable(self, x, level, left, right, maxiter, trail=''):
        n = len(x)
        if level <= 0 and n:
            s = '...'
        else:
            newlevel = level - 1
            repr1 = self.repr1
            pieces = [repr1(elem, newlevel) for elem in itertools.islice(x, maxiter)]
            if n > maxiter: pieces.append('...')
            s = ',\n'.join(pieces)
            if n == 1 and trail: right = trail + right
        return '%s%s%s' % (left, s, right)


short_repr = ShortRepr()


def scan_args(args, kwargs):
    errs = []
    placeholders = False
    for result in args:
        try:
            wait(result)
        except SuspendTask:
            placeholders = True
        except Exception:
            errs.append(result)
    for key, result in kwargs.items():
        try:
            wait(result)
        except SuspendTask:
            placeholders = True
        except Exception:
            errs.append(result)
    return errs, placeholders


# Stolen from Pyramid
def caller_module(level=2, sys=sys):
    module_globals = sys._getframe(level).f_globals
    module_name = module_globals.get('__name__') or '__main__'
    module = sys.modules[module_name]
    return module


def caller_package(level=2, caller_module=caller_module):
    # caller_module in arglist for tests
    module = caller_module(level + 1)
    f = getattr(module, '__file__', '')
    if (('__init__.py' in f) or ('__init__$py' in f)):  # empty at >>>
        # Module is a package
        return module  # pragma: no cover
    # Go up one level to get package
    package_name = module.__name__.rsplit('.', 1)[0]
    return sys.modules[package_name]
