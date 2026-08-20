# Utilisation

## CLI

```bash
condata analyze dataset.csv
condata analyze dataset.csv --format json -o rapport.json
condata analyze dataset.csv --format all --no-browser
condata analyze dataset.csv --target label
condata --version
```

Par défaut, CONDATA écrit `condata-report.html` et l’ouvre dans le navigateur. Le terminal affiche toujours un résumé (profil, scores, schéma, warnings, recommandations).

`--format` :

| Valeur | Sortie |
| --- | --- |
| `html` | Rapport HTML (défaut) |
| `json` | Fichier JSON pour l’automatisation |
| `all` | HTML + JSON |

## API Python

```python
from condata import AnalysisConfig, DatasetInspector

inspector = DatasetInspector("dataset.csv")
result = inspector.analyze()

print(result.quality.score)
print(result.readiness.score)
print(result.quality.duplicates.n_duplicates)
print(result.statistics.numeric)
print(result.outliers.total_potential_outliers)

result.export_html("report.html", frame=inspector.dataframe)
result.export_json("report.json")
```

`frame=inspector.dataframe` permet de tracer les distributions dans le HTML. Sans DataFrame, le rapport reste complet pour les tableaux (doublons, stats, warnings, outliers) mais sans histogramme.

## Configuration

Les seuils (manquants, doublons, IQR, Z-score, corrélations) se règlent via `AnalysisConfig`. Ils ne sont pas des constantes magiques du moteur.

```python
config = AnalysisConfig(outlier_method="zscore", target_column="label")
inspector = DatasetInspector("dataset.csv", config=config)
```

## Périmètre MVP

Support : **CSV**. Excel, JSON et Parquet sont hors MVP. CONDATA n’envoie aucun dataset vers un serveur.
