"""HYDROSTAT — jeux de données de secours (pré-collectés via Open-Meteo).

Un fichier CSV par ville, rangé dans le dossier « donnees » et nommé
<ville>_<annee debut>_<annee fin>.csv (exemple : yaounde_1995_2024.csv).
Il n'est utilisé que si la collecte en direct échoue, ou à l'ouverture de
l'application avant toute collecte. L'application l'annonce toujours.
"""
from pathlib import Path

import pandas as pd

DOSSIER_DONNEES = Path(__file__).resolve().parent / "donnees"

VILLES = {
    "Yaoundé": {"slug": "yaounde", "latitude": 3.87, "longitude": 11.52},
    "Douala": {"slug": "douala", "latitude": 4.05, "longitude": 9.70},
    "Bafoussam": {"slug": "bafoussam", "latitude": 5.48, "longitude": 10.42},
    "Garoua": {"slug": "garoua", "latitude": 9.30, "longitude": 13.40},
}

VILLE_PAR_DEFAUT = "Yaoundé"

SOURCE_SECOURS = (
    "Fichier de secours pré-collecté depuis Open-Meteo Historical Weather API"
)

COLONNE_DATE = "Date"
COLONNE_PLUIE = "Précipitations (mm)"


def fichier_secours(ville):
    """Chemin du CSV pré-collecté de la ville, ou None s'il n'existe pas."""
    if ville not in VILLES:
        return None

    trouves = sorted(DOSSIER_DONNEES.glob(f"{VILLES[ville]['slug']}_*.csv"))

    return trouves[-1] if trouves else None


def villes_secours():
    """Villes pour lesquelles un jeu pré-collecté est disponible."""
    return [ville for ville in VILLES if fichier_secours(ville) is not None]


def nom_fichier_csv(ville, date_debut, date_fin):
    """Nom conventionnel du CSV d'une collecte : yaounde_1995_2024.csv."""
    return f"{VILLES[ville]['slug']}_{str(date_debut)[:4]}_{str(date_fin)[:4]}.csv"


def charger_secours(
    ville=VILLE_PAR_DEFAUT,
    date_debut=None,
    date_fin=None,
    chemin=None
):
    """
    Lit le jeu pré-collecté de la ville et le renvoie sous la même forme que
    la réponse de l'API : {"daily": {"time": [...], "precipitation_sum": [...]}}.

    Si une période est demandée, elle doit être entièrement couverte par le
    fichier ; sinon une ValueError explique la couverture disponible.
    """
    if chemin is None:
        chemin = fichier_secours(ville)

    if chemin is None or not Path(chemin).is_file():
        disponibles = villes_secours()
        raise FileNotFoundError(
            f"Aucun jeu pré-collecté pour {ville} "
            + (
                f"(disponible pour : {', '.join(disponibles)})."
                if disponibles
                else "(aucun jeu pré-collecté n'est installé)."
            )
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

    hors_couverture = (
        (date_debut is not None and pd.Timestamp(date_debut) < debut_fichier)
        or (date_fin is not None and pd.Timestamp(date_fin) > fin_fichier)
    )

    if hors_couverture:
        raise ValueError(
            f"La période demandée n'est pas couverte par le jeu pré-collecté "
            f"de {ville} (du {debut_fichier:%d/%m/%Y} au {fin_fichier:%d/%m/%Y})."
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
        "ville": ville,
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
    ville = reponse.get("ville", VILLE_PAR_DEFAUT)
    dates = reponse["daily"]["time"]

    return {
        "ville": ville,
        "latitude": VILLES[ville]["latitude"],
        "longitude": VILLES[ville]["longitude"],
        "date_debut": dates[0],
        "date_fin": dates[-1],
        "date_collecte": "pré-collecté",
        "source": SOURCE_SECOURS,
        "origine": "secours",
    }
