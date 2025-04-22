import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ============================
# Configuração da Página
# ============================
st.set_page_config(
    page_title="Dashboard A3P",
    layout="wide",
    page_icon="images/Logo-a3p-fundo.png"
)

st.markdown("<h1 style='text-align: center;'>Dashboard de Adesões à A3P</h1>", unsafe_allow_html=True)

# ============================
# Função para carregar dados
# ============================
@st.cache_data

def load_data(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name, skipfooter=2)

uploaded_file = "Adesões à A3P - Banco de Dados 3 - Davi.xlsx"
sheet_name = "Adesões à A3P"

try:
    data = load_data(uploaded_file, sheet_name)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# ============================
# Pré-processamento
# ============================
data = data.drop_duplicates()
data['Esfera'] = data['Esfera'].str.strip().str.title()
data['Poder'] = data['Poder'].str.strip().str.title()
data['UF'] = data['UF'].str.upper().str.strip()
data['Início da Vigência'] = pd.to_datetime(data['Início da Vigência'], errors='coerce')
data['Final da Vigência'] = pd.to_datetime(data['Final da Vigência'], errors='coerce')

hoje = pd.Timestamp.today().normalize()
data['Vigente'] = data['Final da Vigência'].apply(lambda x: x >= hoje if pd.notnull(x) else False)

ufs_validas = sorted(data['UF'].dropna().unique())

# ============================
# Filtros Gerais
# ============================
st.sidebar.header("Filtros")
filtrar_vigente = st.sidebar.checkbox("Somente vigentes", value=True)
filtro_poder = st.sidebar.multiselect("Poder", options=sorted(data['Poder'].dropna().unique()))
filtro_esfera = st.sidebar.multiselect("Esfera", options=sorted(data['Esfera'].dropna().unique()))
filtro_uf = st.sidebar.multiselect("Estado (UF)", options=ufs_validas)

# ============================
# Aplicação dos Filtros
# ============================
df_filtrado = data.copy()
if filtrar_vigente:
    df_filtrado = df_filtrado[df_filtrado['Vigente']]
if filtro_poder:
    df_filtrado = df_filtrado[df_filtrado['Poder'].isin(filtro_poder)]
if filtro_esfera:
    df_filtrado = df_filtrado[df_filtrado['Esfera'].isin(filtro_esfera)]
if filtro_uf:
    df_filtrado = df_filtrado[df_filtrado['UF'].isin(filtro_uf)]

# ============================
# KPIs
# ============================
st.subheader("Visão Geral")
k1, k2, k3 = st.columns(3)
k1.metric("Adesões Totais", df_filtrado.shape[0])
k2.metric("Adesões Vigentes", df_filtrado[df_filtrado['Vigente']].shape[0])
k3.metric("Estados com Adesão", df_filtrado['UF'].nunique())

# ============================
# Contagem por UF
# ============================
st.subheader("Contagem de Instituições por UF")
contagem_uf = df_filtrado.groupby("UF").size().reset_index(name="Total Instituições")
contagem_uf = contagem_uf.sort_values(by="Total Instituições", ascending=False)
st.dataframe(contagem_uf, use_container_width=True, hide_index=True)

# ============================
# Gráfico de Mapa
# ============================
st.subheader("Mapa de Adesões por Estado")
brazil_geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
map_data = df_filtrado.groupby("UF").size().reset_index(name="Total")

fig_mapa = px.choropleth(
    map_data,
    geojson=brazil_geojson_url,
    locations="UF",
    featureidkey="properties.sigla",
    color="Total",
    color_continuous_scale="Blues",
    scope="south america",
    labels={"Total": "Número de Adesões"},
    height=600
)
fig_mapa.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    coloraxis_colorbar=dict(
        thickness=10,
        len=0.5,
        yanchor='middle',
        y=0.5,
        xanchor='left',
        x=1.05
    )
)
st.plotly_chart(fig_mapa, use_container_width=True)

# ============================
# Gráfico de Linha: Adesões Vigentes ao Longo do Tempo
# ============================
st.subheader("Adesões Vigentes ao Longo do Tempo")
filtered_dates = df_filtrado.dropna(subset=["Início da Vigência", "Final da Vigência"]).copy()
filtered_dates["Final da Vigência"] = filtered_dates["Final da Vigência"].apply(lambda x: min(x, hoje))

