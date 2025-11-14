# queuectl – CLI-Based Background Job Queue in Python

A minimal and production-aware background job system built in Python. It supports:

* ✅ Shell-command job execution
* ✅ Parallel worker processes
* ✅ Retry with exponential backoff
* ✅ Dead Letter Queue (DLQ)
* ✅ Config persistence via JSON
* ✅ SQLite-backed durability
* ✅ CLI via `click`

---

## 📺 Project Structure

| File / Folder           | Purpose                                         |
| ----------------------- | ----------------------------------------------- |
| `queuectl/`             | Core Python package (CLI, DB, worker logic)     |
| `queuectl.db`           | SQLite DB file (auto-created)                   |
| `queuectl_config.json`  | Config settings (`max_retries`, `backoff_base`) |
| `queuectl_workers.pids` | Tracks background worker PIDs                   |
| `tests/run_tests.py`    | Automated end-to-end test script                |
| `setup.py`              | Install script for editable dev mode            |
| `requirements.txt`      | Required packages (`click`)                     |

---

## ⚙️ Setup Instructions (Windows PowerShell)

### 1. Clone & Open Project

```powershell
git clone <your-repo-url>
cd queuectl
```

### 2. Create & Activate Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Install in Editable Mode

```powershell
pip install -e .
```

---

## 🔧 Usage Guide

### ✅ Enqueue a Job

```powershell
queuectl --% enqueue "{\"id\":\"job1\",\"command\":\"echo Hello from queuectl\"}"
```

### 🚀 Start Background Worker(s)

```powershell
queuectl worker start --count 2
```

### 📊 Monitor Job Status

```powershell
queuectl status
queuectl list --state completed
queuectl list --state pending
queuectl list --state dead
```

### 🚫 Stop Workers

```powershell
queuectl worker stop
```

---

## 🔁 Retry Logic and DLQ

### Set retry & backoff (optional):

```powershell
queuectl config set max_retries 2
queuectl config set backoff_base 2
```

### Enqueue a failing job:

```powershell
queuectl --% enqueue "{\"id\":\"failjob\",\"command\":\"badcommandthatfails\"}"
```

Let the worker run and retry. After all retries fail:

### View Dead Letter Queue:

```powershell
queuectl dlq list
```

### Retry a DLQ Job:

```powershell
queuectl dlq retry failjob
```

---

## 🦐 Automated Test

The project includes a test script that:

* Enqueues a test job
* Starts a worker
* Waits for completion
* Asserts job success

### Run the test:

```powershell
python tests/run_tests.py
```

Expected output:

```
SUCCESS: Automated test passed
```

---

## ✅ Summary

With `queuectl`, you can easily:

* Run CLI jobs in the background
* Retry on failure with exponential backoff
* Manage jobs and workers from the terminal
* Use a DLQ for inspecting or retrying permanently failed jobs
