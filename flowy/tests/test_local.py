import inspect
import time
import unittest

from flowy import LocalWorkflow
from flowy import parallel_reduce

try:
    from concurrent.futures import ThreadPoolExecutor
except ImportError:
    from futures import ThreadPoolExecutor


def m(n):
    return n + 1


def r(a, b):
    return a + b


class W(object):
    def __init__(self, m, r):
        self.m = m
        self.r = r

    def __call__(self, n):
        return parallel_reduce(self.r, map(self.m, range(n + 1)))


class TestLocalWorkflow(unittest.TestCase):
    def setUp(self):
        self.sub = LocalWorkflow(W)
        self.sub.conf_activity('m', m)
        self.sub.conf_activity('r', r)

    def test_processes(self):
        main = LocalWorkflow(W)
        main.conf_workflow('m', self.sub)
        main.conf_activity('r', r)
        result = main.run(8, _wait=True)  # avoid broken pipe
        self.assertEquals(result, 165)

    def test_threads(self):
        try:
            from futures import ThreadPoolExecutor
        except ImportError:
            from concurrent.futures import ThreadPoolExecutor
        main = LocalWorkflow(W, executor=ThreadPoolExecutor)
        main.conf_workflow('m', self.sub)
        main.conf_activity('r', r)
        result = main.run(8)
        self.assertEquals(result, 165)


class TestExamples(unittest.TestCase):
    """Since there are time assertions, this tests can generate false
    positives. Changing TIME_SCALE to 1 should fix most of the problems but
    will significantly increase the tests duration."""
    pass


TIME_SCALE = 0.3


def make_t(wf_name, wf):
    def test(self):
        lw = LocalWorkflow(wf,
                           activity_workers=16,
                           workflow_workers=2,
                           executor=ThreadPoolExecutor)
        lw.conf_activity('a', examples.activity)
        start = time.time()
        result = lw.run(TIME_SCALE)
        duration = time.time() - start
        lines = [l.strip() for l in wf.__doc__.split("\n")]
        expected = None
        for line in lines:
            if line.startswith('R '):
                expected = int(line.split()[-1].split("-")[-1])
                break
        self.assertEquals(expected, result)
        for line in lines:
            if line.startswith('Duration:'):
                expected_duration = int(line.split()[-1]) * TIME_SCALE * 0.1
                break
        print(expected_duration, duration)
        self.assertTrue(abs(expected_duration - duration) < TIME_SCALE * 0.9)

    return test


import flowy.examples as examples
for wf_name, wf in vars(examples).items():
    if inspect.isclass(wf) and wf.__module__ == 'flowy.examples':
        setattr(TestExamples, 'test_%s' % wf_name, make_t(wf_name, wf))
