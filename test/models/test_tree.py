import unittest

from pview.utilities import ps
from pview.models.tree import ProcessNode

class ProcessTreeTest(unittest.TestCase):
    def test_something(self):
        latest_ps = ps.ProcessStatus()
        process: ps.ProcessEntry = next((
            process
            for process in latest_ps.processes
            if process.memory_percent is not None
               and process.current_cpu_percent is not None
               and process.status == 'running'
        ), None)

        self.assertIsNotNone(process)

        node = ProcessNode.from_entry(entry=process)


if __name__ == '__main__':
    unittest.main()
