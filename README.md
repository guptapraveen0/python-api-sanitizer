# API Sanitizer

## Setup
```bash
python -m pip install requests
```

## Run
```bash
python api_sanitizer.py --limit 3
python api_sanitizer.py --mock
python api_sanitizer.py --fixture fixtures/malformed_fixture.json
python api_sanitizer.py --url https://jsonplaceholder.typicode.com/does-not-exist --limit 3
python api_sanitizer.py --url https://does-not-exist.invalid/users --timeout 2 --limit 3
```

The report is written to `reports/api_summary.json` by default. Every HTTP call has an explicit timeout; TLS verification remains enabled. The live/404/unreachable transcripts are illustrative because this package was built in an environment without outbound network access. Run those commands locally to capture actual network-dependent output.
