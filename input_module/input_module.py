
import csv
import time
from multiprocessing import Queue
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# InputProducer
# ---------------------------------------------------------------------------

class InputProducer:
    """
    Producer process: reads the dataset and feeds the raw_queue.

    Designed to run inside a multiprocessing.Process – call run().
    After all rows are sent, pushes one None sentinel per Core worker
    so each worker knows when to stop.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        raw_queue: Queue,
        num_workers: int,
    ) -> None:
        self._dataset_path: str  = config["dataset_path"]
        self._delay: float       = config["pipeline_dynamics"]["input_delay_seconds"]
        self._column_map         = _build_column_map(config["schema_mapping"]["columns"])
        self._raw_queue: Queue   = raw_queue
        self._num_workers: int   = num_workers

    def run(self) -> None:
        """Entry-point for the producer process."""
        try:
            with open(self._dataset_path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    packet = _map_row(row, self._column_map)
                    self._raw_queue.put(packet)          # blocks if queue is full → backpressure
                    time.sleep(self._delay)
        except FileNotFoundError:
            print(f"[InputProducer] File not found: {self._dataset_path}")
        except Exception as exc:
            print(f"[InputProducer] Error: {exc}")
        finally:
            # Send one sentinel per worker to signal end-of-stream
            for _ in range(self._num_workers):
                self._raw_queue.put(None)


