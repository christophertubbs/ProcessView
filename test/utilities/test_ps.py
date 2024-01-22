"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import os
from unittest import TestCase

from pview.utilities.ps import ProcessStatus
from utilities.ps import ProcessEntry
from pview.utilities.ps import PSTableGenerator


def get_user_key() -> str:
    return "USER"


def get_username() -> str:
    return os.environ.get(get_user_key())


class TestProcessStatus(TestCase):
    def test_process_entry(self):
        current_process_id = os.getpid()

        process = ProcessEntry.from_pid(current_process_id)
        self.assertIsNotNone(process)
        self.assertEqual(process.name, "Python")
        self.assertEqual(process.status, "running")

    def test_latest(self):
        current_process_id = os.getpid()

        status = ProcessStatus.latest()

        self.assertGreater(len(status), 1)

        self.assertNotIn(current_process_id, status)

    def test_pstable(self):
        table = PSTableGenerator()
        processes = table.create_process_list()

        required_columns = [
            table.process_id_column(),
            table.parent_process_id_column(),
            table.command_column(),
            table.arguments_column(),
            table.state_column(),
            table.cpu_percent_column(),
            table.memory_percent_column(),
            table.memory_column(),
        ]

        for process in processes:
            for required_column in required_columns:
                self.assertIn(
                    required_column,
                    process,
                    f"Data is missing in the {required_column} column."
                )

        current_process_id = os.getpid()

        matching_processes = [
            process
            for process in processes
            if process[table.process_id_column()] == current_process_id
        ]

        self.assertEqual(len(matching_processes), 1)

        frame = table.create_frame()

        for required_column in required_columns:
            self.assertIn(required_column, frame.columns)
            self.assertTrue(
                frame[required_column].notna().all(),
                f"Data is missing in the {required_column} column."
            )

        rows_that_match_current_process = frame[table.process_id_column()] == current_process_id
        current_process = frame[rows_that_match_current_process]

        self.assertEqual(len(current_process), 1)

        current_process_is_owned_by_current_user = (current_process[table.user_column()] == get_username()).all()
        self.assertTrue(current_process_is_owned_by_current_user)

        entries = table.create_entries()
        self.assertGreater(len(entries), 1)

