# ==========================================
# HYDROSTAT - MODULE 6
# ANALYSE PROBABILISTE DES PRECIPITATIONS
# ==========================================

import math
from bisect import bisect_right

from statistiques import SEUIL_JOUR_PLUVIEUX


def analyser_probabilites(
    donnees_valides,
    seuil_pluie=SEUIL_JOUR_PLUVIEUX,
    seuil_forte_pluie=20.0,
    afficher=True
):
    """
    Analyse probabiliste des précipitations.

    Paramètres :
        donnees_valides : liste de tuples (date, pluie)
        seuil_pluie : seuil définissant un jour pluvieux (mm)
        seuil_forte_pluie : seuil de dépassement (mm)
        afficher : True = affiche les résultats dans la console

    Retour :
        Dictionnaire des résultats probabilistes.
    """

    # 1. Vérification des données

    if not donnees_valides:
        raise ValueError(
            "Aucune donnée valide pour l'analyse probabiliste."
        )

    if seuil_pluie < 0 or seuil_forte_pluie < 0:
        raise ValueError(
            "Les seuils doivent être positifs ou nuls."
        )

    # Extraction des précipitations

    pluies = []

    for date, pluie in donnees_valides:

        if (
            isinstance(pluie, bool)
            or not isinstance(pluie, (int, float))
            or not math.isfinite(pluie)
            or pluie < 0
        ):
            raise ValueError(
                f"Précipitation invalide à la date {date}."
            )

        pluies.append(float(pluie))

    # 2. Nombre d'observations

    n = len(pluies)

    # 3. Probabilité empirique de pluie

    jours_pluvieux = sum(
        1 for pluie in pluies
        if pluie >= seuil_pluie
    )

    probabilite_pluie = jours_pluvieux / n

    # 4. Probabilité de dépassement

    jours_forte_pluie = sum(
        1 for pluie in pluies
        if pluie > seuil_forte_pluie
    )

    probabilite_depassement = jours_forte_pluie / n

    # 5. Classement des précipitations

    pluies_triees = sorted(pluies)

    # 6. Calcul des quantiles
    # Méthode : interpolation linéaire

    def quantile(p):

        position = (n - 1) * p

        indice_bas = math.floor(position)
        indice_haut = math.ceil(position)

        if indice_bas == indice_haut:
            return pluies_triees[indice_bas]

        poids = position - indice_bas

        return (
            pluies_triees[indice_bas] * (1 - poids)
            + pluies_triees[indice_haut] * poids
        )

    q50 = quantile(0.50)
    q90 = quantile(0.90)
    q95 = quantile(0.95)

    # 7. Fonction de répartition empirique
    # F(x) = (nombre de valeurs <= x) / n
    # bisect_right sur la liste triée donne ce nombre en O(log n)

    repartition = [
        (pluie, bisect_right(pluies_triees, pluie) / n)
        for pluie in pluies_triees
    ]

    # 8. Affichage des résultats

    if afficher:

        print("\n" + "=" * 45)
        print("ANALYSE PROBABILISTE HYDROSTAT")
        print("=" * 45)

        print("\nRESULTATS PROBABILISTES :")

        print("Nombre de jours :", n)

        print(
            f"Jours avec pluie >= {seuil_pluie} mm :",
            jours_pluvieux
        )

        print(
            "Probabilité empirique de pluie :",
            f"{probabilite_pluie * 100:.2f} %"
        )

        print(
            f"Jours avec pluie > {seuil_forte_pluie} mm :",
            jours_forte_pluie
        )

        print(
            "Probabilité empirique de dépassement :",
            f"{probabilite_depassement * 100:.2f} %"
        )

        print(f"Quantile 50 % : {q50:.2f} mm")
        print(f"Quantile 90 % : {q90:.2f} mm")
        print(f"Quantile 95 % : {q95:.2f} mm")

        # 9. Interprétation

        print("\nINTERPRETATION GENIE CIVIL :")

        print(
            f"{probabilite_pluie * 100:.2f} % des jours "
            f"observés ont reçu au moins {seuil_pluie} mm."
        )

        print(
            f"{probabilite_depassement * 100:.2f} % des jours "
            f"observés ont dépassé {seuil_forte_pluie} mm."
        )

        print(
            "Ces résultats décrivent la période observée."
        )

        print(
            "Ils ne suffisent pas à dimensionner "
            "un ouvrage hydraulique."
        )

    # 10. Retour des résultats

    return {
        "nombre_jours": n,
        "probabilite_pluie": probabilite_pluie,
        "probabilite_depassement": probabilite_depassement,
        "quantile_50": q50,
        "quantile_90": q90,
        "quantile_95": q95,
        "repartition": repartition
    }


# ==========================================
# TEST DU MODULE
# ==========================================

if __name__ == "__main__":

    donnees_test = [
        ("2025-01-01", 0.0),
        ("2025-01-02", 5.0),
        ("2025-01-03", 12.0),
        ("2025-01-04", 0.0),
        ("2025-01-05", 25.0),
        ("2025-01-06", 40.0),
        ("2025-01-07", 8.0)
    ]

    analyser_probabilites(
        donnees_test,
        seuil_pluie=1.0,
        seuil_forte_pluie=20.0
    )