date_range = pd.date_range(
    start=filtered_dates["Início da Vigência"].min(),
    end=hoje,
    freq='D'
)

vigentes_por_dia = np.array([
    ((filtered_dates["Início da Vigência"] <= dia) & (filtered_dates["Final da Vigência"] >= dia)).sum()
    for dia in date_range
])

vigentes_df = pd.DataFrame({"Data": date_range, "Adesões Vigentes": vigentes_por_dia})
vigentes_trimestre = vigentes_df.resample('Q', on='Data').max().reset_index()

fig_linha = px.line(
    vigentes_trimestre,
    x="Data",
    y="Adesões Vigentes",
    markers=True,
    title=f"Adesões Vigentes até {hoje.strftime('%d/%m/%Y')}",
    labels={"Adesões Vigentes": "Adesões Vigentes"},
    height=500
)
st.plotly_chart(fig_linha, use_container_width=True)

# ============================
# Gráfico de Pizza por Esfera
# ============================
st.subheader("Distribuição por Esfera")
group_esfera = df_filtrado.groupby("Esfera").size().reset_index(name="Total")
fig_pie = px.pie(group_esfera, values="Total", names="Esfera", hole=0.4)
fig_pie.update_traces(
    texttemplate='%{label}<br>%{value}',
    hovertemplate="<b>%{label}</b><br>Total: %{value}<br>%{percent}<extra></extra>",
    textfont=dict(size=14)
)
st.plotly_chart(fig_pie, use_container_width=True)

# ============================
# Gráfico de Barras por Poder
# ============================
st.subheader("Distribuição por Poder")
group_poder = df_filtrado.groupby("Poder").size().reset_index(name="Total")
fig_bar = px.bar(group_poder, x="Total", y="Poder", orientation="h", text="Total")
fig_bar.update_layout(xaxis_title="Quantidade", yaxis_title="Poder")
fig_bar.update_traces(textposition="outside")
st.plotly_chart(fig_bar, use_container_width=True)

# ============================
# Gráfico de Municípios com filtro por UF e detalhes
# ============================
st.subheader("Top Municípios com Mais Adesões")

if "Cidade " in df_filtrado.columns:
    df_municipios = df_filtrado.copy()
    df_municipios["Cidade "] = df_municipios["Cidade "].astype(str).str.strip().str.title()

    uf_municipio = st.selectbox("Selecione um estado para visualizar os municípios:", options=ufs_validas)
    municipios_filtrados = df_municipios[df_municipios["UF"] == uf_municipio]

    municipios_count = municipios_filtrados.groupby("Cidade ").size().reset_index(name="Total Instituições")
    municipios_count = municipios_count.sort_values(by="Total Instituições", ascending=False).head(20)

    if not municipios_count.empty:
        fig_mun = px.bar(
            municipios_count,
            x="Total Instituições",
            y="Cidade ",
            orientation="h",
            title=f"Top 20 Municípios com Mais Adesões - {uf_municipio}",
            text="Total Instituições"
        )
        fig_mun.update_traces(textposition="outside")
        fig_mun.update_layout(yaxis_title="Município", xaxis_title="Total de Instituições")
        st.plotly_chart(fig_mun, use_container_width=True)

        # Novo: seleção de município
        municipio_selecionado = st.selectbox(
            "Selecione um município para ver detalhes:",
            options=municipios_count["Cidade "].tolist()
        )

        dados_municipio = municipios_filtrados[municipios_filtrados["Cidade "] == municipio_selecionado]
        st.markdown(f"### Instituições em *{municipio_selecionado} - {uf_municipio}*:")
        st.dataframe(dados_municipio.sort_values("Início da Vigência"), use_container_width=True, hide_index=True)
    else:
        st.info(f"Nenhum município encontrado para o estado selecionado: {uf_municipio}")
else:
    st.warning("A coluna 'Cidade ' não está presente no conjunto de dados.")

# ============================
# Botão de download dos dados filtrados
# ============================
st.download_button(
    label="📥 Baixar dados filtrados",
    data=df_filtrado.to_csv(index=False).encode("utf-8"),
    file_name="dados_filtrados.csv",
    mime="text/csv"
)