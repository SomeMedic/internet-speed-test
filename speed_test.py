from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True)
class RequestResult:
    elapsed_seconds: float
    downloaded_bytes: int


@dataclass(frozen=True)
class Summary:
    request_count: int
    total_bytes: int
    total_time_seconds: float
    average_request_time_seconds: float
    average_speed_bytes_per_second: float

    @property
    def average_speed_mb_s(self) -> float:
        return self.average_speed_bytes_per_second / 1_000_000

    @property
    def average_speed_mbit_s(self) -> float:
        return self.average_speed_bytes_per_second * 8 / 1_000_000


def download_once(client: httpx.Client, url: str) -> RequestResult:
    started_at = time.perf_counter()
    downloaded_bytes = 0

    with client.stream("GET", url) as response:
        response.raise_for_status()

        for chunk in response.iter_raw(chunk_size=CHUNK_SIZE):
            downloaded_bytes += len(chunk)

    return RequestResult(
        elapsed_seconds=time.perf_counter() - started_at,
        downloaded_bytes=downloaded_bytes,
    )


def summarize(results: list[RequestResult]) -> Summary:
    if not results:
        raise ValueError("At least one request result is required")

    total_bytes = sum(result.downloaded_bytes for result in results)
    total_time = sum(result.elapsed_seconds for result in results)

    if total_time <= 0:
        raise ValueError("Total request time must be greater than zero")

    return Summary(
        request_count=len(results),
        total_bytes=total_bytes,
        total_time_seconds=total_time,
        average_request_time_seconds=total_time / len(results),
        average_speed_bytes_per_second=total_bytes / total_time,
    )


def run_speed_test(
    url: str,
    *,
    transport: httpx.BaseTransport | None = None,
    output: Callable[[str], None] = print,
) -> Summary:
    results: list[RequestResult] = []

    with httpx.Client(
        follow_redirects=True,
        timeout=httpx.Timeout(TIMEOUT_SECONDS),
        headers={"Accept-Encoding": "identity"},
        transport=transport,
    ) as client:
        for request_number in range(1, REQUEST_COUNT + 1):
            result = download_once(client, url)
            results.append(result)
            output(
                f"[{request_number:02}/{REQUEST_COUNT}] "
                f"{result.downloaded_bytes / 1_000_000:.2f} MB "
                f"in {result.elapsed_seconds:.3f} s"
            )

    summary = summarize(results)

    output("")
    output("Results")
    output("-------")
    output(f"Requests:              {summary.request_count}")
    output(f"Average request time:  {summary.average_request_time_seconds:.3f} s")
    output(f"Downloaded:            {summary.total_bytes / 1_000_000:.2f} MB")
    output(
        "Average speed:         "
        f"{summary.average_speed_mb_s:.2f} MB/s "
        f"({summary.average_speed_mbit_s:.2f} Mbit/s)"
    )

    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure HTTP download speed using 10 sequential requests."
    )
    parser.add_argument("url", help="URL of a file to download")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        run_speed_test(args.url)
    except httpx.HTTPStatusError as exc:
        print(
            f"HTTP error: {exc.response.status_code} for {exc.request.url}",
            file=sys.stderr,
        )
        return 1
    except httpx.RequestError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Invalid result: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
