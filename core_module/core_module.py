
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
    """
    Pure function – returns True only if the packet's signature is valid.
    raw_value is rounded to 2 decimal places before signing (spec requirement).
    """
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


