# queuectl/worker.py

import subprocess
import time
from datetime import datetime
from queuectl import db
from queuectl.config import get_config
from queuectl.db import fetch_and_claim_pending  # ✅ use safe job locking

def execute_job(job):
    command = job['command']
    job_id = job['id']
    attempts = job['attempts']
    max_retries = job['max_retries']
    
    try:
        print(f"🔧 Executing job {job_id}: {command}")
        result = subprocess.run(command, shell=True)
        print(f"➡️ Command returncode: {result.returncode}")
        print(f"➡️ Current attempts: {attempts} / max_retries: {max_retries}")

        if result.returncode == 0:
            # Success
            conn = db.get_db()
            conn.execute(
                "UPDATE jobs SET state='completed', updated_at=? WHERE id=?",
                (datetime.utcnow().isoformat(), job_id)
            )
            conn.commit()
            conn.close()
            print(f"✅ Job {job_id} completed successfully.")
        else:
            raise Exception(f"Command failed with exit code {result.returncode}")

    except Exception as e:
        print(f"❌ Error running job {job_id}: {e}")
        attempts += 1
        now = datetime.utcnow().isoformat()
        conn = db.get_db()

        if attempts >= max_retries:
            # Final failure → move to DLQ
            conn.execute(
                "UPDATE jobs SET state='dead', attempts=?, updated_at=? WHERE id=?",
                (attempts, now, job_id)
            )
            print(f"💀 Job {job_id} failed permanently and moved to DLQ.")
        else:
            # Retry with exponential backoff
            delay = get_config('backoff_base', default=2) ** attempts
            print(f"⚠️ Job {job_id} failed (attempt {attempts}/{max_retries}). Retrying in {delay}s...")
            time.sleep(delay)
            conn.execute(
                "UPDATE jobs SET state='pending', attempts=?, updated_at=? WHERE id=?",
                (attempts, now, job_id)
            )

        conn.commit()
        conn.close()


def run_worker():
    while True:
        print("👀 Looking for pending job...")
        job = fetch_and_claim_pending()
        if job:
            print(f"✅ Claimed job {job['id']}")
            execute_job(job)
        else:
            time.sleep(2)
