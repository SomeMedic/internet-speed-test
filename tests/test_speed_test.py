from __future__ import annotations

import httpx
import pytest

import speed_test


def test_summarize_calculates_expected_values() -> None:
    results = [
        speed_test.RequestResult(elapsed_seconds=1.0, downloaded_bytes=1_000_000),
        speed_test.RequestResult(elapsed_seconds=3.0, downloaded_bytes=3_000_000),
    ]

    summary = speed_test.summarize(results)

    assert summary.request_count == 2
    assert summary.total_bytes == 4_000_000
    assert summary.total_time_seconds == pytest.approx(4.0)
    assert summary.average_request_time_seconds == pytest.approx(2.0)
    assert summary.average_speed_mb_s == pytest.approx(1.0)
    assert summary.average_speed_mbit_s == pytest.approx(8.0)


def test_run_speed_test_performs_exactly_ten_requests() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, content=b"x" * 1_000, request=request)

    output: list[str] = []
    summary = speed_test.run_speed_test(
        "https://example.com/image.jpg",
        transport=httpx.MockTransport(handler),
        output=output.append,
    )

    assert request_count == speed_test.REQUEST_COUNT == 10
    assert summary.request_count == 10
    assert summary.total_bytes == 10_000
    assert any(line.startswith("Average speed:") for line in output)


def test_download_once_counts_full_body() -> None:
    payload = b"abc123" * 5_000

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payload, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = speed_test.download_once(client, "https://example.com/file.bin")

    assert result.downloaded_bytes == len(payload)
    assert result.elapsed_seconds >= 0


def test_download_once_raises_for_http_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, content=b"unavailable", request=request)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        speed_test.download_once(client, "https://example.com/file.bin")


def test_summarize_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="At least one"):
        speed_test.summarize([])
