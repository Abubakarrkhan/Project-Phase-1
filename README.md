# GDP Dashboard – Phase 2
## Modular Architecture with Dependency Inversion Principle

---

## Project Structure

```
gdp_dashboard/
├── main.py               # Orchestrator / Bootstrap entry-point
├── config.json           # Runtime configuration (swap IO without code changes)
├── architecture.puml     # PlantUML diagram of full architecture
│
├── core/                 # Domain package – owns contracts & logic
│   ├── __init__.py
│   ├── contracts.py      # DataSink & PipelineService Protocols (the "boss")
│   └── engine.py         # TransformationEngine – all 8 analytics
│
├── plugins/              # Plugin package – I/O implementations
│   ├── __init__.py
│   ├── inputs.py         # CSVReader, JSONReader
│   └── outputs.py        # ConsoleWriter, GraphicsChartWriter, DashboardWriter
│
└── data/
    └── gdp.csv           # World Bank GDP dataset (1960–2024)
```

---

## Configuration (`config.json`)

| Key            | Type    | Description                                      |
|----------------|---------|--------------------------------------------------|
| `region`       | string  | Continent name or exact Country Name             |
| `year`         | int     | Single year for Top/Bottom 10 analysis           |
| `year_start`   | int     | Start year for range analytics                   |
| `year_end`     | int     | End year for range analytics                     |
| `decline_years`| int     | How many consecutive years to check for decline  |
| `input`        | string  | `"csv"` or `"json"` – selects Input plugin       |
| `output`       | string  | `"console"`, `"chart"`, or `"dashboard"`         |


---

## How to Run

```bash
python main.py
```

---

## Analytics Produced (all 8 required outputs)

1. **Top 10 Countries by GDP** – for the given region & year
2. **Bottom 10 Countries by GDP** – for the given region & year
3. **GDP Growth Rate per Country** – for the given region & date range
4. **Average GDP by Continent** – for the given date range
5. **Total Global GDP Trend** – year-by-year for the given range
6. **Fastest Growing Continent** – for the given date range
7. **Countries with Consistent GDP Decline** – over last N years
8. **Continent Contribution to Global GDP** – for the given date range

---

## Dependency Inversion Rules Satisfied

| Rule | Implementation |
|------|---------------|
| **Inbound Abstraction** | `CSVReader` / `JSONReader` call only `PipelineService.execute()` – never import `TransformationEngine` |
| **Outbound Abstraction** | `TransformationEngine` calls only `DataSink.write()` – never imports writers |
| **Core owns contracts** | `DataSink` and `PipelineService` protocols live in `core/contracts.py` |
| **DI via constructor** | Sink injected into Engine; Engine injected into Reader in `main.py` |
| **Factory / Registry** | `INPUT_DRIVERS` and `OUTPUT_DRIVERS` dicts in `main.py` map config strings to classes |

---

## Architecture Diagram

See `architecture.puml`.  Render with any PlantUML tool, e.g.:
- https://www.plantuml.com/plantuml/uml/
- VS Code PlantUML extension
