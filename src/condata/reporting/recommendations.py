"""Recommandations d'action (signale, ne corrige pas)."""

from __future__ import annotations

from condata.models.schema import AnalysisResult


def build_recommendations(result: AnalysisResult) -> list[str]:
    """Suggestions humaines, sans modification automatique des données."""
    recs: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        if text not in seen:
            seen.add(text)
            recs.append(text)

    for issue in result.quality.issues:
        if issue.code == "missing_values" and issue.column:
            add(
                f"Investiguer les valeurs manquantes de « {issue.column} » "
                "avant tout drop ou imputation."
            )
        elif issue.code == "duplicates":
            add(
                "Inspecter les lignes dupliquées "
                "et décider d'une règle de déduplication."
            )
        elif issue.code == "categorical_inconsistency" and issue.column:
            add(
                f"Normaliser la casse et les espaces de « {issue.column} »."
            )
        elif issue.code == "mixed_types" and issue.column:
            add(f"Harmoniser le type de « {issue.column} » (valeurs mixtes).")
        elif issue.code == "constant_column" and issue.column:
            add(f"Évaluer l'utilité de la colonne constante « {issue.column} ».")

    for column in result.outliers.columns:
        if column.n_potential_outliers > 0:
            add(
                f"Vérifier les {column.n_potential_outliers} potential outliers "
                f"de « {column.name} » (méthode {column.method.upper()}) : "
                "ce ne sont pas forcément des erreurs."
            )

    for warning in result.correlations.warnings:
        if warning.code == "redundancy":
            cols = " et ".join(f"« {name} »" for name in warning.columns)
            add(
                f"Deux variables redondantes ({cols}) : "
                "en conserver une pour le modèle."
            )
        elif warning.code == "multicollinearity":
            add("Surveiller la multicolinéarité avant une régression linéaire.")

    for check in result.readiness.checks:
        if check.status == "ok":
            continue
        if check.code == "schema":
            add("Collecter davantage de lignes avant un entraînement ML.")
        elif check.code == "target_variable":
            add(
                "Préciser la colonne cible avec --target "
                "/ AnalysisConfig.target_column."
            )
        elif check.code == "class_balance":
            add(
                "Traiter le déséquilibre des classes "
                "(pondération, resampling) si la cible est catégorielle."
            )
        elif check.code == "potential_leakage":
            add("Retirer les identifiants et fuites potentielles avant l'entraînement.")

    if not recs:
        add("Aucun problème bloquant détecté. Poursuivre l'exploration métier.")
    return recs
