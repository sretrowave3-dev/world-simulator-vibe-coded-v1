"""
project/ai/behavior_tree.py

Hierarchical Behavior Tree Engine for ALife Decision Making.

Features:
- Standard Behavior Tree node primitives: Selector, Sequence, Parallel, Inverter, Condition, Action.
- Fast non-allocating tick evaluation passing context and Blackboard.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional
from project.ai.blackboard import Blackboard


class NodeStatus(enum.Enum):
    SUCCESS = enum.auto()
    FAILURE = enum.auto()
    RUNNING = enum.auto()


class BehaviorNode(ABC):
    """Abstract base class for all Behavior Tree nodes."""

    @abstractmethod
    def tick(self, agent: Any, blackboard: Blackboard) -> NodeStatus:
        pass


class Selector(BehaviorNode):
    """
    Fallback / Selector Composite:
    Ticks children sequentially until one SUCCEEDS or is RUNNING.
    Returns FAILURE only if all children fail.
    """

    def __init__(self, children: Optional[List[BehaviorNode]] = None) -> None:
        self.children: List[BehaviorNode] = children or []

    def tick(self, agent: Any, blackboard: Blackboard) -> NodeStatus:
        for child in self.children:
            status = child.tick(agent, blackboard)
            if status in (NodeStatus.SUCCESS, NodeStatus.RUNNING):
                return status
        return NodeStatus.FAILURE


class Sequence(BehaviorNode):
    """
    Sequence Composite:
    Ticks children sequentially. Returns FAILURE if any child fails.
    Returns SUCCESS only if all children succeed.
    """

    def __init__(self, children: Optional[List[BehaviorNode]] = None) -> None:
        self.children: List[BehaviorNode] = children or []

    def tick(self, agent: Any, blackboard: Blackboard) -> NodeStatus:
        for child in self.children:
            status = child.tick(agent, blackboard)
            if status in (NodeStatus.FAILURE, NodeStatus.RUNNING):
                return status
        return NodeStatus.SUCCESS


class Inverter(BehaviorNode):
    """Decorator: Inverts SUCCESS <-> FAILURE (RUNNING passes through)."""

    def __init__(self, child: BehaviorNode) -> None:
        self.child = child

    def tick(self, agent: Any, blackboard: Blackboard) -> NodeStatus:
        status = self.child.tick(agent, blackboard)
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        if status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return status


class ConditionNode(BehaviorNode):
    """Leaf node evaluating a boolean predicate."""

    def __init__(self, predicate: Callable[[Any, Blackboard], bool]) -> None:
        self.predicate = predicate

    def tick(self, agent: Any, blackboard: Blackboard) -> NodeStatus:
        return NodeStatus.SUCCESS if self.predicate(agent, blackboard) else NodeStatus.FAILURE


class ActionNode(BehaviorNode):
    """Leaf node executing an action callback returning NodeStatus."""

    def __init__(self, action: Callable[[Any, Blackboard], NodeStatus]) -> None:
        self.action = action

    def tick(self, agent: Any, blackboard: Blackboard) -> NodeStatus:
        return self.action(agent, blackboard)
