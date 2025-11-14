# tests/run_tests.py
# Simple automated test that uses the package internals and spawns a worker process.
# Run: python tests/run_tests.py

import time
import os
import sys
from multiprocessing import Process
from queuectl import db
from queuectl.worker import run_worker
from click.testing import CliRunner
from queuectl.cli import cli
import sqlite3
import json

TEST_JOB_ID = "py_test_job_1"

def enqueue_job_via_cli(job_id):
    runner = CliRunner()
    job_json = json.dumps({"id": job_id, "command": "echo automated_test"})
    res = runner.invoke(cli, ["enqueue", job_json])
    print("enqueue output:", res.output)
    if res.exit_code != 0:
        raise RuntimeError("Failed to enqueue job via CLI")

def check_job_state(job_id):
    row = db.get_job(job_id)
    if not row:
        return None
    return row['state']

def main():
    # Ensure DB initialized
    db.init_db()

    # Clean up previous test job if present
    existing = db.get_job(TEST_JOB_ID)
    if existing:
        print("removing existing test job")
        conn = db.get_db()
        conn.execute("DELETE FROM jobs WHERE id=?", (TEST_JOB_ID,))
        conn.commit()
        conn.close()

    # Enqueue job
    enqueue_job_via_cli(TEST_JOB_ID)

    # Start worker in a separate process
    p = Process(target=run_worker)
    p.start()
    print("Worker started, waiting for job to be processed...")
    # wait up to 10 seconds for completion
    for _ in range(12):
        state = check_job_state(TEST_JOB_ID)
        print("current state:", state)
        if state == 'completed':
            print("Test job completed successfully.")
            break
        time.sleep(1)
    else:
        print("Test job did not complete in time. State:", state)

    # Stop worker process
    p.terminate()
    p.join(timeout=2)

    if state != 'completed':
        print("FAILED: Job did not complete")
        sys.exit(2)
    else:
        print("SUCCESS: Automated test passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
