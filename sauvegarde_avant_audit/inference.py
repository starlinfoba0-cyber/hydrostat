# ==========================================
# HYDROSTAT - MODULE 7
# ANALYSE STATISTIQUE INFERENTIELLE
# ==========================================

import math
from scipy.stats import t


def analyser_inference(donnees_valides, confiance=0.95):

    print("\n====================================")
    print("ANALYSE INFERENTIELLE HYDROSTAT")
    print("====================================")

    if not 0 < confiance < 1:
        print("Erreur : niveau de confiance invalide.")
        return None

    pluies = []

    for date, pluie in donnees_valides:
        try:
            valeur = float(pluie)

            if math.isfinite(valeur) and valeur >= 0:
                pluies.append(valeur)

        except (ValueError, TypeError):
            continue

    n = len(pluies)

    if n < 2:
        print("Donnees insuffisantes pour l'analyse.")
        return None

    # Moyenne
    moyenne = sum(pluies) / n

    # Variance corrigee
    variance = sum(
        (x - moyenne) ** 2 for x in pluies
    ) / (n - 1)

    # Ecart-type corrige
    ecart_type = math.sqrt(variance)

    # Erreur standard
    erreur_standard = ecart_type / math.sqrt(n)

    # Quantile de Student
    alpha = 1 - confiance

    t_critique = t.ppf(
        1 - alpha / 2,
        df=n - 1
    )

    # Marge d'erreur
    marge = t_critique * erreur_standard

    # Intervalle de confiance
    borne_inf = moyenne - marge
    borne_sup = moyenne + marge

    print("\nRESULTATS INFERENTIELS :")

    print(f"Nombre d'observations : {n}")
    print(f"Moyenne : {moyenne:.3f} mm")
    print(f"Ecart-type : {ecart_type:.3f} mm")
    print(f"Erreur standard : {erreur_standard:.3f} mm")

    print(f"\nIntervalle de confiance a {confiance*100:.0f} % :")

    print(
        f"[{borne_inf:.3f} ; {borne_sup:.3f}] mm"
    )

    print("\nINTERPRETATION GENIE CIVIL :")

    print(
        "Cet intervalle estime la moyenne des "
        "precipitations journalieres sous les "
        "hypotheses du modele de Student."
    )

    if n < 30:
        print(
            "ATTENTION : petit echantillon. "
            "La normalite et l'independance "
            "des observations sont importantes."
        )

    if any(x == 0 for x in pluies):
        print(
            "ATTENTION : presence de jours secs. "
            "La distribution peut etre asymetrique."
        )

    print(
        "L'intervalle ne doit pas etre utilise "
        "directement pour dimensionner un ouvrage."
    )

    return {
        "n": n,
        "moyenne": moyenne,
        "ecart_type": ecart_type,
        "erreur_standard": erreur_standard,
        "confiance": confiance,
        "borne_inferieure": borne_inf,
        "borne_superieure": borne_sup
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

    analyser_inference(donnees_test)