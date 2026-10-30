# HYDROSTAT

Application web (Python / Streamlit) de **collecte et d'analyse de données pluviométriques**, appliquée au **drainage pluvial en génie civil**.
Projet de Probabilités et Statistiques, ENSPY, 3e année Génie Civil.

Auteur : *(à compléter)*

## Ce que fait l'application

- **Collecte en direct** des précipitations journalières (API Open-Meteo, archive ERA5) pour Yaoundé, Douala, Bafoussam et Garoua.
- **Données brutes visibles avant toute analyse** : réponse JSON de l'API, valeurs reçues jour par jour, contrôle de qualité (valeurs manquantes, doublons, valeurs négatives).
- **Statistiques** descriptives, probabilités empiriques, intervalle de confiance et test t.
- **Valeurs extrêmes** : maxima annuels, loi de Gumbel, périodes de retour, risque de dépassement sur la durée de vie d'un ouvrage.
- **Synthèse du terrain** : repères concrets pour quelqu'un qui prend un terrain maintenant (pluie annuelle, mois courant, pluie décennale, effet de l'imperméabilisation) et classement de cinq types de travaux sensibles à la pluie, avec un score sur 100 selon le mois de démarrage et la durée, et des mesures possibles.
- **Génie civil** : pluie de projet, débit de pointe (méthode rationnelle), vérification d'un caniveau (Manning-Strickler) avec mesures possibles s'il est insuffisant, effet de l'aménagement avant/après, planification de chantier (jours de pluie perdus par mois).
- **Robustesse** : 3 essais automatiques si l'API est lente, messages d'erreur explicites.
- **Jeux de données de secours** : un fichier CSV pré-collecté par ville dans `donnees/` (nommé `<ville>_<annee debut>_<annee fin>.csv`, par exemple `yaounde_1995_2024.csv`). Il est utilisé uniquement si la collecte en direct échoue ou avant la première collecte, pour les villes dont le fichier existe ; l'application l'annonce toujours à l'écran. Pour en ajouter un : collecter la ville dans l'application, télécharger le CSV (le nom est déjà au bon format) et le placer dans `donnees/`.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `app.py` | Interface Streamlit (toutes les pages) |
| `collecte.py` | Appel de l'API Open-Meteo (délai maximal, 3 essais, validation de la réponse) |
| `nettoyage.py` | Validation des données (manquantes, doublons, négatives) |
| `statistiques.py`, `probabilites.py`, `inference.py` | Calculs statistiques |
| `extremes.py` | Maxima annuels, loi de Gumbel, périodes de retour |
| `genie_civil.py` | Formules de génie civil (ruissellement, débit de pointe, caniveau) |
| `chantier.py` | Jours de pluie perdus selon le mois de démarrage |
| `secours.py`, `donnees/` | Jeux de données de secours (un CSV par ville) |
| `theme.py`, `tableau_bord.py` | Apparence et agrégats du tableau de bord |
| `pipeline.py`, `visualisation.py` | Version console du traitement (nécessite `matplotlib`) |

## Lancer en local

```
pip install -r requirements.txt
python -m streamlit run app.py
```

## Limites et hypothèses

- Les données viennent d'une **réanalyse** (ERA5, maille de plusieurs kilomètres), pas d'un pluviomètre : les pluies extrêmes y sont généralement atténuées et les petites pluies trop fréquentes. Les résultats sont indicatifs.
- La conversion de la pluie journalière en intensité utilise l'hypothèse simplifiée `i = (P/24) × (24/t)^k` avec `k = 0,7`. Pour un vrai dimensionnement, saisir les courbes intensité-durée-fréquence (IDF) locales : l'application le permet.
- Dimensionnement à vocation pédagogique ; les jours de chantier perdus sont des jours calendaires.
