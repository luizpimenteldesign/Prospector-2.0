# ========== IMPORTS / CONFIG (início) ==========
import streamlit as st
import pandas as pd
from io import StringIO
from urllib.parse import quote

st.set_page_config(
    page_title="Agente de Prospecção - LP Design",
    page_icon="🧭",
    layout="wide",
)

# Logo LP Design no topo
st.logo(
    "https://luizpimentel.com/wp-content/uploads/2022/09/PNG-72dpi-Identidade-Visual-LP-Design-05.png",
    size="large",
)
# ========== IMPORTS / CONFIG (fim) ==========


# ========== DADOS SIMULADOS (início) ==========
# ATENÇÃO: depois este bloco será substituído por chamadas reais (Google Trends / APIs de leads)

def gerar_dados_simulados_oportunidades():
    data = [
        {
            "palavra_chave": "criação de sites",
            "periodo": "últimos 7 dias",
            "buscas": 2100,
            "localidades_top": "Vitória/ES; Vila Velha/ES; Serra/ES",
        },
        {
            "palavra_chave": "identidade visual",
            "periodo": "últimos 7 dias",
            "buscas": 1350,
            "localidades_top": "Aracruz/ES; Vitória/ES; Cariacica/ES",
        },
        {
            "palavra_chave": "social media",
            "periodo": "últimos 7 dias",
            "buscas": 980,
            "localidades_top": "Vitória/ES; Linhares/ES; Colatina/ES",
        },
        {
            "palavra_chave": "logo design",
            "periodo": "últimos 7 dias",
            "buscas": 720,
            "localidades_top": "Vitória/ES; Serra/ES; Guarapari/ES",
        },
    ]
    return pd.DataFrame(data)


def gerar_dados_simulados_leads():
    data = [
        {
            "id": 1,
            "empresa": "Clínica Vitória Saúde",
            "nicho_geral": "Saúde",
            "nicho_especifico": "Clínica de estética",
            "estado": "ES",
            "cidade": "Vitória",
            "localidade": "Vitória - Centro",
            "site": "https://clinicavitoriasaude.com.br",
            "tem_site": True,
            "status_site": "Online",
            "whatsapp": "27999990001",
            "telefone_bruto": "(27) 99999-0001",
            "email": "contato@clinicavitoriasaude.com.br",
            "endereco": "Av. Beira Mar, 123 - Centro, Vitória - ES",
            "facebook": "https://facebook.com/clinicavitoriasaude",
            "instagram": "https://instagram.com/clinicavitoriasaude",
            "tem_redes": True,
            "logo_url": None,
            "tem_logo": True,
        },
        {
            "id": 2,
            "empresa": "Pizzaria Sabor da Serra",
            "nicho_geral": "Alimentação",
            "nicho_especifico": "Pizzaria",
            "estado": "ES",
            "cidade": "Serra",
            "localidade": "Serra - Laranjeiras",
            "site": "",
            "tem_site": False,
            "status_site": "Sem site",
            "whatsapp": "27988880002",
            "telefone_bruto": "(27) 98888-0002",
            "email": "",
            "endereco": "Rua das Palmeiras, 456 - Laranjeiras, Serra - ES",
            "facebook": "",
            "instagram": "https://instagram.com/pizzariasabordaserra",
            "tem_redes": True,
            "logo_url": None,
            "tem_logo": False,
        },
        {
            "id": 3,
            "empresa": "Escritório Contábil Aracruz",
            "nicho_geral": "Serviços",
            "nicho_especifico": "Contabilidade",
            "estado": "ES",
            "cidade": "Aracruz",
            "localidade": "Aracruz - Centro",
            "site": "http://escritorioaracruz.com.br",
            "tem_site": True,
            "status_site": "Site desatualizado",
            "whatsapp": "27997770003",
            "telefone_bruto": "(27) 99777-0003",
            "email": "contato@escritorioaracruz.com.br",
            "endereco": "Rua das Flores, 789 - Centro, Aracruz - ES",
            "facebook": "",
            "instagram": "",
            "tem_redes": False,
            "logo_url": None,
            "tem_logo": True,
        },
        {
            "id": 4,
            "empresa": "Academia Corpo em Dia",
            "nicho_geral": "Saúde",
            "nicho_especifico": "Academia",
            "estado": "ES",
            "cidade": "Vila Velha",
            "localidade": "Vila Velha - Praia da Costa",
            "site": "",
            "tem_site": False,
            "status_site": "Sem site",
            "whatsapp": "27996660004",
            "telefone_bruto": "(27) 99666-0004",
            "email": "contato@corpoemdia.com.br",
            "endereco": "Av. Praia da Costa, 1010 - Vila Velha - ES",
            "facebook": "https://facebook.com/academiacorpoemdia",
            "instagram": "",
            "tem_redes": True,
            "logo_url": None,
            "tem_logo": False,
        },
    ]
    return pd.DataFrame(data)


