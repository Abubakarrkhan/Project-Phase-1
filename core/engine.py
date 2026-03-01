
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


def _growth_rates(rows: List[Dict], year_start: int, year_end: int) -> List[Dict]:
    def compute(row: Dict) -> Dict:
        start = _gdp(row, str(year_start))
        end   = _gdp(row, str(year_end))
        return {
            "Country":      row["Country Name"],
            "GDP_Start":    start,
            "GDP_End":      end,
            "Growth_Rate_%": round(_growth_rate(start, end), 2),
        }

    return sorted(
        [compute(r) for r in rows if _is_country(r)],
        key=lambda x: x["Growth_Rate_%"],
        reverse=True,
    )


def _average_gdp_by_continent(all_rows: List[Dict], year_start: int, year_end: int) -> List[Dict]:
    years = [str(y) for y in range(year_start, year_end + 1)]
    buckets: Dict[str, List[float]] = defaultdict(list)

    for row in filter(_is_country, all_rows):
        continent = row.get("Continent", "Unknown")
        gdp_vals  = [v for y in years if (v := _gdp(row, y)) > 0]
        if gdp_vals:
            buckets[continent].extend(gdp_vals)

    return sorted(
        [{"Continent": c, "Average_GDP": round(sum(vals) / len(vals), 2)}
         for c, vals in buckets.items()],
        key=lambda x: x["Average_GDP"],
        reverse=True,
    )


def _global_gdp_trend(all_rows: List[Dict], year_start: int, year_end: int) -> List[Dict]:
    country_rows = [r for r in all_rows if _is_country(r)]
    return [
        {"Year": y, "Global_GDP": round(sum(_gdp(r, str(y)) for r in country_rows), 2)}
        for y in range(year_start, year_end + 1)
    ]


def _fastest_growing_continent(all_rows: List[Dict], year_start: int, year_end: int) -> Dict:
    totals: Dict[str, Dict[str, float]] = defaultdict(lambda: {"start": 0.0, "end": 0.0})

    for row in filter(_is_country, all_rows):
        continent = row.get("Continent", "Unknown")
        totals[continent]["start"] += _gdp(row, str(year_start))
        totals[continent]["end"]   += _gdp(row, str(year_end))

    rates = [
        {"Continent": c, "Growth_Rate_%": round(_growth_rate(v["start"], v["end"]), 2)}
        for c, v in totals.items()
    ]
    return max(rates, key=lambda x: x["Growth_Rate_%"])


def _consistent_decliners(rows: List[Dict], year_end: int, n_years: int) -> List[Dict]:
    years = [str(year_end - i) for i in range(n_years - 1, -1, -1)]

    def is_declining(row: Dict) -> bool:
        vals = [_gdp(row, y) for y in years]
        return all(prev > curr > 0 for prev, curr in zip(vals, vals[1:]))

    return [
        {
            "Country":           r["Country Name"],
            f"GDP_{years[0]}":   _gdp(r, years[0]),
            f"GDP_{years[-1]}":  _gdp(r, years[-1]),
        }
        for r in rows if _is_country(r) and is_declining(r)
    ]


def _continent_contribution(all_rows: List[Dict], year_start: int, year_end: int) -> List[Dict]:
    years        = [str(y) for y in range(year_start, year_end + 1)]
    totals: Dict[str, float] = defaultdict(float)

    for row in filter(_is_country, all_rows):
        continent = row.get("Continent", "Unknown")
        totals[continent] += sum(_gdp(row, y) for y in years)

    global_total = sum(totals.values())

    return sorted(
        [
            {
                "Continent":      c,
                "Total_GDP":      round(val, 2),
                "Contribution_%": round(val / global_total * 100 if global_total else 0, 2),
            }
            for c, val in totals.items()
        ],
        key=lambda x: x["Contribution_%"],
        reverse=True,
    )
