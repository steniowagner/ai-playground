from __future__ import annotations

import os
import socket
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def block_network(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Iterator[None]:
    """Fail immediately if a test accidentally attempts a real network call."""

    live_model_test = request.node.get_closest_marker("live_model") is not None
    live_model_opt_in = os.getenv("RUN_LIVE_MODEL_EVALUATIONS") == "1"
    held_out_opt_in = os.getenv("RUN_HELD_OUT_MODEL_EVALUATIONS") == "1"
    if live_model_test and (live_model_opt_in or held_out_opt_in):
        yield
        return

    def guarded_connect(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError(
            "Network access is disabled in tests. Replace the external dependency "
            "with a fake or mock."
        )

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect)
    yield


@pytest.fixture
def fixed_uuid(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Make proposal identifiers deterministic in tests that opt into it."""
    from uuid import UUID

    import triage_ops.graph.nodes.prepare_approvals.node as approvals_node

    identifiers = iter(
        [
            UUID("00000000-0000-0000-0000-000000000001"),
            UUID("00000000-0000-0000-0000-000000000002"),
            UUID("00000000-0000-0000-0000-000000000003"),
        ]
    )
    monkeypatch.setattr(approvals_node, "uuid4", lambda: next(identifiers))
    yield
