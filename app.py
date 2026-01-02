# ========== IMPORTS / CONFIG (início) ==========
import streamlit as st
import pandas as pd
from io import StringIO
from urllib.parse import quote
import requests
from datetime import datetime, timedelta
import json

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


# ========== CONFIGURAÇÕES DE API (início) ==========
# Configure suas chaves de API aqui ou use secrets do Streamlit
GOOGLE_PLACES_API_KEY = st.secrets.get("GOOGLE_PLACES_API_KEY", "")
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")  # Alternativa para buscas

# ========== CONFIGURAÇÕES DE API (fim) ==========


# ========== FUNÇÕES DE BUSCA REAL (início) ==========
def buscar_oportunidades_google_trends(palavras_chave, regiao="BR-ES"):
    """
    Busca tendências usando pytrends (Google Trends não-oficial)
    """
    try:
        from pytrends.request import TrendReq
        
        pytrends = TrendReq(hl='pt-BR', tz=360)
        
        resultados = []
        
        for palavra in palavras_chave:
            try:
                # Busca interesse ao longo do tempo (últimos 7 dias)
                pytrends.build_payload([palavra], timeframe='now 7-d', geo=regiao)
                interesse_tempo = pytrends.interest_over_time()
                
                # Busca interesse por região
                pytrends.build_payload([palavra], timeframe='today 3-m', geo=regiao)
                interesse_regiao = pytrends.interest_by_region(resolution='CITY', inc_low_vol=True)
                
                # Pega as top 3 cidades
                if not interesse_regiao.empty:
                    top_cidades = interesse_regiao.nlargest(3, palavra).index.tolist()
                    localidades = "; ".join(top_cidades)
                else:
                    localidades = "Dados insuficientes"
                
                # Calcula volume aproximado (baseado no interesse médio)
                if not interesse_tempo.empty:
                    interesse_medio = interesse_tempo[palavra].mean()
                    # Estima volume (interesse * fator de escala)
                    volume_estimado = int(interesse_medio * 50)  # Fator ajustável
                else:
                    volume_estimado = 0
                
                resultados.append({
                    "palavra_chave": palavra,
                    "periodo": "últimos 7 dias",
                    "buscas": volume_estimado,
                    "localidades_top": localidades,
                })
                
            except Exception as e:
                st.warning(f"Erro ao buscar '{palavra}': {str(e)}")
                continue
        
        return pd.DataFrame(resultados)
        
    except ImportError:
        st.error("❌ pytrends não está instalado. Execute: pip install pytrends")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao buscar tendências: {str(e)}")
        return pd.DataFrame()


def buscar_leads_google_places(query, location, radius_km=20000, api_key=""):
    """
    Busca empresas usando Google Places API
    """
    if not api_key:
        st.error("❌ Configure sua GOOGLE_PLACES_API_KEY nos secrets do Streamlit")
        return pd.DataFrame()
    
    try:
        # Endpoint da API do Google Places
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        params = {
            "query": query,
            "location": location,  # formato: "lat,lng"
            "radius": radius_km,
            "language": "pt-BR",
            "key": api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") != "OK":
            st.error(f"❌ Erro na API: {data.get('status')} - {data.get('error_message', '')}")
            return pd.DataFrame()
        
        leads = []
        
        for i, place in enumerate(data.get("results", []), 1):
            # Busca detalhes do lugar
            place_id = place.get("place_id")
            details = buscar_detalhes_lugar(place_id, api_key)
            
            lead = {
                "id": i,
                "empresa": place.get("name", ""),
                "nicho_geral": classificar_nicho_geral(place.get("types", [])),
                "nicho_especifico": ", ".join(place.get("types", [])[:2]),
                "estado": "ES",  # Ajustar conforme localização
                "cidade": extrair_cidade(place.get("formatted_address", "")),
                "localidade": place.get("formatted_address", ""),
                "site": details.get("website", ""),
                "tem_site": bool(details.get("website")),
                "status_site": "Online" if details.get("website") else "Sem site",
                "whatsapp": formatar_telefone_whatsapp(details.get("formatted_phone_number", "")),
                "telefone_bruto": details.get("formatted_phone_number", ""),
                "email": "",  # Google Places não fornece email diretamente
                "endereco": place.get("formatted_address", ""),
                "facebook": "",  # Precisaria de scraping adicional
                "instagram": "",  # Precisaria de scraping adicional
                "tem_redes": False,
                "logo_url": buscar_logo_url(place.get("photos", []), api_key) if place.get("photos") else None,
                "tem_logo": bool(place.get("photos")),
                "rating": place.get("rating", 0),
                "total_reviews": place.get("user_ratings_total", 0),
                "aberto_agora": details.get("opening_hours", {}).get("open_now", None),
            }
            
            leads.append(lead)
        
        return pd.DataFrame(leads)
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar leads: {str(e)}")
        return pd.DataFrame()


def buscar_detalhes_lugar(place_id, api_key):
    """Busca detalhes completos de um lugar específico"""
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website,formatted_phone_number,opening_hours",
            "key": api_key
        }
        response = requests.get(url, params=params)
        data = response.json()
        return data.get("result", {})
    except:
        return {}


