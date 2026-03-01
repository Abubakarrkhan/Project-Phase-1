"""
plugins/outputs.py
==================
Output implementations: ConsoleWriter, GraphicsChartWriter, DashboardWriter.
All three satisfy the DataSink protocol owned by the Core.
"""

from typing import Any, List

import matplotlib.pyplot as plt
import numpy as np


# Shared GDP axis formatter: $1.2T / $345.6B / plain number
_gdp_formatter = plt.FuncFormatter(
    lambda x, _: f"${x/1e12:.1f}T" if abs(x) >= 1e12
    else (f"${x/1e9:.1f}B" if abs(x) >= 1e9 else f"{x:.1f}")
)


class ConsoleWriter:
    """Prints each result set as a plain text table."""

    _COL_WIDTH = 45

    def write(self, label: str, records: List[Any]) -> None:
        print(f"\n{'=' * 70}")
        print(f"  {label}")
        print(f"{'=' * 70}")

        if not records:
            print("  (no data)")
            return

        if isinstance(records[0], dict):
            keys = list(records[0].keys())
            header = "  ".join(k.ljust(self._COL_WIDTH) for k in keys)
            print(header)
            print("-" * min(len(header), 120))
            for rec in records:
                print("  ".join(str(rec.get(k, "")).ljust(self._COL_WIDTH) for k in keys))
        else:
            for rec in records:
                print(f"  {rec}")




class DashboardWriter:
    """Writes to both console and charts at the same time."""

    def __init__(self) -> None:
        self._console = ConsoleWriter()

    def write(self, label: str, records: List[Any]) -> None:
        self._console.write(label, records)
        self._charts.write(label, records)