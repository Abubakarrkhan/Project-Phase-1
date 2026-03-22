

import threading
import time
from multiprocessing import Queue
from typing import Any, Callable, Dict, List, Optional


class PipelineTelemetry:


    def __init__(
        self,
        raw_queue: Queue,
        intermediate_queue: Queue,
        processed_queue: Queue,
        poll_interval: float = 0.2,
    ) -> None:
        self._raw_queue          = raw_queue
        self._intermediate_queue = intermediate_queue
        self._processed_queue    = processed_queue
        self._poll_interval      = poll_interval
        self._observers: List[Any] = []
        self._running            = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Observer registration
    # ------------------------------------------------------------------

    def subscribe(self, observer: Any) -> None:
        """Register an observer.  Observer must have update_telemetry(dict)."""
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: Any) -> None:
        self._observers = [o for o in self._observers if o is not observer]

    # ------------------------------------------------------------------
    # Subject lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background polling thread."""
        self._running = True
        self._thread  = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the polling thread to stop."""
        self._running = False

    # ------------------------------------------------------------------
    # Internal polling loop
    # ------------------------------------------------------------------

    def _poll_loop(self) -> None:
        while self._running:
            state = self._snapshot()
            self._notify(state)
            time.sleep(self._poll_interval)

    def _snapshot(self) -> Dict[str, int]:
        """Safely read queue sizes (qsize may raise on some platforms)."""
        def safe_qsize(q: Queue) -> int:
            try:
                return q.qsize()
            except NotImplementedError:
                return 0  # macOS multiprocessing.Queue does not support qsize

        return {
            "raw":          safe_qsize(self._raw_queue),
            "intermediate": safe_qsize(self._intermediate_queue),
            "processed":    safe_qsize(self._processed_queue),
        }

    def _notify(self, state: Dict[str, int]) -> None:
        for observer in self._observers:
            try:
                observer.update_telemetry(state)
            except Exception as exc:
                print(f"[Telemetry] Observer notification error: {exc}")
