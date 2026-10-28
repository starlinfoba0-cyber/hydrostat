"""HYDROSTAT — valeurs extrêmes : maxima annuels, loi de Gumbel, périodes de retour.

Modèle : le maximum annuel X de la pluie journalière suit une loi de Gumbel
(valeurs extrêmes de type I, pour des maxima) :

    F(x) = P(X <= x) = exp( -exp( -(x - mu) / beta ) ),   beta > 0

Les maxima annuels de années différentes sont supposés indépendants et de
même loi.

Aucune dépendance à Streamlit : toutes les fonctions renvoient des valeurs.
"""
import calendar
import math

import numpy as np
from scipy import optimize, stats

EULER = 0.5772156649015329     # constante d'Euler-Mascheroni (gamma)
ZETA3 = 1.2020569031595942     # zeta(3)

# Coefficient d'asymétrie et kurtosis de la loi de Gumbel (loi standard)
ASYMETRIE_GUMBEL = 12 * math.sqrt(6) * ZETA3 / math.pi ** 3   # ~ 1,1395
KURTOSIS_GUMBEL = 5.4

NOMBRE_MIN_MAXIMA = 5
METHODES = ("moments", "vraisemblance")


# ==========================================
# 1. MAXIMA ANNUELS
# ==========================================

def maxima_annuels(donnees_valides, couverture_min=0.9):
    """
    Maximum de la pluie journalière pour chaque année civile.

    Une année n'est retenue que si au moins `couverture_min` de ses jours
    sont valides : une année lacunaire donnerait un maximum biaisé vers
    le bas, et les années de début et de fin de période, incomplètes,
    sont ainsi écartées.

    Paramètres :
        donnees_valides : liste de tuples (date "AAAA-MM-JJ", pluie en mm)

    Retour :
        (retenues, ecartees)
        retenues : liste de dictionnaires
                   {annee, maximum, date_maximum, jours_valides, jours_attendus}
        ecartees : liste de dictionnaires
                   {annee, jours_valides, jours_attendus}
    """
    par_annee = {}

    for date, pluie in donnees_valides:
        annee = int(str(date)[:4])
        par_annee.setdefault(annee, []).append((str(date), float(pluie)))

    retenues = []
    ecartees = []

    for annee in sorted(par_annee):

        jours = par_annee[annee]
        attendus = 366 if calendar.isleap(annee) else 365
        valides = len(jours)

        if valides < couverture_min * attendus:
            ecartees.append({
                "annee": annee,
                "jours_valides": valides,
                "jours_attendus": attendus
            })
            continue

        date_max, maximum = max(jours, key=lambda element: element[1])

        retenues.append({
            "annee": annee,
            "maximum": maximum,
            "date_maximum": date_max,
            "jours_valides": valides,
            "jours_attendus": attendus
        })

    return retenues, ecartees


# ==========================================
# 2. AJUSTEMENT DE LA LOI DE GUMBEL
# ==========================================

def ajuster_gumbel(maxima, methode="moments"):
    """
    Estime (mu, beta) de la loi de Gumbel.

    methode = "moments" :
        E[X] = mu + gamma*beta  et  Var[X] = pi^2 * beta^2 / 6
        donc  beta = s * sqrt(6) / pi   et   mu = moyenne - gamma * beta
        (s : écart-type de l'échantillon, division par n - 1)

    methode = "vraisemblance" (maximum de vraisemblance) :
        beta est l'unique solution de
            beta = moyenne - S1(beta) / S0(beta)
            avec S0 = somme exp(-x_i/beta)  et  S1 = somme x_i exp(-x_i/beta)
        puis  mu = -beta * ln( S0 / n )
        (résolution numérique par la méthode de Brent)
    """
    if methode not in METHODES:
        raise ValueError(f"Méthode inconnue : {methode}.")

    x = np.asarray(maxima, dtype=float)
    n = x.size

    if n < 2 or not np.all(np.isfinite(x)):
        raise ValueError("Il faut au moins deux maxima finis.")

    moyenne = float(x.mean())
    ecart = float(x.std(ddof=1))

    if ecart == 0:
        raise ValueError("Tous les maxima sont identiques : ajustement impossible.")

    beta_moments = ecart * math.sqrt(6) / math.pi
    mu_moments = moyenne - EULER * beta_moments

    if methode == "moments":
        return {
            "mu": mu_moments,
            "beta": beta_moments,
            "methode": methode,
            "n": int(n)
        }

    # Maximum de vraisemblance.
    # On décale les exposants par x_min : le rapport S1/S0 est inchangé
    # et on évite tout dépassement de capacité de exp().
    x_min = float(x.min())

    def g(beta):
        poids = np.exp(-(x - x_min) / beta)
        return beta - moyenne + float(np.sum(x * poids) / np.sum(poids))

    # g(beta) < 0 près de 0 (le rapport tend vers x_min < moyenne)
    # et g(beta) > 0 pour beta grand (le rapport tend vers la moyenne).
    borne_basse = 1e-6 * beta_moments
    borne_haute = max(10 * beta_moments, 2 * (moyenne - x_min)) + 1.0

    beta = optimize.brentq(g, borne_basse, borne_haute, xtol=1e-12, rtol=1e-12)

    poids = np.exp(-(x - x_min) / beta)
    mu = x_min - beta * math.log(float(np.sum(poids)) / n)

    return {"mu": mu, "beta": float(beta), "methode": methode, "n": int(n)}


# ==========================================
# 3. NIVEAUX ET PERIODES DE RETOUR, RISQUE
# ==========================================

def variable_reduite(periode_retour):
    """
    y_T = -ln(-ln(1 - 1/T)).
    Le niveau de retour vaut alors  x_T = mu + beta * y_T.
    """
    if periode_retour <= 1:
        raise ValueError("La période de retour doit être supérieure à 1 an.")
    return -math.log(-math.log1p(-1.0 / periode_retour))


