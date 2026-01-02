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
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Cards de Leads */
    .lead-card {
        background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%);
        border: 1px solid #404040;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .lead-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.4);
        border-color: #ff6b35;
    }
    
    .lead-name {
        color: #ffffff;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    .lead-category {
        color: #ff6b35;
        font-size: 14px;
        margin-bottom: 5px;
    }
    
    .lead-info {
        color: #b0b0b0;
        font-size: 13px;
        margin: 5px 0;
    }
    
    .lead-rate {
        background: linear-gradient(90deg, #ff6b35, #ff8c42);
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
        margin: 5px 0;
    }
    
    .lead-rate-high {
        background: linear-gradient(90deg, #00c853, #00e676);
    }
    
    .lead-rate-medium {
        background: linear-gradient(90deg, #ffa726, #ffb74d);
    }
    
    .lead-rate-low {
        background: linear-gradient(90deg, #ef5350, #e57373);
    }
    
    /* Redes sociais */
    .social-icons {
        display: flex;
        gap: 10px;
        margin: 10px 0;
    }
    
    .social-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #404040;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.3s;
    }
    
    .social-icon:hover {
        background: #ff6b35;
    }
    
    /* Títulos */
    .section-title {
        color: #ff6b35;
        font-size: 24px;
        font-weight: 700;
        margin: 20px 0 15px 0;
        border-left: 4px solid #ff6b35;
        padding-left: 15px;
    }
    
    /* Botões personalizados */
    .stButton > button {
        background: linear-gradient(90deg, #ff6b35, #ff8c42);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #ff8c42, #ff6b35);
        box-shadow: 0 4px 8px rgba(255, 107, 53, 0.3);
    }
    
    /* Selectbox e inputs */
    .stSelectbox, .stTextInput {
        background-color: #2d2d2d;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #2d2d2d;
        padding: 10px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #b0b0b0;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        color: #ff6b35;
        border-bottom-color: #ff6b35;
    }
    
    /* Logo */
    .logo-container {
        padding: 20px 0;
        text-align: center;
    }
    
    /* Stats cards */
    .stat-card {
        background: #2d2d2d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        border: 1px solid #404040;
    }
    
    .stat-number {
        font-size: 32px;
        font-weight: 700;
        color: #ff6b35;
    }
    
    .stat-label {
        font-size: 14px;
        color: #b0b0b0;
        margin-top: 5px;
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


def buscar_leads_overpass_api(cidade, estado, raio_km, nicho):
    """Busca estabelecimentos usando Overpass API"""
    try:
        lat, lon = geocodificar_cidade_gratis(cidade, estado)
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
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.markdown("### 🧭 Agente de Prospecção")
    st.caption("Busca por nichos e localidades com oportunidades reais")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Oportunidades Reais
    st.markdown('<p class="section-title" style="font-size: 16px; margin: 10px 0;">📊 Oportunidades Reais</p>', unsafe_allow_html=True)
    st.caption("Resultados do Google Trends relacionados aos serviços da LP Design")
    st.caption("Quais serviços foram mais buscados em determinada localidade")
    
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
    
    nichos_disponiveis = ["Todos"] + obter_todos_nichos()
    nicho_selecionado = st.selectbox(
        "Nicho principal",
        nichos_disponiveis,
        index=0
    )
    
    # Categorias específicas do nicho
    if nicho_selecionado != "Todos":
        categorias = obter_categorias_nicho(nicho_selecionado)
        if categorias:
            with st.expander("📋 Ver categorias deste nicho"):
                for cat in categorias:
                    st.caption(f"• {cat}")
    
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
    if nicho_selecionado == "Todos":
        st.warning("⚠️ Selecione um nicho específico para buscar leads")
    elif cidade_selecionada == "Todas":
        st.warning("⚠️ Selecione uma cidade específica para buscar leads")
    else:
        st.session_state.df_leads = buscar_leads_overpass_api(
            cidade_selecionada,
            uf,
            raio_km,
            nicho_selecionado
        )
        if not st.session_state.df_leads.empty:
            st.success(f"✅ {len(st.session_state.df_leads)} leads encontrados!")
            st.session_state.selecionados = set()

df_leads = st.session_state.df_leads.copy()
# ========== SIDEBAR (fim) ==========


# ========== HEADER (início) ==========
st.markdown('<h1 style="color: #ff6b35; font-size: 36px;">🧭 Agente de Prospecção LP Design</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #b0b0b0; font-size: 16px;">Ferramenta completa e gratuita para prospecção de clientes</p>', unsafe_allow_html=True)

# Stats
if not df_leads.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(df_leads)}</div>
            <div class="stat-label">Leads Encontrados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        selecionados = len(st.session_state.selecionados)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{selecionados}</div>
            <div class="stat-label">Selecionados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        com_site = len(df_leads[df_leads["tem_site"] == True])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{com_site}</div>
            <div class="stat-label">Com Site</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        com_redes = len(df_leads[df_leads["tem_redes"] == True])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{com_redes}</div>
            <div class="stat-label">Com Redes Sociais</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

tab_opp, tab_leads = st.tabs(["📊 Oportunidades", "🧲 Leads"])
# ========== HEADER (fim) ==========


# ========== ABA OPORTUNIDADES (início) ==========
with tab_opp:
    st.markdown('<p class="section-title">📊 Oportunidades de Mercado</p>', unsafe_allow_html=True)

    if st.session_state.df_oportunidades.empty:
        st.info("👆 Clique em **'Buscar Oportunidades'** na barra lateral para carregar dados do Google Trends")
    else:
        df_opp = st.session_state.df_oportunidades
        
        for _, row in df_opp.iterrows():
            st.markdown(f"""
            <div class="lead-card">
                <div class="lead-name">🔍 {row['palavra_chave']}</div>
                <div class="lead-info">📈 Volume estimado: <strong>{row['buscas']:,}</strong> buscas</div>
                <div class="lead-info">📅 Período: {row['periodo']}</div>
                <div class="lead-info">📍 Top cidades: {row['localidades_top']}</div>
            </div>
            """, unsafe_allow_html=True)
        
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
    st.markdown('<p class="section-title">🧲 Leads Prospectados</p>', unsafe_allow_html=True)

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
                # Card HTML
                redes_html = ""
                if row.get("facebook"):
                    redes_html += f'<a href="{row["facebook"]}" target="_blank"><div class="social-icon">📘</div></a>'
                if row.get("instagram"):
                    redes_html += f'<a href="{row["instagram"]}" target="_blank"><div class="social-icon">📷</div></a>'
                
                site_html = f'<div class="lead-info">🌐 <a href="{row["site"]}" target="_blank" style="color: #ff6b35;">Site</a></div>' if row.get("site") else '<div class="lead-info">🌐 Sem site</div>'
                
                st.markdown(f"""
                <div class="lead-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <div class="lead-name">{row['empresa']}</div>
                            <div class="lead-category">{row['nicho_geral']} • {row['nicho_especifico']}</div>
                            <div class="lead-rate {row['rate_class']}">Rate: {row['rate']}</div>
                        </div>
                        <div style="width: 80px; height: 80px; background: #404040; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 40px;">
                            🏢
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px;">
                        <div class="social-icons">{redes_html}</div>
                        {site_html}
                        <div class="lead-info">📍 {row['endereco']}</div>
                        {f'<div class="lead-info">📞 {row["telefone_bruto"]}</div>' if row.get("telefone_bruto") else ''}
                        {f'<div class="lead-info">🕐 {row["horario"]}</div>' if row.get("horario") else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Controles interativos (checkbox e WhatsApp)
                col1, col2 = st.columns([3, 1])
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
                        st.link_button("💬 WhatsApp", link, type="primary")

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
