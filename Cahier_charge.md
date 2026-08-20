# Cahier des charges — CONDATA

## 1. Identité du projet

**Nom :** CONDATA
**Signification :** *Congo + Data*
**Nature :** Bibliothèque Python + outil CLI de Data Quality et Data Profiling
**Positionnement :** outil destiné aux développeurs, Data Analysts, Data Scientists et ML Engineers
**Niveau :** projet portfolio professionnel
**Phase :** Phase 1 — Data Engineering / Data Quality

### Vision

> **CONDATA est un outil permettant d'analyser automatiquement un dataset depuis le terminal, d'évaluer sa qualité, d'identifier ses problèmes et de générer un rapport détaillé et interactif consultable dans un navigateur.**

L'utilisateur **ne clone pas le repository GitHub pour utiliser CONDATA**. Il installe le package et l'utilise comme une dépendance ou une commande CLI.

Exemple :

```bash
pip install condata
```

Puis :

```bash
condata analyze dataset.csv
```

---

# 2. Problématique

Avant d'utiliser un dataset pour de l'analyse de données ou du Machine Learning, il est nécessaire de savoir s'il est suffisamment fiable.

Un dataset peut contenir :

* des valeurs manquantes ;
* des doublons ;
* des valeurs aberrantes ;
* des types incorrects ;
* des catégories incohérentes ;
* des colonnes inutiles ;
* des distributions déséquilibrées ;
* des corrélations problématiques ;
* des problèmes susceptibles d'affecter un futur modèle ML.

Actuellement, un développeur ou Data Scientist doit souvent utiliser plusieurs bibliothèques, notebooks et scripts pour effectuer ces vérifications.

**CONDATA vise à centraliser cette première étape d'audit dans un outil simple à utiliser.**

---

# 3. Objectif général

Développer une bibliothèque Python et une interface CLI permettant à un utilisateur de fournir un dataset et d'obtenir automatiquement :

1. un profil détaillé du dataset ;
2. une analyse de sa qualité ;
3. la détection des principaux problèmes ;
4. des statistiques descriptives ;
5. des visualisations pertinentes ;
6. des recommandations ;
7. un indicateur de qualité ;
8. un indicateur de préparation au Machine Learning ;
9. un rapport HTML interactif ;
10. éventuellement des résultats exploitables par programme au format JSON.

---

# 4. Utilisateurs cibles

CONDATA est principalement destiné à :

### Data Scientist / ML Engineer

Il utilise CONDATA avant de commencer l'exploration ou l'entraînement d'un modèle.

```text
Dataset
   ↓
CONDATA
   ↓
Data Quality Report
   ↓
Préparation ML
   ↓
Training
```

### Data Analyst

Il utilise CONDATA pour comprendre rapidement la structure et la qualité d'un nouveau dataset avant son analyse.

### Data Engineer

Il peut utiliser CONDATA dans un pipeline de données ou intégrer la bibliothèque dans ses propres scripts.

### Développeur

Il peut utiliser la bibliothèque Python ou la CLI dans un projet logiciel nécessitant une validation des données.

---

# 5. Mode d'utilisation

CONDATA doit privilégier une utilisation **orientée développeur**, sans interface web d'upload.

## Utilisation CLI

Exemple principal :

```bash
condata analyze dataset.csv
```

CONDATA :

```text
lit le fichier
    ↓
profile le dataset
    ↓
analyse la qualité
    ↓
détecte les problèmes
    ↓
calcule les indicateurs
    ↓
génère le rapport
    ↓
ouvre le rapport dans le navigateur
```

Le terminal affiche également un résumé.

---

# 6. Architecture générale

```text
                    UTILISATEUR
                         │
                         ▼
                    CONDATA CLI
                         │
                         ▼
               ┌──────────────────┐
               │  CONDATA CORE     │
               │ Python Library    │
               └────────┬─────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    Profiling       Data Quality      Statistics
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                 ML Readiness
                        │
                        ▼
                Report Generator
                   │          │
                   ▼          ▼
                HTML        JSON
                   │
                   ▼
                Browser
```

---

# 7. Fonctionnalités principales

## 7.1 Dataset Profiling

CONDATA doit déterminer automatiquement :

