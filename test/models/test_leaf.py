import unittest

from pview.utilities import ps
from pview.models.tree import ProcessLeaf
from pview.models.tree import Sunburst

class TestProcessLeaf(unittest.TestCase):
    def test_creation(self):
        latest_ps = ps.ProcessStatus()
        process: ps.ProcessEntry = next((
            process
            for process in latest_ps.processes
            if process.memory_percent is not None
               and process.current_cpu_percent is not None
               and process.status == 'running'
        ), None)

        self.assertIsNotNone(process)

        leaf = ProcessLeaf.from_entry(process)

        self.assertEqual(leaf.process_id, process.process_id)
        self.assertEqual(leaf.parent_process_id, process.parent_process_id)
        self.assertEqual(leaf.name, process.name)
        self.assertEqual(leaf.state, process.status)
        self.assertEqual(leaf.command, process.executable)

        self.assertEqual(
            leaf.get_sunburst_data(),
            [{
                Sunburst.ids_key(): leaf.process_id,
                Sunburst.parent_key(): '',
                Sunburst.values_key(): leaf.memory_usage,
                Sunburst.names_key(): leaf.name
            }]
        )

        sunburst = Sunburst()

        leaf.add_sunburst_data(sunburst=sunburst)

        copied_leaf: ProcessLeaf = leaf.duplicate()

        self.assertEqual(leaf.process_id, copied_leaf.process_id)
        self.assertEqual(leaf.parent_process_id, copied_leaf.parent_process_id)
        self.assertEqual(leaf.cpu_percent, copied_leaf.cpu_percent)
        self.assertEqual(leaf.memory_percent, copied_leaf.memory_percent)
        self.assertEqual(leaf.memory_usage, copied_leaf.memory_usage)
        self.assertEqual(leaf.memory_amount, copied_leaf.memory_amount)
        self.assertEqual(leaf.state, copied_leaf.state)
        self.assertEqual(leaf.user, copied_leaf.user)
        self.assertEqual(leaf.name, copied_leaf.name)
        self.assertEqual(leaf.state, copied_leaf.state)
        self.assertEqual(leaf.command, copied_leaf.command)
        self.assertEqual(leaf.arguments, copied_leaf.arguments)

        process.process_id = 932923
        leaf.add_instance(process)

        self.assertEqual(leaf.count, 2)
        self.assertEqual(len(leaf.process_id), 2)
        self.assertEqual(leaf.memory_percent, copied_leaf.memory_percent * 2)
        self.assertEqual(leaf.memory_usage, copied_leaf.memory_usage * 2)
        self.assertEqual(leaf.cpu_percent, copied_leaf.cpu_percent * 2)
        self.assertEqual(leaf.command, copied_leaf.command)
        self.assertEqual(leaf.arguments, copied_leaf.arguments)
        self.assertEqual(leaf.name, copied_leaf.name)



if __name__ == '__main__':
    unittest.main()
