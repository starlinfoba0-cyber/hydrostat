"""HYDROSTAT — thème visuel sobre : fond clair, barre latérale bleu marine,
une seule couleur d'accent, titres en empattement, aucun effet décoratif."""
import html

import streamlit as st

# ==========================================
# PALETTE
# ==========================================

MARINE = "#0F2A43"
PRIMAIRE = "#1E4E8C"
CLAIR = "#9DBBDD"
ACCENT = "#D97706"
VERT = "#2F855A"
ROUGE = "#B83A2E"
ENCRE = "#14213D"
DOUX = "#5B6B7F"
TRAIT = "#E3E8EF"

# Noms conservés pour le reste du code
CYAN = PRIMAIRE
BLEU = PRIMAIRE
AMBRE = ACCENT

COULEURS = [PRIMAIRE, ACCENT, VERT, "#5B8DB8", "#7A5C99", ROUGE]

# Échelle séquentielle à une teinte : du bleu pâle au bleu marine
ICE = [
    [0.0, "#E6EEF7"],
    [0.5, "#6FA0D0"],
    [1.0, "#1E4E8C"],
]

# ==========================================
# FEUILLE DE STYLE
# ==========================================

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap');

:root {
    --encre: #14213D;
    --doux: #475569;
    --trait: #D5DDE6;
    --fond: #EEF1F5;
    --carte: #FFFFFF;
    --primaire: #1E4E8C;
    --accent: #D97706;
    --marine: #0F2A43;
}

.stApp {
    background: var(--fond) !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    color: var(--encre);
}

header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none; }
#MainMenu, footer { visibility: hidden; }

.block-container { padding-top: 2.4rem !important; max-width: 1180px; }

/* ----- Titres ----- */
h1, h2, h3, h4 {
    font-family: 'Source Serif 4', Georgia, serif !important;
    color: var(--marine) !important;
    letter-spacing: -0.01em;
}
h1 { font-weight: 700 !important; font-size: 2.3rem !important; }
h2 { font-weight: 600 !important; font-size: 1.6rem !important; }
h3 { font-weight: 600 !important; font-size: 1.3rem !important; }

p, label, li { color: var(--encre); }
[data-testid="stCaptionContainer"] { color: var(--doux) !important; }

/* ----- Barre latérale ----- */
[data-testid="stSidebar"] { background: var(--marine) !important; }
[data-testid="stSidebar"] * { color: #E8EEF5; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 8px 12px; border-radius: 6px; margin-bottom: 2px;
    transition: background 0.15s;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255, 255, 255, 0.07); }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding-left: 12px; border-left: 3px solid transparent; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: rgba(255, 255, 255, 0.14); font-weight: 600; border-left-color: var(--accent);
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #9FB3C8 !important; }

