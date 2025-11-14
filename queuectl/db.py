# queuectl/db.py
import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'queuectl.db')

def get_db():
    # allow multi-thread/process access; small timeout for locks
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            state TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    # Reset any jobs that were 'processing' (from an unclean shutdown) back to pending
    _reset_processing_jobs()

def _reset_processing_jobs():
    conn = get_db()
    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE jobs SET state='pending', updated_at=? WHERE state='processing'", (now,))
    conn.commit()
    conn.close()

# enqueue helper (used by CLI)
def enqueue_job(job_id, command, max_retries=3):
    now = datetime.utcnow().isoformat()
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO jobs (id, command, state, attempts, max_retries, created_at, updated_at)
            VALUES (?, ?, 'pending', 0, ?, ?, ?)
        """, (job_id, command, max_retries, now, now))
        conn.commit()
    finally:
        conn.close()

def fetch_and_claim_pending():
    """
    Atomically fetch one pending job and mark it 'processing'.
    Returns a sqlite3.Row or None.
    """
    conn = get_db()
    cur = conn.cursor()
    # Select oldest pending job
    cur.execute("""
        SELECT * FROM jobs WHERE state='pending' ORDER BY created_at ASC LIMIT 1
    """)
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    # Try to claim it: update only if still pending
    updated_at = datetime.utcnow().isoformat()
    cur.execute("UPDATE jobs SET state='processing', updated_at=? WHERE id=? AND state='pending'",
                (updated_at, row['id']))
    conn.commit()
    # Re-fetch to ensure the claimed state
    cur.execute("SELECT * FROM jobs WHERE id=?", (row['id'],))
    claimed = cur.fetchone()
    conn.close()
    return claimed

def update_job_state(job_id, state, attempts=None):
    conn = get_db()
    updated_at = datetime.utcnow().isoformat()
    if attempts is None:
        conn.execute("UPDATE jobs SET state=?, updated_at=? WHERE id=?", (state, updated_at, job_id))
    else:
        conn.execute("UPDATE jobs SET state=?, attempts=?, updated_at=? WHERE id=?", (state, attempts, updated_at, job_id))
    conn.commit()
    conn.close()

def increment_attempts_and_get(job_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT attempts FROM jobs WHERE id=?", (job_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    attempts = row['attempts'] + 1
    updated_at = datetime.utcnow().isoformat()
    cur.execute("UPDATE jobs SET attempts=?, updated_at=? WHERE id=?", (attempts, updated_at, job_id))
    conn.commit()
    # fetch max_retries
    cur.execute("SELECT attempts, max_retries FROM jobs WHERE id=?", (job_id,))
    row2 = cur.fetchone()
    conn.close()
    return dict(attempts=row2['attempts'], max_retries=row2['max_retries'])

def list_jobs(state=None):
    conn = get_db()
    cur = conn.cursor()
    if state:
        cur.execute("SELECT * FROM jobs WHERE state=? ORDER BY created_at ASC", (state,))
    else:
        cur.execute("SELECT * FROM jobs ORDER BY created_at ASC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_job(job_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    row = cur.fetchone()
    conn.close()
    return row

def reset_job_to_pending(job_id):
    conn = get_db()
    updated_at = datetime.utcnow().isoformat()
    conn.execute("UPDATE jobs SET state='pending', attempts=0, updated_at=? WHERE id=?", (updated_at, job_id))
    conn.commit()
    conn.close()

def counts_by_state():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT state, COUNT(*) as cnt FROM jobs GROUP BY state")
    rows = cur.fetchall()
    conn.close()
    result = {r['state']: r['cnt'] for r in rows}
    return result
