
from collections import defaultdict
from typing import Any, Dict, List

from core.contracts import DataSink



def _gdp(row: Dict, year: str) -> float:
    """Return the GDP float for a year column, defaulting to 0.0."""
    val = row.get(year, 0.0)
    return float(val) if val and val != "" else 0.0


def _growth_rate(old: float, new: float) -> float:
    """Percentage growth from old to new. Returns 0.0 when base is zero."""
    return (new - old) / old * 100.0 if old else 0.0



_AGGREGATE_CODES = {
    "WLD", "LMY", "HIC", "MIC", "LIC", "LMC", "UMC",
    "EAP", "ECA", "LAC", "MNA", "SAR", "SSA", "NAC",
    "AFE", "AFW", "EAR", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS",
}


def _is_country(row: Dict) -> bool:
    return row.get("Country Code", "") not in _AGGREGATE_CODES


def _in_region(row: Dict, region: str) -> bool:
    return row.get("Continent") == region or row.get("Country Name") == region



# Engine


class TransformationEngine:
    """
    Implements PipelineService so Input plugins can call execute().
    Uses an injected DataSink so the Core never knows how results are rendered.
    """

    def __init__(self, sink: DataSink, config: dict) -> None:
        if not isinstance(sink, DataSink):
            raise TypeError("sink must satisfy the DataSink protocol")
        self._sink   = sink
        self._config = config

 
    # PipelineService interface
 

    def execute(self, raw_data: List[Any]) -> None:
        """Called by the Input plugin with the full cleaned dataset."""
        region       = self._config["region"]
        year         = self._config["year"]
        year_start   = self._config["year_start"]
        year_end     = self._config["year_end"]
        decline_years = self._config.get("decline_years", 5)

        region_rows = list(filter(lambda r: _in_region(r, region), raw_data))

        if not region_rows:
            self._sink.write("ERROR", [{"message": f"No data found for region: {region}"}])
            return

        self._sink.write(
            f"Top 10 Countries by GDP in {region} ({year})",
            _top_n(region_rows, str(year), 10, ascending=False),
        )
        self._sink.write(
            f"Bottom 10 Countries by GDP in {region} ({year})",
            _top_n(region_rows, str(year), 10, ascending=True),
        )
        self._sink.write(
            f"GDP Growth Rate per Country in {region} ({year_start}–{year_end})",
            _growth_rates(region_rows, year_start, year_end),
        )
        self._sink.write(
            f"Average GDP by Continent ({year_start}–{year_end})",
            _average_gdp_by_continent(raw_data, year_start, year_end),
        )
        self._sink.write(
            f"Total Global GDP Trend ({year_start}–{year_end})",
            _global_gdp_trend(raw_data, year_start, year_end),
        )
        self._sink.write(
            f"Fastest Growing Continent ({year_start}–{year_end})",
            [_fastest_growing_continent(raw_data, year_start, year_end)],
        )
        self._sink.write(
            f"Countries with Consistent GDP Decline (last {decline_years} years ending {year_end})",
            _consistent_decliners(region_rows, year_end, decline_years),
        )
        self._sink.write(
            f"Continent Contribution to Global GDP ({year_start}–{year_end})",
            _continent_contribution(raw_data, year_start, year_end),
        )



# Pure transformation functions


def _top_n(rows: List[Dict], year_col: str, n: int, ascending: bool) -> List[Dict]:
    keyed = [
        {"Country": r["Country Name"], "GDP": _gdp(r, year_col)}
        for r in rows if _is_country(r)
    ]
    return sorted(keyed, key=lambda x: x["GDP"], reverse=not ascending)[:n]



