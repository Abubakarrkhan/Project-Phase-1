

from multiprocessing import Queue
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch




def _bar_color(current: int, max_size: int) -> str:
    """Green < 40 % | Orange 40-75 % | Red > 75 %  (matches screenshot legend)."""
    ratio = current / max_size if max_size > 0 else 0
    if ratio < 0.40:
        return "#4caf50"
    if ratio < 0.75:
        return "#ff9800"
    return "#f44336"


# ---------------------------------------------------------------------------
# DashboardConsumer
# ---------------------------------------------------------------------------

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

        # ── Stream progress-bar rows ──────────────────────────────────
        gs_streams = gridspec.GridSpecFromSubplotSpec(
            n_streams, 1,
            subplot_spec=gs_outer[0],
            hspace=0.05,
        )

        BAR_LEFT   = 0.40   # axes-fraction where bar starts
        BAR_WIDTH  = 0.52   # max bar width in axes fraction
        BAR_BOTTOM = 0.20
        BAR_HEIGHT = 0.60

        for row_i, (tele_key, label) in enumerate(active):
            ax = fig.add_subplot(gs_streams[row_i])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")

            # panel background
            ax.add_patch(FancyBboxPatch(
                (0.005, 0.05), 0.990, 0.90,
                boxstyle="round,pad=0.01",
                linewidth=0.7, edgecolor="#cccccc", facecolor="#f7f7f7",
                transform=ax.transAxes, zorder=1,
            ))

            # stream label
            ax.text(
                0.012, 0.50, label,
                transform=ax.transAxes,
                ha="left", va="center",
                fontsize=9.5, color="#222222", zorder=3,
            )

            # grey track
            ax.add_patch(FancyBboxPatch(
                (BAR_LEFT, BAR_BOTTOM), BAR_WIDTH, BAR_HEIGHT,
                boxstyle="round,pad=0.005",
                linewidth=0.5, edgecolor="#bbbbbb", facecolor="#e0e0e0",
                transform=ax.transAxes, zorder=2,
            ))

            # green fill (starts empty)
            fill = FancyBboxPatch(
                (BAR_LEFT, BAR_BOTTOM), 0.0, BAR_HEIGHT,
                boxstyle="square,pad=0.0",
                linewidth=0, edgecolor="none", facecolor="#4caf50",
                transform=ax.transAxes, zorder=3,
            )
            ax.add_patch(fill)
            self._bar_fills.append(fill)

            # counter text
            txt = ax.text(
                BAR_LEFT + BAR_WIDTH + 0.015, 0.50,
                f"0/{self._max_size}",
                transform=ax.transAxes,
                ha="left", va="center",
                fontsize=9, color="#444444", zorder=4,
            )
            self._bar_texts.append(txt)

        # ── Chart axes ────────────────────────────────────────────────
        gs_charts = gridspec.GridSpecFromSubplotSpec(
            n_charts, 1,
            subplot_spec=gs_outer[1],
            hspace=0.55,
        )

        LINE_COLORS = ["#1f77b4", "#ff7f0e"]

        for ci, chart in enumerate(self._charts):
            ax = fig.add_subplot(gs_charts[ci])
            self._style_chart_ax(ax, chart)
            label = "metric_value" if ci == 0 else "running avg"
            ax.plot([], [], color=LINE_COLORS[ci % 2], linewidth=1.3, label=label)
            ax.legend(loc="upper left", fontsize=8, frameon=True,
                      framealpha=0.8, edgecolor="#cccccc")
            self._chart_axes.append(ax)

    # ── Per-frame refresh ─────────────────────────────────────────────
    def _refresh(self) -> None:
        self._update_bars()
        self._update_charts()
        try:
            self._fig.canvas.draw_idle()
            self._fig.canvas.flush_events()
        except Exception:
            pass

    def _update_bars(self) -> None:
        BAR_WIDTH = 0.52
        for i, (tele_key, _) in enumerate(self._active_streams()):
            if i >= len(self._bar_fills):
                break
            current = self._tele_state.get(tele_key, 0)
            ratio   = min(current / self._max_size, 1.0) if self._max_size > 0 else 0
            self._bar_fills[i].set_width(BAR_WIDTH * ratio)
            self._bar_fills[i].set_facecolor(_bar_color(current, self._max_size))
            self._bar_texts[i].set_text(f"{current}/{self._max_size}")

    def _update_charts(self) -> None:
        LINE_COLORS = ["#1f77b4", "#ff7f0e"]
        for ci, (ax, chart) in enumerate(zip(self._chart_axes, self._charts)):
            if not self._x_data[ci]:
                continue
            ax.clear()
            self._style_chart_ax(ax, chart)
            label = "metric_value" if ci == 0 else "running avg"
            ax.plot(
                self._x_data[ci], self._y_data[ci],
                color=LINE_COLORS[ci % 2], linewidth=1.3, label=label,
            )
            ax.legend(loc="upper left", fontsize=8, frameon=True,
                      framealpha=0.8, edgecolor="#cccccc")

    # ── Helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _style_chart_ax(ax, chart: Dict) -> None:
        ax.set_facecolor("white")
        ax.set_title(chart["title"], fontsize=11, fontweight="normal",
                     color="black", pad=6)
        ax.set_xlabel(chart["x_axis"], fontsize=9, color="#555555")
        ax.set_ylabel(chart["y_axis"], fontsize=9, color="#555555")
        ax.tick_params(colors="#555555", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#cccccc")
            spine.set_linewidth(0.7)
        ax.grid(True, linestyle="--", linewidth=0.4, color="#dddddd", alpha=0.9)

    def _active_streams(self) -> List[Tuple[str, str]]:
        result = []
        for (cfg_key, label), tele_key in zip(self._STREAM_DEFS, self._TELE_KEYS):
            if self._tele_cfg.get(cfg_key, False):
                result.append((tele_key, label))
        return result

    def _route_packet(self, packet: Dict[str, Any]) -> None:
        for i, chart in enumerate(self._charts):
            x_key = chart["x_axis"]
            y_key = chart["y_axis"]
            if x_key in packet and y_key in packet:
                self._x_data[i].append(packet[x_key])
                self._y_data[i].append(float(packet[y_key]))
