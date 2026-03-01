
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


class GraphicsChartWriter:
    """Renders each result set as a Matplotlib chart."""

    def write(self, label: str, records: List[Any]) -> None:
        if not records:
            return

        lbl = label.lower()

        if "top 10" in lbl:
            self._horizontal_bar(label, records, "Country", "GDP", color="steelblue")
        elif "bottom 10" in lbl:
            self._horizontal_bar(label, records, "Country", "GDP", color="salmon")
        elif "growth rate per country" in lbl:
            self._horizontal_bar(label, records, "Country", "Growth_Rate_%",
                                 color="mediumseagreen", xlabel="Growth Rate (%)")
        elif "average gdp by continent" in lbl:
            self._bar_chart(label, records, "Continent", "Average_GDP")
        elif "global gdp trend" in lbl:
            self._line_chart(label, records, "Year", "Global_GDP")
        elif "fastest growing" in lbl:
            self._single_stat(label, records)
        elif "consistent gdp decline" in lbl:
            self._decline_comparison_chart(label, records)
        elif "contribution" in lbl:
            self._pie_chart(label, records, "Continent", "Contribution_%")

    def _horizontal_bar(self, title: str, records: List[dict],
                        key_col: str, val_col: str,
                        color: str = "skyblue", xlabel: str = "GDP (USD)") -> None:
        names  = [r.get(key_col, "") for r in records]
        values = [float(r.get(val_col, 0) or 0) for r in records]

        fig, ax = plt.subplots(figsize=(12, max(6, len(names) * 0.55)))
        ax.barh(names, values, color=color)
        ax.invert_yaxis()
        ax.set_xlabel(xlabel)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.xaxis.set_major_formatter(_gdp_formatter)
        plt.tight_layout()
        plt.show()

    def _bar_chart(self, title: str, records: List[dict],
                   key_col: str, val_col: str) -> None:
        names  = [r.get(key_col, "") for r in records]
        values = [float(r.get(val_col, 0) or 0) for r in records]

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(names, values, color="cornflowerblue")
        ax.set_ylabel(val_col)
        ax.set_title(title, fontsize=12, fontweight="bold")
        plt.xticks(rotation=30, ha="right")
        ax.yaxis.set_major_formatter(_gdp_formatter)
        plt.tight_layout()
        plt.show()

    def _line_chart(self, title: str, records: List[dict],
                    key_col: str, val_col: str) -> None:
        x = [r.get(key_col, "") for r in records]
        y = [float(r.get(val_col, 0) or 0) for r in records]

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(x, y, marker="o", linewidth=2, color="darkorange")
        ax.fill_between(x, y, alpha=0.15, color="darkorange")
        ax.set_xlabel(key_col)
        ax.set_ylabel(val_col)
        ax.set_title(title, fontsize=12, fontweight="bold")
        plt.xticks(rotation=45, ha="right")
        ax.yaxis.set_major_formatter(_gdp_formatter)
        plt.tight_layout()
        plt.show()

    def _pie_chart(self, title: str, records: List[dict],
                   label_col: str, val_col: str) -> None:
        labels = [r.get(label_col, "") for r in records]
        values = [float(r.get(val_col, 0) or 0) for r in records]

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140, pctdistance=0.85)
        ax.set_title(title, fontsize=12, fontweight="bold")
        plt.tight_layout()
        plt.show()

    @staticmethod
    def _single_stat(title: str, records: List[dict]) -> None:
        print(f"  {title}")
        for k, v in records[0].items():
            print(f"    {k}: {v}")

    def _decline_comparison_chart(self, title: str, records: List[dict]) -> None:
        """Grouped bar chart comparing GDP at start vs end year for declining countries."""
        if not records or not isinstance(records[0], dict):
            print(f"[GraphicsChartWriter] No declining countries found for: {title}")
            return

        keys        = list(records[0].keys())
        country_col = keys[0]
        start_col   = keys[1]
        end_col     = keys[2]

        countries  = [r[country_col] for r in records]
        start_vals = [float(r.get(start_col, 0) or 0) for r in records]
        end_vals   = [float(r.get(end_col, 0) or 0) for r in records]

        x, width = np.arange(len(countries)), 0.35

        fig, ax = plt.subplots(figsize=(max(8, len(countries) * 1.8), 6))
        ax.bar(x - width / 2, start_vals, width, label=start_col, color="steelblue")
        bars2 = ax.bar(x + width / 2, end_vals, width, label=end_col, color="tomato")

        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Country")
        ax.set_ylabel("GDP (USD)")
        ax.set_xticks(x)
        ax.set_xticklabels(countries, rotation=30, ha="right")
        ax.legend()
        ax.yaxis.set_major_formatter(_gdp_formatter)

        for bar, start, end in zip(bars2, start_vals, end_vals):
            if start > 0:
                pct = (end - start) / start * 100
                ax.annotate(f"{pct:.1f}%",
                            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            xytext=(0, 4), textcoords="offset points",
                            ha="center", va="bottom", fontsize=9, color="darkred")

        plt.tight_layout()
        plt.show()


class DashboardWriter:
    """Writes to both console and charts at the same time."""

    def __init__(self) -> None:
        self._console = ConsoleWriter()
        self._charts  = GraphicsChartWriter()

    def write(self, label: str, records: List[Any]) -> None:
        self._console.write(label, records)
        self._charts.write(label, records)