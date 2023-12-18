"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import typing

from pydantic import BaseModel
from pydantic import Field

from plotly import express
from plotly import graph_objects
from pydantic import PrivateAttr

from utilities.ps import ProcessEntry
from utilities.ps import byte_size_to_text

SEPARATOR = "/"


class ProcessLeaf(BaseModel):
    process_id: typing.Union[int, typing.MutableSequence[int]]
    parent_process_id: int
    cpu_percent: typing.Optional[float] = Field(default=None)
    memory_usage: typing.Optional[float] = Field(default=None)
    memory_percent: typing.Optional[float] = Field(default=None)
    memory_amount: typing.Optional[str] = Field(default=None)
    state: str
    user: str
    thread_count: typing.Optional[int] = Field(default=1)
    open_file_count: typing.Optional[int] = Field(default=0)
    file_descriptor_count: typing.Optional[int] = Field(default=0)
    command: str
    arguments: typing.Optional[typing.Union[typing.List[str], str]] = Field(default_factory=list)
    name: str
    instance_count: int = Field(default=1)
    _parent: typing.Optional[typing.Union[ProcessNode, ProcessTree]] = PrivateAttr(default=None)

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
            command=entry.executable or entry.name,
            arguments=entry.arguments,
            name=entry.name
        )

    def add_instance(self, entry: ProcessEntry):
        if entry.process_id == self.process_id:
            return

        if isinstance(self.process_id, int):
            self.process_id = [self.process_id]

        self.process_id.append(entry.process_id)

        if self.cpu_percent is not None and entry.current_cpu_percent is not None:
            self.cpu_percent += entry.current_cpu_percent
        elif entry.current_cpu_percent is not None:
            self.cpu_percent = entry.current_cpu_percent

        if self.memory_usage is not None and entry.memory_usage is not None:
            self.memory_usage += entry.memory_usage
        elif entry.memory_usage is not None:
            self.memory_usage = entry.memory_usage

        if self.memory_percent is not None and entry.memory_percent is not None:
            self.memory_percent += entry.memory_percent
        elif entry.memory_percent is not None:
            self.memory_percent = entry.memory_percent

        if self.thread_count is not None and entry.thread_count is not None:
            self.thread_count += entry.thread_count
        elif entry.thread_count is not None:
            self.thread_count = entry.thread_count

        if self.open_file_count is not None and entry.open_file_count is not None:
            self.open_file_count += entry.open_file_count
        elif entry.open_file_count is not None:
            self.open_file_count = entry.open_file_count

        if self.file_descriptor_count is not None and entry.file_descriptor_count is not None:
            self.file_descriptor_count += entry.file_descriptor_count
        elif entry.file_descriptor_count is not None:
            self.file_descriptor_count = entry.file_descriptor_count

        self.instance_count += 1

    @property
    def parent(self) -> typing.Optional[typing.Union[ProcessNode, ProcessTree]]:
        return self._parent

    @parent.setter
    def parent(self, parent_object: typing.Union[ProcessNode, ProcessTree]):
        if not isinstance(parent_object, (ProcessNode, ProcessTree)):
            raise TypeError(f"The parent of a ProcessNode may only be another ProcessNode or the Tree")

        self._parent = parent_object

    @property
    def count(self) -> int:
        return self.instance_count

    def __len__(self):
        return self.count

    def copy_leaf(self) -> ProcessLeaf:
        return ProcessLeaf(
            process_id=self.process_id,
            parent_process_id=self.parent_process_id,
            cpu_percent=self.cpu_percent,
            memory_usage=self.memory_usage,
            memory_percent=self.memory_percent,
            memory_amount=self.memory_amount,
            state=self.state,
            user=self.user,
            thread_count=self.thread_count,
            open_file_count=self.open_file_count,
            file_descriptor_count=self.file_descriptor_count,
            command=self.command,
            arguments=self.arguments,
            name=self.name
        )

    def get_sunburst_data(self, value_attribute: str = None) -> typing.Dict[
        typing.Literal["path", "parent", "value"],
        typing.Union[typing.MutableSequence[str], typing.MutableSequence[float], typing.MutableSequence[int]]
    ]:
        if not value_attribute:
            value_attribute = "memory_usage"
        elif not hasattr(self, value_attribute):
            raise ValueError(f"'{value_attribute}' is not a member of of {self} - it may not be used as a value")
        elif not isinstance(getattr(self, value_attribute), (str, float, int)):
            raise TypeError(
                f"The '{value_attribute}' value ({getattr(self, value_attribute)}: "
                f"{type(getattr(self, value_attribute))}) is not a valid value - it must be either a "
                f"string, float, or integer"
            )

        value = getattr(self, value_attribute)
        return {
            "path": [self.name],
            "parent": [self._parent.name if self._parent else ''],
            "value": [value]
        }

    @property
    def top(self) -> typing.Optional[ProcessNode, ProcessTree]:
        if self._parent is None:
            return None
        return self._parent.top

    def __str__(self):
        return f"{self.command} {' '.join(self.arguments)}"


