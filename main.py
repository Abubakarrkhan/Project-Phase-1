"""
main.py — Orchestrator / Bootstrap
====================================
1. Load config.json
2. Instantiate the Output (Sink)
3. Instantiate the Core Engine, injecting the Sink
4. Instantiate the Input Reader, injecting the Engine
5. Trigger the pipeline

No business logic lives here. Swapping CSV ↔ JSON or
Console ↔ Chart ↔ Dashboard requires only a config.json change.
"""

import json
import sys

from core.engine import TransformationEngine
from plugins.inputs  import CSVReader, JSONReader
from plugins.outputs import ConsoleWriter, GraphicsChartWriter, DashboardWriter


INPUT_DRIVERS = {
    "csv":  CSVReader,
    "json": JSONReader,
}

OUTPUT_DRIVERS = {
    "console":   ConsoleWriter,
    "chart":     GraphicsChartWriter,
    "dashboard": DashboardWriter,
}


def load_config(path: str = "config.json") -> dict:
    try:
        with open(path) as f:
            cfg = json.load(f)
    except FileNotFoundError:
        sys.exit(f"[main] Config file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"[main] Invalid JSON in config: {e}")

    errors = []
    if not cfg.get("region") and cfg["region"] in ["Asia","Oceania","Europe","North America","South America","Africa","Global"]:

        errors.append("'region' is required")
    if not isinstance(cfg.get("year"), int) or cfg["year"] < 1960:
        errors.append("'year' must be an integer >= 1960")
    if "year_start" not in cfg or "year_end" not in cfg:
        errors.append("'year_start' and 'year_end' are required")
    elif cfg["year_start"] > cfg["year_end"]:
        errors.append("'year_start' must be <= 'year_end'")
    if cfg.get("input", "csv") not in INPUT_DRIVERS:
        errors.append(f"'input' must be one of {list(INPUT_DRIVERS)}")
    if cfg.get("output", "dashboard") not in OUTPUT_DRIVERS:
        errors.append(f"'output' must be one of {list(OUTPUT_DRIVERS)}")

    if errors:
        sys.exit("[main] Config errors:\n" + "\n".join(f"  • {e}" for e in errors))

    return cfg


def bootstrap(config_path: str = "config.json") -> None:
    cfg = load_config(config_path)

    print("\n========== GDP DASHBOARD ==========")
    print(f"  Region : {cfg['region']}")
    print(f"  Year   : {cfg['year']}")
    print(f"  Range  : {cfg['year_start']} – {cfg['year_end']}")
    print(f"  Input  : {cfg.get('input', 'csv').upper()}")
    print(f"  Output : {cfg.get('output', 'dashboard').upper()}")
    print("====================================")

    sink   = OUTPUT_DRIVERS[cfg.get("output", "dashboard")]()
    engine = TransformationEngine(sink=sink, config=cfg)

    input_key = cfg.get("input", "csv")
    reader    = INPUT_DRIVERS[input_key](service=engine, file_path=f"data/gdp.{input_key}")
    reader.load()


if __name__ == "__main__":
    bootstrap(sys.argv[1] if len(sys.argv) > 1 else "config.json")