* nombre de lignes ;
* nombre de colonnes ;
* taille du fichier ;
* types de données ;
* colonnes numériques ;
* colonnes catégorielles ;
* colonnes temporelles ;
* cardinalité ;
* valeurs uniques ;
* colonnes constantes.

Exemple :

```text
Rows       : 25,430
Columns    : 14
Numerical  : 8
Categorical: 5
Datetime   : 1
```

---

# 8. Analyse des valeurs manquantes

CONDATA doit détecter :

* nombre de valeurs manquantes ;
* pourcentage par colonne ;
* colonnes les plus affectées ;
* éventuellement les lignes concernées.

Exemple :

```text
weather       12.4%   ⚠
speed          3.2%   ⚠
region        0.0%    ✓
```

L'outil doit **signaler le problème**, sans supprimer automatiquement les données dans la première version.

---

# 9. Détection des doublons

Le système doit identifier :

* nombre de lignes dupliquées ;
* pourcentage de duplication ;
* éventuellement les colonnes pouvant servir d'identifiant.

Exemple :

```text
Duplicates: 427
Rate      : 1.68%
Status    : WARNING
```

---

# 10. Détection des valeurs aberrantes

Pour les variables numériques, CONDATA pourra utiliser notamment :

* IQR ;
* Z-score ;
* méthodes robustes selon le contexte.

Le rapport devra indiquer :

```text
Column: speed

Potential outliers: 83
Method: IQR
```

Important : **une valeur aberrante ne signifie pas nécessairement une erreur**. CONDATA doit donc parler de *potential outlier* ou *valeur potentiellement aberrante*.

---

# 11. Analyse statistique

Pour les variables numériques :

* moyenne ;
* médiane ;
* minimum ;
* maximum ;
* écart-type ;
* quartiles ;
* percentiles.

Pour les variables catégorielles :

* nombre de catégories ;
* fréquence ;
* catégorie dominante ;
* distribution.

---

# 12. Analyse des corrélations

CONDATA doit pouvoir analyser les relations entre variables numériques.

Le rapport pourra présenter :

* matrice de corrélation ;
* corrélations fortes ;
* variables fortement redondantes ;
* avertissements éventuels concernant la multicolinéarité.

Une visualisation sous forme de **heatmap** pourra être générée dans le rapport HTML.

---

# 13. Détection des incohérences

CONDATA doit pouvoir signaler des incohérences potentielles.

Exemple :

```text
Brazzaville
brazzaville
BRAZZAVILLE
```

Le système peut identifier :

> Possible categorical inconsistency.

Il doit éviter de modifier automatiquement les données sans règle explicitement définie.

---

# 14. Data Quality Score

CONDATA doit produire un indicateur synthétique permettant d'avoir une vision rapide de la qualité.

Exemple :

```text
DATA QUALITY SCORE

91 / 100
```

Le score devra être calculé à partir de règles documentées concernant notamment :

* valeurs manquantes ;
* doublons ;
* validité des types ;
* cohérence ;
* valeurs aberrantes ;
* contraintes définies.

Le score ne devra donc pas être arbitraire.

---

# 15. ML Readiness Score

C'est une fonctionnalité différenciante de CONDATA.

L'objectif est de répondre à :

> **« Mon dataset présente-t-il les conditions minimales pour commencer un projet de Machine Learning ? »**

Le système peut examiner :

```text
Schema                  ✓
Missing values          ⚠
Duplicates              ✓
Class balance           ⚠
Outliers                ⚠
Target variable         ✓
Data types              ✓
Potential leakage       ⚠
```

Puis produire :

```text
ML READINESS
82 / 100
```

Il s'agit d'un **indicateur heuristique**, pas d'une garantie que le dataset est réellement prêt pour le Machine Learning.

---

# 16. Génération du rapport

C'est l'un des éléments centraux du projet.

Après :

```bash
condata analyze dataset.csv
```

CONDATA génère :

```text
condata-report.html
```

et ouvre automatiquement le fichier dans le navigateur.

Le rapport doit présenter :

### Résumé général

```text
Dataset
Rows
Columns
Size
Quality Score
ML Readiness
```

### Schema

Table des colonnes :

