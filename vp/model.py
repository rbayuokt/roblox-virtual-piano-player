from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union, TypedDict, Literal

PrintMode = Literal["paired", "current", "cumulative", "both", "off"]

@dataclass
class SongSettings:
    title: str = "Untitled VP Sheet"
    author: str = ""
    bpm: int = 97
    subdiv: int = 4
    start_delay: float = 5.0
    chord_hold: float = 0.75
    print_mode: Optional[PrintMode] = None

@dataclass
class TokenEvent:
    keys: List[str]
    text: str

@dataclass
class RestEvent:
    steps: int
    text: str

class NewlineEvent(TypedDict):
    newline: bool

Event = Union[TokenEvent, RestEvent, NewlineEvent]

DEFAULT_SETTINGS = SongSettings()

def is_newline(e: Event) -> bool:
    return isinstance(e, dict) and e.get("newline") is True

__all__ = [
    "PrintMode",
    "SongSettings",
    "TokenEvent",
    "RestEvent",
    "NewlineEvent",
    "Event",
    "DEFAULT_SETTINGS",
    "is_newline",
]
