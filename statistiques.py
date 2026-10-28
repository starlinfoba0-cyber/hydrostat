# HYDROSTAT
# Module 4 : Analyse statistique des precipitations

import math
import statistics

# Definition UNIQUE d'un jour pluvieux (en mm) pour tout le projet
SEUIL_JOUR_PLUVIEUX = 1.0


def analyser_precipitations(donnees_valides, afficher=True):
    """
    Statistiques descriptives des precipitations.

    Parametres :
        donnees_valides : liste de tuples (date, pluie)
        afficher        : True = affiche les resultats dans la console

    Retour :
        Dictionnaire des resultats. L'ecart-type et la variance sont
        ceux de l'echantillon (division par n - 1) ; ils valent None
        s'il y a une seule observation.
    """

    if not donnees_valides:
        raise ValueError("Aucune donnee valide disponible.")

    pluies = [pluie for date, pluie in donnees_valides]

    nombre_jours = len(pluies)

    cumul = math.fsum(pluies)

    moyenne = statistics.mean(pluies)

    mediane = statistics.median(pluies)

    maximum = max(pluies)

    minimum = min(pluies)

    jours_pluvieux = sum(
        1 for pluie in pluies if pluie >= SEUIL_JOUR_PLUVIEUX
    )

    jours_secs = nombre_jours - jours_pluvieux

    if nombre_jours >= 2:
        ecart_type = statistics.stdev(pluies)
        variance = statistics.variance(pluies)
    else:
        ecart_type = None
        variance = None

    resultats = {
        "nombre_jours": nombre_jours,
        "cumul": cumul,
        "moyenne": moyenne,
        "mediane": mediane,
        "maximum": maximum,
        "minimum": minimum,
        "jours_pluvieux": jours_pluvieux,
        "jours_secs": jours_secs,
        "ecart_type": ecart_type,
        "variance": variance
    }

    if afficher:

        print("\n================================")
        print(" ANALYSE STATISTIQUE HYDROSTAT")
        print("================================")

        print("\nRESULTATS STATISTIQUES :")

        print(f"Nombre de jours : {nombre_jours}")
        print(f"Cumul des pluies : {cumul:.2f} mm")
        print(f"Moyenne journaliere : {moyenne:.2f} mm")
        print(f"Mediane : {mediane:.2f} mm")
        print(f"Precipitation maximale : {maximum:.2f} mm")
        print(f"Precipitation minimale : {minimum:.2f} mm")
        print(
            f"Jours pluvieux (>= {SEUIL_JOUR_PLUVIEUX:g} mm) : "
            f"{jours_pluvieux}"
        )
        print(f"Jours secs : {jours_secs}")

        if ecart_type is not None:
            print(f"Ecart-type (n-1) : {ecart_type:.2f} mm")
        else:
            print("Ecart-type : non defini (une seule observation)")

    return resultats


if __name__ == "__main__":

    donnees_test = [
        ("2025-01-01", 0.0),
        ("2025-01-02", 0.0),
        ("2025-01-03", 0.1),
        ("2025-01-04", 0.0),
        ("2025-01-05", 0.0),
        ("2025-01-06", 0.0),
        ("2025-01-07", 0.0)
    ]

    analyser_precipitations(donnees_test)
