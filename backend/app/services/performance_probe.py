"""A small, real HTTP load-probing utility — used manually against a live
running instance (see docs/validation/url-shortener-performance.md for the
actual measured results). Not wired into any API endpoint; this is a dev
tool, not a production feature. Reports only what it actually measured —
no target/threshold is invented (see app.services.validation_runner's
PERFORMANCE type, which defers to this for any concrete measurement)."""

import time
from dataclasses import dataclass, field

import httpx


@dataclass
class ProbeResult:
    request_count: int
    success_count: int
    error_count: int
    durations_ms: list[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.request_count == 0:
            return 0.0
        return self.success_count / self.request_count

    @property
    def p50_ms(self) -> float:
        return _percentile(self.durations_ms, 50)

    @property
    def p95_ms(self) -> float:
        return _percentile(self.durations_ms, 95)

    @property
    def p99_ms(self) -> float:
        return _percentile(self.durations_ms, 99)

    def throughput_rps(self, wall_time_s: float) -> float:
        if wall_time_s <= 0:
            return 0.0
        return self.request_count / wall_time_s


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1))))
    return ordered[index]


def probe_get(
    client: httpx.Client, path: str, *, count: int, expected_status: int = 200
) -> tuple[ProbeResult, float]:
    """Sends `count` real sequential GET requests to `path` and measures
    wall-clock latency of each. Returns (result, total_wall_time_seconds)."""
    durations = []
    success = 0
    errors = 0

    wall_start = time.perf_counter()
    for _ in range(count):
        start = time.perf_counter()
        try:
            response = client.get(path, follow_redirects=False)
            elapsed_ms = (time.perf_counter() - start) * 1000
            durations.append(elapsed_ms)
            if response.status_code == expected_status:
                success += 1
            else:
                errors += 1
        except httpx.HTTPError:
            elapsed_ms = (time.perf_counter() - start) * 1000
            durations.append(elapsed_ms)
            errors += 1
    wall_time = time.perf_counter() - wall_start

    return (
        ProbeResult(
            request_count=count, success_count=success, error_count=errors, durations_ms=durations
        ),
        wall_time,
    )


def probe_post(
    client: httpx.Client, path: str, *, count: int, json_factory, expected_status: int = 201
) -> tuple[ProbeResult, float]:
    durations = []
    success = 0
    errors = 0

    wall_start = time.perf_counter()
    for i in range(count):
        start = time.perf_counter()
        try:
            response = client.post(path, json=json_factory(i))
            elapsed_ms = (time.perf_counter() - start) * 1000
            durations.append(elapsed_ms)
            if response.status_code == expected_status:
                success += 1
            else:
                errors += 1
        except httpx.HTTPError:
            elapsed_ms = (time.perf_counter() - start) * 1000
            durations.append(elapsed_ms)
            errors += 1
    wall_time = time.perf_counter() - wall_start

    return (
        ProbeResult(
            request_count=count, success_count=success, error_count=errors, durations_ms=durations
        ),
        wall_time,
    )

