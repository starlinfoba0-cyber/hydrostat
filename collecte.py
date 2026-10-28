"""HYDROSTAT — collecte pluviométrique historique via Open-Meteo."""
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

API_URL = "https://archive-api.open-meteo.com/v1/archive"
LATITUDE = 3.87
LONGITUDE = 11.52

# Une collecte de plusieurs dizaines d'années peut prendre quelques secondes
DELAI_MAX_SECONDES = 45
NOMBRE_ESSAIS = 3
PAUSE_ENTRE_ESSAIS = 2  # secondes, multipliée par le numéro de l'essai
CODES_HTTP_A_REESSAYER = {429, 500, 502, 503, 504}


def _telecharger_json(url):
    """Télécharge et décode un JSON, avec plusieurs essais si le réseau flanche."""
    derniere_erreur = None

    for essai in range(1, NOMBRE_ESSAIS + 1):
        requete = urllib.request.Request(
            url, headers={"User-Agent": "HYDROSTAT/1.0"}
        )
        try:
            with urllib.request.urlopen(
                requete, timeout=DELAI_MAX_SECONDES
            ) as reponse:
                return json.load(reponse)

        except urllib.error.HTTPError as erreur:
            if erreur.code not in CODES_HTTP_A_REESSAYER:
                raise RuntimeError(
                    f"Erreur Open-Meteo (HTTP {erreur.code})."
                ) from erreur
            derniere_erreur = RuntimeError(
                f"Open-Meteo est indisponible ou limite les requêtes "
                f"(HTTP {erreur.code}) après {NOMBRE_ESSAIS} essais."
            )
            derniere_erreur.__cause__ = erreur

        except (OSError, http.client.HTTPException) as erreur:
            # OSError couvre : pas de connexion, DNS, délai dépassé, coupure
            derniere_erreur = RuntimeError(
                f"Connexion à Open-Meteo impossible ou trop lente après "
                f"{NOMBRE_ESSAIS} essais. Détail : "
                f"{type(erreur).__name__}: {erreur}"
            )
            derniere_erreur.__cause__ = erreur

        except ValueError as erreur:
            raise RuntimeError("Réponse JSON invalide de l'API.") from erreur

        if essai < NOMBRE_ESSAIS:
            time.sleep(PAUSE_ENTRE_ESSAIS * essai)

    raise derniere_erreur


def collecter_precipitations(date_debut, date_fin, latitude=LATITUDE, longitude=LONGITUDE):
    """Retourne la réponse brute Open-Meteo (compatible avec l'ancien pipeline)."""
    debut = datetime.strptime(str(date_debut), "%Y-%m-%d").date()
    fin = datetime.strptime(str(date_fin), "%Y-%m-%d").date()
    if debut > fin:
        raise ValueError("La date de début doit précéder la date de fin.")
    if fin >= date.today():
        raise ValueError("Choisissez une période historique terminée avant aujourd'hui.")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Coordonnées géographiques invalides.")
    params = urllib.parse.urlencode({
        "latitude": latitude, "longitude": longitude,
        "start_date": debut.isoformat(), "end_date": fin.isoformat(),
        "daily": "precipitation_sum", "timezone": "Africa/Douala",
    })
    donnees = _telecharger_json(f"{API_URL}?{params}")
    if not isinstance(donnees, dict):
        raise ValueError("Réponse inattendue de l'API.")
    daily = donnees.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Réponse incomplète : données journalières absentes.")
    dates, pluies = daily.get("time"), daily.get("precipitation_sum")
    if not isinstance(dates, list) or not isinstance(pluies, list) or len(dates) != len(pluies) or not dates:
        raise ValueError("Dates et précipitations absentes ou incohérentes.")
    return donnees


if __name__ == "__main__":
    resultat = collecter_precipitations("2025-01-01", "2025-01-07")
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
