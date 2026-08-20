# CONDATA

Bibliothèque Python et CLI locale d'audit de qualité des datasets.

```bash
pip install condata
condata analyze dataset.csv
```

CONDATA profile un CSV, évalue sa qualité, et produit un résumé terminal ainsi qu'un rapport HTML interactif. Les données restent sur la machine.

## API Python

```python
from condata import DatasetInspector

inspector = DatasetInspector("dataset.csv")
result = inspector.analyze()
print(result.quality.score)
```

## Développement

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```
