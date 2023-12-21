import unittest
import os

import psutil

from messages.responses.process import QueryArg
from pview.messages.responses.process import ProcessInformation


class ProcessTests(unittest.TestCase):
    def test_creation(self):
        master_process = psutil.Process(1)
        response = ProcessInformation.from_process(master_process)
        self.assertIsNotNone(response)

        this_process_id = os.getpid()
        parent_process_id = os.getppid()

        this_process = psutil.Process(this_process_id)
        self.assertIsNotNone(this_process)

        response = ProcessInformation.from_process(this_process)
        self.assertIsNotNone(response)

    def test_serialization(self):
        pass

    def test_query_args(self):
        query = QueryArg("pid", 1, ">")
        processes = [process for process in psutil.process_iter() if query(process)]
        self.assertGreater(len(processes), 0)

        this_process = [
            process
            for process in psutil.process_iter()
            if QueryArg.query(process, {"field": "pid", "comparator": os.getpid()})
        ]

        self.assertEqual(len(this_process), 1)


if __name__ == '__main__':
    unittest.main()