def niveau_retour(mu, beta, periode_retour):
    """Pluie journalière dépassée en moyenne une fois tous les T ans."""
    return mu + beta * variable_reduite(periode_retour)


def periode_retour_de(x, mu, beta):
    """Période de retour d'une pluie journalière x : T = 1 / (1 - F(x))."""
    exposant = -(x - mu) / beta

    if exposant > 700:          # x très inférieur à mu : F(x) ~ 0
        return 1.0

    p_depassement = -math.expm1(-math.exp(exposant))

    if p_depassement <= 0:
        return math.inf

    return 1.0 / p_depassement


def risque_duree_vie(periode_retour, duree_ans):
    """
    Probabilité d'au moins un dépassement du niveau T ans en n années :
        R = 1 - (1 - 1/T)^n
    (années indépendantes).
    """
    if periode_retour <= 1:
        return 1.0
    return -math.expm1(duree_ans * math.log1p(-1.0 / periode_retour))


def periode_retour_requise(risque, duree_ans):
    """
    Période de retour à retenir pour que le risque de dépassement sur
    n années ne dépasse pas R :   T = 1 / (1 - (1 - R)^(1/n))
    """
    if not 0 < risque < 1:
        raise ValueError("Le risque doit être strictement compris entre 0 et 1.")
    if duree_ans <= 0:
        raise ValueError("La durée de vie doit être positive.")

    return 1.0 / -math.expm1(math.log1p(-risque) / duree_ans)


# ==========================================
# 4. INTERVALLE DE CONFIANCE (METHODE DELTA)
# ==========================================

def variance_niveau_retour(beta, n, y, methode):
    """
    Variance asymptotique de l'estimateur de x_T = mu + beta*y.

    Vraisemblance : (beta^2 / n) * [ 1 + (6/pi^2) * (y + 1 - gamma)^2 ]
    Moments       : (sigma^2 / n) * [ 1 + g1*K + ((g2 - 1)/4) * K^2 ]
                    avec sigma^2 = pi^2*beta^2/6, K = (y - gamma)*sqrt(6)/pi,
                    g1 = asymétrie et g2 = kurtosis de la loi de Gumbel.
    """
    if methode == "vraisemblance":
        facteur = 1 + (6 / math.pi ** 2) * (y + 1 - EULER) ** 2
        return beta ** 2 / n * facteur

    k = (y - EULER) * math.sqrt(6) / math.pi
    facteur = 1 + ASYMETRIE_GUMBEL * k + (KURTOSIS_GUMBEL - 1) / 4 * k ** 2
    return (math.pi ** 2 / 6) * beta ** 2 / n * facteur


def intervalle_niveau_retour(mu, beta, n, y, methode, confiance=0.95):
    """
    Intervalle de confiance bilatéral (loi normale asymptotique) pour
    x_T = mu + beta*y. Retourne (borne_inferieure, borne_superieure).
    """
    x = mu + beta * y
    ecart = math.sqrt(variance_niveau_retour(beta, n, y, methode))
    z = float(stats.norm.ppf(1 - (1 - confiance) / 2))
    return x - z * ecart, x + z * ecart


# ==========================================
# 5. ADEQUATION DE LA LOI
# ==========================================

def points_gringorten(maxima):
    """
    Maxima triés, variable réduite et période de retour empirique, avec la
    position de tracé de Gringorten p_i = (i - 0,44) / (n + 0,12),
    adaptée à la loi de Gumbel.
    """
    x = np.sort(np.asarray(maxima, dtype=float))
    n = x.size
    rang = np.arange(1, n + 1)
    p = (rang - 0.44) / (n + 0.12)
    y = -np.log(-np.log(p))
    periodes = 1.0 / (1.0 - p)
    return x, y, periodes


def statistique_ks(x_trie, mu, beta):
    """Statistique de Kolmogorov-Smirnov D entre l'échantillon trié et F."""
    n = len(x_trie)
    with np.errstate(over="ignore"):
        f = np.exp(-np.exp(-(np.asarray(x_trie) - mu) / beta))
    rang = np.arange(1, n + 1)
    return float(max(np.max(rang / n - f), np.max(f - (rang - 1) / n)))


def test_adequation_gumbel(
    maxima,
    mu,
    beta,
    methode="moments",
    repetitions=2000,
    graine=2026
):
    """
    Test de Kolmogorov-Smirnov d'adéquation à la loi de Gumbel.

    Les paramètres étant estimés sur les mêmes données, la loi de D n'est
    plus celle du test classique (la p-value serait trop grande). On
    calcule donc la p-value par simulation (bootstrap paramétrique) :
    on simule des échantillons de la loi ajustée, on les réajuste avec la
    même méthode, et on compare leur D à celui observé.

        p = (nombre de D simulés >= D observé + 1) / (répétitions + 1)

    Le tirage est reproductible (graine fixe).
    """
    x = np.sort(np.asarray(maxima, dtype=float))
    n = x.size
    d_observe = statistique_ks(x, mu, beta)

    generateur = np.random.default_rng(graine)
    superieurs = 0
    valides = 0

    for _ in range(repetitions):

        echantillon = generateur.gumbel(mu, beta, n)

        try:
            ajuste = ajuster_gumbel(echantillon, methode)
        except (ValueError, RuntimeError):
            continue

        d = statistique_ks(np.sort(echantillon), ajuste["mu"], ajuste["beta"])
        valides += 1

        if d >= d_observe:
            superieurs += 1

    return {
        "statistique_ks": d_observe,
        "p_value": (superieurs + 1) / (valides + 1),
        "repetitions": valides
    }
