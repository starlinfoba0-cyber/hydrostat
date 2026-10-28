import pandas as pd


def analyser_precipitations(df):

    pluie = pd.to_numeric(
        df["Précipitations (mm)"],
        errors="coerce"
    ).dropna()

    if pluie.empty:
        return None

    resultats = {
        "pluie_totale": pluie.sum(),
        "pluie_moyenne": pluie.mean(),
        "pluie_maximale": pluie.max(),
        "jours_pluvieux": (pluie > 0).sum(),
        "jours_secs": (pluie == 0).sum(),
        "nombre_observations": len(pluie)
    }

    return resultats
def calculer_ruissellement(pluie_mm, surface_m2, coefficient):

    if pluie_mm < 0:
        raise ValueError("La pluie ne peut pas être négative.")

    if surface_m2 <= 0:
        raise ValueError("La surface doit être positive.")

    if not 0 <= coefficient <= 1:
        raise ValueError("Le coefficient doit être compris entre 0 et 1.")

    pluie_m = pluie_mm / 1000

    volume = coefficient * pluie_m * surface_m2

    return volume
def calculer_debit_pointe(coefficient, intensite_mm_h, surface_ha):

    if not 0 <= coefficient <= 1:
        raise ValueError("Coefficient invalide.")

    if intensite_mm_h < 0:
        raise ValueError("L'intensité doit être positive ou nulle.")

    if surface_ha <= 0:
        raise ValueError("La surface doit être positive.")

    debit = (
        coefficient * intensite_mm_h * surface_ha
    ) / 360

    return debit
def calculer_debit_caniveau(
    largeur,
    hauteur,
    pente,
    strickler
):
    """
    Calcule le débit d'un caniveau rectangulaire
    avec la formule de Manning-Strickler.
    """

    if largeur <= 0 or hauteur <= 0:
        raise ValueError(
            "Les dimensions doivent être positives."
        )

    if pente <= 0 or strickler <= 0:
        raise ValueError(
            "La pente et Strickler doivent être positifs."
        )

    # Section mouillée
    section = largeur * hauteur

    # Périmètre mouillé
    perimetre = largeur + 2 * hauteur

    # Rayon hydraulique
    rayon = section / perimetre

    # Débit
    debit = (
        strickler
        * section
        * rayon ** (2 / 3)
        * pente ** 0.5
    )

    return debit