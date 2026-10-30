"""HYDROSTAT — calculs de génie civil (drainage pluvial).

Aucune dépendance à Streamlit : toutes les fonctions renvoient des valeurs.
"""


def calculer_ruissellement(pluie_mm, surface_m2, coefficient):

    if pluie_mm < 0:
        raise ValueError("La pluie ne peut pas être négative.")

    if surface_m2 <= 0:
        raise ValueError("La surface doit être positive.")

    if not 0 <= coefficient <= 1:
        raise ValueError("Le coefficient doit être compris entre 0 et 1.")

    pluie_m = pluie_mm / 1000

    volume = coefficient * pluie_m * surface_m2

    return volume


def calculer_debit_pointe(coefficient, intensite_mm_h, surface_ha):

    if not 0 <= coefficient <= 1:
        raise ValueError("Coefficient invalide.")

    if intensite_mm_h < 0:
        raise ValueError("L'intensité doit être positive ou nulle.")

    if surface_ha <= 0:
        raise ValueError("La surface doit être positive.")

    debit = (
        coefficient * intensite_mm_h * surface_ha
    ) / 360

    return debit


def calculer_debit_caniveau(
    largeur,
    hauteur,
    pente,
    strickler
):
    """
    Calcule le débit d'un caniveau rectangulaire
    avec la formule de Manning-Strickler.
    """

    if largeur <= 0 or hauteur <= 0:
        raise ValueError(
            "Les dimensions doivent être positives."
        )

    if pente <= 0 or strickler <= 0:
        raise ValueError(
            "La pente et Strickler doivent être positifs."
        )

    # Section mouillée
    section = largeur * hauteur

    # Périmètre mouillé
    perimetre = largeur + 2 * hauteur

    # Rayon hydraulique
    rayon = section / perimetre

    # Débit
    debit = (
        strickler
        * section
        * rayon ** (2 / 3)
        * pente ** 0.5
    )

    return debit


# ==========================================
# PLUIE DE PROJET -> INTENSITE
# ==========================================

def intensite_projet(pluie_jour_mm, duree_min, exposant=0.7):
    """
    Intensité moyenne (mm/h) d'une pluie de durée `duree_min`, déduite de
    la pluie journalière de projet P (mm sur 24 h) :

        i(t) = (P / 24) * (24 / t) ** exposant      (t en heures)

    Pour t = 24 h on retrouve P / 24. C'est une hypothèse simplificatrice :
    pour un vrai dimensionnement, il faut les courbes
    intensité-durée-fréquence (IDF) locales.
    """
    if pluie_jour_mm < 0:
        raise ValueError("La pluie de projet ne peut pas être négative.")

    if not 0 < duree_min <= 1440:
        raise ValueError(
            "La durée doit être comprise entre 0 et 1 440 minutes (24 h)."
        )

    if not 0 <= exposant <= 1:
        raise ValueError("L'exposant doit être compris entre 0 et 1.")

    duree_h = duree_min / 60

    return (pluie_jour_mm / 24) * (24 / duree_h) ** exposant


# ==========================================
# VERIFICATION ET DIMENSIONNEMENT DU CANIVEAU
# ==========================================

def hauteur_normale(debit, largeur, pente, strickler, hauteur_max=100.0):
    """
    Hauteur d'eau (m) pour laquelle un caniveau rectangulaire écoule
    exactement `debit` (m³/s). Le débit croît avec la hauteur : on
    résout par dichotomie.
    """
    if debit < 0:
        raise ValueError("Le débit ne peut pas être négatif.")

    if debit == 0:
        return 0.0

    if calculer_debit_caniveau(largeur, hauteur_max, pente, strickler) < debit:
        raise ValueError("Débit trop élevé pour ce caniveau.")

    bas, haut = 1e-9, hauteur_max

    for _ in range(200):
        milieu = (bas + haut) / 2

        if calculer_debit_caniveau(largeur, milieu, pente, strickler) < debit:
            bas = milieu
        else:
            haut = milieu

        if haut - bas < 1e-12:
            break

    return (bas + haut) / 2


def largeur_minimale(debit, hauteur, pente, strickler, largeur_max=1000.0):
    """
    Plus petite largeur (m) d'un caniveau rectangulaire de hauteur d'eau
    `hauteur` capable d'écouler `debit` (m³/s). Le débit croît avec la
    largeur : on résout par dichotomie.
    """
    if debit < 0:
        raise ValueError("Le débit ne peut pas être négatif.")

    if debit == 0:
        return 0.0

    if calculer_debit_caniveau(largeur_max, hauteur, pente, strickler) < debit:
        raise ValueError("Débit trop élevé pour cette hauteur de caniveau.")

    bas, haut = 1e-9, largeur_max

    for _ in range(200):
        milieu = (bas + haut) / 2

        if calculer_debit_caniveau(milieu, hauteur, pente, strickler) < debit:
            bas = milieu
        else:
            haut = milieu

        if haut - bas < 1e-12:
            break

    return (bas + haut) / 2


def pente_minimale(debit, largeur, hauteur, strickler):
    """
    Plus petite pente (m/m) pour qu'un caniveau rectangulaire de hauteur
    d'eau `hauteur` écoule `debit` (m³/s). On inverse Manning-Strickler :
        I = (Q / (Ks · S · R^(2/3)))²
    """
    if debit < 0:
        raise ValueError("Le débit ne peut pas être négatif.")

    if largeur <= 0 or hauteur <= 0 or strickler <= 0:
        raise ValueError("Les dimensions et Strickler doivent être positifs.")

    section = largeur * hauteur
    rayon = section / (largeur + 2 * hauteur)

    return (debit / (strickler * section * rayon ** (2 / 3))) ** 2


def verifier_caniveau(debit_projet, largeur, hauteur, pente, strickler):
    """
    Compare le débit de projet à la capacité du caniveau (à pleine hauteur).

    Taux de remplissage = débit de projet / capacité :
        <= 80 %  -> "suffisant"
        <= 100 % -> "limite"
        > 100 %  -> "insuffisant"

    Si le caniveau suffit, on calcule aussi la hauteur d'eau et la vitesse
    pour le débit de projet.
    """
    if debit_projet < 0:
        raise ValueError("Le débit de projet ne peut pas être négatif.")

    capacite = calculer_debit_caniveau(largeur, hauteur, pente, strickler)
    taux = debit_projet / capacite

    if taux <= 0.8:
        verdict = "suffisant"
    elif taux <= 1:
        verdict = "limite"
    else:
        verdict = "insuffisant"

    hauteur_eau = None
    vitesse = None

    if debit_projet <= capacite:
        hauteur_eau = hauteur_normale(
            debit_projet, largeur, pente, strickler, hauteur_max=hauteur
        )
        if hauteur_eau > 0:
            vitesse = debit_projet / (largeur * hauteur_eau)

    return {
        "capacite": capacite,
        "taux_remplissage": taux,
        "verdict": verdict,
        "hauteur_eau": hauteur_eau,
        "vitesse": vitesse,
        "vitesse_pleine_section": capacite / (largeur * hauteur)
    }


def periode_retour_supportee(capacite, debits_par_periode):
    """
    Plus grande période de retour T dont le débit de pointe reste dans la
    capacité du caniveau.

    debits_par_periode : liste de tuples (T, débit), T croissant
    (le débit croît avec T). Retourne None si même le plus petit T
    dépasse la capacité.
    """
    supportee = None

    for periode, debit in debits_par_periode:
        if debit <= capacite:
            supportee = periode
        else:
            break

    return supportee
