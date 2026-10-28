import json

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta

from collecte import collecter_precipitations
from nettoyage import nettoyer_donnees
from statistiques import analyser_precipitations, SEUIL_JOUR_PLUVIEUX
from probabilites import analyser_probabilites
from inference import analyser_inference
from genie_civil import calculer_ruissellement
from secours import charger_secours, meta_secours, VILLE_SECOURS
from extremes import (
    maxima_annuels,
    ajuster_gumbel,
    variable_reduite,
    risque_duree_vie,
    periode_retour_requise,
    intervalle_niveau_retour,
    points_gringorten,
    test_adequation_gumbel,
    NOMBRE_MIN_MAXIMA,
    METHODES
)

# ==========================================
# CONFIGURATION HYDROSTAT
# ==========================================

st.set_page_config(
    page_title="HYDROSTAT | Génie Civil",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Archive Open-Meteo : données ERA5 depuis 1950 (ERA5-Land),
# publiées avec un délai de 5 à 7 jours
DATE_MIN_ARCHIVE = date(1950, 1, 1)
DELAI_ARCHIVE_JOURS = 7
DATE_MAX_ARCHIVE = date.today() - timedelta(days=DELAI_ARCHIVE_JOURS)


def formater(valeur, unite="mm", decimales=2):
    """Affiche une valeur, ou 'n/a' si elle n'est pas définie."""
    if valeur is None:
        return "n/a"
    return f"{valeur:.{decimales}f} {unite}"


def enregistrer_collecte(resultat, meta):
    """Nettoie une réponse (API ou fichier de secours) et la range en session."""
    dates_recues = resultat["daily"]["time"]
    pluies_recues = resultat["daily"]["precipitation_sum"]

    donnees_valides, anomalies = nettoyer_donnees(
        dates_recues,
        pluies_recues,
        afficher=False
    )

    # Nouvelle collecte : on efface l'ancienne
    for cle in (
        "reponse_api",
        "meta",
        "anomalies",
        "donnees_valides",
        "donnees_reelles"
    ):
        st.session_state.pop(cle, None)

    # Réponse brute + fiche de la collecte (toujours conservées)
    st.session_state["reponse_api"] = resultat
    st.session_state["anomalies"] = anomalies
    st.session_state["meta"] = dict(meta, nb_recus=len(dates_recues))

    if donnees_valides:

        st.session_state["donnees_valides"] = donnees_valides

        st.session_state["donnees_reelles"] = pd.DataFrame({
            "Date": pd.to_datetime(
                [d for d, p in donnees_valides]
            ),
            "Précipitations (mm)": [
                p for d, p in donnees_valides
            ]
        })

    return donnees_valides, anomalies


def bandeau_origine():
    """Annonce clairement les données de secours. Renvoie True si c'est le cas."""
    meta = st.session_state.get("meta")

    if meta and meta.get("origine") == "secours":
        st.warning(
            "⚠️ Jeu de données pré-collecté (fichier de secours) : "
            f"{meta['ville']}, du {meta['date_debut']} au "
            f"{meta['date_fin']}. Ce sont des données Open-Meteo "
            "enregistrées à l'avance. Lancez une collecte pour "
            "interroger Open-Meteo en direct."
        )
        return True

    return False


@st.cache_data(show_spinner=False)
def tester_adequation(maxima, mu, beta, methode):
    """Test d'adéquation (en cache : la simulation n'est refaite que si les données changent)."""
    return test_adequation_gumbel(list(maxima), mu, beta, methode)


def afficher_valeurs_extremes():
    """Page « Valeurs extrêmes » : maxima annuels, Gumbel, périodes de retour."""

    st.title("📈 Valeurs extrêmes : loi de Gumbel et périodes de retour")

    st.markdown(
        "### De la pluie journalière maximale annuelle à la pluie de projet"
    )

    if "donnees_valides" not in st.session_state:
        st.warning("Veuillez d'abord collecter des données.")
        return

    bandeau_origine()

    # ---------- 1. MAXIMA ANNUELS ----------

    retenues, ecartees = maxima_annuels(st.session_state["donnees_valides"])

    st.subheader("1️⃣ Maxima annuels")

    st.write(
        "Pour chaque année civile suffisamment complète (au moins 90 % "
        "de jours valides), on retient la pluie journalière maximale."
    )

    if ecartees:
        with st.expander(
            f"⚠️ {len(ecartees)} année(s) écartée(s) : données incomplètes"
        ):
            st.dataframe(
                pd.DataFrame(ecartees).rename(columns={
                    "annee": "Année",
                    "jours_valides": "Jours valides",
                    "jours_attendus": "Jours attendus"
                }),
                use_container_width=True,
                hide_index=True
            )

    if len(retenues) < NOMBRE_MIN_MAXIMA:
        st.warning(
            f"Il faut au moins {NOMBRE_MIN_MAXIMA} années complètes pour "
            f"ajuster une loi de Gumbel ({len(retenues)} disponible(s)). "
            "Collectez une période plus longue : 30 ans ou plus sont "
            "recommandés."
        )
        return

    maxima = [r["maximum"] for r in retenues]
    n = len(maxima)

    if n < 30:
        st.warning(
            f"Seulement {n} maxima annuels : les estimations sont très "
            "incertaines. Pour des périodes de retour de 50 ou 100 ans, "
            "30 ans de données au moins sont recommandés."
        )

    tableau = pd.DataFrame({
        "Année": [r["annee"] for r in retenues],
        "Maximum (mm)": maxima,
        "Date du maximum": [r["date_maximum"] for r in retenues]
    })

    st.dataframe(tableau, use_container_width=True, hide_index=True)

    fig_max = px.bar(tableau, x="Année", y="Maximum (mm)")
    fig_max.update_layout(template="plotly_white")
    st.plotly_chart(fig_max, use_container_width=True)

    # ---------- 2. AJUSTEMENT ----------

    st.subheader("2️⃣ Ajustement de la loi de Gumbel")

    choix = st.radio(
        "Méthode d'estimation",
        ["Moments", "Maximum de vraisemblance"],
        horizontal=True
    )

    methode = "moments" if choix == "Moments" else "vraisemblance"

    try:
        ajustement = ajuster_gumbel(maxima, methode)
        comparaison = {m: ajuster_gumbel(maxima, m) for m in METHODES}
    except (ValueError, RuntimeError) as erreur:
        st.error(f"Ajustement impossible : {erreur}")
        return

    mu = ajustement["mu"]
    beta = ajustement["beta"]

    c1, c2, c3 = st.columns(3)

    c1.metric("Années utilisées", n)
    c2.metric("Position μ", f"{mu:.2f} mm")
    c3.metric("Échelle β", f"{beta:.2f} mm")

    st.dataframe(
        pd.DataFrame({
            "Méthode": ["Moments", "Maximum de vraisemblance"],
            "μ (mm)": [
                comparaison["moments"]["mu"],
                comparaison["vraisemblance"]["mu"]
            ],
            "β (mm)": [
                comparaison["moments"]["beta"],
                comparaison["vraisemblance"]["beta"]
            ]
        }).round(3),
        use_container_width=True,
        hide_index=True
    )

    # ---------- 3. ADEQUATION ----------

    st.subheader("3️⃣ Adéquation du modèle")

    test = tester_adequation(tuple(maxima), mu, beta, methode)

    d1, d2 = st.columns(2)

    d1.metric("Statistique de Kolmogorov-Smirnov D", f"{test['statistique_ks']:.4f}")
    d2.metric("p-value (simulation)", f"{test['p_value']:.3f}")

    if test["p_value"] >= 0.05:
        st.success("La loi de Gumbel n'est pas rejetée au seuil de 5 %.")
    else:
        st.error(
            "La loi de Gumbel est rejetée au seuil de 5 % : "
            "les niveaux de retour ci-dessous sont à prendre avec prudence."
        )

    st.caption(
        f"p-value obtenue par simulation ({test['repetitions']} échantillons) : "
        "les paramètres étant estimés sur les mêmes données, le test "
        "classique de Kolmogorov-Smirnov serait trop indulgent."
    )

    # Papier de Gumbel : maxima observés et droite ajustée
    x_tries, y_reduits, _ = points_gringorten(maxima)
    x_tries = [float(v) for v in x_tries]
    y_reduits = [float(v) for v in y_reduits]

    periodes_axe = [2, 5, 10, 20, 50, 100]
    y_axe = [variable_reduite(t) for t in periodes_axe]

    y_debut = min(y_reduits) - 0.3
    y_fin = max(y_reduits + y_axe) + 0.3
    grille = [y_debut + i * (y_fin - y_debut) / 60 for i in range(61)]

    bornes = [
        intervalle_niveau_retour(mu, beta, n, y, methode) for y in grille
    ]

    fig_g = go.Figure()

    fig_g.add_trace(go.Scatter(
        x=y_reduits,
        y=x_tries,
        mode="markers",
        name="Maxima observés (Gringorten)"
    ))

    fig_g.add_trace(go.Scatter(
        x=grille,
        y=[mu + beta * y for y in grille],
        mode="lines",
        name="Gumbel ajustée"
    ))

    fig_g.add_trace(go.Scatter(
        x=grille,
        y=[b[0] for b in bornes],
        mode="lines",
        line=dict(dash="dash"),
        name="IC 95 % (bas)"
    ))

    fig_g.add_trace(go.Scatter(
        x=grille,
        y=[b[1] for b in bornes],
        mode="lines",
        line=dict(dash="dash"),
        name="IC 95 % (haut)"
    ))

    fig_g.update_layout(
        template="plotly_white",
        xaxis=dict(
            title="Période de retour (ans)",
            tickvals=y_axe,
            ticktext=[str(t) for t in periodes_axe]
        ),
        yaxis_title="Pluie journalière maximale (mm)"
    )

    st.plotly_chart(fig_g, use_container_width=True)

    # ---------- 4. NIVEAUX DE RETOUR ET RISQUE ----------

    st.subheader("4️⃣ Niveaux de retour et risque")

    duree_vie = st.number_input(
        "Durée de vie de l'ouvrage (années)",
        min_value=1,
        value=50,
        step=5
    )

    lignes = []

    for periode in periodes_axe:

        y = variable_reduite(periode)
        bas, haut = intervalle_niveau_retour(mu, beta, n, y, methode)

        lignes.append({
            "Période de retour T (ans)": periode,
            "Pluie journalière (mm)": round(mu + beta * y, 1),
            "IC 95 % bas (mm)": round(bas, 1),
            "IC 95 % haut (mm)": round(haut, 1),
            "Probabilité annuelle de dépassement": f"{100 / periode:.1f} %",
            f"Risque sur {duree_vie} ans": (
                f"{100 * risque_duree_vie(periode, duree_vie):.1f} %"
            )
        })

    st.dataframe(
        pd.DataFrame(lignes),
        use_container_width=True,
        hide_index=True
    )

    # ---------- 5. PLUIE DE PROJET ----------

    st.subheader("5️⃣ Pluie de projet pour un risque accepté")

    risque_pct = st.slider(
        "Risque accepté de dépassement sur la durée de vie (%)",
        1, 50, 10
    )

    periode_requise = periode_retour_requise(risque_pct / 100, duree_vie)
    y_projet = variable_reduite(periode_requise)
    pluie_projet = mu + beta * y_projet
    bas_p, haut_p = intervalle_niveau_retour(mu, beta, n, y_projet, methode)

    e1, e2 = st.columns(2)

    e1.metric("Période de retour requise", f"{periode_requise:,.0f} ans")
    e2.metric("Pluie journalière de projet", f"{pluie_projet:.1f} mm")

    st.caption(f"IC 95 % de la pluie de projet : [{bas_p:.1f} ; {haut_p:.1f}] mm.")

    if periode_requise > 3 * n:
        st.warning(
            f"Extrapolation : une période de retour de {periode_requise:,.0f} ans "
            f"est très supérieure à la durée observée ({n} ans). "
            "Le résultat est très incertain."
        )

    st.session_state["extremes"] = {
        "mu": mu,
        "beta": beta,
        "methode": methode,
        "n": n,
        "periode_projet": periode_requise,
        "pluie_projet": pluie_projet
    }

    # ---------- MÉTHODE ET FORMULES ----------

    with st.expander("📘 Méthode et formules (démonstrations)"):

        st.markdown(
            "**Modèle.** Le maximum annuel X de la pluie journalière suit "
            "une loi de Gumbel ; les années sont supposées indépendantes."
        )
        st.latex(
            r"F(x)=P(X\le x)=\exp\!\Big[-\exp\!\Big(-\frac{x-\mu}{\beta}\Big)\Big],\quad \beta>0"
        )

        st.markdown(
            "**Méthode des moments.** Avec Y = (X − μ)/β (Gumbel standard), "
            "E[Y] = γ (constante d'Euler, 0,5772) et Var[Y] = π²/6. Donc :"
        )
        st.latex(
            r"E[X]=\mu+\gamma\beta,\qquad \mathrm{Var}[X]=\frac{\pi^2\beta^2}{6}"
        )
        st.latex(
            r"\hat\beta=\frac{s\sqrt6}{\pi},\qquad \hat\mu=\bar x-\gamma\hat\beta"
        )

        st.markdown(
            "**Maximum de vraisemblance.** La log-vraisemblance vaut "
            "ℓ = −n ln β − Σ zᵢ − Σ e^(−zᵢ), avec zᵢ = (xᵢ − μ)/β."
        )
        st.latex(
            r"\frac{\partial \ell}{\partial \mu}=\frac1\beta\Big(n-\sum_i e^{-z_i}\Big)=0"
            r"\;\Rightarrow\;\hat\mu=-\beta\ln\Big(\frac1n\sum_i e^{-x_i/\beta}\Big)"
        )
        st.latex(
            r"\frac{\partial \ell}{\partial \beta}=0\;\Rightarrow\;"
            r"\beta=\bar x-\frac{\sum_i x_i e^{-x_i/\beta}}{\sum_i e^{-x_i/\beta}}"
        )
        st.markdown(
            "Cette dernière équation n'a pas de solution explicite : elle est "
            "résolue numériquement (méthode de Brent)."
        )

        st.markdown(
            "**Niveau de retour.** x_T est dépassé en moyenne une fois tous les "
            "T ans : F(x_T) = 1 − 1/T. En résolvant :"
        )
        st.latex(
            r"\exp\!\Big[-e^{-(x_T-\mu)/\beta}\Big]=1-\frac1T"
            r"\;\Rightarrow\; e^{-(x_T-\mu)/\beta}=-\ln\Big(1-\frac1T\Big)"
        )
        st.latex(
            r"x_T=\mu-\beta\,\ln\!\Big[-\ln\Big(1-\frac1T\Big)\Big]=\mu+\beta\,y_T"
        )

        st.markdown(
            "**Risque sur la durée de vie.** Chaque année, la probabilité de "
            "ne pas dépasser x_T est 1 − 1/T. Les années étant indépendantes, "
            "la probabilité de n'avoir aucun dépassement pendant n ans est "
            "(1 − 1/T)ⁿ, d'où :"
        )
        st.latex(
            r"R=1-\Big(1-\frac1T\Big)^{n}\qquad\Longleftrightarrow\qquad "
            r"T=\frac{1}{1-(1-R)^{1/n}}"
        )

        st.markdown(
            "**Intervalle de confiance (méthode delta, loi normale "
            "asymptotique).** Pour la vraisemblance :"
        )
        st.latex(
            r"\widehat{\mathrm{Var}}(\hat x_T)=\frac{\hat\beta^2}{n}"
            r"\Big[1+\frac{6}{\pi^2}\,(y_T+1-\gamma)^2\Big]"
        )
        st.markdown(
            "Pour les moments : "
            "Var = (σ²/n)·[1 + g₁K + ((g₂ − 1)/4)K²], avec σ² = π²β²/6, "
            "K = (y_T − γ)√6/π, g₁ ≈ 1,14 (asymétrie) et g₂ = 5,4 (kurtosis). "
            "Bornes : x̂_T ± 1,96·√Var pour 95 %."
        )

        st.markdown(
            "**Positions de tracé (Gringorten).** Le i-ème maximum classé par "
            "ordre croissant est placé à :"
        )
        st.latex(r"p_i=\frac{i-0{,}44}{n+0{,}12},\qquad y_i=-\ln(-\ln p_i)")

        st.markdown(
            "**Adéquation.** Statistique D de Kolmogorov-Smirnov = plus grand "
            "écart entre la fonction de répartition empirique et F. Comme μ et "
            "β sont estimés sur les mêmes données, la p-value est calculée par "
            "simulation : on tire des échantillons de la loi ajustée, on les "
            "réajuste, et p = (nombre de D simulés ≥ D observé + 1)/(N + 1)."
        )

        st.caption(
            "Limites : années supposées indépendantes et de même loi (pas de "
            "tendance climatique) ; données issues d'une réanalyse (ERA5), non "
            "d'un pluviomètre ; extrapoler au-delà de 2 à 3 fois la durée "
            "observée est très incertain."
        )


# ==========================================
# DESIGN PROFESSIONNEL
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #071525;
    color: #FFFFFF;
}