class ProcessNode(BaseModel):
    node_id: str
    name: str
    depth: typing.Optional[int] = Field(default=1)
    children: typing.Optional[typing.List[typing.Union[ProcessNode, ProcessLeaf]]] = Field(default_factory=list)
    _parent: typing.Optional[typing.Union[ProcessNode, ProcessTree]] = PrivateAttr(default=None)

    def get_sunburst_data(self, value_attribute: str = None) -> typing.Dict[
        typing.Literal["path", "parent", "value"],
        typing.Union[typing.MutableSequence[str], typing.MutableSequence[float], typing.MutableSequence[int]]
    ]:
        sunburst_data: typing.Dict[
            typing.Literal["path", "parent", "value"],
            typing.Union[typing.MutableSequence[str], typing.MutableSequence[float], typing.MutableSequence[int]]
        ] = {
            "path": [],
            "parent": [],
            "value": []
        }

        for _, _, leaves in self.walk():
            child_data = [
                leaf.get_sunburst_data(value_attribute=value_attribute)
                for leaf in leaves
            ]

            for child_sunburst_data in child_data:
                sunburst_data['path'].extend(child_sunburst_data['path'])
                sunburst_data['parent'].extend(child_sunburst_data['parent'])
                sunburst_data['value'].extend(child_sunburst_data['value'])

        return sunburst_data

    @property
    def parent(self) -> typing.Optional[typing.Union[ProcessNode, ProcessTree]]:
        return self._parent

    @parent.setter
    def parent(self, parent_object: typing.Union[ProcessNode, ProcessTree]):
        if not isinstance(parent_object, (ProcessNode, ProcessTree)):
            raise TypeError(f"The parent of a ProcessNode may only be another ProcessNode or the Tree")

        self._parent = parent_object

    @property
    def parts(self) -> typing.Sequence[str]:
        return self.node_id.split(sep=SEPARATOR)

    def get_child_by_name(self, name: str) -> typing.Optional[ProcessNode]:
        candidates = [
            child
            for child in self.children
            if child.name == name
        ]
        return candidates[0] if candidates else None

    def get_child_node_by_name(self, name: str) -> typing.Optional[ProcessNode]:
        candidates = [
            child
            for child in self.nodes
            if child.name == name
        ]
        return candidates[0] if candidates else None

    @classmethod
    def from_entry(cls, entry: ProcessEntry) -> ProcessNode:
        node_id = entry.executable_parts[0]
        name = node_id
        node = cls(
            node_id=node_id,
            name=name
        )
        node.add_entry(entry)
        return node

    def add_entry(self, entry: ProcessEntry):
        if self.depth == len(entry.executable_parts) - 1 and entry.executable_parts[self.depth] == entry.name:
            copy = next((
                process
                for process in self.leaves
                if process.parent_process_id == entry.parent_process_id
                   and process.command == entry.executable
                   and process.arguments == entry.arguments
            ), None)

            if copy is None:
                leaf = ProcessLeaf.from_entry(entry)
                leaf.parent = self
                self.children.append(leaf)
            else:
                copy.add_instance(entry=entry)
        elif self.depth >= len(entry.executable_parts):
            leaf = ProcessLeaf.from_entry(entry)
            leaf.parent = self
            self.children.append(leaf)
        else:
            name = entry.executable_parts[self.depth]
            matching_child_node = self.get_child_node_by_name(name)

            if matching_child_node:
                matching_child_node.add_entry(entry)
            else:
                new_node_id = f"{self.node_id}{SEPARATOR}{name}"
                new_node = ProcessNode(node_id=new_node_id, name=name, depth=self.depth + 1)
                new_node.parent = self
                self.children.append(new_node)
                new_node.add_entry(entry)

    @property
    def count(self) -> int:
        child_count = sum([
            child.count
            for child in self.children
        ])
        return child_count

    @property
    def cpu_percent(self) -> typing.Union[int, float]:
        percent = sum([
            child.cpu_percent
            for child in self.children
            if isinstance(child.cpu_percent, (int, float))
        ])
        return percent

    @property
    def memory_usage(self) -> typing.Union[int, float]:
        usage = sum([
            child.memory_usage
            for child in self.children
            if isinstance(child.memory_usage, (int, float))
        ])
        return usage

    @property
    def leaves(self) -> typing.Sequence[ProcessLeaf]:
        return [
            child
            for child in self.children
            if isinstance(child, ProcessLeaf)
        ]

    @property
    def nodes(self) -> typing.Sequence[ProcessNode]:
        return [
            child
            for child in self.children
            if isinstance(child, ProcessNode)
        ]

    @property
    def top(self) -> typing.Union[ProcessNode, ProcessTree]:
        if self._parent is None:
            return self
        return self._parent.top

    def walk(self) -> typing.Sequence[
        typing.Tuple[
            ProcessNode,
            typing.Sequence[ProcessNode],
            typing.Sequence[ProcessLeaf]
        ]
    ]:
        entries = [
            (self, self.nodes, self.leaves),
        ]

        for node in self.nodes:
            entries.extend(node.walk())

        return entries

    @property
    def height(self) -> int:
        if not self.nodes:
            return 1
        return max([node.height for node in self.nodes]) + 1

    def __len__(self):
        return self.count

    def __str__(self):
        return f"{self.node_id} ({byte_size_to_text(self.memory_usage)})"

    def __repr__(self):
        return self.__str__()


