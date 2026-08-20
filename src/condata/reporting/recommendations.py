"""Recommandations d'action (signale, ne corrige pas)."""

from __future__ import annotations

from condata.models.schema import AnalysisResult


def build_recommendation_items(result: AnalysisResult) -> list[dict[str, str]]:
    """Cartes de recommandation pour le rapport HTML."""
    items: list[dict[str, str]] = []
    missing_cols = [
        issue.column
        for issue in result.quality.issues
        if issue.code == "missing_values" and issue.column
    ]
    if missing_cols:
        names = ", ".join(f"« {name} »" for name in dict.fromkeys(missing_cols))
        items.append(
            {
                "kind": "missing",
                "title": "Gérer les valeurs manquantes",
                "detail": (
                    f"Investiguer {names} avant tout drop ou imputation."
                ),
            }
        )

    outlier_cols = [
        col for col in result.outliers.columns if col.n_potential_outliers > 0
    ]
    if outlier_cols:
        detail = "; ".join(
            f"« {col.name} » : {col.n_potential_outliers} potential outliers "
            f"({col.method.upper()})"
            for col in outlier_cols[:3]
        )
        items.append(
            {
                "kind": "outliers",
                "title": "Vérifier les outliers",
                "detail": detail + " — ce ne sont pas forcément des erreurs.",
            }
        )

    type_cols = [
        issue.column
        for issue in result.quality.issues
        if issue.code in {"mixed_types", "categorical_inconsistency"} and issue.column
    ]
    if type_cols:
        names = ", ".join(f"« {name} »" for name in dict.fromkeys(type_cols))
        items.append(
            {
                "kind": "types",
                "title": "Nettoyer les types de données",
                "detail": (
                    "Harmoniser la casse, les espaces et les types mixtes : "
                    f"{names}."
                ),
            }
        )

    if result.quality.duplicates.n_duplicates > 0:
        items.append(
            {
                "kind": "duplicates",
                "title": "Inspecter les doublons",
                "detail": (
                    f"{result.quality.duplicates.n_duplicates} lignes dupliquées "
                    f"({result.quality.duplicates.rate_pct:.2f} %)."
                ),
            }
        )

    target_check = next(
        (c for c in result.readiness.checks if c.code == "target_variable"),
        None,
    )
    if target_check and target_check.status != "ok":
        items.append(
            {
                "kind": "target",
                "title": "Définir une cible ML",
                "detail": (
                    "Préciser la colonne cible avec --target "
                    "/ AnalysisConfig.target_column."
                ),
            }
        )

    leak = next(
        (c for c in result.readiness.checks if c.code == "potential_leakage"),
        None,
    )
    if leak and leak.status != "ok":
        items.append(
            {
                "kind": "leakage",
                "title": "Retirer les fuites potentielles",
                "detail": leak.message,
            }
        )

    schema = next((c for c in result.readiness.checks if c.code == "schema"), None)
    if schema and schema.status != "ok":
        items.append(
            {
                "kind": "schema",
                "title": "Augmenter le volume de données",
                "detail": schema.message,
            }
        )

    if not items:
        items.append(
            {
                "kind": "ok",
                "title": "Aucun problème bloquant",
                "detail": "Poursuivre l'exploration métier.",
            }
        )
    return items


def build_recommendations(result: AnalysisResult) -> list[str]:
    """Liste texte pour le terminal."""
    return [
        f"{item['title']} : {item['detail']}"
        for item in build_recommendation_items(result)
    ]
