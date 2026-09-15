# Internet Speed Test

Small Python CLI that measures HTTP download throughput for a given URL.

The script:

- accepts a URL;
- performs exactly 10 sequential GET requests;
- downloads the full response body on every request;
- measures request duration with `time.perf_counter()`;
- prints the average request time, total downloaded data and average download speed.

## Requirements

- Python 3.10+

## Install

```bash
git clone https://github.com/SomeMedic/internet-speed-test.git
cd internet-speed-test

python -m venv .venv
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python speed_test.py "https://example.com/large-image.jpg"
```

Example output:

```text
[01/10] 5.24 MB in 0.842 s
[02/10] 5.24 MB in 0.801 s
...
[10/10] 5.24 MB in 0.815 s

Results
-------
Requests:              10
Average request time:  0.821 s
Downloaded:            52.43 MB
Average speed:         6.39 MB/s (51.08 Mbit/s)
```

## Calculation

Average request time:

```text
sum(request durations) / number of requests
```

Average download speed is calculated over all ten downloads:

```text
total downloaded bytes / total download time
```

The program reports both decimal MB/s and Mbit/s.

Requests are intentionally sequential, as required by the task. The response body is streamed in chunks, so a large test file is not kept entirely in memory.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Lint

```bash
ruff check .
```

## Notes

This measures HTTP throughput to the selected URL, not the theoretical maximum bandwidth of the network connection. Results can also be affected by the remote server/CDN, routing, TCP/TLS overhead and current network load.
