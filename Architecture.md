condata/
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Tests automatisés (pytest, ruff) à chaque push
│       └── release.yml                # Publication automatique sur PyPI lors d'un tag
├── docs/                              # Documentation projet (MkDocs / Sphinx)
├── examples/
│   ├── basic_usage.py                 # Exemple d'intégration de l'API Python
│   └── sample_dataset.csv             # Dataset de démonstration pour tester la CLI
├── src/
│   └── condata/
│       ├── __init__.py                # Expose la version et DatasetInspector
│       ├── py.typed                   # Marker d'annotation de types PEP 561 (MyPy)
│       │
│       ├── core/                      # MOTEUR METIER (Indépendant de la CLI/UI)
│       │   ├── __init__.py
│       │   ├── inspector.py           # Classe principale DatasetInspector (Orchestrateur)
│       │   ├── profiler.py            # Profiling de base (lignes, colonnes, types)
│       │   ├── quality.py             # Calcul du Data Quality Score (Règles métiers)
│       │   ├── statistics.py          # Stats descriptives (numériques et catégorielles)
│       │   ├── outliers.py            # Détection d'anomalies (IQR, Z-score)
│       │   ├── correlations.py        # Calcul des matrices de corrélation
│       │   └── readiness.py           # Calcul du ML Readiness Score
│       │
│       ├── models/                    # STRUCTURES DE DONNÉES (Pydantic)
│       │   ├── __init__.py
│       │   ├── config.py              # Configuration des seuils d'analyse
│       │   └── schema.py              # Data models de sortie (AnalysisResult)
│       │
│       ├── reporting/                 # FORMATAGE ET EXPORT DES RESULTATS
│       │   ├── __init__.py
│       │   ├── html.py                # Moteur Jinja2 / Générateur du rapport HTML
│       │   ├── json.py                # Serialiseur JSON des résultats Pydantic
│       │   ├── terminal.py            # Rendu CLI enrichi (tableaux Rich)
│       │   └── templates/
│       │       ├── report.html.j2     # Template Jinja2 principal
│       │       ├── assets/            # CSS / JS inlinés (Plotly, styling)
│       │       └── components/        # Sub-templates (cards, tables, charts)
│       │
│       ├── cli/                       # INTERFACE LIGNE DE COMMANDE (Typer)
│       │   ├── __init__.py
│       │   ├── main.py                # Entrée CLI principale (app = typer.Typer())
│       │   └── commands/
│       │       ├── analyze.py         # Commande `condata analyze`
│       │       └── version.py         # Commande `condata --version`
│       │
│       └── utils/                     # UTILITAIRES INTERNES
│           ├── __init__.py
│           ├── io.py                  # Ingestion sécurisée (chargement des CSV)
│           └── formatters.py          # Formatage des octets, pourcentages, nombres
│
├── tests/                             # SUITE DE TESTS (Pytest)
│   ├── conftest.py                    # Fixtures Pytest (DataFrames de test)
│   ├── unit/                          # Tests unitaires des modules core/
│   │   ├── test_profiler.py
│   │   ├── test_quality.py
│   │   ├── test_outliers.py
│   │   └── test_readiness.py
│   ├── integration/                   # Tests d'intégration (API Python + CLI)
│   │   ├── test_inspector.py
│   │   └── test_cli.py
│   └── fixtures/                      # Datasets de test (valid.csv, corrupted.csv)
│
├── .gitignore
├── CHANGELOG.md                       # Historique des versions
├── CONTRIBUTING.md                    # Guide de contribution
├── LICENSE                            # Licence Open Source (ex: MIT)
├── README.md                          # Documentation principale GitHub
└── pyproject.toml                     # Configuration unique (Build, Typer, Ruff, Pytest)