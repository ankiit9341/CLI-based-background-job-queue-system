# queuectl/worker.py

import subprocess
import time
from datetime import datetime, timedelta
from queuectl import db
from queuectl.config import get_config

def execute_job(job):
    command = job['command']
    job_id = job['id']
    attempts = job['attempts']
    max_retries = job['max_retries']
    
    try:
        print(f"🔧 Executing job {job_id}: {command}")
        result = subprocess.run(command, shell=True)
        if result.returncode == 0:
            # Success
            conn = db.get_db()
            conn.execute("UPDATE jobs SET state='completed', updated_at=? WHERE id=?", 
                         (datetime.utcnow().isoformat(), job_id))
            conn.commit()
            conn.close()
            print(f"✅ Job {job_id} completed successfully.")
        else:
            raise Exception(f"Command failed with exit code {result.returncode}")

    except Exception as e:
        attempts += 1
        conn = db.get_db()
        now = datetime.utcnow().isoformat()
        if attempts >= max_retries:
            conn.execute("UPDATE jobs SET state='dead', attempts=?, updated_at=? WHERE id=?", 
                         (attempts, now, job_id))
            print(f"💀 Job {job_id} failed permanently and moved to DLQ.")
        else:
            delay = get_config('backoff_base', default=2) ** attempts
            print(f"⚠️ Job {job_id} failed (attempt {attempts}/{max_retries}). Retrying in {delay}s.")
            time.sleep(delay)
            conn.execute("UPDATE jobs SET state='pending', attempts=?, updated_at=? WHERE id=?", 
                         (attempts, now, job_id))
        conn.commit()
        conn.close()

def run_worker():
    while True:
        conn = db.get_db()
        job = conn.execute("""
            SELECT * FROM jobs 
            WHERE state='pending' 
            ORDER BY created_at ASC 
            LIMIT 1
        """).fetchone()

        if job:
            conn.execute("UPDATE jobs SET state='processing', updated_at=? WHERE id=? AND state='pending'",
                         (datetime.utcnow().isoformat(), job['id']))
            conn.commit()
            conn.close()
            execute_job(job)
        else:
            conn.close()
            time.sleep(2)  # idle sleep when no job
