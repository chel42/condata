# Changelog

## [0.1.0] — Unreleased

- Ingestion CSV locale (`utils.io`)
- Modèles Pydantic de configuration et de résultats
- Profiling de base et Data Quality Score
- Orchestrateur `DatasetInspector`
- Statistiques descriptives (moyenne, médiane, min/max, quartiles, fréquences)
- Détection de potential outliers (IQR / Z-score)
- Corrélations Pearson (matrice, paires fortes, redondance, multicolinéarité)
- ML Readiness Score (heuristique, 8 checks documentés)
- Rapports HTML (Jinja2 / Plotly), JSON et résumé terminal (Rich)
- CLI `condata analyze`
- CI GitHub Actions (pytest + ruff)