# TODO: Can this be collapsed into the process node?
class ProcessTree(BaseModel):
    children: typing.List[typing.Union[ProcessNode, ProcessLeaf]] = Field(default_factory=list)
    depth: int = Field(default=1)

    def count(self) -> int:
        child_count = sum([
            child.count
            for child in self.children
        ])
        return child_count

    def to_sunburst(self, value_attribute: str = None) -> graph_objects.Figure:
        graph_input = self.get_sunburst_data(value_attribute=value_attribute)
        return express.sunburst(
            graph_input,
            names="path",
            parents="parent",
            values="value"
        )

    @property
    def html(self) -> str:
        return self.to_sunburst().to_html()

    @property
    def top(self) -> ProcessTree:
        return self

    def add_entry(self, entry: ProcessEntry):
        if self.depth == len(entry.executable_parts) - 1 and entry.executable[self.depth] == entry.name:
            leaf = ProcessLeaf.from_entry(entry)
            leaf.parent = self
            self.children.append(leaf)
        else:
            name = entry.executable_parts[self.depth]
            matching_child_node = self.get_child_node_by_name(name)

            if matching_child_node:
                matching_child_node.add_entry(entry)
            else:
                new_node_id = f"{self.node_id}{SEPARATOR}{name}"
                new_node = ProcessNode(node_id=new_node_id, name=name, depth=self.depth + 1)
                new_node.parent = self
                self.children.append(new_node)
                new_node.add_entry(entry)

    @property
    def leaves(self) -> typing.Sequence[ProcessLeaf]:
        return [
            child
            for child in self.children
            if isinstance(child, ProcessLeaf)
        ]

    @property
    def nodes(self) -> typing.Sequence[ProcessNode]:
        return [
            child
            for child in self.children
            if isinstance(child, ProcessNode)
        ]

    def get_sunburst_data(self, value_attribute: str = None) -> typing.Dict[
        typing.Literal["path", "parent", "value"],
        typing.Union[typing.MutableSequence[str], typing.MutableSequence[float], typing.MutableSequence[int]]
    ]:
        sunburst_data: typing.Dict[
            typing.Literal["path", "parent", "value"],
            typing.Union[typing.MutableSequence[str], typing.MutableSequence[float], typing.MutableSequence[int]]
        ] = {
            "path": [],
            "parent": [],
            "value": []
        }

        for _, _, leaves in self.walk():
            child_data = [
                leaf.get_sunburst_data(value_attribute=value_attribute)
                for leaf in leaves
            ]

            for child_sunburst_data in child_data:
                sunburst_data['path'].extend(child_sunburst_data['path'])
                sunburst_data['parent'].extend(child_sunburst_data['parent'])
                sunburst_data['value'].extend(child_sunburst_data['value'])

        return sunburst_data

    def walk(self) -> typing.Sequence[
        typing.Tuple[
            ProcessNode,
            typing.Sequence[ProcessNode],
            typing.Sequence[ProcessLeaf]
        ]
    ]:
        entries = [
            (self, self.nodes, self.leaves),
        ]

        for node in self.nodes:
            entries.extend(node.walk())

        return entries

    @property
    def height(self) -> int:
        if not self.nodes:
            return 1
        return max([child.height for child in self.nodes]) + 1

    def __len__(self):
        return self.count()