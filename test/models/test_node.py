import unittest

from pview.models.tree import ProcessNode
from pview.utilities import ps


class ProcessNodeTest(unittest.TestCase):
    def test_something(self):
        latest_ps = ps.ProcessStatus()

        self.assertGreater(len(latest_ps), 0)

        process: ps.ProcessEntry = latest_ps.processes[0]

        self.assertIsNotNone(process)
        node = ProcessNode.from_entry(entry=process)
        self.assertEqual(len(node), 1)

        for process in latest_ps:
            node.add_entry(process)

        self.assertEqual(len(node), len(latest_ps))


if __name__ == '__main__':
    unittest.main()
