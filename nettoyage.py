from datetime import datetime
import math


def nettoyer_donnees(dates, precipitations, afficher=True):
    """
    Separe les donnees valides des anomalies.

    Retour :
        donnees_valides : liste de tuples (date, pluie)
        anomalies       : liste de tuples (date, valeur recue, motif)
    """

    if afficher:
        print("\n===== NETTOYAGE DES DONNEES =====")

    if len(dates) != len(precipitations):
        raise ValueError(
            "Le nombre de dates et de precipitations est different."
        )

    donnees_valides = []
    anomalies = []
    dates_vues = set()

    for date, pluie in zip(dates, precipitations):

        try:
            datetime.strptime(date, "%Y-%m-%d")

            if date in dates_vues:
                anomalies.append((date, pluie, "Date en double"))
                continue

            dates_vues.add(date)

            if pluie is None:
                anomalies.append((date, pluie, "Valeur manquante"))
                continue

            pluie = float(pluie)

            if not math.isfinite(pluie):
                anomalies.append((date, pluie, "Valeur non finie"))
                continue

            if pluie < 0:
                anomalies.append((date, pluie, "Precipitation negative"))
                continue

            donnees_valides.append((date, pluie))

        except (ValueError, TypeError):
            anomalies.append((date, pluie, "Donnee invalide"))

    if afficher:
        print("Nombre de donnees recues :", len(dates))
        print("Nombre de donnees valides :", len(donnees_valides))
        print("Nombre d'anomalies :", len(anomalies))

    return donnees_valides, anomalies


if __name__ == "__main__":

    dates = [
        "2025-01-01",
        "2025-01-02",
        "2025-01-03",
        "2025-01-04",
        "2025-01-05",
        "2025-01-05"
    ]

    precipitations = [
        0.0,
        12.5,
        None,
        -4.0,
        8.2,
        10.0
    ]

    valides, anomalies = nettoyer_donnees(
        dates,
        precipitations
    )

    print("\nDONNEES VALIDES :")
    for donnee in valides:
        print(donnee)

    print("\nANOMALIES DETECTEES :")
    for anomalie in anomalies:
        print(anomalie)
