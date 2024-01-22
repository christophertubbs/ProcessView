import unittest

from models.tree import ProcessTree
from pview.utilities import ps
from pview.models.tree import ProcessNode

class ProcessTreeTest(unittest.TestCase):
    def test_something(self):
        latest_ps = ps.ProcessStatus()

        self.assertGreater(len(latest_ps), 0)

        process: ps.ProcessEntry = latest_ps.processes[0]

        self.assertIsNotNone(process)

        tree = ProcessTree.load()

        sunburst = tree.get_sunburst_data()
        markup = sunburst.plot()
        self.assertTrue(isinstance(markup, str))


if __name__ == '__main__':
    unittest.main()
