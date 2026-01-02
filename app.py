# ========== IMPORTS / CONFIG (início) ==========
import streamlit as st
import pandas as pd
from io import StringIO
from urllib.parse import quote
import requests
from datetime import datetime
import time
from ibge_localidades import buscar_estados, buscar_cidades_por_estado
from nichos_comerciais import obter_todos_nichos, obter_tags_osm_nicho, obter_categorias_nicho

# Configuração da página
st.set_page_config(
    page_title="Agente de Prospecção - LP Design",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado - Dark Theme
st.markdown("""
<style>
    /* Dark Theme Global */
    .stApp {
        background-color: #1a1a1a;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #2d2d2d;
    }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(90deg, #ff6b35, #ff8c42);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #ff8c42, #ff6b35);
        box-shadow: 0 4px 8px rgba(255, 107, 53, 0.3);
    }
    
    /* Containers */
    .stContainer {
        background-color: #2d2d2d;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #404040;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #2d2d2d;
        border-radius: 8px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #ff6b35;
    }
</style>
""", unsafe_allow_html=True)

# Logo no topo
st.logo(
    "https://luizpimentel.com/wp-content/uploads/2022/09/PNG-72dpi-Identidade-Visual-LP-Design-05.png",
    size="large",
)
# ========== IMPORTS / CONFIG (fim) ==========


# ========== FUNÇÕES DE BUSCA (início) ==========
def buscar_logo_site(url):
    """Tenta buscar o favicon/logo do site"""
    if not url:
        return None
    try:
        # Adiciona https:// se não tiver
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Tenta buscar favicon
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        
        # Opções de favicon
        favicon_urls = [
            f"https://www.google.com/s2/favicons?domain={domain}&sz=128",
            f"{url}/favicon.ico",
            f"https://{domain}/favicon.ico"
        ]
        
        return favicon_urls[0]  # Google sempre funciona
    except:
        return None


def analisar_site(url):
    """Analisa qualidade básica do site"""
    if not url:
        return {
            "tem_https": False,
            "responde": False,
            "tempo_resposta": 0,
            "status_code": 0,
            "tem_mobile": False,
            "score_seo": 0
        }
    
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        
        import time
        start = time.time()
        response = requests.get(url, timeout=5, allow_redirects=True)
        tempo = time.time() - start
        
        analise = {
            "tem_https": url.startswith('https'),
            "responde": response.status_code == 200,
            "tempo_resposta": round(tempo, 2),
            "status_code": response.status_code,
            "tem_mobile": 'viewport' in response.text.lower(),
            "score_seo": 0
        }
        
        # Score básico de SEO
        score = 0
        if analise["tem_https"]: score += 20
        if analise["responde"]: score += 30
        if analise["tempo_resposta"] < 3: score += 20
        if analise["tem_mobile"]: score += 30
        analise["score_seo"] = score
        
        return analise
    except:
        return {
            "tem_https": False,
            "responde": False,
            "tempo_resposta": 0,
            "status_code": 0,
            "tem_mobile": False,
            "score_seo": 0
        }


def buscar_redes_sociais(nome_empresa, cidade):
    """Busca redes sociais via Google Search (simplificado)"""
    # Por enquanto retorna apenas as que vêm do OSM
    # Poderia ser expandido com scraping do Google
    return {
        "facebook": "",
        "instagram": "",
        "linkedin": "",
        "twitter": ""
    }


def buscar_oportunidades_google_trends(palavras_chave, regiao="BR"):
    """Busca tendências usando pytrends"""
    try:
        from pytrends.request import TrendReq
        
        pytrends = TrendReq(hl='pt-BR', tz=360)
        resultados = []
        
        for palavra in palavras_chave:
            try:
                pytrends.build_payload([palavra], timeframe='now 7-d', geo=regiao)
                interesse_tempo = pytrends.interest_over_time()
                
                pytrends.build_payload([palavra], timeframe='today 3-m', geo=regiao)
                interesse_regiao = pytrends.interest_by_region(resolution='CITY', inc_low_vol=True)
                
                if not interesse_regiao.empty:
                    top_cidades = interesse_regiao.nlargest(3, palavra).index.tolist()
                    localidades = "; ".join(top_cidades)
                else:
                    localidades = "Dados insuficientes"
                
                if not interesse_tempo.empty:
                    interesse_medio = interesse_tempo[palavra].mean()
                    volume_estimado = int(interesse_medio * 50)
                else:
                    volume_estimado = 0
                
                resultados.append({
                    "palavra_chave": palavra,
                    "periodo": "últimos 7 dias",
                    "buscas": volume_estimado,
                    "localidades_top": localidades,
                })
                
            except Exception as e:
                continue
        
        return pd.DataFrame(resultados)
        
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        return pd.DataFrame()


def geocodificar_cidade_gratis(cidade, estado):
    """Geocodifica usando Nominatim (OpenStreetMap)"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{cidade}, {estado}, Brasil",
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "LP-Design-Prospector/2.0"}
        
        time.sleep(1)
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return -15.7939, -47.8828  # Brasília como padrão
    except:
        return -15.7939, -47.8828


def calcular_rate_lead(lead_data):
    """Calcula o score/rate do lead baseado nos dados disponíveis"""
    score = 0
    
    # Tem site: +30 pontos
    if lead_data.get("site"):
        score += 30
    
    # Tem telefone: +25 pontos
    if lead_data.get("telefone_bruto"):
        score += 25
    
    # Tem redes sociais: +20 pontos
    if lead_data.get("facebook") or lead_data.get("instagram"):
        score += 20
    
    # Tem email: +15 pontos
    if lead_data.get("email"):
        score += 15
    
    # Tem horário: +10 pontos
    if lead_data.get("horario"):
        score += 10
    
    # Classificação
    if score >= 70:
        return "Alta", "lead-rate-high"
    elif score >= 40:
        return "Média", "lead-rate-medium"
    else:
        return "Baixa", "lead-rate-low"


def buscar_leads_overpass_api(cidade, estado, raio_km, nicho, tags_custom=None):
    """Busca estabelecimentos usando Overpass API"""
    try:
        lat, lon = geocodificar_cidade_gratis(cidade, estado)
        
        if tags_custom:
            tags = tags_custom
        else:
            tags = obter_tags_osm_nicho(nicho)
        
        if not tags:
            tags = ["shop"]
        
        query = f"[out:json][timeout:25];("
        for tag in tags:
            key, value = tag.split("=")
            query += f'node["{key}"="{value}"](around:{raio_km * 1000},{lat},{lon});'
            query += f'way["{key}"="{value}"](around:{raio_km * 1000},{lat},{lon});'
        query += ");out center;"
        
        url = "https://overpass-api.de/api/interpreter"
        
        with st.spinner(f"🔍 Buscando em {cidade}/{estado}..."):
            time.sleep(2)
            response = requests.post(url, data={"data": query}, timeout=35)
            data = response.json()
        
        leads = []
        for i, element in enumerate(data.get("elements", [])[:30], 1):
            tags = element.get("tags", {})
            
            if "center" in element:
                elem_lat, elem_lon = element["center"]["lat"], element["center"]["lon"]
            else:
                elem_lat = element.get("lat", lat)
                elem_lon = element.get("lon", lon)
            
            nome = tags.get("name", f"Estabelecimento {i}")
            telefone = tags.get("phone", tags.get("contact:phone", ""))
            whatsapp = "".join([c for c in telefone if c.isdigit()])
            website = tags.get("website", tags.get("contact:website", ""))
            
            rua = tags.get("addr:street", "")
            numero = tags.get("addr:housenumber", "")
            endereco = f"{rua}, {numero}" if rua and numero else f"{cidade}/{estado}"
            
            facebook = tags.get("contact:facebook", "")
            instagram = tags.get("contact:instagram", "")
            email = tags.get("email", tags.get("contact:email", ""))
            horario = tags.get("opening_hours", "")
            
            lead_data = {
                "id": i,
                "empresa": nome,
                "nicho_geral": nicho,
                "nicho_especifico": tags.get("amenity", tags.get("shop", tags.get("office", "outros"))),
                "estado": estado,
                "cidade": cidade,
                "localidade": endereco,
                "site": website,
                "tem_site": bool(website),
                "status_site": "Online" if website else "Sem site",
                "whatsapp": whatsapp,
                "telefone_bruto": telefone,
                "email": email,
                "endereco": endereco,
                "facebook": facebook,
                "instagram": instagram,
                "tem_redes": bool(facebook or instagram),
                "horario": horario,
                "lat": elem_lat,
                "lon": elem_lon,
            }
            
            # Calcula rate
            rate, rate_class = calcular_rate_lead(lead_data)
            lead_data["rate"] = rate
            lead_data["rate_class"] = rate_class
            
            leads.append(lead_data)
        
        return pd.DataFrame(leads)
        
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        return pd.DataFrame()
# ========== FUNÇÕES DE BUSCA (fim) ==========


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
    if not numero_br:
        return None
    digits = "".join([c for c in numero_br if c.isdigit()])
    num_final = "55" + digits if not digits.startswith("55") else digits
    return f"https://wa.me/{num_final}?text={quote(mensagem)}"


def df_para_csv(df, ids_selecionados):
    if not ids_selecionados:
        return None
    subset = df[df["id"].isin(ids_selecionados)].copy()
    buffer = StringIO()
    subset.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
# ========== FUNÇÕES AUXILIARES (fim) ==========


# ========== SIDEBAR (início) ==========
with st.sidebar:
    st.markdown("### 🧭 Agente de Prospecção")
    st.caption("Busca por nichos e localidades com oportunidades reais")
    
    st.markdown("---")
    
    # Oportunidades Reais
    st.markdown("**📊 Oportunidades Reais**")
    st.caption("Resultados do Google Trends")
    
    st.markdown("---")
    
    # Filtros de Localização
    st.markdown("#### 📍 Localização")
    
    # Buscar estados do IBGE
    estados_ibge = buscar_estados()
    estados_opcoes = ["Todos"] + [f"{e['sigla']} - {e['nome']}" for e in estados_ibge]
    
    estado_selecionado = st.selectbox(
        "Estado",
        estados_opcoes,
        index=0
    )
    
    # Extrair sigla do estado
    if estado_selecionado != "Todos":
        uf = estado_selecionado.split(" - ")[0]
        cidades_disponiveis = buscar_cidades_por_estado(uf)
        cidades_opcoes = ["Todas"] + cidades_disponiveis
    else:
        uf = "Todos"
        cidades_opcoes = ["Todas"]
    
    cidade_selecionada = st.selectbox(
        "Cidade",
        cidades_opcoes,
        index=0
    )
    
    raio_km = st.slider("Raio de busca (km)", 5, 100, 20, 5)
    
    st.markdown("---")
    
    # Filtros de Nicho
    st.markdown("#### 🎯 Nichos")
    
    nichos_disponiveis = obter_todos_nichos()
    nicho_selecionado = st.selectbox(
        "Nicho principal",
        nichos_disponiveis,
        index=0
    )
    
    # Categorias específicas do nicho
    categorias = obter_categorias_nicho(nicho_selecionado)
    categoria_selecionada = st.selectbox(
        "Categoria específica",
        ["Todas"] + categorias,
        index=0
    )
    
    st.markdown("---")
    
    # Botões de ação
    st.markdown("#### ⚡ Ações")
    
    buscar_opp = st.button(
        "🔍 Buscar Oportunidades",
        type="primary",
        use_container_width=True
    )
    
    buscar_leads = st.button(
        "🧲 Buscar Leads",
        type="primary",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Status
    st.success("✅ 100% Gratuito")
    st.caption("🌍 OpenStreetMap + IBGE")
    st.caption("📊 Google Trends")
    st.caption(f"🗺️ {len(estados_ibge)} estados disponíveis")


# Executar buscas
if buscar_opp:
    regiao = "BR" if uf == "Todos" else f"BR-{uf}"
    palavras = ["criação de sites", "identidade visual", "social media", "logo design", "marketing digital"]
    st.session_state.df_oportunidades = buscar_oportunidades_google_trends(palavras, regiao)
    if not st.session_state.df_oportunidades.empty:
        st.success(f"✅ {len(st.session_state.df_oportunidades)} oportunidades encontradas!")

if buscar_leads:
    if cidade_selecionada == "Todas":
        st.warning("⚠️ Selecione uma cidade específica para buscar leads")
    else:
        # Determinar qual tag buscar
        if categoria_selecionada != "Todas":
            # Buscar apenas a categoria específica
            tags_busca = [tag for tag in obter_tags_osm_nicho(nicho_selecionado) 
                         if categoria_selecionada.lower() in tag.lower()]
            if not tags_busca:
                tags_busca = obter_tags_osm_nicho(nicho_selecionado)
        else:
            tags_busca = obter_tags_osm_nicho(nicho_selecionado)
        
        st.session_state.df_leads = buscar_leads_overpass_api(
            cidade_selecionada,
            uf,
            raio_km,
            nicho_selecionado,
            tags_busca
        )
        if not st.session_state.df_leads.empty:
            st.success(f"✅ {len(st.session_state.df_leads)} leads encontrados!")
            st.session_state.selecionados = set()

df_leads = st.session_state.df_leads.copy()
# ========== SIDEBAR (fim) ==========


# ========== HEADER (início) ==========
st.title("🧭 Agente de Prospecção LP Design")
st.caption("Ferramenta completa e gratuita para prospecção de clientes")

# Stats
if not df_leads.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Leads Encontrados", len(df_leads))
    
    with col2:
        st.metric("Selecionados", len(st.session_state.selecionados))
    
    with col3:
        com_site = len(df_leads[df_leads["tem_site"] == True])
        st.metric("Com Site", com_site)
    
    with col4:
        com_redes = len(df_leads[df_leads["tem_redes"] == True])
        st.metric("Com Redes Sociais", com_redes)

st.markdown("---")

tab_opp, tab_leads = st.tabs(["📊 Oportunidades", "🧲 Leads"])
# ========== HEADER (fim) ==========


# ========== ABA OPORTUNIDADES (início) ==========
with tab_opp:
    st.markdown("## 📊 Oportunidades de Mercado")

    if st.session_state.df_oportunidades.empty:
        st.info("👆 Clique em **'Buscar Oportunidades'** na barra lateral")
    else:
        df_opp = st.session_state.df_oportunidades
        
        for _, row in df_opp.iterrows():
            with st.container():
                st.markdown(f"### 🔍 {row['palavra_chave']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Volume Estimado", f"{row['buscas']:,}")
                with col2:
                    st.metric("Período", row['periodo'])
                with col3:
                    st.caption("**Top Cidades:**")
                    st.caption(row['localidades_top'])
                
                st.markdown("---")
        
        # Download
        if not df_opp.empty:
            buffer = StringIO()
            df_opp.to_csv(buffer, index=False)
            st.download_button(
                "⬇️ Baixar Relatório CSV",
                buffer.getvalue().encode("utf-8"),
                f"oportunidades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                type="primary"
            )
# ========== ABA OPORTUNIDADES (fim) ==========


# ========== ABA LEADS (início) ==========
with tab_leads:
    st.markdown("## 🧲 Leads Prospectados")

    if df_leads.empty:
        st.info("👆 Clique em **'Buscar Leads'** na barra lateral para carregar estabelecimentos")
    else:
        # Modo de exibição
        col1, col2 = st.columns([3, 1])
        with col1:
            modo = st.radio(
                "Visualização",
                options=["Cards", "Lista Detalhada"],
                horizontal=True,
            )
        with col2:
            csv_bytes = df_para_csv(df_leads, st.session_state.selecionados)
            if csv_bytes:
                st.download_button(
                    "⬇️ CSV Selecionados",
                    csv_bytes,
                    f"leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    "text/csv",
                )

        st.markdown("---")

        # EXIBIÇÃO EM CARDS
        if modo == "Cards":
            for _, row in df_leads.iterrows():
                with st.container():
                    # Buscar logo se tiver site
                    logo_url = buscar_logo_site(row.get("site", ""))
                    
                    col1, col2 = st.columns([1, 4])
                    
                    # Logo
                    with col1:
                        if logo_url:
                            st.image(logo_url, width=80)
                        else:
                            st.markdown("### 🏢")
                    
                    # Informações principais
                    with col2:
                        st.markdown(f"### {row['empresa']}")
                        st.caption(f"{row['nicho_geral']} • {row['nicho_especifico']}")
                        
                        # Rate
                        rate_color = {"lead-rate-high": "🟢", "lead-rate-medium": "🟡", "lead-rate-low": "🔴"}
                        st.markdown(f"{rate_color.get(row['rate_class'], '⚪')} **Rate: {row['rate']}**")
                    
                    st.markdown("---")
                    
                    # Detalhes
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📍 Localização**")
                        st.caption(row['endereco'])
                        
                        if row.get("telefone_bruto"):
                            st.markdown(f"**📞 Telefone**")
                            st.caption(row["telefone_bruto"])
                        
                        if row.get("email"):
                            st.markdown(f"**📧 Email**")
                            st.caption(row["email"])
                    
                    with col2:
                        st.markdown("**🌐 Presença Digital**")
                        
                        if row.get("site"):
                            st.markdown(f"[🔗 Site]({row['site']})")
                            
                            # Análise de site
                            with st.expander("📊 Análise do Site"):
                                analise = analisar_site(row['site'])
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("HTTPS", "✅" if analise["tem_https"] else "❌")
                                    st.metric("Mobile", "✅" if analise["tem_mobile"] else "❌")
                                with col_b:
                                    st.metric("Tempo", f"{analise['tempo_resposta']}s")
                                    st.metric("SEO Score", f"{analise['score_seo']}/100")
                        else:
                            st.caption("Sem site")
                        
                        # Redes sociais
                        if row.get("facebook") or row.get("instagram"):
                            st.markdown("**📱 Redes Sociais**")
                            if row.get("facebook"):
                                st.markdown(f"[📘 Facebook]({row['facebook']})")
                            if row.get("instagram"):
                                st.markdown(f"[📷 Instagram]({row['instagram']})")
                    
                    # Ações
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        marcado = row["id"] in st.session_state.selecionados
                        novo = st.checkbox(
                            "✓ Selecionar Lead",
                            key=f"sel_card_{row['id']}",
                            value=marcado
                        )
                        if novo:
                            st.session_state.selecionados.add(row["id"])
                        else:
                            st.session_state.selecionados.discard(row["id"])
                    
                    with col2:
                        msg = f"Olá! Sou da LP Design. Gostaria de conversar sobre melhorar a presença digital de {row['empresa']}."
                        link = montar_link_whatsapp(row["whatsapp"], msg)
                        if link:
                            st.link_button("💬 WhatsApp", link, type="primary", use_container_width=True)
                    
                    with col3:
                        # Botão de relatório
                        if st.button("📄", key=f"rel_{row['id']}", help="Ver Relatório Completo"):
                            st.session_state[f"show_report_{row['id']}"] = True
                    
                    # Relatório detalhado (se solicitado)
                    if st.session_state.get(f"show_report_{row['id']}", False):
                        with st.expander("📋 Relatório Completo de Comunicação", expanded=True):
                            st.markdown("### Análise de Presença Digital")
                            
                            # Site
                            st.markdown("#### 🌐 Website")
                            if row.get("site"):
                                analise = analisar_site(row['site'])
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Status", "Online" if analise["responde"] else "Offline")
                                    st.metric("HTTPS", "Sim" if analise["tem_https"] else "Não")
                                with col2:
                                    st.metric("Tempo Resposta", f"{analise['tempo_resposta']}s")
                                    st.metric("Mobile-Friendly", "Sim" if analise["tem_mobile"] else "Não")
                                with col3:
                                    st.metric("Score SEO", f"{analise['score_seo']}/100")
                                
                                # Recomendações
                                st.markdown("**Recomendações:**")
                                if not analise["tem_https"]:
                                    st.warning("⚠️ Site não usa HTTPS - recomendável para segurança")
                                if analise["tempo_resposta"] > 3:
                                    st.warning("⚠️ Site lento - otimizar performance")
                                if not analise["tem_mobile"]:
                                    st.warning("⚠️ Site não responsivo - implementar design mobile")
                                if analise["score_seo"] < 50:
                                    st.error("❌ SEO precisa de melhorias significativas")
                                elif analise["score_seo"] < 80:
                                    st.info("ℹ️ SEO pode ser otimizado")
                                else:
                                    st.success("✅ SEO em bom estado")
                            else:
                                st.warning("Empresa não possui website - **Oportunidade de venda!**")
                            
                            # Redes Sociais
                            st.markdown("#### 📱 Redes Sociais")
                            redes_encontradas = []
                            
                            if row.get("facebook"):
                                redes_encontradas.append(f"[Facebook]({row['facebook']})")
                            if row.get("instagram"):
                                redes_encontradas.append(f"[Instagram]({row['instagram']})")
                            if row.get("linkedin"):
                                redes_encontradas.append(f"[LinkedIn]({row['linkedin']})")
                            
                            if redes_encontradas:
                                st.markdown(" • ".join(redes_encontradas))
                            else:
                                st.warning("Sem redes sociais cadastradas - **Oportunidade de venda!**")
                            
                            # Contato
                            st.markdown("#### 📞 Informações de Contato")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Telefone:** {row.get('telefone_bruto', 'Não informado')}")
                                st.markdown(f"**Email:** {row.get('email', 'Não informado')}")
                            with col2:
                                st.markdown(f"**Endereço:** {row['endereco']}")
                                st.markdown(f"**Horário:** {row.get('horario', 'Não informado')}")
                            
                            # Score final e oportunidades
                            st.markdown("#### 💼 Oportunidades de Venda")
                            oportunidades = []
                            
                            if not row.get("site"):
                                oportunidades.append("🌐 Criação de website profissional")
                            elif row.get("site"):
                                analise = analisar_site(row['site'])
                                if analise["score_seo"] < 70:
                                    oportunidades.append("📈 Otimização de SEO")
                                if analise["tempo_resposta"] > 3:
                                    oportunidades.append("⚡ Melhoria de performance")
                                if not analise["tem_mobile"]:
                                    oportunidades.append("📱 Design responsivo/mobile")
                            
                            if not row.get("facebook") and not row.get("instagram"):
                                oportunidades.append("📱 Gestão de redes sociais")
                            
                            if not row.get("email") or not "@" in row.get("email", ""):
                                oportunidades.append("📧 Email marketing profissional")
                            
                            oportunidades.append("🎨 Identidade visual / Logo")
                            oportunidades.append("📊 Marketing digital")
                            
                            for oport in oportunidades:
                                st.markdown(f"• {oport}")
                    
                    st.markdown("---")

        # EXIBIÇÃO EM LISTA
        else:
            for _, row in df_leads.iterrows():
                col1, col2, col3 = st.columns([5, 3, 2])
                
                with col1:
                    st.markdown(f"**{row['empresa']}**")
                    st.caption(f"{row['nicho_geral']} • {row['nicho_especifico']}")
                    st.caption(f"📍 {row['endereco']}")
                    if row.get("site"):
                        st.markdown(f"[🌐 Site]({row['site']})")
                
                with col2:
                    st.markdown(f"**Rate:** {row['rate']}")
                    st.caption(f"📞 {row['telefone_bruto']}" if row.get("telefone_bruto") else "Sem telefone")
                    st.caption(f"🕐 {row['horario']}" if row.get("horario") else "Horário não informado")
                
                with col3:
                    marcado = row["id"] in st.session_state.selecionados
                    novo = st.checkbox("Selecionar", key=f"sel_lista_{row['id']}", value=marcado)
                    if novo:
                        st.session_state.selecionados.add(row["id"])
                    else:
                        st.session_state.selecionados.discard(row["id"])
                    
                    msg = f"Olá! Sou da LP Design e gostaria de conversar sobre {row['empresa']}."
                    link = montar_link_whatsapp(row["whatsapp"], msg)
                    if link:
                        st.link_button("💬", link, type="primary", use_container_width=True)
                
                st.markdown("---")
# ========== ABA LEADS (fim) ==========