| Colonne | Type   | Non-null | Unique |
| ------- | ------ | -------: | -----: |
| age     | int    |      98% |     52 |
| region  | string |     100% |     12 |
| speed   | float  |      97% |   1250 |

### Missing Values

Visualisation des valeurs manquantes.

### Duplicates

Analyse des doublons.

### Statistics

Statistiques descriptives.

### Distributions

Histogrammes et graphiques adaptés.

### Correlations

Matrice de corrélation.

### Warnings

Liste des problèmes détectés.

### Recommendations

Suggestions d'actions à effectuer.

---

# 17. Formats de sortie

CONDATA doit pouvoir produire plusieurs formats.

### HTML

```bash
condata analyze dataset.csv --format html
```

Destiné à la consultation humaine.

### JSON

```bash
condata analyze dataset.csv --format json
```

Destiné à l'automatisation et à l'intégration dans d'autres outils.

### Terminal

Un résumé doit toujours être affiché directement dans le terminal.

Le PDF pourra être envisagé dans une version ultérieure.

---

# 18. Bibliothèque Python

CONDATA ne doit pas être uniquement une CLI.

Le moteur doit être utilisable directement depuis Python.

Exemple conceptuel :

```python
from condata import DatasetInspector

dataset = DatasetInspector("dataset.csv")

result = dataset.analyze()

result.export_html("report.html")
```

Cela permet à un autre développeur d'intégrer CONDATA dans son propre projet.

---

# 19. Architecture logicielle interne

Le projet devra être organisé de manière modulaire.

Exemple :

```text
condata/
│
├── core/
│   ├── profiler.py
│   ├── quality.py
│   ├── statistics.py
│   ├── outliers.py
│   ├── correlations.py
│   └── readiness.py
│
├── cli/
│   └── commands.py
│
├── reporting/
│   ├── html.py
│   ├── json.py
│   └── templates/
│
├── models/
│   └── schemas.py
│
└── utils/
```

L'objectif est d'éviter d'avoir toute la logique dans un seul script.

---

# 20. Technologies envisagées

### Core

* Python 3
* Pandas
* NumPy

### CLI

**Typer** ou une technologie équivalente.

### Validation

* Pydantic

### Visualisation

* Plotly pour les graphiques interactifs.

### Rapport

* Jinja2 + HTML/CSS/JavaScript.

### Tests

* Pytest

### Packaging

* `pyproject.toml`
* build Python standard.

### Qualité du code

* Ruff
* éventuellement MyPy.

### Versionnement

* Git
* GitHub

### CI/CD

* GitHub Actions.

### Conteneurisation

* Docker, si nécessaire.

---

# 21. Formats de datasets

### MVP

Le support prioritaire sera :

```text
CSV
```

### Évolution

Puis :

```text
JSON
Excel
Parquet
```

Il ne faut pas essayer de supporter tous les formats dès la première version.

---

# 22. Sécurité et confidentialité

Point important : CONDATA travaille potentiellement avec des données sensibles.

La première version devra donc privilégier une architecture **locale**.

Lorsque l'utilisateur exécute :

```bash
condata analyze dataset.csv
```

les données restent sur sa machine.

Le projet ne doit pas envoyer automatiquement les datasets vers un serveur externe.

Cela constitue également un argument important pour l'utilisation professionnelle.

---

# 23. Workflow complet

Le workflow cible est :

```text
1. Installation
      ↓
pip install condata
      ↓
2. Analyse
      ↓
condata analyze dataset.csv
      ↓
3. Profiling
      ↓
4. Quality Analysis
      ↓
5. Statistics
      ↓
6. Anomaly Detection
      ↓
7. ML Readiness
      ↓
8. Report Generation
      ↓
9. Browser
      ↓
10. Decision
```

L'utilisateur décide ensuite s'il doit :

* nettoyer les données ;
* corriger les erreurs ;
* supprimer certaines colonnes ;
* effectuer du feature engineering ;
* poursuivre vers le Machine Learning.

---

# 24. MVP de CONDATA

Pour éviter que le projet devienne trop important, le **MVP** devra se limiter à :