def buscar_logo_url(photos, api_key):
    """Retorna URL da primeira foto (logo) do estabelecimento"""
    if not photos or not api_key:
        return None
    
    photo_reference = photos[0].get("photo_reference")
    if photo_reference:
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={api_key}"
    return None


def classificar_nicho_geral(types):
    """Classifica o tipo de negócio em nichos gerais"""
    saude = ["doctor", "dentist", "hospital", "pharmacy", "physiotherapist", "health", "gym", "spa"]
    alimentacao = ["restaurant", "food", "cafe", "bakery", "bar", "meal_delivery", "meal_takeaway"]
    servicos = ["lawyer", "accounting", "real_estate_agency", "insurance_agency", "travel_agency"]
    
    types_lower = [t.lower() for t in types]
    
    if any(t in types_lower for t in saude):
        return "Saúde"
    elif any(t in types_lower for t in alimentacao):
        return "Alimentação"
    elif any(t in types_lower for t in servicos):
        return "Serviços"
    else:
        return "Outros"


def extrair_cidade(endereco):
    """Extrai o nome da cidade do endereço formatado"""
    partes = endereco.split(",")
    if len(partes) >= 2:
        # Geralmente a cidade está antes do estado
        return partes[-2].strip().split("-")[0].strip()
    return ""


def formatar_telefone_whatsapp(telefone):
    """Extrai apenas dígitos do telefone para WhatsApp"""
    if not telefone:
        return ""
    return "".join([c for c in telefone if c.isdigit()])


def geocodificar_cidade(cidade, estado="ES"):
    """Converte cidade/estado em coordenadas lat,lng"""
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": f"{cidade}, {estado}, Brasil",
            "key": GOOGLE_PLACES_API_KEY
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return f"{location['lat']},{location['lng']}"
        else:
            # Coordenadas padrão de Vitória/ES
            return "-20.3155,-40.3128"
    except:
        return "-20.3155,-40.3128"
# ========== FUNÇÕES DE BUSCA REAL (fim) ==========


# ========== STATE MANAGEMENT (início) ==========
if "df_leads" not in st.session_state:
    st.session_state.df_leads = pd.DataFrame()

if "selecionados" not in st.session_state:
    st.session_state.selecionados = set()

if "df_oportunidades" not in st.session_state:
    st.session_state.df_oportunidades = pd.DataFrame()
# ========== STATE MANAGEMENT (fim) ==========


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
    st.caption("Busca REAL por localidades e nichos usando APIs.")

    st.markdown("---")
    st.markdown("#### Filtros de Localidade")
    estado = st.selectbox("Estado", ["ES", "RJ", "SP", "MG"], index=0)
    cidade = st.text_input("Cidade", value="Vitória")
    raio_km = st.slider("Raio (km)", min_value=5, max_value=100, value=20, step=5)

    st.markdown("---")
    st.markdown("#### Filtros de Nicho")
    nicho_geral = st.selectbox(
        "Nicho geral",
        ["Todos", "Saúde", "Alimentação", "Serviços"],
        index=0,
    )
    nicho_especifico = st.text_input("Termo de busca", value="clínica")

    st.markdown("---")
    st.markdown("#### Ações")
    buscar_oportunidades_btn = st.button("🔍 Buscar Oportunidades (Google Trends)", type="primary")
    buscar_leads_btn = st.button("🧲 Buscar Leads (Google Places)", type="primary")
    
    # Informações sobre configuração
    st.markdown("---")
    st.markdown("#### ⚙️ Configuração")
    if GOOGLE_PLACES_API_KEY:
        st.success("✅ Google Places API configurada")
    else:
        st.warning("⚠️ Configure GOOGLE_PLACES_API_KEY")
    
    with st.expander("Como configurar APIs"):
        st.markdown("""
        **Google Places API:**
        1. Acesse [Google Cloud Console](https://console.cloud.google.com)
        2. Crie um projeto e ative a API Places
        3. Gere uma chave de API
        4. No Streamlit, vá em Settings > Secrets
        5. Adicione: `GOOGLE_PLACES_API_KEY = "sua-chave"`
        
        **pytrends (Google Trends):**
        - Não requer chave de API
        - Instale: `pip install pytrends`
        """)


