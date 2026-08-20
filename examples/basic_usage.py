"""Exemple d'intégration de l'API Python CONDATA."""

from pathlib import Path

from condata import DatasetInspector

DATASET = Path(__file__).resolve().parent / "sample_dataset.csv"


def main() -> None:
    inspector = DatasetInspector(DATASET)
    result = inspector.analyze()
    print(f"Quality score: {result.quality.score}/100")
    print(f"ML readiness: {result.readiness.score}/100")
    print(f"Rows: {result.profile.n_rows} | Columns: {result.profile.n_columns}")
    html = result.export_html("condata-report.html", frame=inspector.dataframe)
    json_path = result.export_json("condata-report.json")
    print(f"HTML: {html}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
