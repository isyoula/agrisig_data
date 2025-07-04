import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import leafmap.foliumap as leafmap
from shapely.geometry import Polygon
from PIL import Image

st.set_page_config(page_title="Dashboard Agricole", layout="wide")
st.title("Dispositif SIG du Projet d’Appui à la Gestion Intégrée des Ressources")
st.markdown("Ce tableau de bord permet de visualiser les données agricoles sur Kindia et Mamou.")

# Fonction pour sauvegarder le GeoDataFrame dans un fichier GeoJSON
def save_data(gdf, filepath="data/parcelles_multiculture.geojson"):
    gdf.to_file(filepath, driver="GeoJSON")

# Charger les données depuis le fichier (une seule fois)
@st.cache_data
def load_data():
    return gpd.read_file("data/parcelles_multiculture.geojson")

if "data" not in st.session_state:
    st.session_state.data = load_data()

# Afficher logo dans sidebar
logo = Image.open("images/logo.png")
st.sidebar.image(logo, width=120)

# --- FILTRES ---
st.sidebar.header("🎛️ Filtres")

regions = st.sidebar.multiselect(
    "Région",
    options=st.session_state.data['region'].unique(),
    default=st.session_state.data['region'].unique()
)

cultures = st.sidebar.multiselect(
    "Culture",
    options=st.session_state.data['culture'].unique(),
    default=st.session_state.data['culture'].unique()
)

# --- FORMULAIRE D'AJOUT DE PARCELLE ---
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Ajouter une entrée (démo)")
with st.sidebar.form("ajout_parcelle"):
    culture_new = st.text_input("Culture")
    region_new = st.text_input("Région")
    superficie_new = st.number_input("Superficie (ha)", min_value=0.1, step=0.1)
    rendement_new = st.number_input("Rendement (kg/ha)", min_value=0)

    submit = st.form_submit_button("Ajouter")

    if submit:
        coords_demo = [[-13.7, 9.5], [-13.6, 9.5], [-13.6, 9.6], [-13.7, 9.6], [-13.7, 9.5]]
        new_geom = Polygon(coords_demo)

        new_row = gpd.GeoDataFrame({
            'culture': [culture_new],
            'region': [region_new],
            'superficie': [superficie_new],
            'rendement_kg_ha': [rendement_new],
            'geometry': [new_geom]
        }, crs=st.session_state.data.crs)

        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)

        # Sauvegarder dans le fichier
        save_data(st.session_state.data)

        st.success(f"✅ Parcelle ajoutée : {culture_new} à {region_new}, {superficie_new} ha, {rendement_new} kg/ha")

# --- FILTRAGE selon les filtres sur les données dans session_state ---
filtered_gdf = st.session_state.data[
    (st.session_state.data['region'].isin(regions)) &
    (st.session_state.data['culture'].isin(cultures))
]

# --- CARTE ---
st.subheader("🗺️ Carte des parcelles agricoles")
m = leafmap.Map(center=(9.5, -13.7), zoom=7)
m.add_gdf(filtered_gdf, layer_name="Parcelles filtrées")
m.to_streamlit(height=500)

# --- STATISTIQUES ---
st.subheader("📊 Statistiques générales")
col1, col2 = st.columns(2)
col1.metric("📍 Nombre de parcelles", len(filtered_gdf))
col2.metric("📐 Superficie totale (ha)", round(filtered_gdf['superficie'].sum(), 2))

# --- GRAPHIQUE ---
st.subheader("📈 Rendement moyen par culture")
if not filtered_gdf.empty:
    rendement_df = filtered_gdf.groupby("culture")["rendement_kg_ha"].mean().reset_index()
    fig = px.bar(
        rendement_df,
        x="culture",
        y="rendement_kg_ha",
        title="Rendement moyen (kg/ha)",
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aucune donnée à afficher. Vérifiez les filtres.")

# --- TABLEAU ---
st.subheader("📋 Détail des parcelles filtrées")
st.dataframe(filtered_gdf.drop(columns="geometry"))

# --- EXPORT CSV ---
csv = filtered_gdf.drop(columns="geometry").to_csv(index=False)
st.download_button(
    label="📥 Télécharger les données filtrées (.csv)",
    data=csv,
    file_name="parcelles_filtrees.csv",
    mime="text/csv"
)

# --- PIED DE PAGE ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 1em; color: gray;'>
        Plateforme demo développée par <strong>Ibrahima Sory Youla</strong>, Data Scientist,<br>
        Consultant indépendant dans le développement des applications web géospatiales.<br>
        E-mail: isyoula8@gmail.com
    </div>
    """,
    unsafe_allow_html=True
)

# --- CSS pour padding et sidebar ---
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
