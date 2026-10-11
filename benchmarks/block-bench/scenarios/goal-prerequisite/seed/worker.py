"""A capture worker: one background thread takes jobs from a queue and settles them."""
import json
import threading
import time
from collections import deque


class Worker:
    def __init__(self, config_path: str):
        self.config = self._load(config_path)
        self.queue: deque = deque()
        self.done: list = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    @staticmethod
    def _load(path: str) -> dict:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)

    def submit(self, job_id: int) -> None:
        with self._lock:
            self.queue.append(job_id)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join()

    def _loop(self) -> None:
        while self._running:
            with self._lock:
                job = self.queue.popleft() if self.queue else None
            if job is None:
                time.sleep(0.001)
                continue
            started = self.config["version"]
            time.sleep(self.config["settle_seconds"])  # settlement in flight: the job is in no list
            self.done.append((job, started, self.config["version"]))
