# HYDROSTAT
# Module 4 : Analyse statistique des precipitations

import statistics


def analyser_precipitations(donnees_valides):

    print("\n================================")
    print(" ANALYSE STATISTIQUE HYDROSTAT")
    print("================================")

    if not donnees_valides:
        raise ValueError("Aucune donnee valide disponible.")

    pluies = [pluie for date, pluie in donnees_valides]

    nombre_jours = len(pluies)

    cumul = sum(pluies)

    moyenne = statistics.mean(pluies)

    maximum = max(pluies)

    minimum = min(pluies)

    jours_pluvieux = sum(1 for pluie in pluies if pluie >= 1.0)

    jours_secs = sum(1 for pluie in pluies if pluie < 1.0)

    ecart_type = statistics.pstdev(pluies)

    resultats = {
        "nombre_jours": nombre_jours,
        "cumul": cumul,
        "moyenne": moyenne,
        "maximum": maximum,
        "minimum": minimum,
        "jours_pluvieux": jours_pluvieux,
        "jours_secs": jours_secs,
        "ecart_type": ecart_type
    }

    print("\nRESULTATS STATISTIQUES :")

    print(f"Nombre de jours : {nombre_jours}")
    print(f"Cumul des pluies : {cumul:.2f} mm")
    print(f"Moyenne journaliere : {moyenne:.2f} mm")
    print(f"Precipitation maximale : {maximum:.2f} mm")
    print(f"Precipitation minimale : {minimum:.2f} mm")
    print(f"Jours pluvieux : {jours_pluvieux}")
    print(f"Jours secs : {jours_secs}")
    print(f"Ecart-type : {ecart_type:.2f} mm")

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