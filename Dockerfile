FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

# QA finding #3: _SESSIONS, FRAUD_CASES, CARDS, and AUDIT_LOG in
# server.py/data/fraud_cases.py/guardrails.py are in-memory Python
# structures with no cross-process sharing. Multiple Gunicorn workers
# do NOT share memory, so a request landing on a different worker than
# the one that verified a call would see it as unverified, and freeze
# state could disagree between workers. For this sandbox: exactly one
# worker, documented here rather than silently wrong. Roadmap: move
# session/state/audit to Redis or a real database before running
# multi-worker in any real deployment.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "server:app"]
