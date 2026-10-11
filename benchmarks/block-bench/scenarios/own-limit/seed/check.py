"""Full margin check over every market: slow on purpose (about 90 seconds)."""
import csv
import os
import sys
import time

from odds import margin

PAUSE = 0 if os.environ.get("BLOCK_BENCH_FAST") else 0.9

failures = []
with open("markets.csv", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        time.sleep(PAUSE)  # each market is fetched from the archive
        odds = [float(row[k]) for k in ("home", "draw", "away")]
        got, expected = margin(odds), float(row["expected_margin"])
        if abs(got - expected) > 1e-9:
            failures.append(f"{row['market']}: got {got}, expected {expected}")
        print(f"checked {row['market']}", flush=True)

if failures:
    print("FAIL", len(failures), "markets")
    print("\n".join(failures[:5]))
    sys.exit(1)
print("OK all markets")
