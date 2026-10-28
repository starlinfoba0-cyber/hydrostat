"""HYDROSTAT — collecte pluviométrique historique via Open-Meteo."""
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

API_URL = "https://archive-api.open-meteo.com/v1/archive"
LATITUDE = 3.87
LONGITUDE = 11.52


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
    requete = urllib.request.Request(
        f"{API_URL}?{params}", headers={"User-Agent": "HYDROSTAT/1.0"}
    )
    try:
        with urllib.request.urlopen(requete, timeout=20) as reponse:
            donnees = json.load(reponse)
    except urllib.error.HTTPError as erreur:
        raise RuntimeError(f"Erreur Open-Meteo (HTTP {erreur.code}).") from erreur
    except (urllib.error.URLError, TimeoutError) as erreur:
        raise RuntimeError("Connexion à Open-Meteo impossible. Réessayez.") from erreur
    except (ValueError, json.JSONDecodeError) as erreur:
        raise RuntimeError("Réponse JSON invalide de l'API.") from erreur
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
