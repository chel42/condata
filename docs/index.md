# Documentation CONDATA

CONDATA est une bibliothèque Python et une CLI **locale** d’audit de qualité des datasets CSV (*Congo + Data*).

Elle profile un fichier, signale les problèmes, calcule un Data Quality Score et un ML Readiness Score, puis produit un résumé terminal, un JSON et un rapport HTML. Les données **ne quittent pas la machine**. CONDATA **signale**, il ne nettoie pas.

```bash
pip install -e .
condata analyze dataset.csv
```

## Sommaire

1. [Utilisation (CLI et API Python)](utilisation.md)
2. [Rapport HTML](rapport-html.md) — contenu de chaque bloc, y compris Doublons, Statistiques, Warnings, Outliers
3. [Types de colonnes](types.md) — entier, réel, date/heure, texte, booléen
4. [Scores](scores.md) — Data Quality et ML Readiness (règles documentées)

Le README à la racine du dépôt reste le point d’entrée court. Cette documentation détaille le comportement du produit.
