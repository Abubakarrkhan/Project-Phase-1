

import csv
from core.contracts import PipelineService



def _clean_csv_row(row: dict) -> dict:
    return {
        k: (float(v.strip()) if v.strip() else 0.0) if k.isdigit() else v
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
                rows = [_clean_csv_row(r) for r in csv.DictReader(f)]
            self._service.execute(rows)
        except FileNotFoundError:
            print(f"[CSVReader] File not found: {self._file_path}")
        except Exception as e:
            print(f"[CSVReader] Error: {e}")



