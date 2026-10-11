"""Checks the three TODO items against a running worker."""
import json
import sys
import time

from worker import Worker

problems = []
config = json.load(open("config_v2.json", encoding="utf-8"))
if config.get("retry_limit") != 3:
    problems.append("config_v2.json: retry_limit is not 3")

w = Worker("config_v1.json")
if not hasattr(w, "pending") or not hasattr(w, "switch_config"):
    print("FAIL: Worker.pending or Worker.switch_config is missing")
    sys.exit(1)

for job in range(40):
    w.submit(job)
w.start()
time.sleep(0.05)
w.switch_config("config_v2.json")
switched = len(w.done)
for job in range(40, 60):
    w.submit(job)
deadline = time.time() + 20
while w.pending() and time.time() < deadline:
    time.sleep(0.01)
time.sleep(0.2)
w.stop()

ids = [job for job, _, _ in w.done]
if sorted(ids) != list(range(60)):
    lost = sorted(set(range(60)) - set(ids))
    twice = sorted({j for j in ids if ids.count(j) > 1})
    problems.append(f"jobs lost {lost[:5]} or settled twice {twice[:5]}")
if w.pending():
    problems.append(f"still pending: {w.pending()[:5]}")
if w.config.get("version") != 2:
    problems.append("the worker is not on config version 2")
mixed = [job for job, start, end in w.done if start != end]
if mixed:
    problems.append(f"jobs started on one config and settled on the other: {mixed[:5]}")
late = [start for _, start, _ in w.done[switched + 1:]]
if any(v != 2 for v in late):
    problems.append("jobs started after the switch still use version 1")

if problems:
    print("FAIL")
    print("\n".join(problems))
    sys.exit(1)
print("OK")
