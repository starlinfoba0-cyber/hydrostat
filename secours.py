"""HYDROSTAT — jeu de données de secours (Yaoundé, pré-collecté via Open-Meteo).

Ce fichier n'est utilisé que si la collecte en direct échoue, ou à
l'ouverture de l'application avant toute collecte. L'application
l'annonce toujours clairement à l'utilisateur.
"""
from pathlib import Path

import pandas as pd

FICHIER_SECOURS = (
    Path(__file__).resolve().parent / "donnees" / "yaounde_1995_2024.csv"
)

VILLE_SECOURS = "Yaoundé"
LATITUDE_SECOURS = 3.87
LONGITUDE_SECOURS = 11.52
SOURCE_SECOURS = (
    "Fichier de secours pré-collecté depuis Open-Meteo Historical Weather API"
)

COLONNE_DATE = "Date"
COLONNE_PLUIE = "Précipitations (mm)"


def charger_secours(date_debut=None, date_fin=None, chemin=FICHIER_SECOURS):
    """
    Lit le fichier de secours et le renvoie sous la même forme que la
    réponse de l'API : {"daily": {"time": [...], "precipitation_sum": [...]}}.

    Si une période est demandée, elle doit être entièrement couverte par
    le fichier ; sinon une ValueError explique la couverture disponible.
    """
    if not Path(chemin).is_file():
        raise FileNotFoundError(
            "Fichier de secours introuvable (dossier « donnees »)."
        )

    try:
        tableau = pd.read_csv(chemin, encoding="utf-8-sig")
    except (OSError, ValueError) as erreur:
        raise ValueError(f"Fichier de secours illisible : {erreur}") from erreur

    if COLONNE_DATE not in tableau.columns or COLONNE_PLUIE not in tableau.columns:
        raise ValueError(
            "Fichier de secours invalide : colonnes « Date » et "
            "« Précipitations (mm) » attendues."
        )

    dates = pd.to_datetime(tableau[COLONNE_DATE], errors="coerce")
    if dates.empty or dates.isna().any():
        raise ValueError("Fichier de secours invalide : dates absentes ou illisibles.")

    pluies = pd.to_numeric(tableau[COLONNE_PLUIE], errors="coerce")

    debut_fichier, fin_fichier = dates.min(), dates.max()

    if date_debut is not None and pd.Timestamp(date_debut) < debut_fichier:
        hors_couverture = True
    elif date_fin is not None and pd.Timestamp(date_fin) > fin_fichier:
        hors_couverture = True
    else:
        hors_couverture = False

    if hors_couverture:
        raise ValueError(
            "La période demandée n'est pas couverte par le fichier de "
            f"secours (du {debut_fichier:%d/%m/%Y} au {fin_fichier:%d/%m/%Y})."
        )

    masque = pd.Series(True, index=tableau.index)
    if date_debut is not None:
        masque &= dates >= pd.Timestamp(date_debut)
    if date_fin is not None:
        masque &= dates <= pd.Timestamp(date_fin)

    dates, pluies = dates[masque], pluies[masque]

    if dates.empty:
        raise ValueError("Aucune donnée du fichier de secours sur cette période.")

    return {
        "origine": "secours",
        "avertissement": (
            "Données lues dans le fichier de secours, "
            "pas dans une réponse en direct de l'API."
        ),
        "daily": {
            "time": [d.strftime("%Y-%m-%d") for d in dates],
            "precipitation_sum": [
                None if pd.isna(x) else float(x) for x in pluies
            ],
        },
    }


def meta_secours(reponse):
    """Fiche de collecte correspondant à une réponse du fichier de secours."""
    dates = reponse["daily"]["time"]
    return {
        "ville": VILLE_SECOURS,
        "latitude": LATITUDE_SECOURS,
        "longitude": LONGITUDE_SECOURS,
        "date_debut": dates[0],
        "date_fin": dates[-1],
        "date_collecte": "pré-collecté",
        "source": SOURCE_SECOURS,
        "origine": "secours",
    }
