# Rapport HTML

Après `condata analyze dataset.csv`, CONDATA génère un fichier HTML autonome (CSS, logo et graphiques Plotly inclus) et l’ouvre dans le navigateur.

Toutes les valeurs affichées viennent du même `AnalysisResult` que le JSON et le terminal. La page ne calcule rien de supplémentaire.

## Structure de la page

L’ordre suit le cahier des charges (§16) : résumé, schéma, manquants, **doublons**, **statistiques**, distributions, corrélations, **warnings**, recommandations — plus le bloc **outliers**.

### Résumé général

- Lignes, colonnes, taille, types (**entier**, **réel**, **date/heure**, **texte**, **booléen**)
- Data Quality Score / 100
- ML Readiness Score / 100 (indicateur heuristique)

### Aperçu qualité, manquants, distribution

- Donut des checks ML Readiness (ok / attention / critique)
- Barres des valeurs manquantes par colonne
- Distribution d’une colonne numérique (si le DataFrame est fourni)

### Aperçu des colonnes (schéma)

Table : nom, type sémantique, non nuls, uniques, répétitions dans la colonne, % manquant.

### Doublons

Bloc dédié, aligné sur `quality.duplicates` :

| Champ | Signification |
| --- | --- |
| Lignes dupliquées | Nombre de lignes entièrement identiques à une ligne précédente |
| Taux | Pourcentage de lignes dupliquées |
| Statut | `OK` / `Attention` / `Critique` selon les seuils de `AnalysisConfig` |

CONDATA compare des **lignes entières**. Il signale, il ne déduplique pas.

### Warnings

Liste des problèmes détectés, même source que le tableau *Warnings* du terminal :

- issues de qualité (`quality.issues`) : manquants, doublons, types mixtes, incohérences catégorielles, colonnes constantes
- alertes de corrélation (`correlations.warnings`) : redondance, risque de multicolinéarité

Chaque ligne affiche la sévérité, la colonne concernée (ou `—`) et le message. Aucune donnée n’est modifiée.

### Outliers

Bloc dédié aux *potential outliers* (`outliers`) :

- total, nombre de colonnes concernées, méthode (`IQR` par défaut ou `Z-score`)
- table par colonne : nombre, taux, bornes, échantillon de valeurs

Une détection **n’implique pas une erreur**. Le rapport le rappelle explicitement. Les colonnes trop courtes ou à variance nulle sont indiquées comme non analysées.

### Statistiques

Deux tableaux issus de `statistics` :

**Entiers et réels** — N, moyenne, médiane, min, max, écart-type, Q1, Q3, P5, P95.

**Texte et booléens** — nombre de valeurs distinctes, valeur dominante, fréquence et part. Les listes de fréquences complètes restent dans le JSON (éventuellement tronquées si la cardinalité dépasse `max_category_frequencies`). Il n’y a pas de type « catégoriel » : voir [types.md](types.md).

### Corrélations

Heatmap Pearson des colonnes numériques, si au moins deux colonnes numériques sont disponibles.

### Recommandations

Actions suggérées (investiguer, ne pas drop/imputer automatiquement). Elles s’appuient sur les mêmes constats que les blocs ci-dessus.

## Export depuis la page

Les boutons *Exporter HTML / JSON* et *Partager* restent locaux : téléchargement du fichier déjà généré, ou copie d’un résumé texte. Aucun upload.

## Correspondance JSON

| Bloc HTML | Chemin JSON |
| --- | --- |
| Doublons | `quality.duplicates` |
| Warnings | `quality.issues` + `correlations.warnings` |
| Outliers | `outliers` |
| Statistiques | `statistics.numeric` / `statistics.categorical` |
| Scores | `quality.score`, `readiness.score` |
