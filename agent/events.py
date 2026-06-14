from dataclasses import dataclass


@dataclass
class Event:
    pass


@dataclass()
class ThinkingEvent(Event):
    pass


@dataclass
class StreamEvent(Event):
    token: str


@dataclass
class ToolCallEvent(Event):
    name: str
    arguments: dict

@dataclass
class ToolResultEvent(Event):
    name: str
    result: str
    duration: float
