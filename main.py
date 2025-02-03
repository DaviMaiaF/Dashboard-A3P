import streamlit as st
import pandas as pd
import plotly.express as px

# Função para carregar os dados
@st.cache_data
def load_data(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name)

# Streamlit - Interface do Dashboard
st.title("Dashboard - Análise de Adesões à A3P")

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

# Adicionar após a validação das colunas
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
st.header("Visualizações Principais:")

# Primeira linha: Gráfico de Pizza e Gráfico de Barras Horizontais com uma coluna invisível no meio
col1, espaco1,  col2 = st.columns([6, 0.5, 6]) # 6: Largura do gráfico, 0.5: largura do espaço
with col1:
    # Gráfico de Pizza
    fig_pizza = px.pie(
        grouped_data,
        values="Total",
        names="Esfera",
        title="Distribuição Percentual de Adesões por Esfera",
        hole=0.4,
        height=400
    )
    fig_pizza.update_traces(textfont=dict(size=14))
    fig_pizza.update_layout(title=dict(font=dict(size=20)), legend=dict(font=dict(size=14)))
    st.plotly_chart(fig_pizza, use_container_width=True)

with espaco1:
    st.write("") #Coluna Fantasma

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
        title=f"Esferas para o Poder {selected_power}",
        labels={"Total": "Quantidade", "Esfera": "Esfera"},
        height=400
    )
    fig_barra.update_traces(textposition="outside", textfont=dict(size=14))
    fig_barra.update_layout(
        title=dict(font=dict(size=20)),
        xaxis=dict(title_font=dict(size=16), tickfont=dict(size=14)),
        yaxis=dict(title_font=dict(size=16), tickfont=dict(size=14))
    )
    st.plotly_chart(fig_barra, use_container_width=True)

# Adicionar espaço entre as linhas
st.markdown("<br><br>", unsafe_allow_html=True) # Dá o espaço de duas linhas

# Segunda linha: Mapa e Gráfico de Linha com um espaço no meio
col3, espaco2, col4 = st.columns([15, 1, 15]) # 6: largura do gráfico, 0.5: largura do espaço

with col3:
    # Mapa do Brasil (ATUALIZADO)
    st.subheader("Mapa de Adesões por Estado")
    brazil_geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    state_data = data.groupby("UF").size().reset_index(name="Total")

    # Verificar siglas válidas
    valid_ufs = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE",
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
            title="Adesões por Estado no Brasil",
            labels={"Total": "Número de Adesões"},
            custom_data=["UF"],
            height=800,
            width=1300
        )
        fig_mapa.update_geos(center={"lat": -14.2350, "lon": -51.9253}, projection_scale=4)

        # 👇 Remover completamente a barra de cores
        fig_mapa.update_traces(showscale=False)  # Remove a barra de cores
        fig_mapa.update_layout(coloraxis_showscale=False)  # Garante que a escala de cores não seja exibida

        # Exibir o mapa
        st.plotly_chart(fig_mapa, use_container_width=True)

        # Capturar o estado clicado manualmente
        if "map_click_data" not in st.session_state:
            st.session_state["map_click_data"] = None

        # Botão para selecionar estado manualmente (FILTRO PERMANECE)
        estado_selecionado = st.selectbox("Selecione um estado", valid_ufs, index=0)
        if st.button("Aplicar seleção"):
            st.session_state["map_click_data"] = estado_selecionado
    else:
        st.warning("Nenhum dado válido para exibir o mapa.")

with espaco2:
    st.write("") # Coluna fantasma

with col4:
    # Gráfico de Linha - Evolução Diária (ATUALIZADO)
    st.subheader("Evolução das Adesões até Hoje")

    # Usar data de INÍCIO da vigência para a evolução
    data["Data"] = pd.to_datetime(data["Início da Vigência"], errors="coerce").dt.date

    today = pd.Timestamp.today().date()
    filtered_data = data.dropna(subset=["Data"]).query("Data <= @today")

    # Filtrar por estado clicado (se houver)
    if st.session_state.get("map_click_data"):
        estado_selecionado = st.session_state["map_click_data"]
        filtered_data = filtered_data[filtered_data["UF"] == estado_selecionado]
        st.write(f"Mostrando dados para o estado: *{estado_selecionado}*")

    # Verificar se há dados
    if filtered_data.empty:
        st.warning("Não há dados históricos disponíveis.")
        st.stop()

    daily_data = filtered_data.groupby("Data").size().reset_index(name="Total")

    # Definir limites do slider corretamente
    min_date = daily_data["Data"].min()
    max_date = daily_data["Data"].max()

    # Criar slider
    selected_dates = st.sidebar.date_input(
        "Selecione o intervalo de datas",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Filtrar dados pelo intervalo de datas
    if len(selected_dates) == 2:
        filtered_daily_data = daily_data[
            (daily_data["Data"] >= selected_dates[0]) & (daily_data["Data"] <= selected_dates[1])
            ]
    else:
        filtered_daily_data = daily_data

    # Gráfico de Linha
    fig_linha = px.line(
        filtered_daily_data,
        x="Data",
        y="Total",
        title=f"Evolução das Adesões até {today}",
        markers=True,
        labels={"Total": "Adesões", "Data": "Data"},
        height=500
    )
    fig_linha.update_xaxes(range=[min_date, today])
    st.plotly_chart(fig_linha, use_container_width=True)