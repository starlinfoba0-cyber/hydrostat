# HYDROSTAT - Module 1 : Collecte des données
# Source : Open-Meteo Historical Weather API

import json
import urllib.request
import urllib.error
from datetime import datetime

# Adresse de l'API Open-Meteo
API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Coordonnées approximatives de Yaoundé
LATITUDE = 3.87
LONGITUDE = 11.52


def collecter_precipitations(date_debut, date_fin):
    """
    Récupère les précipitations journalières de Yaoundé.

    Paramètres :
        date_debut : date au format AAAA-MM-JJ
        date_fin : date au format AAAA-MM-JJ

    Retour :
        Dictionnaire contenant les données brutes.
    """

    # Vérification des dates
    debut = datetime.strptime(date_debut, "%Y-%m-%d")
    fin = datetime.strptime(date_fin, "%Y-%m-%d")

    if debut > fin:
        raise ValueError(
            "La date de début doit précéder la date de fin."
        )

    # Construction de la requête
    parametres = (
        f"?latitude={LATITUDE}"
        f"&longitude={LONGITUDE}"
        f"&start_date={date_debut}"
        f"&end_date={date_fin}"
        f"&daily=precipitation_sum"
        f"&timezone=Africa%2FDouala"
    )

    url = API_URL + parametres

    try:
        # Connexion au serveur
        with urllib.request.urlopen(url, timeout=20) as reponse:
            donnees = json.load(reponse)

        # Vérification de la structure
        if "daily" not in donnees:
            raise ValueError(
                "Les données journalières sont absentes."
            )

        return donnees

    except urllib.error.HTTPError as erreur:
        raise RuntimeError(
            f"Erreur HTTP : {erreur.code}"
        ) from erreur

    except urllib.error.URLError as erreur:
        raise RuntimeError(
            "Impossible de contacter Open-Meteo."
        ) from erreur


# Test du module
if __name__ == "__main__":

    try:
        resultat = collecter_precipitations(
            "2025-01-01",
            "2025-01-07"
        )

        print("\nCOLLECTE REUSSIE !\n")

        print("Source : Open-Meteo")
        print("Date de collecte :", datetime.now())

        print("\nDONNEES BRUTES :")
        print(json.dumps(resultat, indent=4, ensure_ascii=False))

    except Exception as erreur:
        print("ERREUR :", erreur)