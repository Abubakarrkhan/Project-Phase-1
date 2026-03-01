


import csv
import json
from typing import Any, List

from core.contracts import PipelineService



def _clean_csv_row(row: dict) -> dict:
    """Convert digit-keyed year columns from str → float. Empty string becomes 0.0."""
    return {
        k: (float(v.strip()) if v.strip() else 0.0) if k.isdigit() else v
        for k, v in row.items()
    }


def _clean_json_row(row: dict) -> dict:
    """Convert digit-keyed year columns from int/float/None → float."""
    return {
        k: (float(v) if v is not None else 0.0) if k.isdigit() else v
        for k, v in row.items()
    }




class CSVReader:
    """Reads a GDP CSV file, cleans it, and passes rows to the engine."""

    def __init__(self, service: PipelineService, file_path: str) -> None:
        self._service   = service
        self._file_path = file_path

    def load(self) -> None:
        try:
            with open(self._file_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                cleaned: List[Any] = list(map(_clean_csv_row, reader))
            self._service.execute(cleaned)
        except FileNotFoundError:
            print(f"[CSVReader] File not found: {self._file_path}")
        except Exception as e:
            print(f"[CSVReader] Error: {e}")


class JSONReader:
    """Reads a GDP JSON file (list of record dicts) and passes rows to the engine."""

    def __init__(self, service: PipelineService, file_path: str) -> None:
        self._service   = service
        self._file_path = file_path

    def load(self) -> None:
        try:
            with open(self._file_path, encoding="utf-8") as f:
                raw: List[Any] = json.load(f)
            cleaned = list(map(_clean_json_row, raw))
            self._service.execute(cleaned)
        except FileNotFoundError:
            print(f"[JSONReader] File not found: {self._file_path}")
        except json.JSONDecodeError as e:
            print(f"[JSONReader] Invalid JSON: {e}")
        except Exception as e:
            print(f"[JSONReader] Error: {e}")
