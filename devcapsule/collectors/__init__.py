"""Context collectors."""

from devcapsule.collectors.clipboard import ClipboardCollector
from devcapsule.collectors.environment import EnvironmentCollector
from devcapsule.collectors.git import GitCollector
from devcapsule.collectors.project import ProjectCollector
from devcapsule.collectors.terminal import TerminalCollector

__all__ = [
    "ClipboardCollector",
    "EnvironmentCollector",
    "GitCollector",
    "ProjectCollector",
    "TerminalCollector",
]
