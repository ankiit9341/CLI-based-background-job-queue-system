## Running locally

1. create & activate venv
   python -m venv venv
   .\venv\Scripts\activate

2. install package
   pip install -e .

3. enqueue a job (PowerShell):
   queuectl --% enqueue "{\"id\":\"job1\",\"command\":\"echo Hello from queuectl\"}"

4. start background workers:
   queuectl worker start --count 2

5. check status:
   queuectl status

6. stop workers:
   queuectl worker stop

7. list DLQ:
   queuectl dlq list
   queuectl dlq retry job1


# queuectl

`queuectl` — a minimal, production-oriented CLI background job queue system written in Python.
It supports enqueuing shell-command jobs, running worker processes, retry with exponential backoff,
and a Dead Letter Queue (DLQ). Persistence is implemented with SQLite.

---

## Contents
- `queuectl/` : Python package (CLI, DB, worker, config)
- `queuectl.db` : SQLite database (auto-created)
- `queuectl_config.json` : configuration (created when using `config set`)
- `queuectl_workers.pids` : tracked PIDs of background worker processes
- `requirements.txt`, `setup.py`
- `tests/` : test helper scripts

---

## Prerequisites
- Python 3.8+ (Windows tested)
- Git (for pushing to GitHub)
- PowerShell (Windows) or bash

---

## Quick setup (Windows PowerShell)

1. Clone or copy the project folder and open it in VS Code.
2. Create & activate virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
