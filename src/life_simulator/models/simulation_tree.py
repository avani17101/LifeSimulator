from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from life_simulator.models.person_state import PersonState


def _short_id() -> str:
    return str(uuid.uuid4())[:8]


class SimNode(BaseModel):
    """A single node in the simulation tree."""

    id: str = Field(default_factory=_short_id)
    year: int
    state: PersonState
    action_taken: str | None = None
    confidence: float = 0.5
    children: list[SimNode] = []

    def leaf_nodes(self) -> list[SimNode]:
        if not self.children:
            return [self]
        leaves: list[SimNode] = []
        for child in self.children:
            leaves.extend(child.leaf_nodes())
        return leaves


class SimTree(BaseModel):
    """Complete simulation result — a tree of possible futures."""

    root: SimNode
    decision: "Decision"  # noqa: F821
    metadata: dict = {}

    def all_paths(self) -> list[list[SimNode]]:
        """Return all root-to-leaf paths."""
        paths: list[list[SimNode]] = []

        def _walk(node: SimNode, path: list[SimNode]) -> None:
            path = [*path, node]
            if not node.children:
                paths.append(path)
            for child in node.children:
                _walk(child, path)

        _walk(self.root, [])
        return paths


# Resolve forward reference
from life_simulator.models.decision import Decision  # noqa: E402

SimTree.model_rebuild()