if "df_leads" not in st.session_state:
    st.session_state.df_leads = gerar_dados_simulados_leads()

if "selecionados" not in st.session_state:
    st.session_state.selecionados = set()
# ========== DADOS SIMULADOS (fim) ==========


# ========== FUNÇÕES AUXILIARES (início) ==========
def montar_link_whatsapp(numero_br, mensagem):
    """Gera link wa.me para WhatsApp Web (sempre usando 55 + DDD + número)."""
    if not numero_br:
        return None
    digits = "".join([c for c in numero_br if c.isdigit()])
    if digits.startswith("55"):
        num_final = digits
    else:
        num_final = "55" + digits
    texto = quote(mensagem)
    return f"https://wa.me/{num_final}?text={texto}"


def df_selecionados_para_csv(df, ids_selecionados):
    if not ids_selecionados:
        return None
    subset = df[df["id"].isin(ids_selecionados)].copy()
    csv_buffer = StringIO()
    subset.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode("utf-8")
# ========== FUNÇÕES AUXILIARES (fim) ==========


# ========== SIDEBAR / FILTROS (início) ==========
with st.sidebar:
    st.markdown("### Agente de Prospecção")
    st.caption("Busca por localidades e nichos com oportunidades reais.")

    st.markdown("---")
    st.markdown("#### Filtros de Localidade")
    estado = st.selectbox("Estado", ["Todos", "ES", "RJ", "SP"], index=1)
    cidade = st.text_input("Cidade", value="Vitória")
    raio_km = st.slider("Raio (km)", min_value=5, max_value=100, value=20, step=5)

    st.markdown("---")
    st.markdown("#### Filtros de Nicho")
    nicho_geral = st.selectbox(
        "Nicho geral",
        ["Todos", "Saúde", "Alimentação", "Serviços"],
        index=0,
    )
    nicho_especifico = st.text_input("Nicho específico / derivado", value="criação de sites")

    st.markdown("---")
    st.markdown("#### Ações")
    buscar_oportunidades_btn = st.button("🔍 Atualizar Oportunidades (simulado)")
    buscar_leads_btn = st.button("🧲 Buscar Leads (simulado)")

# Filtragem simples em cima dos mocks
df_leads = st.session_state.df_leads.copy()
if estado != "Todos":
    df_leads = df_leads[df_leads["estado"] == estado]
if cidade.strip():
    df_leads = df_leads[df_leads["cidade"].str.contains(cidade.strip(), case=False)]
if nicho_geral != "Todos":
    df_leads = df_leads[df_leads["nicho_geral"] == nicho_geral]
if nicho_especifico.strip():
    df_leads = df_leads[
        df_leads["nicho_especifico"].str.contains(nicho_especifico.strip(), case=False)
    ]
# ========== SIDEBAR / FILTROS (fim) ==========


