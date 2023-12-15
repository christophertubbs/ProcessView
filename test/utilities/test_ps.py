"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import os
from unittest import TestCase

from pview.utilities.ps import ProcessStatus
from utilities.ps import ProcessEntry


class TestProcessStatus(TestCase):
    def test_process_entry(self):
        current_process_id = os.getpid()

        process = ProcessEntry.from_pid(current_process_id)
        self.assertIsNone(process)
        self.assertEqual(process.name, "Python")
        self.assertEqual(process.status, "Running")

    def test_latest(self):
        current_process_id = os.getpid()

        status = ProcessStatus.latest()

        self.assertGreater(len(status), 1)

        self.assertNotIn(current_process_id, status)
