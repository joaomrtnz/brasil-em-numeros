
import streamlit as st
import urllib.request
import urllib.error
import json
import zlib
import pandas as pd
import altair as alt


st.set_page_config(
    page_title="O Brasil em Números",
    page_icon="🇧🇷",
    layout="wide"
)

st.title("🇧🇷 O Brasil em Números")

st.markdown(
    """
    ### Conheça o Brasil através dos dados

    Explore informações populacionais dos estados brasileiros,
    consulte diferentes anos e acompanhe a evolução da população
    com dados da API do IBGE.
    """
)

st.divider()

def consultar_api(url):
    with urllib.request.urlopen(url, timeout=30) as resposta:
        dados = resposta.read()

    if dados.startswith(b"\x1f\x8b"):
        dados = zlib.decompress(
            dados, 16 + zlib.MAX_WBITS
        )

    return json.loads(dados.decode("utf-8"))

try:
    url_estados = (
        "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    )

    estados = consultar_api(url_estados)

except (
    urllib.error.URLError,
    TimeoutError,
    json.JSONDecodeError,
    zlib.error,
    ValueError
) as erro:
    st.error("Não foi possível consultar os estados no IBGE.")
    st.stop()

tabela_estados = []

for estado in estados:
    tabela_estados.append({
        "Sigla": estado["sigla"],
        "Estado": estado["nome"],
        "Região": estado["regiao"]["nome"]
    })

tabela_estados = pd.DataFrame(tabela_estados)

st.subheader("Estados do Brasil")
st.dataframe(
    tabela_estados,
    hide_index=True,
    use_container_width=True
)

nomes_estados = sorted(
    estado["nome"] for estado in estados
)

estado_selecionado = st.selectbox(
    "Escolha um estado:",
    nomes_estados
)

estado_encontrado = next(
    estado for estado in estados
    if estado["nome"] == estado_selecionado
)

st.write("**Sigla:**", estado_encontrado["sigla"])
st.write("**Região:**", estado_encontrado["regiao"]["nome"])

url_periodos = (
    "https://servicodados.ibge.gov.br/api/v3/"
    "agregados/6579/periodos"
)

try:
    periodos = consultar_api(url_periodos)

    anos = sorted(
        int(periodo["id"])
        for periodo in periodos
        if periodo["id"].isdigit()
        and 2019 <= int(periodo["id"]) <= 2026
    )

except (
    urllib.error.URLError,
    TimeoutError,
    json.JSONDecodeError,
    zlib.error,
    ValueError,
    KeyError,
    AttributeError
):
    anos = list(range(2019, 2027))

    st.warning(
        "Não foi possível consultar os períodos. "
        "Vamos tentar os anos de 2019 a 2026."
    )

dados_por_ano = {}
erros_anos = []

for ano in anos:
    url_populacao = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/"
        f"6579/periodos/{ano}/variaveis/9324"
        "?localidades=N3%5Ball%5D"
    )

    try:
        dados_ano = consultar_api(url_populacao)

        if dados_ano and dados_ano[0].get("resultados"):
            dados_por_ano[ano] = dados_ano
        else:
            erros_anos.append(ano)

    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        zlib.error,
        ValueError
    ):
        erros_anos.append(ano)

populacoes = []

for ano, resposta_ano in dados_por_ano.items():
    for resultado in resposta_ano[0]["resultados"]:
        for serie in resultado["series"]:
            if serie["localidade"]["nome"] == estado_selecionado:
                valor = serie["serie"].get(str(ano))

                if valor not in (None, ""):
                    populacoes.append({
                        "Ano": ano,
                        "População": int(valor)
                    })

st.divider()
st.subheader(f"População de {estado_selecionado}")

if populacoes:
    tabela_populacao = pd.DataFrame(populacoes)
    tabela_populacao = tabela_populacao.sort_values("Ano")

    ultimo_registro = tabela_populacao.iloc[-1]
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "👥 População",
            f"{int(ultimo_registro['População']):,}".replace(",", ".")
        )

    with col2:
        st.metric(
            "📅 Ano de referência",
            int(ultimo_registro["Ano"])
        )

    with col3:
        st.metric(
            "📍 Região",
            estado_encontrado["regiao"]["nome"]
        )


    tabela_exibicao = tabela_populacao.copy()
    tabela_exibicao["População"] = tabela_exibicao[
        "População"
    ].map(lambda valor: f"{valor:,}".replace(",", "."))

    st.dataframe(
        tabela_exibicao,
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Evolução da população")

    grafico = alt.Chart(tabela_populacao).mark_line(
        point=True
    ).encode(
        x=alt.X(
            "Ano:O",
            title="Ano",
            sort="ascending",
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y(
            "População:Q",
            title="População",
            axis=alt.Axis(format=",.0f")
        ),
        tooltip=[
            alt.Tooltip("Ano:O", title="Ano"),
            alt.Tooltip(
                "População:Q",
                title="População",
                format=",.0f"
            )
        ]
    ).properties(
        height=350
    )

    
    tab_grafico, tab_tabela = st.tabs([
        "📈 Evolução da população",
        "📋 Dados por ano"
    ])

    with tab_grafico:
        grafico = alt.Chart(tabela_populacao).mark_line(
            point=True
        ).encode(
            x=alt.X(
                "Ano:O",
                title="Ano",
                sort="ascending",
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "População:Q",
                title="População",
                axis=alt.Axis(format=",.0f")
            ),
            tooltip=[
                alt.Tooltip("Ano:O", title="Ano"),
                alt.Tooltip(
                    "População:Q",
                    title="População",
                    format=",.0f"
                )
            ]
        ).properties(
            height=350
        )

        st.altair_chart(
            grafico,
            use_container_width=True
        )

    with tab_tabela:
        tabela_exibicao = tabela_populacao.copy()

        tabela_exibicao["População"] = tabela_exibicao[
            "População"
        ].map(lambda valor: f"{valor:,}".replace(",", "."))

        st.dataframe(
            tabela_exibicao,
            hide_index=True,
            use_container_width=True
        )


else:
    st.warning(
        "Não foram encontrados dados populacionais "
        "para esse estado nos períodos consultados."
    )

if erros_anos:
    st.info(
        "Não foi possível obter dados para estes anos: "
        + ", ".join(map(str, erros_anos))
        + ". Eles foram ignorados nos resultados."
    )