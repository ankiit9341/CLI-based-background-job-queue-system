# queuectl/worker_runner.py
from .worker import run_worker

if __name__ == "__main__":
    # run single worker loop (blocks)
    run_worker()
