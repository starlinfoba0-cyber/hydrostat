# HYDROSTAT - Module 5
# Visualisation des données pluviométriques

import matplotlib.pyplot as plt
from pathlib import Path


def visualiser_precipitations(donnees_valides):

    if not donnees_valides:
        print("Aucune donnée disponible pour les graphiques.")
        return

    # Création du dossier des graphiques
    dossier = Path(__file__).resolve().parent / "graphiques"
    dossier.mkdir(exist_ok=True)

    # Extraction des données
    dates = [date for date, pluie in donnees_valides]
    pluies = [pluie for date, pluie in donnees_valides]

    # GRAPHIQUE 1 : Précipitations journalières

    plt.figure(figsize=(12, 5))

    plt.bar(dates, pluies, color="royalblue")

    plt.title("HYDROSTAT - Précipitations journalières")
    plt.xlabel("Dates")
    plt.ylabel("Précipitations (mm)")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(dossier / "precipitations_journalieres.png")
    plt.close()

    print("Graphique journalier enregistré.")

    # GRAPHIQUE 2 : Précipitations cumulées

    cumul = []
    total = 0

    for pluie in pluies:
        total += pluie
        cumul.append(total)

    plt.figure(figsize=(12, 5))

    plt.plot(dates, cumul, marker="o", color="green")

    plt.title("HYDROSTAT - Précipitations cumulées")
    plt.xlabel("Dates")
    plt.ylabel("Cumul des précipitations (mm)")

    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(dossier / "precipitations_cumulees.png")
    plt.close()

    print("Graphique cumulé enregistré.")

    # GRAPHIQUE 3 : Histogramme des précipitations

    plt.figure(figsize=(10, 5))

    plt.hist(pluies, bins=10, color="orange", edgecolor="black")

    plt.title("HYDROSTAT - Distribution des précipitations")
    plt.xlabel("Précipitations (mm)")
    plt.ylabel("Nombre de jours")

    plt.tight_layout()

    plt.savefig(dossier / "histogramme_precipitations.png")
    plt.close()

    print("Histogramme enregistré.")


# Test du module
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

    visualiser_precipitations(donnees_test)