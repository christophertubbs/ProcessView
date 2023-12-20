"""
@TODO: Put a module wide description here
"""
from __future__ import annotations

import json
import typing
from collections import defaultdict

import pandas

from pydantic import BaseModel
from pydantic import Field

from plotly import express
from plotly import graph_objects
from pydantic import PrivateAttr

from utilities.ps import ProcessStatus
from utilities.ps import ProcessEntry
from utilities.ps import byte_size_to_text

SEPARATOR = "/"

VALUE_SEQUENCE = typing.Union[typing.List[str], typing.List[typing.Optional[int]], typing.List[typing.Optional[float]]]


class Sunburst:
    @classmethod
    def sunburst_keys(cls) -> typing.Tuple[str, ...]:
        return (
            cls.parent_key(),
            cls.values_key(),
            cls.ids_key(),
            cls.names_key()
        )

    @classmethod
    def parent_key(cls) -> str:
        return "parents"

    @classmethod
    def values_key(cls) -> str:
        return "values"

    @classmethod
    def ids_key(cls) -> str:
        return "ids"

    @classmethod
    def names_key(cls) -> str:
        return "names"

    @property
    def names(self) -> typing.Sequence[str]:
        return [
            name
            for name in self.__sunburst_map[self.names_key()]
        ]

    @property
    def ids(self) -> typing.Sequence[typing.Union[str, int]]:
        return [
            id_value
            for id_value in self.__sunburst_map[self.ids_key()]
        ]

    @property
    def values(self) -> typing.Sequence[typing.Union[str, int, float]]:
        return [
            value
            for value in self.__sunburst_map[self.values_key()]
        ]

    @property
    def parents(self) -> typing.Sequence[typing.Union[str, int]]:
        return [
            parent
            for parent in self.__sunburst_map[self.parent_key()]
        ]

    def to_dict(self) -> typing.Dict[str, typing.Sequence[typing.Union[str, int, float]]]:
        return {
            key: [value for value in values]
            for key, values in self.__sunburst_map.items()
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

    def __getitem__(self, key: str) -> typing.Sequence[str]:
        if key not in self.__sunburst_map:
            raise ValueError(f"There are no values mapped to '{key}' within {self}")

        return self.__sunburst_map[key]

    @property
    def has_traces(self) -> bool:
        return any([
            max([len(values) for values in items.values()]) > 0
            for items in self.__traces.values()
        ])

    def add_trace(self, name: str):
        if name not in self.__traces:
            self.__traces[name] = {
                key: []
                for key in self.sunburst_keys()
            }

    def __init__(self, **kwargs):

        self.__traces: typing.Dict[str, typing.MutableMapping[str, VALUE_SEQUENCE]] = {}
        self.__sunburst_map: typing.MutableMapping[str, VALUE_SEQUENCE] = {
            key: []
            for key in self.sunburst_keys()
        }

        self.color = kwargs.get("color")
        self.color_continuous_scale = kwargs.get("color_continuous_scale")
        self.color_continuous_midpoint = kwargs.get("color_continuous_midpoint")
        self.color_discrete_map = kwargs.get("color_discrete_map")
        self.color_discrete_sequence = kwargs.get("color_discrete_sequence")
        self.range_color = kwargs.get("range_color")
        self.hover_data = kwargs.get("hover_data")
        self.hover_name = kwargs.get("hover_name")
        self.maxdepth = kwargs.get("maxdepth")
        self.branchvalues = kwargs.get("branchvalues")
        self.height = kwargs.get("height")
        self.width = kwargs.get("width")
        self.template = kwargs.get("template")
        self.title = kwargs.get("title")

    def copy(self) -> Sunburst:
        copied_sunburst = Sunburst(
            color=self.color,
            color_continuous_scale=self.color_continuous_scale,
            color_continuous_midpoint=self.color_continuous_midpoint,
            color_discrete_map=self.color_discrete_map,
            color_discrete_sequence=self.color_discrete_sequence,
            range_color=self.range_color,
            hover_data=self.hover_data,
            hover_name=self.hover_name,
            maxdepth=self.maxdepth,
            branchvalues=self.branchvalues,
            height=self.height,
            width=self.width,
            template=self.template,
            title=self.title
        )

        copied_sunburst = copied_sunburst.combine(other=self)
        return copied_sunburst

    def to_dataframe(self) -> pandas.DataFrame:
        return pandas.DataFrame(self.__sunburst_map)

    def insert_trace(self, name: str, data: Sunburst) -> Sunburst:
        if data.has_traces:
            raise ValueError(f"Cannot add sunburst data to another sunburst if it has traces.")

        self.add_trace(name)

        for key in self.sunburst_keys():
            self.__traces[name][key].extend(data[key])

        return self

    def add(self, values: typing.Mapping[str, typing.Union[str, float, int]], trace_name: str = None):
        for key in self.sunburst_keys():
            if key not in values:
                raise ValueError(f"Cannot add values to a sunburst - it is missing a value for the '{key}' key")

            if values[key] is not None and not isinstance(values[key], (str, float, int)):
                raise TypeError(
                    f"The value for the '{key}' key ({values[key]}: {type(values[key])}) cannot be added as a "
                    f"sunburst value - it must be either an int, float, or string"
                )

        if isinstance(trace_name, str):
            self.add_trace(name=trace_name)
            for key in self.sunburst_keys():
                self.__traces[trace_name][key].append(
                    values[key]
                )
        else:
            for key in self.sunburst_keys():
                self.__sunburst_map[key].append(
                    values[key]
                )

    def to_figure(self, **kwargs) -> graph_objects.Figure:
        expected_figure_count = len(self.__traces) + 1

        positions = [
            divmod(figure_index, 3)
            for figure_index in range(expected_figure_count)
        ]

        row_count = max([coordinates[0] for coordinates in positions]) + 1

        figure = graph_objects.Figure()

        figure.update_layout(
            margin=dict(t=0, l=0, r=0, b=0)
        )

        position_index = 0

        trace = graph_objects.Sunburst(
            labels=self.names,
            ids=self.ids,
            parents=self.parents,
            values=self.values,
            hovertemplate='%{label}<br>%{text}',
            name="All",
            text=[
                byte_size_to_text(value)
                for value in self.values
            ],
            maxdepth=3,
            **kwargs
        )

        figure.add_trace(trace=trace)

        position_index += 1

        for trace_name, trace in self.__traces.items():
            trace = graph_objects.Sunburst(
                labels=trace[self.names_key()],
                ids=trace[self.ids_key()],
                parents=trace[self.parent_key()],
                values=trace[self.values_key()],
                hovertemplate='%{label}<br>%{text}',
                name=trace_name,
                text=[
                    byte_size_to_text(value)
                    for value in trace[self.values_key()]
                ],
                **kwargs
            )
            figure.add_trace(trace=trace)
            position_index += 1

        return figure

    def plot(self, div_id: str = None, figure_kwargs: typing.Dict[str, typing.Any] = None, **kwargs) -> str:
        if figure_kwargs is None:
            figure_kwargs = {}

        sunburst_figure = self.to_figure(**figure_kwargs)

        if div_id is None:
            div_id = "ps_view"

        return sunburst_figure.to_html(
            include_plotlyjs=False,
            full_html=False,
            div_id=div_id,
            default_width="95vw",
            default_height="95vh",
            **kwargs
        )

    def to_entries(self):
        return (
            {
                key: self.__sunburst_map[key][data_index]
                for key in self.sunburst_keys()
            }
            for data_index in range(len(self))
        )

    def combine(self, other: Sunburst) -> Sunburst:
        for key in self.sunburst_keys():
            self.__sunburst_map[key].extend(other[key])

        for trace_name, trace in other.__traces.items():
            self.add_trace(name=trace_name)
            for key in self.sunburst_keys():
                self.__traces[trace_name][key].extend(trace[key])

        return self

    def __iadd__(self, other: Sunburst) -> Sunburst:
        if other is None:
            return self

        if not isinstance(other, Sunburst):
            raise TypeError(f"Cannot add a '{type(other)}' to a sunburst")

        return self.combine(other)

    @classmethod
    def merge(cls, first: Sunburst, second: Sunburst) -> Sunburst:
        if first is None and second is not None:
            return second.copy()
        elif first is not None and second is None:
            return first.copy()
        elif first is None and second is None:
            raise ValueError(f"Cannot merge two non-existent sunbursts")
        elif first is not None and second is not None:
            return first.copy().combine(other=second.copy())

    def __len__(self):
        return len(self.__sunburst_map[self.sunburst_keys()[0]])


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

    def duplicate(self, parent: typing.Union[ProcessNode, ProcessTree] = None) -> ProcessLeaf:
        new_leaf = ProcessLeaf(
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

        if isinstance(parent, (ProcessNode, ProcessTree)):
            new_leaf.parent = parent

        return new_leaf

    def get_sunburst_data(self, value_attribute: str = None) -> typing.Sequence[typing.Dict[str, typing.Union[float, str, int]]]:
        if not value_attribute:
            value_attribute = "memory_usage"

        if not hasattr(self, value_attribute):
            raise ValueError(f"'{value_attribute}' is not a value for a process")

        if isinstance(self.process_id, (str, int, float)):
            return [{
                Sunburst.parent_key(): self._parent.node_id if self._parent else "",
                Sunburst.values_key(): getattr(self, value_attribute),
                Sunburst.ids_key(): self.process_id,
                Sunburst.names_key(): self.name
            }]

        return [
            {
                Sunburst.parent_key(): self._parent.node_id if self._parent else "",
                Sunburst.values_key(): getattr(self, value_attribute),
                Sunburst.ids_key(): process_id,
                Sunburst.names_key(): self.name
            }
            for process_id in self.process_id
        ]

    def add_sunburst_data(self, sunburst: Sunburst, value_attribute: str = None, trace_name: str = None) -> Sunburst:
        sunburst_data = self.get_sunburst_data(value_attribute=value_attribute)

        if isinstance(sunburst_data, typing.Mapping):
            sunburst.add(values=sunburst_data, trace_name=trace_name)
        elif isinstance(sunburst_data, typing.Sequence):
            for sunburst_entry in sunburst_data:  # type: typing.Mapping[str, typing.Union[str, float, int]]
                sunburst.add(values=sunburst_entry, trace_name=trace_name)

        return sunburst

    @property
    def top(self) -> typing.Optional[ProcessNode, ProcessTree]:
        if self._parent is None:
            return None
        return self._parent.top

    def __str__(self):
        return f"{self.command} {' '.join(self.arguments)}"


class ProcessNode(BaseModel):
    node_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    depth: typing.Optional[int] = Field(default=1)
    children: typing.Optional[typing.List[typing.Union[ProcessNode, ProcessLeaf]]] = Field(default_factory=list)
    _parent: typing.Optional[typing.Union[ProcessNode, ProcessTree]] = PrivateAttr(default=None)

    def duplicate(self, parent: typing.Union[ProcessNode, ProcessTree] = None) -> ProcessNode:
        new_node = ProcessNode(node_id=self.node_id, name=self.name, depth=self.depth)

        if isinstance(parent, (ProcessNode, ProcessTree)):
            new_node.parent = parent

        for child in self.children:
            new_node.children.append(child.duplicate(new_node))

        return new_node

    @classmethod
    def load(cls, **kwargs) -> ProcessNode:
        entries = ProcessStatus()

        kwargs = {key: value for key, value in kwargs.items()}
        if 'node_id' not in kwargs:
            kwargs['node_id'] = ''

        if 'name' not in kwargs:
            kwargs['name'] = ''

        tree = cls(**kwargs)

        for entry in entries:
            tree.add_entry(entry)

        return tree

    @property
    def depth_prop(self) -> int:
        current_depth = 1

        current_element = self

        while current_element._parent is not None:
            current_depth += 1
            current_element = current_element._parent

        return current_depth


    @classmethod
    def sunburst(cls, value_attribute: str = None) -> graph_objects.Figure:
        tree = cls.load()
        return express.sunburst(
            tree.get_sunburst_data(value_attribute=value_attribute),
            names="path",
            parents="parent",
            values="value"
        )

    @classmethod
    def plot(cls) -> str:
        return cls.sunburst().to_html()

    def add_sunburst_data(self, sunburst: Sunburst, value_attribute: str = None, trace_name: str = None) -> Sunburst:
        if value_attribute is None:
            value_attribute = "memory_usage"

        if not hasattr(self, value_attribute):
            raise ValueError(f"Cannot add a node to sunburst data - it has no '{value_attribute}' value")

        sunburst.add(
            {
                sunburst.names_key(): self.name,
                sunburst.ids_key(): self.node_id,
                sunburst.parent_key(): self._parent.node_id if self._parent else '',
                sunburst.values_key(): getattr(self, value_attribute)
            },
            trace_name=trace_name
        )

        return sunburst

    def get_sunburst_data(self, value_attribute: str = None, trace_name: str = None) -> Sunburst:
        if value_attribute is None:
            value_attribute = "memory_usage"

        if not hasattr(self, value_attribute):
            raise ValueError(f"Cannot add a node to sunburst data - it has no '{value_attribute}' value")

        sunburst_data = Sunburst()

        duplicate = self.duplicate()

        duplicate.collapse()

        for current_node, _, leaves in duplicate.walk():
            current_node.add_sunburst_data(
                sunburst=sunburst_data,
                value_attribute=value_attribute,
                trace_name=trace_name
            )

            for leaf in leaves:
                leaf.add_sunburst_data(sunburst=sunburst_data, value_attribute=value_attribute, trace_name=trace_name)

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

    def collapse(self) -> bool:
        """
        Shrink single value nodes
        """

        shrank = False

        if self.depth >= 2:
            for child in self.nodes:
                child_shrank = child.collapse()
                shrank = shrank or child_shrank

        if len(self.children) == 1 and len(self.nodes) == 1:
            collapsing_node = self.children.pop()
            self.node_id = collapsing_node.node_id
            self.name = f"{self.name}{SEPARATOR}{collapsing_node.name}"
            for child in collapsing_node.children:
                self.children.append(child)
                child.parent = self

            shrank = True

        return shrank

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
    @classmethod
    def load(cls, include_self: bool = None, **kwargs) -> ProcessTree:
        entries = ProcessStatus(include_self=include_self)

        tree = cls(**kwargs)

        for entry in entries:
            tree.add_entry(entry)

        return tree

    @property
    def node_id(self) -> str:
        return ''

    def duplicate(self) -> ProcessTree:
        new_tree = ProcessTree()
        for child in self.children:
            new_tree.children.append(child.duplicate(new_tree))
        return new_tree

    children: typing.List[typing.Union[ProcessNode, ProcessLeaf]] = Field(default_factory=list)
    depth: int = Field(default=1)

    def count(self) -> int:
        child_count = sum([
            child.count
            for child in self.children
        ])
        return child_count

    @property
    def top(self) -> ProcessTree:
        return self

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
                new_node_id = name
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

    def collapse(self) -> bool:
        shrank = False
        for node in self.nodes:
            node_shrank = node.collapse()
            shrank = shrank or node_shrank

        return shrank

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

    def add_sunburst_data(self, sunburst: Sunburst, value_attribute: str = None, trace_name: str = None) -> Sunburst:
        if value_attribute is None:
            value_attribute = "memory_usage"

        if not hasattr(self, value_attribute):
            raise ValueError(f"Cannot add a node to sunburst data - it has no '{value_attribute}' value")

        value = {
            sunburst.names_key(): self.node_id,
            sunburst.parent_key(): "",
            sunburst.values_key(): getattr(self, value_attribute),
            sunburst.ids_key(): self.node_id
        }
        sunburst.add(values=value, trace_name=trace_name)
        return sunburst

    def plot_json(self, value_attribute: str = None, **kwargs) -> str:
        sunburst = self.get_sunburst_data(value_attribute=value_attribute)
        figure = sunburst.to_figure()
        json_data = figure.to_json()
        return json_data

    def trim_empty_nodes(self):
        self.children = [
            child
            for child in self.children
            if isinstance(child, ProcessLeaf)
               or (
                       isinstance(child, ProcessNode)
                       and child.memory_usage is not None
                       and child.memory_usage != 0
               )
        ]

    def get_sunburst_data(self, value_attribute: str = None) -> Sunburst:
        if value_attribute is None:
            value_attribute = "memory_usage"

        sunburst_data = Sunburst()

        duplicate = self.duplicate()

        duplicate.collapse()
        duplicate.trim_empty_nodes()

        duplicate.add_sunburst_data(sunburst=sunburst_data, value_attribute=value_attribute)

        for leaf in self.leaves:
            leaf.add_sunburst_data(sunburst=sunburst_data, value_attribute=value_attribute)

        for current_node, child_nodes, leaves in duplicate.walk():
            current_node.add_sunburst_data(sunburst=sunburst_data, value_attribute=value_attribute)
            for leaf in leaves:
                leaf.add_sunburst_data(sunburst=sunburst_data, value_attribute=value_attribute)

        traces = {}

        for child in sorted(self.nodes, key=lambda node: node.memory_usage, reverse=True):
            percent_of_total = (getattr(child, value_attribute) / getattr(self, value_attribute)) * 100.0
            child_sunburst = child.get_sunburst_data(value_attribute=value_attribute)
            trace_name = child.name if percent_of_total > 10.0 else 'Other'

            sunburst_data.insert_trace(name=trace_name, data=child_sunburst)

        #for node in sorted(self.nodes, key=lambda node: node.memory_usage, reverse=True):
        #    child_sunburst = node.get_sunburst_data(value_attribute=value_attribute)
        #    sunburst_data.insert_trace(name=node.name, data=child_sunburst)

        return sunburst_data

    def plot(self, value_attribute: str = None, div_id: str = None, **kwargs) -> str:
        sunburst_data = self.get_sunburst_data(value_attribute=value_attribute)
        return sunburst_data.plot(div_id=div_id, **kwargs)

    def plot_dict(self, value_attribute: str = None, **kwargs) -> typing.Dict[str, typing.Any]:
        sunburst_data = self.get_sunburst_data(value_attribute=value_attribute)
        figure = sunburst_data.to_figure()
        return figure.to_dict()

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