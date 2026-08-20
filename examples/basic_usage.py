"""Exemple d'intégration de l'API Python CONDATA."""

from pathlib import Path

from condata import DatasetInspector

DATASET = Path(__file__).resolve().parent / "sample_dataset.csv"


def main() -> None:
    result = DatasetInspector(DATASET).analyze()
    print(f"Quality score: {result.quality.score}/100")
    print(f"Rows: {result.profile.n_rows} | Columns: {result.profile.n_columns}")
    for issue in result.quality.issues:
        location = f" [{issue.column}]" if issue.column else ""
        print(f"- {issue.severity}{location}: {issue.message}")


if __name__ == "__main__":
    main()
