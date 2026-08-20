# Contribuer à CONDATA

## Setup

```bash
git clone https://github.com/chel42/condata.git
cd condata
pip install -e ".[dev]"
```

## Branche

Travaillez sur une branche `feature/...`, pas directement sur `main`.

## Checks

```bash
pytest
ruff check src tests
```

## Règles

- Le moteur (`core/`) ne doit pas dépendre de la CLI.
- CONDATA reste local : pas d'envoi de datasets vers un serveur.
- On signale les problèmes, on ne corrige pas les données automatiquement.
- Les scores (qualité, ML readiness) doivent rester documentés, pas magiques.