```text
✓ CSV
✓ CLI
✓ Dataset profiling
✓ Missing values
✓ Duplicates
✓ Basic outlier detection
✓ Statistics
✓ Correlations
✓ Data Quality Score
✓ HTML report
✓ JSON output
✓ Tests
✓ Documentation
```

Le **ML Readiness Score** peut être inclus si son implémentation reste raisonnable.

---

# 25. Fonctionnalités futures

Après le MVP :

```text
V2
├── Dataset cleaning
├── Custom validation rules
└── Configuration YAML

V3
├── Excel
├── JSON
├── Parquet
└── Advanced profiling

V4
├── ML readiness avancé
├── Data drift detection
└── Dataset comparison

V5
├── Python API avancée
├── Plugin system
└── Intégration dans des pipelines ML
```

À terme, CONDATA pourrait devenir un outil de **Data Quality / Dataset Intelligence** plutôt qu'un simple analyseur CSV.

---

# 26. Structure du repository

```text
condata/
│
├── src/
│   └── condata/
│       ├── core/
│       ├── cli/
│       ├── reporting/
│       ├── models/
│       └── utils/
│
├── tests/
│
├── examples/
│
├── docs/
│
├── templates/
│
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
└── .gitignore
```

Le repository GitHub sera destiné au **code source et au développement du projet**. L'utilisateur final pourra installer CONDATA comme package Python.

---

# 27. Critères de réussite

CONDATA sera considéré comme réussi lorsque :

* l'installation fonctionne avec `pip` ;
* la commande CLI fonctionne ;
* un dataset CSV peut être analysé ;
* les problèmes principaux sont correctement détectés ;
* les statistiques sont cohérentes ;
* les résultats sont reproductibles ;
* le rapport HTML est généré automatiquement ;
* le rapport est lisible et professionnel ;
* un fichier JSON peut être généré ;
* les fonctions principales sont testées ;
* la documentation permet à un nouvel utilisateur de commencer sans assistance ;
* les données restent locales par défaut.

---

# 28. Valeur ajoutée du projet

CONDATA doit démontrer plusieurs compétences simultanément :

**Software Engineering**

* architecture modulaire ;
* CLI ;
* packaging ;
* tests ;
* documentation.

**Data Engineering**

* ingestion ;
* profiling ;
* validation ;
* qualité des données ;
* transformation.

**Data Science**

* statistiques ;
* distributions ;
* corrélations ;
* détection d'anomalies.

**Machine Learning**

* préparation des données ;
* ML Readiness ;
* identification de problèmes pouvant affecter un modèle.

**DevOps**

* Git ;
* GitHub Actions ;
* packaging ;
* éventuellement Docker.

---

# 29. Positionnement dans ton portfolio

CONDATA sera le **projet fondateur** de ta roadmap.

Il ne s'agit pas simplement d'un projet isolé.

La suite pourra être construite autour de lui :

```text
                 CONDATA
                    │
                    ▼
             Données propres
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     Projet ML           Projet Data
          │
          ▼
   Computer Vision
          │
          ▼
      IA générative
          │
          ▼
      AI Agents
```

Ainsi, lorsque tu présenteras ton portfolio, tu pourras montrer une progression logique :

> **Je commence par maîtriser la donnée → je construis des modèles → je les intègre dans des systèmes logiciels → je construis ensuite des systèmes IA plus complexes.**

---

## Résumé exécutif

**CONDATA** sera donc une **bibliothèque Python et une CLI locale d'analyse de qualité des datasets**.

Son utilisation principale sera extrêmement simple :

```bash
pip install condata
```

puis :

```bash
condata analyze mon_dataset.csv
```

CONDATA analysera automatiquement le dataset et fournira dans le terminal un résumé ainsi qu'un **rapport HTML interactif ouvert dans le navigateur**.

Le projet ne cherchera pas à remplacer les outils de Data Science ou les notebooks. Son rôle sera plutôt de devenir **la première étape d'audit d'un dataset avant son exploitation** :

> **« Avant de commencer mon analyse ou mon entraînement ML, je passe mon dataset dans CONDATA pour comprendre sa structure, identifier ses problèmes et évaluer sa qualité. »**

C'est cette proposition de valeur qui doit rester au centre de toute l'implémentation.
