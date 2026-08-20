# CONDATA

Bibliothèque Python et CLI locale d'audit de qualité des datasets
(*Congo + Data*).

```bash
pip install -e .
condata analyze dataset.csv
```

CONDATA lit un CSV **sur la machine**, profile le dataset, évalue sa qualité,
détecte les problèmes, calcule un score de préparation ML, affiche un résumé
dans le terminal, puis génère un rapport HTML interactif ouvert dans le
navigateur. Aucune donnée n'est envoyée vers un serveur.

## CLI

```bash
condata analyze dataset.csv
condata analyze dataset.csv --format json -o rapport.json
condata analyze dataset.csv --format all --no-browser
condata analyze dataset.csv --target label
condata --version
```

Par défaut : `condata-report.html` + ouverture du navigateur.

## API Python

```python
from condata import AnalysisConfig, DatasetInspector

inspector = DatasetInspector("dataset.csv")
result = inspector.analyze()

print(result.quality.score)
print(result.readiness.score)

result.export_html("report.html", frame=inspector.dataframe)
result.export_json("report.json")
```

## Ce que l'outil fait (MVP)

- Profiling (lignes, colonnes, types, cardinalité)
- Valeurs manquantes, doublons, incohérences catégorielles
- Statistiques descriptives
- Potential outliers (IQR / Z-score)
- Corrélations Pearson
- Data Quality Score et ML Readiness Score (heuristiques documentées)
- Rapport HTML / JSON / terminal

CONDATA **signale**, il ne nettoie pas les données.

## Développement

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

Les données de test restent locales (`tests/fixtures/`, `examples/`).