# Executar buscas quando botões forem clicados
if buscar_oportunidades_btn:
    with st.spinner("🔍 Buscando oportunidades no Google Trends..."):
        palavras_chave = [
            "criação de sites",
            "identidade visual",
            "social media",
            "logo design",
            "marketing digital"
        ]
        st.session_state.df_oportunidades = buscar_oportunidades_google_trends(
            palavras_chave,
            regiao=f"BR-{estado}"
        )
        if not st.session_state.df_oportunidades.empty:
            st.success(f"✅ {len(st.session_state.df_oportunidades)} oportunidades encontradas!")

if buscar_leads_btn:
    with st.spinner("🧲 Buscando leads no Google Places..."):
        # Geocodifica a cidade
        location = geocodificar_cidade(cidade, estado)
        
        # Monta query de busca
        query = nicho_especifico if nicho_especifico.strip() else "empresa"
        if nicho_geral != "Todos":
            query += f" {nicho_geral.lower()}"
        
        st.session_state.df_leads = buscar_leads_google_places(
            query=query,
            location=location,
            radius_km=raio_km * 1000,  # Converter para metros
            api_key=GOOGLE_PLACES_API_KEY
        )
        if not st.session_state.df_leads.empty:
            st.success(f"✅ {len(st.session_state.df_leads)} leads encontrados!")
            st.session_state.selecionados = set()  # Limpa seleção anterior


# Filtragem local (caso necessário)
df_leads = st.session_state.df_leads.copy()
if not df_leads.empty:
    if nicho_geral != "Todos":
        df_leads = df_leads[df_leads["nicho_geral"] == nicho_geral]
# ========== SIDEBAR / FILTROS (fim) ==========


# ========== HEADER PRINCIPAL (início) ==========
st.title("🧭 Agente de Prospecção - LP Design")
st.markdown(
    "Ferramenta completa para identificar **oportunidades de mercado** e **prospectar leads** "
    "com base em buscas reais (Google Trends + Google Places)."
)
st.markdown("---")

tab_oportunidades, tab_leads = st.tabs(["📊 Oportunidades", "🧲 Leads"])
# ========== HEADER PRINCIPAL (fim) ==========