.logo-nom {
    font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 1.6rem;
    letter-spacing: 0.05em; color: #FFFFFF; line-height: 1.1;
    border-left: 4px solid var(--accent); padding-left: 12px;
}
.logo-sous {
    font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase;
    color: #9FB3C8; margin: 6px 0 22px 16px;
}
.statut { font-size: 0.82rem; font-weight: 500; }
.statut.ok { color: #7DD3A8; }
.statut.alerte { color: #F5B454; }
.statut.neutre { color: #9FB3C8; }

/* ----- En-tête de page ----- */
.entete { margin: 0 0 1.4rem 0; }
.entete-sur {
    font-size: 0.78rem; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--accent); font-weight: 600;
}
.entete-titre {
    font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 2.7rem;
    color: var(--marine); line-height: 1.1; margin: 4px 0 8px 0; letter-spacing: -0.015em;
}
.entete-sous { color: var(--doux); font-size: 1.02rem; max-width: 62ch; margin: 0; line-height: 1.5; }

/* ----- Cartes d'indicateurs ----- */
.kpi {
    background: var(--carte); border: 1px solid var(--trait); border-radius: 10px;
    padding: 18px 20px; box-shadow: 0 1px 3px rgba(15, 42, 67, 0.10);
}
.kpi-titre {
    font-size: 0.72rem; letter-spacing: 0.09em; text-transform: uppercase;
    color: var(--doux); font-weight: 600;
}
.kpi-valeur {
    font-size: 2.1rem; font-weight: 600; color: var(--marine); margin-top: 4px;
    font-variant-numeric: tabular-nums; white-space: nowrap;
}
.kpi-unite { font-size: 0.95rem; font-weight: 500; color: var(--doux); }
.kpi-detail { font-size: 0.82rem; color: var(--doux); margin-top: 2px; }

.ouvrage {
    background: var(--carte); border: 1px solid var(--trait); border-left: 5px solid var(--primaire);
    border-radius: 10px; padding: 14px 18px; margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(15, 42, 67, 0.10);
}
.ouvrage.ok { border-left-color: #2F855A; }
.ouvrage.moyen { border-left-color: #D97706; }
.ouvrage.non { border-left-color: #B83A2E; }
.ouvrage-tete { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.ouvrage-rang { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.12em; color: var(--accent); }
.ouvrage-nom {
    font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 1.2rem; color: var(--marine);
}
.ouvrage-score { font-size: 1.9rem; font-weight: 600; color: var(--marine); font-variant-numeric: tabular-nums; white-space: nowrap; }
.ouvrage-score span { font-size: 0.9rem; font-weight: 500; color: var(--doux); }
.ouvrage-niveau { font-size: 0.84rem; font-weight: 600; }
.ouvrage.ok .ouvrage-niveau { color: #2F855A; }
.ouvrage.moyen .ouvrage-niveau { color: #B45309; }
.ouvrage.non .ouvrage-niveau { color: #B83A2E; }
.barre { height: 8px; background: #E5EAF0; border-radius: 4px; margin: 8px 0 10px 0; }
.barre > div { height: 100%; border-radius: 4px; background: var(--primaire); }
.ouvrage.ok .barre > div { background: #2F855A; }
.ouvrage.moyen .barre > div { background: #D97706; }
.ouvrage.non .barre > div { background: #B83A2E; }
.ouvrage-detail { font-size: 0.9rem; color: var(--doux); }
.ouvrage-mesure { font-size: 0.9rem; color: var(--encre); margin-top: 6px; }

.usage {
    background: var(--carte); border: 1px solid var(--trait); border-top: 3px solid var(--primaire);
    border-radius: 10px; padding: 16px 18px; min-height: 150px;
    box-shadow: 0 1px 3px rgba(15, 42, 67, 0.10);
}
.usage-num { font-size: 0.74rem; font-weight: 600; color: var(--accent); letter-spacing: 0.12em; }
.usage-titre {
    font-family: 'Source Serif 4', Georgia, serif; font-weight: 700; font-size: 1.25rem;
    color: var(--marine); margin: 2px 0 6px 0;
}
.usage-texte { font-size: 0.9rem; color: var(--doux); line-height: 1.5; }

/* ----- Composants Streamlit ----- */
[data-testid="stMetric"] {
    background: var(--carte) !important; border: 1px solid var(--trait) !important;
    border-radius: 10px; padding: 14px 16px !important;
    box-shadow: 0 1px 3px rgba(15, 42, 67, 0.10);
}
[data-testid="stMetricLabel"] { color: var(--doux) !important; }
[data-testid="stMetricValue"] {
    color: var(--marine) !important; font-weight: 600 !important;
    font-variant-numeric: tabular-nums;
}

[data-testid="stAlert"] { border-radius: 8px; }
[data-baseweb="input"], [data-baseweb="select"] > div { border: 1px solid #B8C4D2 !important; background: #FFFFFF !important; }

div.stButton > button, div.stDownloadButton > button {
    background: var(--primaire) !important; color: #FFFFFF !important; font-weight: 500;
    border: none !important; border-radius: 6px; padding: 0.5rem 1.2rem;
}
div.stButton > button *, div.stDownloadButton > button * { color: #FFFFFF !important; }
div.stButton > button:hover, div.stDownloadButton > button:hover { background: #173F73 !important; }

[data-testid="stDataFrame"] { border: 1px solid var(--trait); border-radius: 10px; overflow: hidden; }
[data-testid="stExpander"] { border: 1px solid var(--trait) !important; border-radius: 8px; background: var(--carte); }
[data-testid="stPlotlyChart"] {
    background: var(--carte); border: 1px solid var(--trait); border-radius: 10px; padding: 8px;
}
hr { border-color: var(--trait) !important; }

[data-baseweb="tab-list"] { gap: 8px; }
button[role="tab"] { font-weight: 500 !important; font-size: 1rem !important; color: var(--doux) !important; }
button[role="tab"][aria-selected="true"] { color: var(--marine) !important; font-weight: 600 !important; }
[data-baseweb="tab-highlight"] { background-color: var(--accent) !important; }
"""


def _compacter(css):
    """Supprime indentation et lignes vides : évite que le Markdown les interprète."""
    return "\n".join(ligne.strip() for ligne in css.splitlines() if ligne.strip())


def appliquer_theme():
    """Injecte la feuille de style dans la page."""
    st.markdown(f"<style>{_compacter(CSS)}</style>", unsafe_allow_html=True)


# ==========================================
# GRAPHIQUES
# ==========================================

def style_figure(fig):
    """Applique le style HYDROSTAT à une figure Plotly (fond transparent, grilles claires)."""
    try:
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Inter, Segoe UI, sans-serif",
                color=ENCRE,
                size=13
            ),
            colorway=COULEURS,
            margin=dict(l=48, r=22, t=56, b=44),
            hoverlabel=dict(
                bgcolor="#FFFFFF",
                bordercolor=TRAIT,
                font=dict(color=ENCRE)
            ),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            title=dict(
                font=dict(
                    family="Source Serif 4, Georgia, serif",
                    size=18,
                    color=MARINE
                )
            )
        )

        axe = dict(
            gridcolor="#E1E7EE",
            zerolinecolor="#CBD5E1",
            linecolor="#CBD5E1",
            tickfont=dict(color=DOUX),
            title=dict(font=dict(color=DOUX))
        )

        fig.update_xaxes(**axe)
        fig.update_yaxes(**axe)

    except (ValueError, KeyError, TypeError):
        pass    # un échec de style ne doit jamais empêcher d'afficher le graphique

    return fig


# ==========================================
# BLOCS HTML
# ==========================================

def nombre(valeur, decimales=0):
    """Nombre à la française : espace pour les milliers, virgule décimale (1 560,5)."""
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def _html(texte):
    """HTML sur une seule ligne : le Markdown ne doit pas l'interpréter."""
    return "".join(ligne.strip() for ligne in texte.splitlines())


def logo_sidebar():
    """Nom et sous-titre de la barre latérale."""
    return _html("""
        <div class="logo-nom">HYDROSTAT</div>
        <div class="logo-sous">Pluies &amp; drainage</div>
    """)


def puce_statut(texte, etat="neutre"):
    """Indicateur d'état (etat : ok, alerte ou neutre)."""
    return f'<span class="statut {etat}">● {html.escape(texte)}</span>'


def entete(surtitre, titre, sous_titre):
    """En-tête de page : petit surtitre, grand titre, une phrase d'explication."""
    return _html(f"""
        <div class="entete">
        <div class="entete-sur">{html.escape(surtitre)}</div>
        <div class="entete-titre">{html.escape(titre)}</div>
        <p class="entete-sous">{html.escape(sous_titre)}</p>
        </div>
    """)


def carte_kpi(titre, valeur, unite="", detail=""):
    """Carte d'indicateur : libellé, grande valeur, unité, précision."""
    unite_html = f'<span class="kpi-unite"> {html.escape(unite)}</span>' if unite else ""
    detail_html = f'<div class="kpi-detail">{html.escape(detail)}</div>' if detail else ""

    return _html(f"""
        <div class="kpi">
        <div class="kpi-titre">{html.escape(titre)}</div>
        <div class="kpi-valeur">{html.escape(str(valeur))}{unite_html}</div>
        {detail_html}
        </div>
    """)


def carte_usage(numero, titre, texte):
    """Carte « à quoi servent les données » (numéro, titre, courte explication)."""
    return _html(f"""
        <div class="usage">
        <div class="usage-num">{html.escape(numero)}</div>
        <div class="usage-titre">{html.escape(titre)}</div>
        <div class="usage-texte">{html.escape(texte)}</div>
        </div>
    """)


def carte_travaux(rang, nom, score, niveau, detail, mesure):
    """Carte d'un type de travaux : rang, nom, score sur 100, niveau, explication, mesure."""
    classe = {"Favorable": "ok", "Sous conditions": "moyen", "Déconseillé": "non"}.get(niveau, "")
    largeur = 0 if score is None else max(0, min(100, int(score)))
    score_html = (
        f'<div class="ouvrage-score">{int(score)}<span> / 100</span></div>'
        if score is not None else '<div class="ouvrage-score"><span>n/d</span></div>'
    )

    return _html(f"""
        <div class="ouvrage {classe}">
        <div class="ouvrage-tete">
        <div><div class="ouvrage-rang">N° {int(rang)}</div><div class="ouvrage-nom">{html.escape(nom)}</div></div>
        <div style="text-align:right">{score_html}<div class="ouvrage-niveau">{html.escape(niveau)}</div></div>
        </div>
        <div class="barre"><div style="width:{largeur}%"></div></div>
        <div class="ouvrage-detail">{html.escape(detail)}</div>
        <div class="ouvrage-mesure"><b>Mesures possibles :</b> {html.escape(mesure)}</div>
        </div>
    """)
