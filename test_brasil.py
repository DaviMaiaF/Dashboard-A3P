import streamlit as st
import pandas as pd
import plotly.express as px

# Dados de exemplo
data = {
    "UF": ["SP", "RJ", "MG", "RS", "PR"],
    "Total": [100, 80, 70, 60, 50]
}
state_data = pd.DataFrame(data)

# Mapa do Brasil
st.subheader("Mapa de Adesões por Estado")
brazil_geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

fig_mapa = px.choropleth(
    state_data,
    geojson=brazil_geojson_url,
    locations="UF",
    featureidkey="properties.sigla",
    color="Total",
    color_continuous_scale="Blues",
    scope="south america",
    title="Adesões por Estado no Brasil",
    labels={"Total": "Número de Adesões"},
    height=800,
    width=1300
)
fig_mapa.update_geos(center={"lat": -14.2350, "lon": -51.9253}, projection_scale=4)

# Exibir o mapa
st.plotly_chart(fig_mapa, use_container_width=True)