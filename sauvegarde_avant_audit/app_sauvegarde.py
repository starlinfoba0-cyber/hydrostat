import streamlit as st
import pandas as pd
import plotly.express as px

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
# DONNEES DE DEMONSTRATION
# ==========================================

donnees = pd.DataFrame({
    "Date": pd.date_range(
        start="2025-01-01",
        periods=7
    ),
    "Précipitations (mm)": [
        0, 5, 12, 0, 25, 40, 8
    ]
})

# ==========================================
# TABLEAU DE BORD
# ==========================================

if menu == "🏠 Tableau de bord":

    st.title("🌊 HYDROSTAT")

    st.markdown(
        "### Tableau de bord d'analyse pluviométrique"
    )

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
            template="plotly_dark",
            paper_bgcolor="#102A43",
            plot_bgcolor="#102A43"
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
            template="plotly_dark",
            paper_bgcolor="#102A43",
            plot_bgcolor="#102A43"
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
# AUTRES PAGES
# ==========================================

else:

    st.title(menu)

    st.info(
        "Cet espace sera connecté progressivement "
        "aux modules scientifiques HYDROSTAT."
    )