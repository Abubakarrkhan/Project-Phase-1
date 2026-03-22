
import hashlib
from collections import deque
from functools import reduce
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Contracts  (DIP: Core owns the abstractions)
# ---------------------------------------------------------------------------

@runtime_checkable
class DataSink(Protocol):
    """Output plugin contract – receives processed result packets."""
    def write(self, packet: Dict[str, Any]) -> None:
        ...


@runtime_checkable
class PipelineService(Protocol):
    """Core worker contract – called by the Input process per raw packet."""
    def process(self, raw_packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ...


# ---------------------------------------------------------------------------
# Pure functional helpers  (stateless – safe for multiprocessing)
# ---------------------------------------------------------------------------

def _generate_signature(raw_value_str: str, key: str, iterations: int) -> str:
    
    password_bytes = key.encode("utf-8")
    salt_bytes = raw_value_str.encode("utf-8")
    hash_bytes = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password_bytes,
        salt=salt_bytes,
        iterations=iterations,
    )
    return hash_bytes.hex()


def _verify_packet(
    packet: Dict[str, Any],
    key: str,
    iterations: int,
    value_field: str = "metric_value",
    hash_field: str = "security_hash",
) -> bool:
    
    raw_val = packet.get(value_field)
    expected_sig = packet.get(hash_field, "")
    if raw_val is None:
        return False
    raw_value_str = f"{float(raw_val):.2f}"
    actual_sig = _generate_signature(raw_value_str, key, iterations)
    return actual_sig == expected_sig


def _compute_running_average(window: deque) -> float:
    """Pure function – average of a window of floats."""
    if not window:
        return 0.0
    return reduce(lambda acc, x: acc + x, window, 0.0) / len(window)


# ---------------------------------------------------------------------------
# TransformationEngine  – Scatter-Gather + Functional-Core / Imperative-Shell
# ---------------------------------------------------------------------------

class TransformationEngine:
    
    def __init__(self, config: Dict[str, Any]) -> None:
        proc = config.get("processing", {})

        # Stateless task config
        stateless = proc.get("stateless_tasks", {})
        self._secret_key: str = stateless.get("secret_key", "")
        self._iterations: int = stateless.get("iterations", 100000)

        # Stateful task config
        stateful = proc.get("stateful_tasks", {})
        self._window_size: int = stateful.get("running_average_window_size", 10)

        # Imperative Shell: mutable sliding window (per-engine-instance state)
        self._window: deque = deque(maxlen=self._window_size)

    # ------------------------------------------------------------------
    # PipelineService interface
    # ------------------------------------------------------------------

    def process(self, raw_packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
     
        # --- Scatter-Gather: stateless verification (pure function) ---
        is_valid = _verify_packet(
            raw_packet,
            key=self._secret_key,
            iterations=self._iterations,
        )
        if not is_valid:
            return None  # Drop unverified packet

        # --- Functional-Core / Imperative-Shell: sliding window average ---
        # Imperative Shell: update mutable state
        metric_value = float(raw_packet.get("metric_value", 0.0))
        self._window.append(metric_value)

        # Functional Core: pure computation on an immutable snapshot
        window_snapshot: List[float] = list(self._window)
        running_avg = _compute_running_average(deque(window_snapshot))

        # Build enriched output packet
        result = dict(raw_packet)
        result["verified"] = True
        result["computed_metric"] = round(running_avg, 4)
        return result
