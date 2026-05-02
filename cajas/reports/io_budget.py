"""Lightweight IO budget reporting helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict


@dataclass
class IoEvent:
    name: str
    seconds: float
    file_count: int = 0
    bytes_read_estimate: int = 0
    bytes_written_estimate: int = 0


def timed_io(name: str):
    start = time.time()

    def done(*, file_count: int = 0, bytes_read_estimate: int = 0, bytes_written_estimate: int = 0) -> IoEvent:
        return IoEvent(
            name=name,
            seconds=round(time.time() - start, 3),
            file_count=file_count,
            bytes_read_estimate=bytes_read_estimate,
            bytes_written_estimate=bytes_written_estimate,
        )

    return done


def render_io_events(events: list[IoEvent]) -> list[dict]:
    return [asdict(e) for e in events]
