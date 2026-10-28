import streamlit as st
import pandas as pd
import plotly.express as px
from collecte import collecter_precipitations
from datetime import date, timedelta

# ==========================================
# CONFIGURATION HYDROSTAT
# ==========================================

st.set_page_config(
    page_title="HYDROSTAT | Génie Civil",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
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
            "☔ Jours pluvieux",
            int((pluies >= 1).sum())
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
            value=date(2025, 1, 1)
        )

    with col2:
        date_fin = st.date_input(
            "Date de fin",
            value=date(2025, 1, 7)
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

                    donnees_reelles = pd.DataFrame({
                        "Date": pd.to_datetime(
                            resultat["daily"]["time"]
                        ),
                        "Précipitations (mm)":
                            resultat["daily"]["precipitation_sum"]
                    })

                    st.session_state["donnees_reelles"] = donnees_reelles

                st.success("✅ Collecte terminée avec succès !")

            except Exception as erreur:
                st.error(f"Erreur de collecte : {erreur}")

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"]

        st.subheader("📋 Données collectées")

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
        "### Données collectées depuis Open-Meteo"
    )

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"]

        st.success("✅ Données disponibles")

        st.metric(
            "Nombre d'observations",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            label="📥 Télécharger les données CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="hydrostat_donnees_brutes.csv",
            mime="text/csv"
        )

    else:

        st.warning(
            "Aucune donnée réelle disponible. "
            "Effectuez d'abord une collecte."
        )

elif menu == "🧹 Qualité des données":

    st.title("🧹 Qualité des données")

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"].copy()

        st.success("Données disponibles pour vérification")

        st.subheader("🔍 Contrôle de qualité")

        col1, col2, col3 = st.columns(3)

        col1.metric("Observations", len(df))
        col2.metric("Valeurs manquantes", int(df.isna().sum().sum()))
        col3.metric("Doublons", int(df.duplicated().sum()))

        st.subheader("📊 Statistiques descriptives")
        st.dataframe(df.describe(), use_container_width=True)

        st.subheader("⚠️ Précipitations négatives")

        negatives = (df["Précipitations (mm)"] < 0).sum()

        if negatives == 0:
            st.success("Aucune précipitation négative détectée.")
        else:
            st.error(f"{negatives} valeurs négatives détectées.")

    else:
        st.warning("Veuillez d'abord collecter des données.")
elif menu == "📊 Statistiques":

    st.title("📊 Analyse statistique des précipitations")

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"].copy()

        pluie = df["Précipitations (mm)"].dropna()

        if len(pluie) > 0:

            st.subheader("📈 Indicateurs statistiques")

            c1, c2, c3 = st.columns(3)

            c1.metric("Moyenne", f"{pluie.mean():.2f} mm")
            c2.metric("Médiane", f"{pluie.median():.2f} mm")
            c3.metric("Écart-type", f"{pluie.std():.2f} mm")

            c4, c5, c6 = st.columns(3)

            c4.metric("Variance", f"{pluie.var():.2f} mm²")
            c5.metric("Minimum", f"{pluie.min():.2f} mm")
            c6.metric("Maximum", f"{pluie.max():.2f} mm")

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
                pluie.describe().to_frame("Valeur"),
                use_container_width=True
            )

        else:
            st.warning("Aucune précipitation exploitable.")

    else:
        st.warning("Veuillez d'abord collecter des données.")
elif menu == "🎲 Probabilités":

    st.title("🎲 Analyse probabiliste des précipitations")

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"].copy()
        pluie = df["Précipitations (mm)"].dropna()

        if len(pluie) > 0:

            st.subheader("📊 Probabilités empiriques")

            seuil = st.number_input(
                "Seuil de précipitations (mm)",
                min_value=0.0,
                value=1.0,
                step=0.5
            )

            p_pluie = (pluie > 0).mean()
            p_seuil = (pluie > seuil).mean()

            c1, c2 = st.columns(2)

            c1.metric(
                "Probabilité d'un jour pluvieux",
                f"{p_pluie * 100:.2f} %"
            )

            c2.metric(
                "Probabilité de dépasser le seuil",
                f"{p_seuil * 100:.2f} %"
            )

            st.subheader("📈 Fonction de répartition empirique")

            # Fonction de répartition empirique
    import numpy as np
    import plotly.graph_objects as go

    valeurs = np.sort(
        df["Précipitations (mm)"].dropna().to_numpy()
    )

    n = len(valeurs)

    fig = go.Figure()

    if n > 0:
        probabilites = np.arange(1, n + 1) / n

        fig.add_trace(
            go.Scatter(
                x=valeurs,
                y=probabilites,
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
            st.warning("Aucune donnée exploitable.")

    else:
        st.warning("Veuillez d'abord collecter des données.")
elif menu == "📐 Inférence":

    st.title("📐 Inférence statistique")

    import numpy as np
    from scipy import stats

    if "donnees_reelles" in st.session_state:

        df = st.session_state["donnees_reelles"].copy()

        pluie = df["Précipitations (mm)"].dropna()

        n = len(pluie)

        if n >= 2:

            moyenne = pluie.mean()
            ecart_type = pluie.std(ddof=1)

            st.subheader("📊 Estimation statistique")

            c1, c2, c3 = st.columns(3)

            c1.metric("Échantillon", n)
            c2.metric("Moyenne", f"{moyenne:.3f} mm")
            c3.metric("Écart-type", f"{ecart_type:.3f} mm")

            st.subheader("📏 Intervalle de confiance")

            niveau = st.slider(
                "Niveau de confiance (%)",
                90, 99, 95
            )

            alpha = 1 - niveau / 100

            erreur = stats.t.ppf(
                1 - alpha / 2,
                df=n - 1
            ) * ecart_type / np.sqrt(n)

            borne_inf = moyenne - erreur
            borne_sup = moyenne + erreur

            st.success(
                f"IC à {niveau}% : "
                f"[{borne_inf:.3f} ; {borne_sup:.3f}] mm"
            )

            st.subheader("🧪 Test d'hypothèse")

            mu0 = st.number_input(
                "Moyenne théorique H₀ (mm)",
                min_value=0.0,
                value=1.0,
                step=0.5
            )

            if ecart_type > 0:

                t_stat, p_value = stats.ttest_1samp(
                    pluie,
                    popmean=mu0
                )

                st.write(f"Statistique t : {t_stat:.4f}")
                st.write(f"p-value : {p_value:.4f}")

                if p_value < alpha:
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
else:

    st.title(menu)

    st.info(
        "Cet espace sera connecté progressivement "
        "aux modules scientifiques HYDROSTAT."
    )