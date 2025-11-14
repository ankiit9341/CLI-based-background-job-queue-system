# queuectl/cli.py
import click
import json
import os
import sys
import signal
import subprocess
from datetime import datetime
from queuectl import db
from queuectl.config import get_config, set_config

PID_FILE = os.path.join(os.path.dirname(__file__), '..', 'queuectl_workers.pids')

@click.group()
def cli():
    """queuectl: A CLI-based background job queue system."""
    db.init_db()

@cli.command()
@click.argument('job_json')
def enqueue(job_json):
    """Enqueue a new job. Example: queuectl enqueue '{"id":"job1","command":"echo hi"}'"""
    try:
        job = json.loads(job_json)
        job_id = job.get("id")
        command = job.get("command")
        max_retries = int(job.get("max_retries", get_config('max_retries', 3)))
        if not job_id or not command:
            click.echo("Error: 'id' and 'command' fields are required.")
            return
        db.enqueue_job(job_id, command, max_retries=max_retries)
        click.echo(f"✅ Enqueued job '{job_id}' with command: {command}")
    except json.JSONDecodeError:
        click.echo("Error: Invalid JSON.")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.group()
def worker():
    """Manage worker processes."""
    pass

@worker.command('start')
@click.option('--count', default=1, help='Number of worker processes to start (background).')
def start(count):
    """Start worker processes in background and record PIDs."""
    click.echo(f"🚀 Starting {count} worker process(es)...")
    pids = []
    for _ in range(count):
        # spawn a new Python process that runs the package module worker_runner
        p = subprocess.Popen([sys.executable, "-m", "queuectl.worker_runner"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pids.append(p.pid)
    # append to PID file
    existing = []
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                existing = [int(x.strip()) for x in f if x.strip()]
        except Exception:
            existing = []
    with open(PID_FILE, 'w') as f:
        for pid in existing + pids:
            f.write(str(pid) + "\n")
    click.echo(f"Started worker PIDs: {pids}")
    click.echo("Use 'queuectl worker stop' to stop workers.")

@worker.command('stop')
def stop():
    """Stop background worker processes recorded in PID file."""
    if not os.path.exists(PID_FILE):
        click.echo("No workers PID file found.")
        return
    stopped = []
    remaining = []
    with open(PID_FILE, 'r') as f:
        pids = [line.strip() for line in f if line.strip()]
    for pid_s in pids:
        try:
            pid = int(pid_s)
            # try polite termination
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                # last resort
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
            stopped.append(pid)
        except Exception:
            remaining.append(pid_s)
    # rewrite PID file with any remaining PIDs
    if remaining:
        with open(PID_FILE, 'w') as f:
            for r in remaining:
                f.write(str(r) + "\n")
    else:
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
    click.echo(f"Stopped workers: {stopped}")

@cli.command('status')
def status():
    """Show summary of job states & active workers."""
    counts = db.counts_by_state()
    states = ['pending', 'processing', 'completed', 'failed', 'dead']
    click.echo("Job counts by state:")
    for s in states:
        click.echo(f"  {s}: {counts.get(s, 0)}")
    # active workers from PID file
    workers = 0
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            workers = len([l for l in f if l.strip()])
    click.echo(f"Active worker processes (tracked): {workers}")

@cli.command('list')
@click.option('--state', default=None, help='Filter jobs by state (pending, processing, completed, dead)')
def list_jobs(state):
    """List jobs (optionally filter by --state)."""
    rows = db.list_jobs(state=state)
    if not rows:
        click.echo("No jobs found.")
        return
    for r in rows:
        click.echo(f"- id={r['id']} state={r['state']} attempts={r['attempts']} max_retries={r['max_retries']} created_at={r['created_at']} command={r['command']}")

@cli.group()
def dlq():
    """Dead Letter Queue commands."""
    pass

@dlq.command('list')
def dlq_list():
    rows = db.list_jobs(state='dead')
    if not rows:
        click.echo("DLQ is empty.")
        return
    for r in rows:
        click.echo(f"- id={r['id']} attempts={r['attempts']} command={r['command']} updated_at={r['updated_at']}")

@dlq.command('retry')
@click.argument('job_id')
def dlq_retry(job_id):
    row = db.get_job(job_id)
    if not row:
        click.echo("Job not found.")
        return
    if row['state'] != 'dead':
        click.echo("Job is not in DLQ (state != dead).")
        return
    db.reset_job_to_pending(job_id)
    click.echo(f"✅ Job {job_id} reset to pending for retry.")

@cli.group()
def config():
    """Configuration management."""
    pass

@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    # convert some known keys to int where appropriate
    if key in ('max_retries', 'backoff_base'):
        try:
            value = int(value)
        except Exception:
            click.echo("Value must be integer for this key.")
            return
    set_config(key, value)
    click.echo(f"Config set: {key} = {value}")

@config.command('get')
@click.argument('key')
def config_get(key):
    val = get_config(key, default=None)
    click.echo(f"{key} = {val}")
