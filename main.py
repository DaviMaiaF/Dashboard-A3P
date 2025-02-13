import streamlit as st
import pandas as pd
import plotly.express as px

# Função para carregar os dados
@st.cache_data
def load_data(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name, skipfooter=2)  # Ignora linhas extras no final

# Streamlit - Interface do Dashboard
st.markdown("<h1 style='text-align: center;'>Análise de Adesões à A3P</h1>", unsafe_allow_html=True)

# Nome da aba fixa e arquivo
sheet_name = "Adesões à A3P"
uploaded_file = "Adesões à A3P - Banco de Dados 3 - Davi.xlsx"

# Carregar os dados
try:
    data = load_data(uploaded_file, sheet_name=sheet_name)
except FileNotFoundError:
    st.error(f"Arquivo '{uploaded_file}' não encontrado. Verifique o caminho e tente novamente.")
    st.stop()
except ValueError:
    st.error(f"A aba '{sheet_name}' não foi encontrada no arquivo. Verifique o nome da aba e tente novamente.")
    st.stop()

# Validar a existência de colunas relevantes
required_columns = ["Poder", "Esfera", "UF", "Início da Vigência", "Final da Vigência"]
if not all(column in data.columns for column in required_columns):
    st.error(f"As colunas necessárias {required_columns} não foram encontradas nos dados. Verifique o arquivo e tente novamente.")
    st.stop()

# Remover duplicatas
data = data.drop_duplicates()

# Padronizar textos para evitar dupla contagem
data['Esfera'] = data['Esfera'].str.strip().str.title()
data['Poder'] = data['Poder'].str.strip().str.title()

# Converter colunas de datas
data['Início da Vigência'] = pd.to_datetime(data['Início da Vigência'], errors='coerce')
data['Final da Vigência'] = pd.to_datetime(data['Final da Vigência'], errors='coerce')

# Criar coluna de vigência
hoje = pd.Timestamp.today().normalize()
data['Vigente'] = data['Final da Vigência'].apply(
    lambda x: x >= hoje if pd.notnull(x) else False
)

# Contar o número de registros por "Poder" e "Esfera"
grouped_data = data[data['Vigente']].groupby(["Poder", "Esfera"]).size().reset_index(name="Total")

# Filtros interativos
st.sidebar.header("Filtros")
selected_power = st.sidebar.selectbox("Selecione um Poder", grouped_data["Poder"].unique(), index=1)
selected_sphere = st.sidebar.selectbox("Selecione uma Esfera", grouped_data["Esfera"].unique(), index=0)

# Filtrar dados com base na seleção
filtered_data = grouped_data[
    (grouped_data["Poder"] == selected_power) & (grouped_data["Esfera"] == selected_sphere)
]

# Exibir dados filtrados na sidebar
st.sidebar.subheader("Dados Filtrados:")
st.sidebar.dataframe(
    filtered_data[["Poder", "Esfera", "Total"]],
    hide_index=True,
    use_container_width=True
)

# Gráficos em uma estrutura de linhas e colunas
st.header("Gráficos Principais:")

# Primeira linha: Gráfico de Pizza e Gráfico de Barras Horizontais com uma coluna invisível no meio
col1, espaco1, col2 = st.columns([10, 0.5, 10])  # 6: Largura do gráfico, 0.5: largura do espaço
with col1:
    # Gráfico de Pizza
    fig_pizza = px.pie(
        grouped_data,
        values="Total",
        names="Esfera",
        title="Percentual de Adesões por Esfera",
        hole=0.4,
        height=550,
        width=800
    )
    fig_pizza.update_traces(textfont=dict(size=14))
    fig_pizza.update_layout(title=dict(font=dict(size=20)), legend=dict(font=dict(size=14)))
    st.plotly_chart(fig_pizza, use_container_width=True)

with espaco1:
    st.write("")  # Coluna Fantasma

with col2:
    # Gráfico de Barras Horizontais por Poder
    st.subheader(f"Contagem de Esferas do Poder: {selected_power}")
    power_data = grouped_data[grouped_data["Poder"] == selected_power]
    fig_barra = px.bar(
        power_data,
        x="Total",
        y="Esfera",
        orientation="h",
        text="Total",
        title=f"Esferas do Poder {selected_power}",
        labels={"Total": "Quantidade", "Esfera": "Esfera"},
        height=550,
        width=800
    )
    fig_barra.update_traces(textposition="outside", textfont=dict(size=14))
    fig_barra.update_layout(
        title=dict(font=dict(size=20)),
        xaxis=dict(title_font=dict(size=16), tickfont=dict(size=14)),
        yaxis=dict(title_font=dict(size=16), tickfont=dict(size=14))
    )
    st.plotly_chart(fig_barra, use_container_width=True)

