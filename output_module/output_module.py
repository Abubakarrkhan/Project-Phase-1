
from multiprocessing import Queue
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch


class DashboardConsumer:
    """
    Consumer process: drains processed_queue and renders the live dashboard.
    Observer : update_telemetry() is called by PipelineTelemetry (Subject).
    DataSink : write() accepts single packets directly.
    """

    # (config_key  ,  display label)
    _STREAM_DEFS: List[Tuple[str, str]] = [
        ("show_raw_stream",          "Raw Stream (Input \u2192 Core)"),
        ("show_intermediate_stream", "Verified Stream (Core \u2192 Aggregator)"),
        ("show_processed_stream",    "Processed Stream (Aggregator \u2192 Output)"),
    ]
    _TELE_KEYS = ["raw", "intermediate", "processed"]

    def __init__(
        self,
        config: Dict[str, Any],
        processed_queue: Queue,
        telemetry_subject,
    ) -> None:
        self._processed_queue           = processed_queue
        self._telemetry                 = telemetry_subject
        self._charts: List[Dict]        = config["visualizations"]["data_charts"]
        self._tele_cfg: Dict            = config["visualizations"]["telemetry"]
        self._max_size: int             = config["pipeline_dynamics"]["stream_queue_max_size"]

        self._telemetry.subscribe(self)

        self._x_data: List[List]        = [[] for _ in self._charts]
        self._y_data: List[List]        = [[] for _ in self._charts]
        self._tele_state: Dict[str,int] = {"raw": 0, "intermediate": 0, "processed": 0}

        # set by _build_figure
        self._fig        = None
        self._bar_fills:  List = []   # FancyBboxPatch per stream
        self._bar_texts:  List = []   # Text "N/50" per stream
        self._chart_axes: List = []

    # ── Observer ──────────────────────────────────────────────────────
    def update_telemetry(self, state: Dict[str, int]) -> None:
        self._tele_state = state

    # ── DataSink ──────────────────────────────────────────────────────
    def write(self, packet: Dict[str, Any]) -> None:
        self._route_packet(packet)

    # ── Main run loop ─────────────────────────────────────────────────
    def run(self) -> None:
        self._build_figure()
        plt.ion()
        sentinel_received = False

        while not sentinel_received:
            for _ in range(30):
                try:
                    packet = self._processed_queue.get(timeout=0.04)
                    if packet is None:
                        sentinel_received = True
                        break
                    self._route_packet(packet)
                except Exception:
                    break
            self._refresh()
            plt.pause(0.08)

        self._refresh()
        plt.ioff()
        plt.show()

    # ── Figure construction (once) ────────────────────────────────────
    def _build_figure(self) -> None:
        active         = self._active_streams()
        n_streams      = len(active)
        n_charts       = len(self._charts)

        # figure height: header + stream rows + chart rows
        fig_h = 1.0 + 0.62 * n_streams + 2.9 * n_charts + 0.5
        fig   = plt.figure(figsize=(14, max(fig_h, 7.0)), facecolor="white")
        try:
            fig.canvas.manager.set_window_title("Figure 1")
        except Exception:
            pass
        self._fig = fig

        # ── Title ────────────────────────────────────────────────────
        fig.text(
            0.5, 0.975,
            "GDP Pipeline \u2013 Phase 3 Real-Time Dashboard",
            ha="center", va="top",
            fontsize=14, fontweight="bold", color="black",
        )

        # ── Legend top-right ─────────────────────────────────────────
        legend_patches = [
            mpatches.Patch(facecolor="#4caf50", label="< 40% \u2013 flowing"),
            mpatches.Patch(facecolor="#ff9800", label="40\u201375% \u2013 filling"),
            mpatches.Patch(facecolor="#f44336", label="> 75% \u2013 backpressure"),
        ]
        fig.legend(
            handles=legend_patches,
            loc="upper right",
            bbox_to_anchor=(0.998, 0.985),
            fontsize=8,
            frameon=True,
            framealpha=0.95,
            edgecolor="#bbbbbb",
        )

        # ── Layout: streams section + charts section ──────────────────
        stream_h_ratio = 0.62 * n_streams
        chart_h_ratio  = 2.9  * n_charts
        total          = stream_h_ratio + chart_h_ratio

        gs_outer = gridspec.GridSpec(
            2, 1,
            figure=fig,
            top=0.93, bottom=0.05,
            hspace=0.12,
            height_ratios=[stream_h_ratio / total, chart_h_ratio / total],
        )

      