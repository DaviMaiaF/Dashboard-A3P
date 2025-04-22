import streamlit as st
import pandas as pd
import plotly.express as px

# Configurar a página com o ícone
st.set_page_config(
    page_title="Análise de Adesões à A3P",
    page_icon="images/Logo-a3p-fundo.png",  # Caminho relativo para o ícone
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar o estado selecionado
if "map_click_data" not in st.session_state:
    st.session_state["map_click_data"] = None

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

# Filtros interativos na sidebar
st.sidebar.header("Filtros")
selected_powers = st.sidebar.multiselect(
    "Selecione um ou mais Poderes",
    grouped_data["Poder"].unique(),
    default=grouped_data["Poder"].unique()[0]
)
selected_sphere = st.sidebar.selectbox("Selecione uma Esfera", grouped_data["Esfera"].unique(), index=0)

# Filtrar dados com base na seleção
filtered_data = grouped_data[
    (grouped_data["Poder"].isin(selected_powers)) & (grouped_data["Esfera"] == selected_sphere)
]

# Exibir dados filtrados na sidebar
st.sidebar.subheader("Dados Filtrados:")
st.sidebar.dataframe(
    filtered_data[["Poder", "Esfera", "Total"]],
    hide_index=True,
    use_container_width=True
)

# Função para atualizar gráficos com base no estado selecionado
def update_charts(selected_state):
    # Filtrar dados para o estado selecionado
    state_data = data[data["UF"] == selected_state]

    # Verificar dados
    grouped_esfera = state_data.groupby("Esfera").size().reset_index(name="Total")
    grouped_esfera["Total"] = grouped_esfera["Total"].astype(int)  # Converter para inteiro

    # Gráfico de Pizza com Plotly Express
    fig_pizza = px.pie(
        grouped_esfera,
        values="Total",
        names="Esfera",
        title=f"Adesões por Esfera - {selected_state}",
        hole=0.4,
        height=550,
        width=800
    )
    fig_pizza.update_traces(
        texttemplate='%{label}<br>%{value:.0f}',  # Valor como inteiro
        textfont=dict(size=14),
        textinfo='none',  # Remove percentuais padrão
        hovertemplate="<b>%{label}</b><br>Total: %{value}<br>Percentual: %{percent}<extra></extra>",
        pull=[0.1 if max(grouped_esfera["Total"]) == val else 0 for val in grouped_esfera["Total"]]  # Explodir fatia maior
    )
    fig_pizza.update_layout(title=dict(font=dict(size=20)))

    # Gráfico de Barras Horizontais
    fig_barra = px.bar(
        state_data.groupby("Poder").size().reset_index(name="Total"),
        x="Total",
        y="Poder",
        orientation="h",
        text="Total",
        title=f"Adesões por Poder - {selected_state}",
        labels={"Total": "Quantidade", "Poder": "Poder"},
        height=550,
        width=800
    )
    fig_barra.update_traces(textposition="outside", textfont=dict(size=14))
    fig_barra.update_layout(
        title=dict(font=dict(size=20)),
        xaxis=dict(title_font=dict(size=16), tickfont=dict(size=14)),
        yaxis=dict(title_font=dict(size=16), tickfont=dict(size=14))
    )

    return fig_pizza, fig_barra

# =============================================
# NOVA ESTRUTURA PARA ORDENAÇÃO DOS GRÁFICOS
# =============================================

# 1. Gráfico de Mapa em full width
# ---------------------------------
with st.container():
    # Reduzir o espaço acima do título do mapa
    st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)

    # Criar colunas para mapa e seleção de estado
    mapa_col, filtro_col = st.columns([4, 1])  # 75% mapa, 25% seleção

    with mapa_col:
        brazil_geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        state_data = data.groupby("UF").size().reset_index(name="Total")

        valid_ufs = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR",
                     "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
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
                labels={"Total": "Número de Adesões"},
                height=700,
                width=1200
            )

            fig_mapa.update_traces(
                hovertemplate="<b>%{location}</b><br>Adesões: %{z}<extra></extra>"
            )

            fig_mapa.update_layout(
                margin=dict(l=0, r=100, t=0, b=0),
                height=600,
                coloraxis_colorbar=dict(
                    thickness=10,
                    len=0.5,
                    title=None,
                    yanchor='middle',
                    y=0.5,
                    xanchor='left',
                    x=1.05
                )
            )

            st.plotly_chart(fig_mapa, use_container_width=True)