# Adicionar espaço entre as linhas
st.markdown("<br><br>", unsafe_allow_html=True)  # Dá o espaço de duas linhas

# Segunda linha: Mapa e Gráfico de Linha com um espaço no meio
col3, espaco2, col4 = st.columns([18, 2, 18])  # 15: largura do gráfico, 5: largura do espaço

with col3:
    # Reduzir o espaço acima do título do mapa
    st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)

    st.subheader("Mapa de Adesões")

    # Criar colunas dentro de col3 para dividir o espaço do mapa e da seleção
    mapa_col, filtro_col = st.columns([5, 3])  # 75% mapa, 25% seleção

    with mapa_col:
        brazil_geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        state_data = data.groupby("UF").size().reset_index(name="Total")

        valid_ufs = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
                     "PE",
                     "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
        state_data["UF"] = state_data["UF"].str.upper().str.strip()
        state_data = state_data[state_data["UF"].isin(valid_ufs)]

        if not state_data.empty:
            fig_mapa = px.choropleth(
                state_data,
                geojson=brazil_geojson_url,
                locations="UF",
                featureidkey="properties.sigla",
                color="Total",
                color_continuous_scale="Blues",
                scope="south america",
                title="Adesões por Estado",
                labels={"Total": "Número de Adesões"},
                custom_data=["UF"],
                height=500,
                width=900
            )
            fig_mapa.update_geos(center={"lat": -14.2350, "lon": -51.9253}, projection_scale=1.6)
            fig_mapa.update_traces(showscale=False)
            fig_mapa.update_layout(coloraxis_showscale=False)

            st.plotly_chart(fig_mapa, use_container_width=True)

    with filtro_col:
        # Adiciona espaço extra acima do filtro para descer ele um pouco
        st.markdown("<br><br>", unsafe_allow_html=True)

        if "map_click_data" not in st.session_state:
            st.session_state["map_click_data"] = None

        estado_selecionado = st.selectbox("Selecione um estado", valid_ufs, index=0)
        if st.button("Aplicar seleção"):
            st.session_state["map_click_data"] = estado_selecionado
            st.success(f"Estado: {estado_selecionado}")

with espaco2:
    st.write("")  # Coluna fantasma
    st.write("")

with col4:
    # Gráfico de Linha - Adesões Vigentes ao Longo do Tempo (Até Hoje)
    st.subheader("Adesões Vigentes ao Longo do Tempo (Até Hoje)")

    # Filtrar dados válidos e ajustar "Final da Vigência" para hoje se for futuro
    filtered_data = data.dropna(subset=["Início da Vigência", "Final da Vigência"]).copy()

    # Ajustar "Final da Vigência" para não ultrapassar hoje
    filtered_data["Final da Vigência"] = filtered_data["Final da Vigência"].apply(
        lambda x: min(x, hoje)  # Cap final date at today
    )

    # Criar intervalo de datas até hoje
    date_range = pd.date_range(
        start=filtered_data["Início da Vigência"].min(),
        end=hoje,
        freq='D'
    )

    # Calcular adesões vigentes por dia
    vigentes_por_dia = []
    for dia in date_range:
        # Contar apenas as adesões que estavam vigentes naquele dia
        vigentes = filtered_data[
            (filtered_data["Início da Vigência"] <= dia) &
            (filtered_data["Final da Vigência"] >= dia)
            ].shape[0]
        vigentes_por_dia.append(vigentes)

    vigentes_df = pd.DataFrame({"Data": date_range, "Adesões Vigentes": vigentes_por_dia})

    # Agrupar por trimestre usando o MÁXIMO de adesões vigentes no trimestre
    vigentes_por_trimestre = vigentes_df.resample('Q', on='Data').max().reset_index()

    # Gráfico de Linha
    fig_linha = px.line(
        vigentes_por_trimestre,
        x="Data",
        y="Adesões Vigentes",
        title=f"Adesões Vigentes até {hoje.strftime('%d/%m/%Y')}",
        markers=True,
        labels={"Adesões Vigentes": "Adesões Vigentes"},
        height=550
    )
    st.plotly_chart(fig_linha, use_container_width=True)