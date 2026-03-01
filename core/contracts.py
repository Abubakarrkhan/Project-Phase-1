

from typing import Protocol, List, Any, runtime_checkable


@runtime_checkable
class DataSink(Protocol):
    """Output plugin contract. Receives labelled result sets from the engine."""

    def write(self, label: str, records: List[Any]) -> None: ...


@runtime_checkable
class PipelineService(Protocol):
    """Engine contract. Input plugins hand raw rows to the engine via execute."""

    def execute(self, raw_data: List[Any]) -> None: ...
