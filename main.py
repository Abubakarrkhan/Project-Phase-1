
import json
import multiprocessing
import sys
import time
from multiprocessing import Process, Queue
from typing import Any, Dict, Optional

from core_module.core_module   import TransformationEngine
from input_module.input_module import InputProducer
from output_module.output_module import DashboardConsumer
from telemetry.telemetry         import PipelineTelemetry


# ---------------------------------------------------------------------------
# Worker entry-point functions  (must be module-level for pickle/spawn)
# ---------------------------------------------------------------------------

def _run_producer(config: Dict, raw_queue: Queue, num_workers: int) -> None:
    """Process target: InputProducer."""
    producer = InputProducer(config, raw_queue, num_workers)
    producer.run()


def _run_core_worker(
    config: Dict,
    raw_queue: Queue,
    intermediate_queue: Queue,
    worker_id: int,
) -> None:
    """
    Process target: one Core worker.
    Pulls packets from raw_queue, verifies + processes, pushes to intermediate_queue.
    Stops when it receives a None sentinel.
    """
    engine = TransformationEngine(config)
    while True:
        packet = raw_queue.get()
        if packet is None:
            # Pass sentinel downstream (one per aggregator input slot)
            intermediate_queue.put(None)
            break
        result: Optional[Dict] = engine.process(packet)
        if result is not None:
            intermediate_queue.put(result)


def _run_aggregator(
    intermediate_queue: Queue,
    processed_queue: Queue,
    num_workers: int,
) -> None:
    """
    Process target: Aggregator.
    Collects results from all Core workers in arrival order,
    forwards to processed_queue.  Stops after receiving num_workers sentinels.
    """
    sentinels_received = 0
    while sentinels_received < num_workers:
        packet = intermediate_queue.get()
        if packet is None:
            sentinels_received += 1
        else:
            processed_queue.put(packet)
    processed_queue.put(None)   # Signal DashboardConsumer


def _run_dashboard(config: Dict, processed_queue: Queue, telemetry) -> None:
    """Process target: DashboardConsumer."""
    consumer = DashboardConsumer(config, processed_queue, telemetry)
    consumer.run()


# ---------------------------------------------------------------------------
# Config loader & validator
# ---------------------------------------------------------------------------

def load_config(path: str = "config.json") -> Dict[str, Any]:
    try:
        with open(path, "r") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print(f"[main] config.json not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[main] Invalid JSON in config: {exc}")
        sys.exit(1)

    errors = []
    if not cfg.get("dataset_path"):
        errors.append("'dataset_path' is required")
    dyn = cfg.get("pipeline_dynamics", {})
    if not isinstance(dyn.get("core_parallelism"), int) or dyn["core_parallelism"] < 1:
        errors.append("'pipeline_dynamics.core_parallelism' must be an int >= 1")
    if not isinstance(dyn.get("stream_queue_max_size"), int) or dyn["stream_queue_max_size"] < 1:
        errors.append("'pipeline_dynamics.stream_queue_max_size' must be an int >= 1")
    if not cfg.get("schema_mapping", {}).get("columns"):
        errors.append("'schema_mapping.columns' must be a non-empty list")

    if errors:
        print("[main] Configuration errors:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

    return cfg


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def bootstrap(config_path: str = "config.json") -> None:
    cfg         = load_config(config_path)
    dyn         = cfg["pipeline_dynamics"]
    num_workers = dyn["core_parallelism"]
    max_size    = dyn["stream_queue_max_size"]

    print("\n========== GDP-STYLE PIPELINE – Phase 3 ==========")
    print(f"  Dataset       : {cfg['dataset_path']}")
    print(f"  Core workers  : {num_workers}")
    print(f"  Queue max size: {max_size}")
    print(f"  Input delay   : {dyn['input_delay_seconds']}s")
    print("=" * 50)

    # 1. Create bounded queues
    raw_queue          = Queue(maxsize=max_size)
    intermediate_queue = Queue(maxsize=max_size)
    processed_queue    = Queue(maxsize=max_size)

    # 2. Telemetry Subject
    telemetry = PipelineTelemetry(
        raw_queue, intermediate_queue, processed_queue, poll_interval=0.25
    )
    telemetry.start()

    # 3. Dashboard Consumer (Observer) – subscribes inside __init__
    consumer = DashboardConsumer(cfg, processed_queue, telemetry)

    # 4. Processes
    producer_proc = Process(
        target=_run_producer,
        args=(cfg, raw_queue, num_workers),
        name="InputProducer",
        daemon=True,
    )

    core_procs = [
        Process(
            target=_run_core_worker,
            args=(cfg, raw_queue, intermediate_queue, i),
            name=f"CoreWorker-{i}",
            daemon=True,
        )
        for i in range(num_workers)
    ]

    aggregator_proc = Process(
        target=_run_aggregator,
        args=(intermediate_queue, processed_queue, num_workers),
        name="Aggregator",
        daemon=True,
    )

    # Dashboard runs in main process so matplotlib can use the main thread
    # All other processes are started first
    producer_proc.start()
    for p in core_procs:
        p.start()
    aggregator_proc.start()

    print("[main] All pipeline processes started.")
    print("[main] Dashboard launching – close the window to exit.\n")

    # Run dashboard in the main process (GUI must be on main thread)
    consumer.run()

    # Cleanup
    telemetry.stop()
    producer_proc.join(timeout=5)
    for p in core_procs:
        p.join(timeout=5)
    aggregator_proc.join(timeout=5)
    print("\n[main] Pipeline complete.")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    bootstrap(config_path)
