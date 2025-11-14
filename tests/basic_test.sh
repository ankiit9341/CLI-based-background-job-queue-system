#!/bin/bash
# basic smoke test for bash
set -e

pip install -e .

queuectl enqueue '{"id":"sh_test_1","command":"echo bash_test"}'
queuectl worker start --count 1
sleep 4
queuectl status
queuectl list --state completed
queuectl worker stop
