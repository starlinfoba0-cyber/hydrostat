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
            try:
                with st.spinner("Collecte des données en cours..."):

                    resultat = collecter_precipitations(
                        str(date_debut),
                        str(date_fin),
                        latitude,
                        longitude
                    )

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
                st.session_state["meta"] = {
                    "ville": ville,
                    "latitude": latitude,
                    "longitude": longitude,
                    "date_debut": str(date_debut),
                    "date_fin": str(date_fin),
                    "date_collecte": datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    "nb_recus": len(dates_recues),
                    "source": "Open-Meteo Historical Weather API"
                }

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

                    st.success("✅ Collecte terminée avec succès !")

                else:
                    st.error(
                        "Aucune donnée valide sur cette période. "
                        "Consultez « Données brutes » et "
                        "« Qualité des données »."
                    )

            except Exception as erreur:
                st.error(f"Erreur de collecte : {erreur}")

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"]
        meta = st.session_state["meta"]

        st.subheader("📋 Données collectées")

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
