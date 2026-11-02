# python-env-checker
Python Environment Checker
A lightweight, installable Python CLI that checks Python version, disk space, selected environment variables, and developer tools. It prints a human-readable report and can also write structured JSON.
Requirements
Python 3.9+
No runtime third-party dependencies
Install (editable)
```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install -e .
```
Usage
```bash
env-checker
env-checker --json
env-checker --output report.json
env-checker --config checker-config.json
```
Optional JSON config:
```json
{
  "required_env": ["PATH"],
  "tools": ["git", "python"]
}
```
A missing required environment variable or developer tool produces exit code `1`. A malformed/unreadable config produces exit code `2`. Successful checks return `0`.
Tests
```bash
python -m unittest discover -s tests -v
```
Sample input
`sample/diagnostic-events.json` is included as a sample diagnostic event dataset from the internship task context.
