# Single worker: see the comment in Dockerfile (QA finding #3) — this
# sandbox's session/case/audit state is in-memory and not shared across
# processes, so multiple workers would produce inconsistent results.
web: gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app
