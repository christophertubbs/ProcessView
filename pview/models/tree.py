"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import typing
from enum import Enum

from pydantic import BaseModel
from pydantic import Field

from utilities.ps import ProcessEntry


class ProcessState(Enum):
    IDLE = "I"
    RUNNABLE = "R"
    SLEEPING = "S"
    SLEEPING_IN_FOREGROUND = "S+"
    SLEEPING_SESSION_LEADER = "Ss"
    STOPPED = "T"
    UNINTERRUPTIBLE_WAIT = "U"
    ZOMBIE = "Z"


class ProcessLeaf(BaseModel):
    process_id: int
    parent_process_id: int
    cpu_percent: float
    memory_usage: float
    memory_percent: float
    memory_amount: str
    state: str
    user: str
    thread_count: int
    open_file_count: int
    file_descriptor_count: int
    command: str
    arguments: typing.List[str]

    @classmethod
    def from_entry(cls, entry: ProcessEntry) -> ProcessLeaf:
        return ProcessLeaf(
            process_id=entry.process_id,
            parent_process_id=entry.parent_process_id,
            cpu_percent=entry.current_cpu_percent,
            memory_usage=entry.memory_usage,
            memory_percent=entry.memory_percent,
            memory_amount=entry.memory_amount,
            state=entry.status,
            user=entry.user,
            thread_count=entry.thread_count,
            open_file_count=entry.open_file_count,
            file_descriptor_count=entry.file_descriptor_count,
            command=entry.executable,
            arguments=entry.arguments
        )

    @property
    def count(self) -> int:
        return 1


class ProcessNode(BaseModel):
    node_id: str
    name: str
    depth: typing.Optional[int] = Field(default=1)
    children: typing.Optional[typing.List[typing.Union[ProcessNode, ProcessLeaf]]] = Field(default_factory=list)

    def get_child_node_by_name(self, name: str) -> typing.Optional[ProcessNode]:
        candidates = [
            child
            for child in self.children
            if isinstance(child, ProcessNode)
               and child.name == name
        ]
        return candidates[0] if candidates else None

    def add_entry(self, entry: ProcessEntry):
        if self.depth == len(entry.executable_parts):
            leaf = ProcessLeaf.from_entry(entry)
            self.children.append(leaf)
        else:
            name = entry.executable_parts[self.depth]
            matching_child_node = self.get_child_node_by_name(name)

            if matching_child_node:
                matching_child_node.add_entry(entry)
            else:
                new_node_id = f"{self.node_id}.{name}"
                new_node = ProcessNode(node_id=new_node_id, name=name, depth=self.depth + 1)
                self.children.append(new_node)
                new_node.add_entry(entry)

    @property
    def count(self) -> int:
        child_count = sum([
            child.count
            for child in self.children
        ])
        return child_count


class ProcessTree(BaseModel):
    children: typing.List[ProcessNode] = Field(default_factory=list)



    def add_entry(self, entry: ProcessEntry):