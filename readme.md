# Phase 3 – Generic Concurrent Real-Time Pipeline

## How to Run

```bash
cd phase-3
python main.py
# or with a custom config:
python main.py path/to/config.json
```

**Main file:** `main.py`  
**Data directory:** `data/`  
**Config file:** `config.json` (root level)

---

---

## Swapping to an Unseen Dataset

1. Place the new CSV in `data/`
2. Update `config.json`:
   - `"dataset_path"`: point to the new file
   - `"schema_mapping.columns"`: match source column names to internal mappings and write its data types 
   - `"processing.stateless_tasks.secret_key"`: use the provided key
3. Run `python main.py` – **zero code changes required**

---

## Project Structure

```
phase-3/
├── main.py                  # Entry-point / Central Orchestrator
├── config.json              # Full pipeline configuration
├── readme.md                # This file
│
├── core_module/
│   ├── __init__.py
│   └── core_module.py       # Contracts (DataSink, PipelineService)
│                            # + TransformationEngine (Scatter-Gather,
│                            #   Functional-Core / Imperative-Shell)
│
├── input_module/
│   ├── __init__.py
│   └── input_module.py      # InputProducer – schema-driven CSV reader
│
├── output_module/
│   ├── __init__.py
│   └── output_module.py     # DashboardConsumer – real-time matplotlib
│                            #   dashboard (Observer)
│
├── telemetry/
│   ├── __init__.py
│   └── telemetry.py         # PipelineTelemetry – Observer Subject
│
└── data/
    └── sample_sensor_data.csv
```



## Architecture Highlights

| Concern | Implementation |
|---|---|
| Generic ingestion | `schema_mapping` in config drives column mapping & casting |
| Concurrency | `multiprocessing.Process` – true multi-core (no GIL) |
| Backpressure | Bounded `multiprocessing.Queue(maxsize=N)` |
| Stateless parallelism | Scatter-Gather: each Core worker independently verifies signature |
| Stateful aggregation | Functional-Core / Imperative-Shell: sliding window average |
| Telemetry | Observer pattern: `PipelineTelemetry` (Subject) → `DashboardConsumer` (Observer) |
| DIP | Core owns `DataSink` & `PipelineService` protocols; nothing else imports Core internals |

---

## Dependencies

```
matplotlib
```

Install: `pip install matplotlib`