# 2. Gráfico de Linha com Tendência
# ---------------------------------
with st.container():
    # Gráfico de Linha - Adesões Vigentes ao Longo do Tempo
    st.subheader("Adesões Vigentes ao Longo do Tempo (Até Hoje)")

    # Filtrar dados válidos e ajustar "Final da Vigência" para hoje se for futuro
    filtered_data = data.dropna(subset=["Início da Vigência", "Final da Vigência"]).copy()

    # Aplicar filtro de estado, se um estado foi selecionado
    if st.session_state["map_click_data"]:
        filtered_data = filtered_data[filtered_data["UF"] == st.session_state["map_click_data"]]

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
        title=f"Adesões Vigentes até {hoje.strftime('%d/%m/%Y')} - Estado: {st.session_state['map_click_data'] if st.session_state['map_click_data'] else 'Todos'}",
        markers=True,
        labels={"Adesões Vigentes": "Adesões Vigentes"},
        height=550
    )

    # Adicionar linha de tendência
    fig_linha.add_scatter(
        x=vigentes_por_trimestre["Data"],
        y=vigentes_por_trimestre["Adesões Vigentes"].rolling(window=2).mean(),
        mode="lines",
        name="Tendência",
        line=dict(color="red", dash="dash")
    )

    st.plotly_chart(fig_linha, use_container_width=True)

# 3. Cards com Métricas Resumidas
# -------------------------------
with st.container():
    # Calcular grouped_esfera globalmente
    grouped_esfera_global = data[data['Vigente']].groupby("Esfera").size().reset_index(name="Total")
    grouped_esfera_global["Total"] = grouped_esfera_global["Total"].astype(int)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Adesões", data.shape[0])
    with col2:
        st.metric("Adesões Vigentes", data[data["Vigente"]].shape[0])
    with col3:
        st.metric("Adesões por Esfera", grouped_esfera_global["Total"].sum())  # Usando grouped_esfera_global

# 4. Gráfico de Barras para Comparação entre UFs
# ----------------------------------------------
with st.container():
    st.subheader("Comparação de Adesões por UF")
    fig_barras_uf = px.bar(
        state_data.sort_values(by="Total", ascending=False),
        x="UF",
        y="Total",
        title="Adesões por UF",
        labels={"Total": "Número de Adesões", "UF": "Unidade Federativa"},
        color="Total",
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_barras_uf, use_container_width=True)

# 5. Gráficos de Pizza
# --------------------
with st.container():
    st.subheader("Distribuição de Adesões por Esfera")
    if st.session_state["map_click_data"]:
        fig_pizza, _ = update_charts(st.session_state["map_click_data"])
    else:
        grouped_esfera_global = data[data['Vigente']].groupby("Esfera").size().reset_index(name="Total")
        grouped_esfera_global["Total"] = grouped_esfera_global["Total"].astype(int)

        fig_pizza = px.pie(
            grouped_esfera_global,
            values="Total",
            names="Esfera",
            title="Adesões por Esfera (Total)",
            hole=0.4,
            height=550,
            width=800
        )
        fig_pizza.update_traces(
            texttemplate='%{label}<br>%{value:.0f}',
            textfont=dict(size=14),
            textinfo='none',
            hovertemplate="<b>%{label}</b><br>Total: %{value}<br>Percentual: %{percent}<extra></extra>",
            pull=[0.1 if max(grouped_esfera_global["Total"]) == val else 0 for val in grouped_esfera_global["Total"]]
        )
        fig_pizza.update_layout(title=dict(font=dict(size=20)))

    st.plotly_chart(fig_pizza, use_container_width=True)

# 6. Exportação de Dados
# ----------------------
with st.container():
    if st.button("Exportar Dados Filtrados"):
        filtered_data.to_csv("dados_filtrados.csv", index=False)
        st.success("Dados exportados com sucesso!")