[data-testid="stSidebar"] {
    background-color: #0D2138;
}

h1, h2, h3 {
    color: #FFFFFF;
}

[data-testid="stMetric"] {
    background: #102A43;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #1D4966;
}

div.stButton > button {
    background-color: #00B4D8;
    color: white;
    border-radius: 10px;
    border: none;
}
/* AMELIORATION DE LA LISIBILITE */

[data-testid="stMetricLabel"] {
    color: #FFFFFF !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
}

[data-testid="stMetric"] {
    background-color: #173B59 !important;
    border: 1px solid #287AA0 !important;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
/* Amélioration de la lisibilité */

[data-testid="stDateInput"] input {
    color: #FFFFFF !important;
    background-color: #1E3A5F !important;
}

[data-testid="stDateInput"] label {
    color: #FFFFFF !important;
}

[data-testid="stSelectbox"] label {
    color: #FFFFFF !important;
}

[data-testid="stMarkdownContainer"] p {
    color: #F1F5F9;
}

[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border-radius: 10px;
}

[data-testid="stAlert"] p {
    color: #FFFFFF !important;
}


</style>
""", unsafe_allow_html=True)

# ==========================================
# MENU LATERAL
# ==========================================

st.sidebar.title("🌊 HYDROSTAT")

st.sidebar.caption(
    "Plateforme intelligente d'analyse pluviométrique"
)

st.sidebar.divider()

menu = st.sidebar.radio(
    "NAVIGATION",
    [
        "🏠 Tableau de bord",
        "🌍 Collecte des données",
        "📋 Données brutes",
        "🧹 Qualité des données",
        "📊 Statistiques",
        "🎲 Probabilités",
        "📐 Inférence",
        "📈 Valeurs extrêmes",
        "🏗️ Génie Civil"
    ]
)

st.sidebar.divider()

st.sidebar.success("● Système opérationnel")

st.sidebar.caption(
    "HYDROSTAT | Version 1.0"
)

# ==========================================
# ==========================================
# GESTION DES DONNEES HYDROSTAT
# ==========================================

# À l'ouverture, avant toute collecte : jeu de données pré-collecté
if (
    "donnees_reelles" not in st.session_state
    and not st.session_state.get("secours_tente")
):

    st.session_state["secours_tente"] = True

    try:
        jeu_secours = charger_secours()
        enregistrer_collecte(jeu_secours, meta_secours(jeu_secours))
    except Exception as erreur_secours:
        st.session_state["secours_erreur"] = str(erreur_secours)

if "donnees_reelles" in st.session_state:

    donnees = st.session_state["donnees_reelles"].copy()

    mode_donnees = "Données réelles"

else:

    donnees = pd.DataFrame({
        "Date": pd.date_range(
            start="2025-01-01",
            periods=7
        ),
        "Précipitations (mm)": [
            0, 5, 12, 0, 25, 40, 8
        ]
    })

    mode_donnees = "Mode démonstration"

# ==========================================
# TABLEAU DE BORD
# ==========================================

if menu == "🏠 Tableau de bord":

    st.title("🌊 HYDROSTAT")

    st.markdown(
        "### Tableau de bord d'analyse pluviométrique"
    )

    if mode_donnees == "Données réelles":
        if not bandeau_origine():
            st.success(
                "✅ Données réelles collectées depuis Open-Meteo."
            )
            meta = st.session_state.get("meta")
            if meta:
                st.caption(
                    f"📍 {meta['ville']} · du {meta['date_debut']} "
                    f"au {meta['date_fin']} · collecté le "
                    f"{meta['date_collecte']}"
                )
    else:
        st.info(
            "Mode démonstration : les données affichées "
            "sont fictives et servent uniquement "
            "à tester l'interface."
        )
        erreur_secours = st.session_state.get("secours_erreur")
        if erreur_secours:
            st.caption(f"Jeu de secours non chargé : {erreur_secours}")

    st.divider()

    # INDICATEURS

    col1, col2, col3, col4 = st.columns(4)

    pluies = donnees["Précipitations (mm)"]

    with col1:
        st.metric(
            "🌧️ Cumul des pluies",
            f"{pluies.sum():.1f} mm"
        )

    with col2:
        st.metric(
            "📊 Moyenne journalière",
            f"{pluies.mean():.2f} mm"
        )

    with col3:
        st.metric(
            f"☔ Jours pluvieux (≥ {SEUIL_JOUR_PLUVIEUX:g} mm)",
            int((pluies >= SEUIL_JOUR_PLUVIEUX).sum())
        )

    with col4:
        st.metric(
            "⚠️ Pluie maximale",
            f"{pluies.max():.1f} mm"
        )

    st.divider()

    # GRAPHIQUES

    gauche, droite = st.columns(2)

    with gauche:

        st.subheader(
            "📈 Évolution des précipitations"
        )

        fig = px.bar(
            donnees,
            x="Date",
            y="Précipitations (mm)",
            color="Précipitations (mm)",
            color_continuous_scale="Blues"
        )

        fig.update_layout(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(
        color="#172B4D",
        size=14
    ),
    title_font=dict(size=18),
    xaxis=dict(
        title="Date",
        showgrid=False,
        tickfont=dict(color="#172B4D")
    ),
    yaxis=dict(
        title="Précipitations (mm)",
        showgrid=True,
        gridcolor="#E2E8F0",
        tickfont=dict(color="#172B4D")
    ),
    coloraxis_colorbar=dict(
        title="Pluie (mm)"
    ),
    margin=dict(l=30, r=30, t=40, b=30)
)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with droite:

        st.subheader(
            "📉 Précipitations cumulées"
        )

        donnees["Cumul (mm)"] = pluies.cumsum()

        fig2 = px.line(
            donnees,
            x="Date",
            y="Cumul (mm)",
            markers=True
        )

        fig2.update_layout(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    font=dict(
        color="#172B4D",
        size=14
    ),
    xaxis=dict(
        title="Date",
        showgrid=False,
        tickfont=dict(color="#172B4D")
    ),
    yaxis=dict(
        title="Précipitations cumulées (mm)",
        showgrid=True,
        gridcolor="#E2E8F0",
        tickfont=dict(color="#172B4D")
    ),
    margin=dict(l=30, r=30, t=40, b=30)
)

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    st.divider()

    st.subheader("📋 Aperçu des données")

    st.dataframe(
        donnees,
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# COLLECTE DES DONNEES REELLES
# ==========================================

elif menu == "🌍 Collecte des données":

    st.title("🌍 Collecte des données météorologiques")

    st.markdown(
        "### Récupération des précipitations historiques"
    )

    st.info(
        "Source : Open-Meteo Historical Weather API"
    )

    st.subheader("📍 Localisation")

    ville = st.selectbox(
        "Choisissez une ville",
        ["Yaoundé", "Douala", "Bafoussam", "Garoua"]
    )

    coordonnees = {
        "Yaoundé": (3.87, 11.52),
        "Douala": (4.05, 9.70),
        "Bafoussam": (5.48, 10.42),
        "Garoua": (9.30, 13.40)
    }

    latitude, longitude = coordonnees[ville]

    st.write(f"Latitude : {latitude}")
    st.write(f"Longitude : {longitude}")

    st.subheader("📅 Période d'analyse")

    col1, col2 = st.columns(2)

    with col1:
        date_debut = st.date_input(
            "Date de début",
            value=date(1995, 1, 1),
            min_value=DATE_MIN_ARCHIVE,
            max_value=DATE_MAX_ARCHIVE
        )

    with col2:
        date_fin = st.date_input(
            "Date de fin",
            value=date(2024, 12, 31),
            min_value=DATE_MIN_ARCHIVE,
            max_value=DATE_MAX_ARCHIVE
        )

    duree_ans = ((date_fin - date_debut).days + 1) / 365.25

    if duree_ans >= 30:
        st.caption(f"Durée choisie : {duree_ans:.1f} ans.")
    else:
        st.caption(
            f"Durée choisie : {duree_ans:.1f} ans "
            "(moins de 30 ans : insuffisant pour estimer des "
            "périodes de retour de 50 ou 100 ans)."
        )

    st.caption(
        f"Archive disponible du {DATE_MIN_ARCHIVE:%d/%m/%Y} au "
        f"{DATE_MAX_ARCHIVE:%d/%m/%Y} : les derniers jours ne sont "
        "pas encore publiés par Open-Meteo."
    )

    if st.button("🚀 Lancer la collecte", type="primary"):

        if date_debut > date_fin:
            st.error("La date de début doit précéder la date de fin.")

        elif date_fin >= date.today():
            st.error("Choisissez une période historique terminée.")

        else:
            resultat = None
            erreur_collecte = None

            try:
                with st.spinner("Collecte des données en cours..."):

                    resultat = collecter_precipitations(
                        str(date_debut),
                        str(date_fin),
                        latitude,
                        longitude
                    )

            except Exception as erreur:
                erreur_collecte = erreur

            if resultat is not None:

                try:
                    donnees_valides, anomalies = enregistrer_collecte(
                        resultat,
                        {
                            "ville": ville,
                            "latitude": latitude,
                            "longitude": longitude,
                            "date_debut": str(date_debut),
                            "date_fin": str(date_fin),
                            "date_collecte": datetime.now().strftime(
                                "%d/%m/%Y %H:%M"
                            ),
                            "source": "Open-Meteo Historical Weather API",
                            "origine": "api"
                        }
                    )

                    if donnees_valides:
                        st.success("✅ Collecte terminée avec succès !")

                    else:
                        st.error(
                            "Aucune donnée valide sur cette période. "
                            "Consultez « Données brutes » et "
                            "« Qualité des données »."
                        )

                except Exception as erreur:
                    st.error(
                        f"Erreur de traitement des données reçues : {erreur}"
                    )

            else:

                st.error(f"Erreur de collecte : {erreur_collecte}")

                if ville == VILLE_SECOURS:

                    try:
                        jeu_secours = charger_secours(date_debut, date_fin)
                        enregistrer_collecte(
                            jeu_secours,
                            meta_secours(jeu_secours)
                        )
                        st.warning(
                            "⚠️ Open-Meteo est injoignable : le jeu de "
                            "données de secours pré-collecté a été chargé "
                            "pour la période demandée."
                        )

                    except Exception as erreur_secours:
                        st.info(
                            "Le jeu de secours n'a pas pu remplacer "
                            f"cette collecte : {erreur_secours}"
                        )

                else:
                    st.info(
                        "Le jeu de secours ne concerne que "
                        f"{VILLE_SECOURS}."
                    )

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"]
        meta = st.session_state["meta"]

        st.subheader("📋 Données collectées")

        bandeau_origine()

        st.caption(
            f"{meta['ville']} · {len(df)} jours valides sur "
            f"{meta['nb_recus']} reçus · "
            f"{len(st.session_state['anomalies'])} anomalie(s) "
            f"(détail dans « Qualité des données »)."
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "📥 Télécharger les données CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="hydrostat_precipitations.csv",
            mime="text/csv"
        )

# ==========================================
# AUTRES PAGES
# ==========================================

elif menu == "📋 Données brutes":

    st.title("📋 Données pluviométriques brutes")

    st.markdown(
        "### Réponse de l'API telle que reçue, avant tout traitement"
    )

    bandeau_origine()

    if "reponse_api" in st.session_state:

        reponse = st.session_state["reponse_api"]
        meta = st.session_state["meta"]
        anomalies = st.session_state["anomalies"]
        valides = st.session_state.get("donnees_valides", [])

        dates_brutes = reponse["daily"]["time"]
        pluies_brutes = reponse["daily"]["precipitation_sum"]

        st.subheader("🧾 Fiche de la collecte")

        m1, m2, m3, m4 = st.columns(4)

        m1.metric("Ville", meta["ville"])
        m2.metric("Jours reçus", len(dates_brutes))
        m3.metric("Données valides", len(valides))
        m4.metric("Anomalies", len(anomalies))

        st.write(
            f"**Source :** {meta['source']}  \n"
            f"**Coordonnées :** {meta['latitude']} ; "
            f"{meta['longitude']}  \n"
            f"**Période :** du {meta['date_debut']} "
            f"au {meta['date_fin']}  \n"
            f"**Collecté le :** {meta['date_collecte']}"
        )

        st.subheader("🧾 Texte brut de la réponse (JSON)")

        st.caption(
            "Aperçu : les 10 premières valeurs de chaque liste. "
            "Le fichier complet se télécharge plus bas."
        )

        apercu = dict(reponse)

        apercu["daily"] = {
            cle: (
                valeurs[:10] + ["..."]
                if isinstance(valeurs, list) and len(valeurs) > 10
                else valeurs
            )
            for cle, valeurs in reponse["daily"].items()
        }

        st.json(apercu, expanded=True)

        st.subheader("📋 Valeurs reçues, jour par jour")

        st.dataframe(
            pd.DataFrame({
                "Date": dates_brutes,
                "Précipitations reçues (mm)": pluies_brutes
            }),
            use_container_width=True,
            hide_index=True
        )

        if anomalies:
            st.warning(
                f"{len(anomalies)} valeur(s) reçue(s) seront écartées "
                "de l'analyse : voir « Qualité des données »."
            )
        else:
            st.success("✅ Aucune anomalie dans les données reçues.")

        st.subheader("📥 Téléchargements")

        st.download_button(
            label="📥 Réponse complète de l'API (JSON)",
            data=json.dumps(
                reponse,
                ensure_ascii=False,
                indent=2
            ).encode("utf-8"),
            file_name="hydrostat_reponse_api.json",
            mime="application/json"
        )

        if "donnees_reelles" in st.session_state:

            st.download_button(
                label="📥 Données valides (CSV)",
                data=st.session_state["donnees_reelles"]
                    .to_csv(index=False)
                    .encode("utf-8-sig"),
                file_name="hydrostat_donnees_valides.csv",
                mime="text/csv"
            )

    else:

        st.warning(
            "Aucune donnée réelle disponible. "
            "Effectuez d'abord une collecte."
        )

elif menu == "🧹 Qualité des données":

    st.title("🧹 Qualité des données")

    if "reponse_api" in st.session_state:

        if bandeau_origine():
            st.info(
                "Le fichier de secours ne contient que des valeurs déjà "
                "validées lors de la collecte initiale : le contrôle "
                "ci-dessous ne peut pas révéler d'anomalies antérieures."
            )

        anomalies = st.session_state["anomalies"]
        recues = len(st.session_state["reponse_api"]["daily"]["time"])
        valides = len(st.session_state.get("donnees_valides", []))

        st.subheader("🔍 Contrôle de qualité")

        col1, col2, col3 = st.columns(3)

        col1.metric("Observations reçues", recues)
        col2.metric("Observations valides", valides)
        col3.metric("Anomalies", len(anomalies))

        motifs = [motif for date_a, valeur, motif in anomalies]

        d1, d2, d3 = st.columns(3)

        d1.metric(
            "Valeurs manquantes",
            motifs.count("Valeur manquante")
        )
        d2.metric(
            "Dates en double",
            motifs.count("Date en double")
        )
        d3.metric(
            "Précipitations négatives",
            motifs.count("Precipitation negative")
        )

        if anomalies:

            st.subheader("⚠️ Anomalies détectées (écartées de l'analyse)")

            st.dataframe(
                pd.DataFrame(
                    [
                        (
                            date_a,
                            "" if valeur is None else str(valeur),
                            motif
                        )
                        for date_a, valeur, motif in anomalies
                    ],
                    columns=["Date", "Valeur reçue", "Motif"]
                ),
                use_container_width=True,
                hide_index=True
            )

        else:
            st.success("Aucune anomalie détectée.")

        if "donnees_reelles" in st.session_state:

            st.subheader("📊 Statistiques descriptives (données valides)")

            st.dataframe(
                st.session_state["donnees_reelles"].describe(),
                use_container_width=True
            )

    else:
        st.warning("Veuillez d'abord collecter des données.")
elif menu == "📊 Statistiques":

    st.title("📊 Analyse statistique des précipitations")

    if "donnees_valides" in st.session_state:

        df = st.session_state["donnees_reelles"].copy()

        res = analyser_precipitations(
            st.session_state["donnees_valides"],
            afficher=False
        )

        st.subheader("📈 Indicateurs statistiques")

        c1, c2, c3 = st.columns(3)

        c1.metric("Moyenne", formater(res["moyenne"]))
        c2.metric("Médiane", formater(res["mediane"]))
        c3.metric("Écart-type (n−1)", formater(res["ecart_type"]))

        c4, c5, c6 = st.columns(3)

        c4.metric("Variance (n−1)", formater(res["variance"], "mm²"))
        c5.metric("Minimum", formater(res["minimum"]))
        c6.metric("Maximum", formater(res["maximum"]))

        st.subheader("📊 Distribution des précipitations")

        fig = px.histogram(
            df,
            x="Précipitations (mm)",
            nbins=15,
            title="Histogramme des précipitations"
        )

        fig.update_layout(template="plotly_white")

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Résumé statistique")

        st.dataframe(
            df["Précipitations (mm)"].describe().to_frame("Valeur"),
            use_container_width=True
        )

    else:
        st.warning("Veuillez d'abord collecter des données.")
elif menu == "🎲 Probabilités":

    st.title("🎲 Analyse probabiliste des précipitations")

    if "donnees_valides" in st.session_state:

        st.subheader("📊 Probabilités empiriques")

        seuil = st.number_input(
            "Seuil de précipitations (mm)",
            min_value=0.0,
            value=1.0,
            step=0.5
        )

        res = analyser_probabilites(
            st.session_state["donnees_valides"],
            seuil_pluie=SEUIL_JOUR_PLUVIEUX,
            seuil_forte_pluie=seuil,
            afficher=False
        )

        c1, c2 = st.columns(2)

        c1.metric(
            f"Probabilité d'un jour pluvieux (≥ {SEUIL_JOUR_PLUVIEUX:g} mm)",
            f"{res['probabilite_pluie'] * 100:.2f} %"
        )

        c2.metric(
            "Probabilité de dépasser le seuil",
            f"{res['probabilite_depassement'] * 100:.2f} %"
        )

        q1, q2, q3 = st.columns(3)

        q1.metric("Quantile 50 %", formater(res["quantile_50"]))
        q2.metric("Quantile 90 %", formater(res["quantile_90"]))
        q3.metric("Quantile 95 %", formater(res["quantile_95"]))

        st.subheader("📈 Fonction de répartition empirique")

        repartition = res["repartition"]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=[valeur for valeur, frequence in repartition],
                y=[frequence for valeur, frequence in repartition],
                mode="lines",
                line=dict(
                    color="#172B4D",
                    width=3,
                    shape="hv"
                ),
                name="Répartition empirique"
            )
        )

        fig.update_yaxes(range=[0, 1.05])

        fig.update_layout(
            template="plotly_white",
            xaxis_title="Précipitations (mm)",
            yaxis_title="Probabilité cumulée"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.info(
            "Les probabilités sont estimées à partir "
            "des fréquences observées."
        )

    else:
        st.warning("Veuillez d'abord collecter des données.")
elif menu == "📐 Inférence":

    st.title("📐 Inférence statistique")

    if "donnees_valides" in st.session_state:

        niveau = st.slider(
            "Niveau de confiance (%)",
            90, 99, 95
        )

        mu0 = st.number_input(
            "Moyenne théorique H₀ (mm)",
            min_value=0.0,
            value=1.0,
            step=0.5
        )

        res = analyser_inference(
            st.session_state["donnees_valides"],
            confiance=niveau / 100,
            mu0=mu0,
            afficher=False
        )

        if res is not None:

            st.subheader("📊 Estimation statistique")

            c1, c2, c3 = st.columns(3)

            c1.metric("Échantillon", res["n"])
            c2.metric("Moyenne", formater(res["moyenne"], decimales=3))
            c3.metric("Écart-type", formater(res["ecart_type"], decimales=3))

            st.subheader("📏 Intervalle de confiance")

            st.success(
                f"IC à {niveau}% : "
                f"[{res['borne_inferieure']:.3f} ; "
                f"{res['borne_superieure']:.3f}] mm"
            )

            st.subheader("🧪 Test d'hypothèse")

            if res["test_possible"]:

                st.write(f"Statistique t : {res['t_statistique']:.4f}")
                st.write(f"p-value : {res['p_value']:.4f}")

                if res["rejet_h0"]:
                    st.error(
                        "H₀ rejetée au seuil choisi."
                    )
                else:
                    st.success(
                        "H₀ non rejetée au seuil choisi."
                    )

            else:
                st.warning(
                    "Test impossible : variance nulle."
                )

            st.info(
                "Ces méthodes supposent des observations "
                "indépendantes et une distribution "
                "approximativement normale, particulièrement "
                "pour les petits échantillons."
            )

        else:
            st.warning(
                "Au moins deux observations sont nécessaires."
            )

    else:
        st.warning(
            "Veuillez d'abord collecter des données."
        )
elif menu == "📈 Valeurs extrêmes":

    afficher_valeurs_extremes()

elif menu == "🏗️ Génie Civil":

    st.title("🏗️ Applications au Génie Civil")

    st.subheader("🌧️ Analyse hydrologique")

    if "donnees_valides" in st.session_state:

        resultats = analyser_precipitations(
            st.session_state["donnees_valides"],
            afficher=False
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "🌧️ Pluie totale",
            f"{resultats['cumul']:.2f} mm"
        )

        c2.metric(
            "📊 Pluie moyenne",
            f"{resultats['moyenne']:.2f} mm"
        )

        c3.metric(
            "⛈️ Pluie maximale",
            f"{resultats['maximum']:.2f} mm"
        )

        c4, c5, c6 = st.columns(3)

        c4.metric(
            f"🌧️ Jours pluvieux (≥ {SEUIL_JOUR_PLUVIEUX:g} mm)",
            resultats["jours_pluvieux"]
        )

        c5.metric(
            "☀️ Jours secs",
            resultats["jours_secs"]
        )

        c6.metric(
            "📅 Observations",
            resultats["nombre_jours"]
        )

    else:
        st.warning("Veuillez d'abord collecter des données.")
    st.divider()

    st.subheader("💧 Simulateur de ruissellement")

    st.write(
        "Estimation du volume d'eau ruisselé "
        "sur une surface donnée."
    )

    col1, col2 = st.columns(2)

    with col1:

        surface = st.number_input(
            "Superficie du terrain (m²)",
            min_value=1.0,
            value=1000.0,
            step=100.0
        )

        pluie_mm = st.number_input(
            "Hauteur de précipitation (mm)",
            min_value=0.0,
            value=50.0,
            step=5.0
        )

    with col2:

        type_surface = st.selectbox(
            "Type de surface",
            [
                "Béton",
                "Asphalte",
                "Sol naturel",
                "Pelouse",
                "Toiture"
            ]
        )

        coefficients = {
            "Béton": 0.90,
            "Asphalte": 0.85,
            "Sol naturel": 0.40,
            "Pelouse": 0.25,
            "Toiture": 0.95
        }

        coefficient = st.number_input(
            "Coefficient de ruissellement",
            min_value=0.0,
            max_value=1.0,
            value=coefficients[type_surface],
            step=0.05
        )

    if st.button("💧 Calculer le ruissellement"):

        volume = calculer_ruissellement(
            pluie_mm,
            surface,
            coefficient
        )

        st.success("Calcul effectué avec succès !")

        st.metric(
            "Volume d'eau ruisselé",
            f"{volume:,.2f} m³"
        )

        st.info(
            f"Une pluie de {pluie_mm:.1f} mm sur "
            f"une surface de {surface:,.0f} m², "
            f"avec un coefficient de {coefficient:.2f}, "
            f"produit un volume estimé de "
            f"{volume:,.2f} m³."
        )

    st.caption(
        "Estimation simplifiée. Les coefficients proposés "
        "sont indicatifs et doivent être adaptés aux "
        "caractéristiques du terrain."
    )
    st.divider()

    st.subheader("🌧️ Calcul du débit de pointe")

    st.write(
        "Estimation du débit maximal des eaux pluviales "
        "par la méthode rationnelle."
    )

    col1, col2 = st.columns(2)

    with col1:
        surface_ha = st.number_input(
            "Superficie du bassin versant (ha)",
            min_value=0.01,
            value=2.0,
            step=0.1
        )

        intensite = st.number_input(
            "Intensité de pluie (mm/h)",
            min_value=0.0,
            value=60.0,
            step=5.0
        )

    with col2:
        coefficient = st.slider(
            "Coefficient de ruissellement",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.05
        )

    if st.button("Calculer le débit de pointe"):

        from genie_civil import calculer_debit_pointe

        debit = calculer_debit_pointe(
            coefficient,
            intensite,
            surface_ha
        )

        st.success("Calcul effectué avec succès !")

        st.metric(
            "Débit de pointe",
            f"{debit:.3f} m³/s"
        )

        st.info(
            f"Pour une superficie de {surface_ha} ha, "
            f"une intensité de {intensite} mm/h "
            f"et un coefficient de {coefficient}, "
            f"le débit de pointe estimé est "
            f"{debit:.3f} m³/s."
        )
    st.divider()

    st.subheader(
        "🏗️ Dimensionnement hydraulique d'un caniveau"
    )

    st.write(
        "Calcul de la capacité hydraulique "
        "d'un caniveau rectangulaire."
    )

    from genie_civil import calculer_debit_caniveau

    col1, col2 = st.columns(2)

    with col1:

        largeur = st.number_input(
            "Largeur du caniveau (m)",
            min_value=0.1,
            value=0.5,
            step=0.1
        )

        hauteur = st.number_input(
            "Hauteur d'eau (m)",
            min_value=0.1,
            value=0.4,
            step=0.1
        )

    with col2:

        pente = st.number_input(
            "Pente longitudinale (m/m)",
            min_value=0.0001,
            value=0.01,
            format="%.4f"
        )

        strickler = st.number_input(
            "Coefficient de Strickler",
            min_value=1.0,
            value=70.0
        )

    if st.button("Calculer la capacité du caniveau"):

        debit_caniveau = calculer_debit_caniveau(
            largeur,
            hauteur,
            pente,
            strickler
        )

        st.success("Calcul effectué avec succès !")

        st.metric(
            "Capacité hydraulique",
            f"{debit_caniveau:.3f} m³/s"
        )
else:

    st.title(menu)

    st.info(
        "Cet espace sera connecté progressivement "
        "aux modules scientifiques HYDROSTAT."
    )
