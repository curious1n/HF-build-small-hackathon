from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from .contracts import NodeId, NodeStatus, RuntimeMetadata, RunTrace


NODE_LABELS: dict[NodeId, str] = {
    "plain_goal_input": "Plain goal input",
    "generate_text": "Generate text",
    "generate_image": "Generate image",
    "generate_audio": "Generate audio",
    "compose_outputs": "Compose outputs",
}


class StatusStore:
    def __init__(self, run_id: str, runtime_metadata: RuntimeMetadata | None = None):
        self.run_id = run_id
        self.runtime_metadata = runtime_metadata or RuntimeMetadata()
        self._statuses: dict[NodeId, NodeStatus] = {
            node_id: NodeStatus(node_id=node_id, label=label)
            for node_id, label in NODE_LABELS.items()
        }
        self._events: list[dict[str, Any]] = []

    def start(self, node_id: NodeId, message: str = "") -> None:
        now = time.time()
        self._statuses[node_id] = replace(
            self._statuses[node_id],
            state="generating",
            message=message,
            started_at=now,
            ended_at=None,
            latency_ms=0,
        )
        self._events.append({"node_id": node_id, "state": "generating", "message": message})

    def done(self, node_id: NodeId, message: str = "") -> None:
        self._finish(node_id, "done", message)

    def error(self, node_id: NodeId, message: str) -> None:
        self._finish(node_id, "error", message)

    def _finish(self, node_id: NodeId, state: str, message: str) -> None:
        now = time.time()
        current = self._statuses[node_id]
        started = current.started_at or now
        self._statuses[node_id] = replace(
            current,
            state=state,  # type: ignore[arg-type]
            message=message,
            ended_at=now,
            latency_ms=round((now - started) * 1000),
        )
        self._events.append({"node_id": node_id, "state": state, "message": message})

    def snapshot(self) -> RunTrace:
        return RunTrace(
            run_id=self.run_id,
            statuses=list(self._statuses.values()),
            events=list(self._events),
            runtime_metadata=self.runtime_metadata,
        )