# ========== HEADER PRINCIPAL (início) ==========
st.markdown("## Agente de Prospecção LP Design")
st.caption(
    "Painel para identificar oportunidades e leads por localidade e nicho. "
    "Versão com dados simulados."
)
# ========== HEADER PRINCIPAL (fim) ==========


# ========== TABS PRINCIPAIS (início) ==========
tab_oportunidades, tab_leads = st.tabs(["💡 Oportunidades", "📇 Leads"])
# ========== TABS PRINCIPAIS (fim) ==========


# ========== ABA OPORTUNIDADES (início) ==========
with tab_oportunidades:
    st.subheader("Oportunidades (Google Trends - Simulado)")

    st.caption(
        "Esta aba simula um levantamento de buscas para as principais palavras-chave "
        "dos serviços da LP Design, como se viessem do Google Trends."
    )

    df_opp = gerar_dados_simulados_oportunidades()

    col1, col2 = st.columns([3, 1])
    with col1:
        periodo_filtro = st.selectbox(
            "Período",
            sorted(df_opp["periodo"].unique()),
            index=0,
        )
    with col2:
        st.write("")  # espaçamento
        st.write("")  # espaçamento
        gerar_relatorio_oportunidades = st.button("📄 Gerar relatório (simulado)")

    df_opp_filtrado = df_opp[df_opp["periodo"] == periodo_filtro]

    st.markdown("#### Palavras-chave em destaque")
    st.dataframe(
        df_opp_filtrado[["palavra_chave", "buscas", "localidades_top"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("##### Seleção de palavras para relatório")
    palavras_selecionadas = st.multiselect(
        "Escolha palavras-chave para o relatório",
        options=df_opp_filtrado["palavra_chave"].tolist(),
    )

    if gerar_relatorio_oportunidades and palavras_selecionadas:
        df_rel = df_opp_filtrado[
            df_opp_filtrado["palavra_chave"].isin(palavras_selecionadas)
        ].copy()
        st.success("Relatório gerado (simulado). Você poderá exportar/usar esses dados em outra etapa.")
        st.dataframe(df_rel, use_container_width=True, hide_index=True)

    st.info(
        "Quando as integrações reais forem ativadas, esta aba passará a consultar o Google Trends "
        "usando as palavras-chave da LP Design e filtros de localidade."
    )
# ========== ABA OPORTUNIDADES (fim) ==========


# ========== ABA LEADS (início) ==========
with tab_leads:
    st.subheader("Leads encontrados (Simulado)")

    st.caption(
        "Aqui você visualiza os leads por lista detalhada ou cards, pode selecionar "
        "os contatos e exportar um CSV para uso em outras etapas."
    )

    # Modo de exibição
    modo = st.radio(
        "Modo de exibição",
        options=["Lista detalhada", "Cards"],
        horizontal=True,
    )

    # CSV selecionados
    csv_bytes = df_selecionados_para_csv(df_leads, st.session_state.selecionados)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.write(f"**{len(df_leads)}** leads encontrados (após filtros).")
    with col_b:
        if csv_bytes:
            st.download_button(
                label="⬇️ Baixar CSV dos selecionados",
                data=csv_bytes,
                file_name="leads_selecionados.csv",
                mime="text/csv",
            )
        else:
            st.caption("Selecione leads para habilitar o download CSV.")

    st.markdown("---")

    # ----- EXIBIÇÃO EM LISTA DETALHADA -----
    if modo == "Lista detalhada":
        st.markdown("### Lista detalhada")

        for _, row in df_leads.iterrows():
            # container de cada lead
            with st.container():
                c1, c2, c3 = st.columns([4, 3, 1])

                with c1:
                    st.markdown(f"**{row['empresa']}**")
                    st.caption(
                        f"{row['nicho_geral']} • {row['nicho_especifico']}"
                    )
                    st.caption(
                        f"{row['endereco']} • {row['cidade']}/{row['estado']}"
                    )

                    if row["site"]:
                        st.markdown(f"[Site]({row['site']})")
                    else:
                        st.markdown("_Sem site cadastrado_")

                    redes = []
                    if row["facebook"]:
                        redes.append(f"[Facebook]({row['facebook']})")
                    if row["instagram"]:
                        redes.append(f"[Instagram]({row['instagram']})")
                    if redes:
                        st.markdown(" | ".join(redes))

                    if row["email"]:
                        st.caption(f"Email: {row['email']}")
                    st.caption(f"Telefone: {row['telefone_bruto']}")

                with c2:
                    st.markdown("**Status digital**")
                    st.write(f"- Site: {row['status_site']}")
                    st.write(f"- Redes sociais: {'Presente' if row['tem_redes'] else 'Ausente'}")
                    st.write(f"- Marca / logo: {'Possui' if row['tem_logo'] else 'Não identificada'}")

                with c3:
                    # Checkbox de seleção
                    marcado = row["id"] in st.session_state.selecionados
                    novo_marcado = st.checkbox(
                        "Selecionar",
                        key=f"sel_lista_{row['id']}",
                        value=marcado,
                    )
                    if novo_marcado:
                        st.session_state.selecionados.add(row["id"])
                    else:
                        st.session_state.selecionados.discard(row["id"])

                    # Botão WhatsApp
                    msg = (
                        f"Olá, tudo bem? Encontrei a {row['empresa']} aqui na região e "
                        f"gostaria de conversar rapidamente sobre como melhorar a presença "
                        f"digital da empresa."
                    )
                    link_whats = montar_link_whatsapp(row["whatsapp"], msg)
                    if link_whats:
                        st.link_button("WhatsApp Web", link_whats, type="primary")
                    else:
                        st.caption("Sem WhatsApp válido")

                st.markdown("---")

    # ----- EXIBIÇÃO EM CARDS -----
    else:
        st.markdown("### Cards")

        for _, row in df_leads.iterrows():
            with st.container():
                c1, c2 = st.columns([3, 2])

                with c1:
                    st.markdown(f"**{row['empresa']}**")
                    st.caption(
                        f"{row['nicho_geral']} • {row['nicho_especifico']}"
                    )
                    st.caption(
                        f"{row['cidade']}/{row['estado']} • {row['localidade']}"
                    )

                    if row["site"]:
                        st.markdown(f"[Site]({row['site']})")
                    else:
                        st.markdown("_Sem site cadastrado_")

                    redes = []
                    if row["facebook"]:
                        redes.append(f"[Facebook]({row['facebook']})")
                    if row["instagram"]:
                        redes.append(f"[Instagram]({row['instagram']})")
                    if redes:
                        st.markdown(" | ".join(redes))

                    st.caption(f"Telefone: {row['telefone_bruto']}")

                with c2:
                    marcado = row["id"] in st.session_state.selecionados
                    novo_marcado = st.checkbox(
                        "Selecionar",
                        key=f"sel_card_{row['id']}",
                        value=marcado,
                    )
                    if novo_marcado:
                        st.session_state.selecionados.add(row["id"])
                    else:
                        st.session_state.selecionados.discard(row["id"])

                    msg = (
                        f"Olá, tudo bem? Encontrei a {row['empresa']} aqui na região e "
                        f"gostaria de conversar rapidamente sobre como melhorar a presença "
                        f"digital da empresa."
                    )
                    link_whats = montar_link_whatsapp(row["whatsapp"], msg)
                    if link_whats:
                        st.link_button("WhatsApp Web", link_whats, type="primary")
                    else:
                        st.caption("Sem WhatsApp válido")

                st.markdown("---")

    st.info(
        "Na próxima etapa, os dados simulados serão trocados por resultados reais "
        "de APIs (Google Maps/Places, etc.), mantendo este mesmo layout."
    )
# ========== ABA LEADS (fim) ==========
