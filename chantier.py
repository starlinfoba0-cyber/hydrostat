"""HYDROSTAT — planification de chantier à partir des pluies observées.

Une journée est « perdue » quand la pluie atteint un seuil (en mm) qui
arrête les travaux. Aucune dépendance à Streamlit.
"""
import calendar

import numpy as np
import pandas as pd

COLONNE_PLUIE = "Précipitations (mm)"
COUVERTURE_MIN = 0.9
NOMBRE_MIN_FENETRES = 10


def jours_perdus_par_mois(df, seuil):
    """
    Nombre moyen de jours perdus pour chacun des 12 mois (Series indexée 1..12).

    Seuls les mois dont 90 % des jours sont valides sont retenus ; le
    décompte est ramené au mois entier.
    """
    d = df.dropna(subset=[COLONNE_PLUIE]).copy()

    if d.empty:
        return pd.Series(np.nan, index=range(1, 13))

    d["annee"] = d["Date"].dt.year
    d["mois"] = d["Date"].dt.month
    d["perdu"] = d[COLONNE_PLUIE] >= seuil

    g = (
        d.groupby(["annee", "mois"])
        .agg(perdus=("perdu", "sum"), jours=("perdu", "size"))
        .reset_index()
    )

    g["jours_mois"] = [
        calendar.monthrange(int(a), int(m))[1]
        for a, m in zip(g["annee"], g["mois"])
    ]

    g = g[g["jours"] >= COUVERTURE_MIN * g["jours_mois"]].copy()

    g["perdus_mois"] = g["perdus"] * g["jours_mois"] / g["jours"]

    return g.groupby("mois")["perdus_mois"].mean().reindex(range(1, 13))


def fenetre_jours_perdus(df, seuil, mois_debut, duree_mois):
    """
    Jours perdus sur un chantier de `duree_mois` mois commençant le 1er du
    mois `mois_debut`, pour chaque année historique où la fenêtre est
    entièrement couverte (90 % de jours valides). Retourne une liste.
    """
    if not 1 <= mois_debut <= 12:
        raise ValueError("Le mois de démarrage doit être compris entre 1 et 12.")

    if duree_mois < 1:
        raise ValueError("La durée doit être d'au moins un mois.")

    d = df.dropna(subset=[COLONNE_PLUIE])

    if d.empty:
        return []

    serie = d.set_index("Date")[COLONNE_PLUIE].sort_index()
    premier, dernier = serie.index.min(), serie.index.max()

    resultats = []

    for annee in range(premier.year, dernier.year + 1):

        debut = pd.Timestamp(year=annee, month=mois_debut, day=1)
        fin = debut + pd.DateOffset(months=int(duree_mois)) - pd.Timedelta(days=1)

        if debut < premier or fin > dernier:
            continue

        morceau = serie.loc[debut:fin]
        jours_fenetre = (fin - debut).days + 1

        if len(morceau) < COUVERTURE_MIN * jours_fenetre:
            continue

        perdus = float((morceau >= seuil).sum())

        resultats.append(perdus * jours_fenetre / len(morceau))

    return resultats


def resume_fenetre(valeurs):
    """Médiane, valeur dépassée 2 années sur 10 (80e centile) et pire cas observé."""
    if len(valeurs) < NOMBRE_MIN_FENETRES:
        return None

    return {
        "annees": len(valeurs),
        "mediane": float(np.median(valeurs)),
        "p80": float(np.percentile(valeurs, 80)),
        "maximum": float(np.max(valeurs))
    }


def mediane_par_mois_de_demarrage(df, seuil, duree_mois):
    """Médiane des jours perdus selon le mois de démarrage (Series 1..12, NaN si trop peu d'années)."""
    medianes = {}

    for mois in range(1, 13):
        valeurs = fenetre_jours_perdus(df, seuil, mois, duree_mois)
        medianes[mois] = (
            float(np.median(valeurs))
            if len(valeurs) >= NOMBRE_MIN_FENETRES
            else np.nan
        )

    return pd.Series(medianes)
