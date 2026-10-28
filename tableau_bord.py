"""HYDROSTAT — agrégats pour le tableau de bord (aucune dépendance à Streamlit)."""
import calendar

import pandas as pd

COLONNE_PLUIE = "Précipitations (mm)"

MOIS = [
    "Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin",
    "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."
]

COUVERTURE_MIN = 0.9    # un mois ou une année est « complet » à 90 % de jours valides


def agregats_mensuels(df):
    """Cumul et nombre de jours valides par (année, mois)."""
    d = df.dropna(subset=[COLONNE_PLUIE]).copy()

    if d.empty:
        return pd.DataFrame(
            columns=["annee", "mois", "cumul", "jours", "jours_mois", "complet"]
        )

    d["annee"] = d["Date"].dt.year
    d["mois"] = d["Date"].dt.month

    g = (
        d.groupby(["annee", "mois"])[COLONNE_PLUIE]
        .agg(cumul="sum", jours="count")
        .reset_index()
    )

    g["jours_mois"] = [
        calendar.monthrange(int(a), int(m))[1]
        for a, m in zip(g["annee"], g["mois"])
    ]
    g["complet"] = g["jours"] >= COUVERTURE_MIN * g["jours_mois"]

    return g


def matrice_annee_mois(mensuel):
    """Tableau année x mois des cumuls (mois complets seulement)."""
    complets = mensuel[mensuel["complet"]]

    if complets.empty:
        return pd.DataFrame(columns=range(1, 13))

    matrice = complets.pivot(index="annee", columns="mois", values="cumul")

    return matrice.reindex(columns=range(1, 13))


def regime_mensuel(mensuel):
    """Cumul mensuel moyen (mm) pour chacun des 12 mois, sur les mois complets."""
    complets = mensuel[mensuel["complet"]]

    moyennes = complets.groupby("mois")["cumul"].mean()

    return moyennes.reindex(range(1, 13))


def cumul_annuel(df):
    """Cumul par année civile, pour les années dont 90 % des jours sont valides."""
    d = df.dropna(subset=[COLONNE_PLUIE]).copy()

    if d.empty:
        return pd.DataFrame(columns=["annee", "cumul"])

    d["annee"] = d["Date"].dt.year

    g = d.groupby("annee")[COLONNE_PLUIE].agg(cumul="sum", jours="count").reset_index()
    g["attendus"] = [366 if calendar.isleap(int(a)) else 365 for a in g["annee"]]

    g = g[g["jours"] >= COUVERTURE_MIN * g["attendus"]]

    return g[["annee", "cumul"]].reset_index(drop=True)


def jours_extremes(df, k=5):
    """Les k journées les plus pluvieuses, avec leur date au format lisible."""
    d = df.dropna(subset=[COLONNE_PLUIE]).nlargest(k, COLONNE_PLUIE)

    return pd.DataFrame({
        "Date": d["Date"].dt.strftime("%d/%m/%Y").tolist(),
        "Pluie (mm)": d[COLONNE_PLUIE].round(1).tolist()
    })


def dates_lisibles(df):
    """Copie du tableau avec la date sans l'heure (00:00:00) pour l'affichage."""
    out = df.copy()
    out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")
    return out