# ========== ABA OPORTUNIDADES (início) ==========
with tab_oportunidades:
    st.subheader("Oportunidades (Google Trends - REAL)")

    st.caption(
        "Esta aba mostra tendências reais de busca das principais palavras-chave "
        "dos serviços da LP Design, obtidas diretamente do Google Trends."
    )

    if st.session_state.df_oportunidades.empty:
        st.info("👆 Clique em **'Buscar Oportunidades'** na barra lateral para carregar dados reais do Google Trends")
    else:
        df_opp = st.session_state.df_oportunidades

        col1, col2 = st.columns([3, 1])
        with col1:
            if "periodo" in df_opp.columns and not df_opp.empty:
                periodo_filtro = st.selectbox(
                    "Período",
                    sorted(df_opp["periodo"].unique()),
                    index=0,
                )
            else:
                periodo_filtro = "últimos 7 dias"
        with col2:
            st.write("")
            st.write("")
            gerar_relatorio_oportunidades = st.button("📄 Gerar relatório")

        df_opp_filtrado = df_opp[df_opp["periodo"] == periodo_filtro] if "periodo" in df_opp.columns else df_opp

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
            st.success("✅ Relatório gerado. Dados prontos para exportação.")
            st.dataframe(df_rel, use_container_width=True, hide_index=True)
            
            # Botão de download
            csv_rel = StringIO()
            df_rel.to_csv(csv_rel, index=False)
            st.download_button(
                label="⬇️ Baixar relatório CSV",
                data=csv_rel.getvalue().encode("utf-8"),
                file_name=f"oportunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
# ========== ABA OPORTUNIDADES (fim) ==========


# ========== ABA LEADS (início) ==========
with tab_leads:
    st.subheader("Leads Encontrados (Google Places - REAL)")

    st.caption(
        "Leads reais encontrados via Google Places API. Selecione os contatos e exporte para CSV."
    )

    if df_leads.empty:
        st.info("👆 Clique em **'Buscar Leads'** na barra lateral para carregar empresas reais do Google Places")
    else:
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
            st.write(f"**{len(df_leads)}** leads encontrados")
        with col_b:
            if csv_bytes:
                st.download_button(
                    label="⬇️ Baixar CSV dos selecionados",
                    data=csv_bytes,
                    file_name=f"leads_selecionados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.caption("Selecione leads para habilitar download")

        st.markdown("---")

        # ----- EXIBIÇÃO EM LISTA DETALHADA -----
        if modo == "Lista detalhada":
            st.markdown("### Lista detalhada")

            for _, row in df_leads.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([4, 3, 1])

                    with c1:
                        st.markdown(f"**{row['empresa']}**")
                        st.caption(f"{row['nicho_geral']} • {row['nicho_especifico']}")
                        st.caption(f"{row['endereco']}")

                        if row["site"]:
                            st.markdown(f"[🌐 Site]({row['site']})")
                        else:
                            st.markdown("_Sem site cadastrado_")

                        if row.get("rating", 0) > 0:
                            st.caption(f"⭐ {row['rating']} ({row.get('total_reviews', 0)} avaliações)")

                        if row["telefone_bruto"]:
                            st.caption(f"📞 {row['telefone_bruto']}")

                    with c2:
                        st.markdown("**Status digital**")
                        st.write(f"- Site: {row['status_site']}")
                        st.write(f"- Marca/logo: {'Possui' if row['tem_logo'] else 'Não identificada'}")
                        if row.get("aberto_agora") is not None:
                            status_aberto = "✅ Aberto" if row["aberto_agora"] else "🔴 Fechado"
                            st.write(f"- Status: {status_aberto}")

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
                            f"Olá! Encontrei a {row['empresa']} e "
                            f"gostaria de conversar sobre como a LP Design pode ajudar "
                            f"a melhorar a presença digital da empresa."
                        )
                        link_whats = montar_link_whatsapp(row["whatsapp"], msg)
                        if link_whats:
                            st.link_button("💬 WhatsApp", link_whats, type="primary")
                        else:
                            st.caption("Sem WhatsApp")

                    st.markdown("---")

        # ----- EXIBIÇÃO EM CARDS -----
        else:
            st.markdown("### Cards")

            for _, row in df_leads.iterrows():
                with st.container():
                    c1, c2 = st.columns([3, 2])

                    with c1:
                        st.markdown(f"**{row['empresa']}**")
                        st.caption(f"{row['nicho_geral']} • {row['nicho_especifico']}")
                        st.caption(f"{row['cidade']}/{row['estado']}")

                        if row["site"]:
                            st.markdown(f"[🌐 Site]({row['site']})")
                        else:
                            st.markdown("_Sem site_")

                        if row.get("rating", 0) > 0:
                            st.caption(f"⭐ {row['rating']} ({row.get('total_reviews', 0)} avaliações)")

                        if row["telefone_bruto"]:
                            st.caption(f"📞 {row['telefone_bruto']}")

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
                            f"Olá! Encontrei a {row['empresa']} e "
                            f"gostaria de conversar sobre melhorar a presença digital."
                        )
                        link_whats = montar_link_whatsapp(row["whatsapp"], msg)
                        if link_whats:
                            st.link_button("💬 WhatsApp", link_whats, type="primary")
                        else:
                            st.caption("Sem WhatsApp")

                    st.markdown("---")
# ========== ABA LEADS (fim) ==========
