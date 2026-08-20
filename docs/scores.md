# Scores

Les deux scores sont des **heuristiques documentées**, pas des notes magiques. Ils aident à prioriser l’audit, ils ne certifient ni la qualité métier ni la performance d’un modèle.

## Data Quality Score (/100)

Somme de quatre composantes bornées (`core/quality.py`) :

| Composante | Points | Règle |
| --- | ---: | --- |
| Completeness | 35 | Taux global de cellules manquantes. 0 % → 35 ; ≥ seuil `missing_zero_score_pct` → 0 ; linéaire entre les deux |
| Uniqueness | 25 | Taux de lignes dupliquées. 0 % → 25 ; ≥ `duplicate_zero_score_pct` → 0 |
| Validity | 20 | 20 au départ, −5 par colonne au type mixte (plancher 0) |
| Consistency | 20 | 20 au départ, −5 par colonne catégorielle incohérente (casse / espaces) |

Les **outliers n’entrent pas** dans ce score : ils sont traités à part (bloc HTML Outliers + composante ML Readiness). Le cahier les cite parmi les signaux possibles ; le MVP les isole pour ne pas confondre « hors-norme » et « erreur ».

## ML Readiness Score (/100)

Répond à : *le dataset a-t-il les conditions minimales pour commencer un projet ML ?* Ce n’est **pas** une garantie.

Huit checks (`core/readiness.py`) :

| Check | Points |
| --- | ---: |
| Schema (≥ 2 colonnes, volume minimal) | 15 |
| Missing values | 15 |
| Duplicates | 10 |
| Data types | 10 |
| Outliers (taux moyen de potential outliers) | 15 |
| Class balance (si cible catégorielle) | 15 |
| Target variable (fournie, inférée, ou absente) | 10 |
| Potential leakage | 10 |

La cible se configure avec `--target` / `AnalysisConfig.target_column`. Sinon, une colonne nommée `target`, `label`, `class`, `y` ou `outcome` peut être inférée.

## Lecture des pastilles

| Pastille | Score |
| --- | ---: |
| Bonne qualité / Prêt pour le ML | ≥ 80 |
| Qualité moyenne / Moyennement prêt | 50–79 |
| Qualité faible / Peu prêt | &lt; 50 |
