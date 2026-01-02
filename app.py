# ========== IMPORTS / CONFIG ==========
import streamlit as st
import pandas as pd
from io import StringIO
from urllib.parse import quote
import requests
from datetime import datetime
import time
from ibge_localidades import buscar_estados, buscar_cidades_por_estado
from nichos_comerciais import obter_todos_nichos, obter_tags_osm_nicho, obter_categorias_nicho

# Configuração
st.set_page_config(
    page_title="Agente de Prospecção | LP Design",
    page_icon="🧭",
    layout="wide",
)

# CSS Dark Theme profissional
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #1a1d24; }
    .stButton > button {
        background: linear-gradient(90deg, #ff6b35, #ff8c42);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #ff8c42, #ff6b35);
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.4);
    }
    [data-testid="stMetricValue"] { color: #ff6b35; font-size: 28px; }
    h1, h2, h3 { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

st.logo(
    "https://luizpimentel.com/wp-content/uploads/2022/09/PNG-72dpi-Identidade-Visual-LP-Design-05.png",
    size="large",
)


# ========== FUNÇÕES ==========
def buscar_logo_site(url):
    """Busca favicon do site"""
    if not url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url if url.startswith('http') else 'https://' + url)
        domain = parsed.netloc or parsed.path
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    except:
        return None


def analisar_site(url):
    """Análise técnica do site"""
    if not url:
        return {
            "tem_https": False,
            "responde": False,
            "tempo_resposta": 0,
            "status_code": 0,
            "tem_mobile": False,
            "wordpress": False,
            "score_seo": 0,
            "score_design": 0
        }
    
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        
        start = time.time()
        response = requests.get(url, timeout=5, allow_redirects=True)
        tempo = time.time() - start
        
        html = response.text.lower()
        
        analise = {
            "tem_https": url.startswith('https'),
            "responde": response.status_code == 200,
            "tempo_resposta": round(tempo, 2),
            "status_code": response.status_code,
            "tem_mobile": 'viewport' in html,
            "wordpress": 'wp-content' in html or 'wp-includes' in html,
            "score_seo": 0,
            "score_design": 0
        }
        
        # Score SEO
        score_seo = 0
        if analise["tem_https"]: score_seo += 25
        if analise["responde"]: score_seo += 35
        if analise["tempo_resposta"] < 3: score_seo += 20
        if analise["tem_mobile"]: score_seo += 20
        analise["score_seo"] = score_seo
        
        # Score Design (básico)
        score_design = 50  # Base
        if 'bootstrap' in html or 'tailwind' in html: score_design += 20
        if 'fontawesome' in html or 'material' in html: score_design += 15
        if analise["tem_mobile"]: score_design += 15
        analise["score_design"] = min(score_design, 100)
        
        return analise
    except:
        return {
            "tem_https": False,
            "responde": False,
            "tempo_resposta": 0,
            "status_code": 0,
            "tem_mobile": False,
            "wordpress": False,
            "score_seo": 0,
            "score_design": 0
        }


def calcular_prioridade_score(lead_data, analise_site):
    """Calcula prioridade e score do lead"""
    score = 0
    motivos = []
    sugestoes = []
    
    # Análise de presença digital
    if not lead_data.get("site"):
        score += 40
        motivos.append("Sem website")
        sugestoes.append("🌐 Criação de Site Profissional")
        sugestoes.append("📱 Landing Page Responsiva")
    elif not analise_site["responde"]:
        score += 35
        motivos.append("Site offline/inacessível")
        sugestoes.append("🔧 Manutenção e Recuperação de Site")
    else:
        if analise_site["score_seo"] < 50:
            score += 25
            motivos.append(f"SEO fraco ({analise_site['score_seo']}/100)")
            sugestoes.append("📈 Otimização de SEO")
        
        if not analise_site["tem_https"]:
            score += 15
            motivos.append("Sem HTTPS")
            sugestoes.append("🔒 Implementação de SSL/HTTPS")
        
        if analise_site["tempo_resposta"] > 3:
            score += 15
            motivos.append("Site lento")
            sugestoes.append("⚡ Otimização de Performance")
        
        if not analise_site["tem_mobile"]:
            score += 20
            motivos.append("Não responsivo")
            sugestoes.append("📱 Design Mobile-First")
        
        if analise_site["wordpress"] and analise_site["score_design"] < 60:
            score += 10
            sugestoes.append("🎨 Redesign WordPress Premium")
    
    # Redes sociais
    if not lead_data.get("facebook") and not lead_data.get("instagram"):
        score += 20
        motivos.append("Sem redes sociais")
        sugestoes.append("📱 Gestão de Redes Sociais")
    
    # Email/telefone
    if not lead_data.get("telefone_bruto"):
        score += 10
    if not lead_data.get("email"):
        score += 10
        sugestoes.append("📧 Email Marketing Profissional")
    
    # Sempre oferece
    sugestoes.append("🎨 Identidade Visual")
    sugestoes.append("📊 Marketing Digital")
    
    # Determina prioridade
    if score >= 70:
        prioridade = "🔴 Alta"
        prioridade_emoji = "🔴"
    elif score >= 40:
        prioridade = "🟡 Média"
        prioridade_emoji = "🟡"
    else:
        prioridade = "🟢 Baixa"
        prioridade_emoji = "🟢"
    
    motivo_principal = motivos[0] if motivos else "Análise completa disponível"
    
    return {
        "prioridade": prioridade,
        "prioridade_emoji": prioridade_emoji,
        "score": min(score, 100),
        "motivo": motivo_principal,
        "motivos_completos": motivos,
        "sugestoes": sugestoes[:5]  # Top 5
    }


def gerar_mensagem_primeiro_contato(empresa, cidade, prioridade_data):
    """Gera mensagem personalizada para WhatsApp"""
    motivo = prioridade_data["motivo"].lower()
    
    msgs = {
        "sem website": f"Olá! Encontrei {empresa} no Google Maps e notei que vocês não têm um site linkado. Sou da LP Design e podemos criar um site profissional que atraia mais clientes. Podemos conversar?",
        "site offline": f"Olá! Tentei acessar o site de {empresa} e parece estar fora do ar. Sou da LP Design, especialista em recuperação e manutenção. Posso ajudar a resolver isso rapidamente.",
        "seo fraco": f"Olá! Analisei {empresa} e vi que o site pode aparecer muito mais no Google. Sou especialista em SEO e marketing digital. Vamos melhorar sua visibilidade?",
        "sem redes sociais": f"Olá! Vi {empresa} no Google e notei que vocês não estão usando redes sociais. Podemos criar uma presença digital forte. Vamos conversar?",
    }
    
    for chave, msg in msgs.items():
        if chave in motivo:
            return msg
    
    return f"Olá! Encontrei {empresa} em {cidade} e vejo oportunidades de melhorar a presença digital. Sou da LP Design. Podemos conversar sobre como atrair mais clientes online?"


def geocodificar_cidade_gratis(cidade, estado):
    """Geocoding via Nominatim"""
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
        return -15.7939, -47.8828
    except:
        return -15.7939, -47.8828


def buscar_leads_overpass_api(cidade, estado, raio_km, nicho, tags_custom=None):
    """Busca estabelecimentos via Overpass API"""
    try:
        lat, lon = geocodificar_cidade_gratis(cidade, estado)
        
        if tags_custom:
            tags = tags_custom
        else:
            tags = obter_tags_osm_nicho(nicho)
        
        if not tags:
            tags = ["shop"]
        
        query = f"[out:json][timeout:30];("
        for tag in tags:
            key, value = tag.split("=")
            query += f'node["{key}"="{value}"](around:{raio_km * 1000},{lat},{lon});'
            query += f'way["{key}"="{value}"](around:{raio_km * 1000},{lat},{lon});'
        query += ");out center;"
        
        url = "https://overpass-api.de/api/interpreter"
        
        with st.spinner(f"🔍 Buscando em {cidade}/{estado}..."):
            time.sleep(2)
            response = requests.post(url, data={"data": query}, timeout=40)
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
                "key": f"{nome}_{cidade}_{i}",
                "empresa": nome,
                "nicho_geral": nicho,
                "nicho_especifico": tags.get("amenity", tags.get("shop", tags.get("office", "outros"))),
                "estado": estado,
                "cidade": cidade,
                "endereco": endereco,
                "site": website,
                "whatsapp": whatsapp,
                "telefone_bruto": telefone,
                "email": email,
                "facebook": facebook,
                "instagram": instagram,
                "horario": horario,
                "lat": elem_lat,
                "lon": elem_lon,
            }
            
            # Análise e score
            analise = analisar_site(website)
            prioridade_data = calcular_prioridade_score(lead_data, analise)
            
            lead_data.update({
                "analise_site": analise,
                "prioridade": prioridade_data["prioridade"],
                "prioridade_emoji": prioridade_data["prioridade_emoji"],
                "score": prioridade_data["score"],
                "motivo": prioridade_data["motivo"],
                "sugestoes": prioridade_data["sugestoes"],
            })
            
            leads.append(lead_data)
        
        return pd.DataFrame(leads)
        
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
        return pd.DataFrame()


def montar_link_whatsapp(numero_br, mensagem):
    """Cria link wa.me"""
    if not numero_br:
        return None
    digits = "".join([c for c in numero_br if c.isdigit()])
    num_final = "55" + digits if not digits.startswith("55") else digits
    return f"https://wa.me/{num_final}?text={quote(mensagem)}"


# ========== STATE ==========
if "df_leads" not in st.session_state:
    st.session_state.df_leads = pd.DataFrame()
if "selecionados" not in st.session_state:
    st.session_state.selecionados = {}


# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🧭 Agente de Prospecção")
    st.caption("Busca inteligente com análise automática")
    st.markdown("---")
    
    # Localização
    st.markdown("**📍 Localização**")
    estados_ibge = buscar_estados()
    estados_opcoes = [f"{e['sigla']} - {e['nome']}" for e in estados_ibge]
    
    estado_sel = st.selectbox("Estado", estados_opcoes, index=0)
    uf = estado_sel.split(" - ")[0]
    
    cidades = buscar_cidades_por_estado(uf)
    cidade_sel = st.selectbox("Cidade", cidades, index=0)
    
    raio = st.slider("Raio (km)", 5, 100, 20, 5)
    
    st.markdown("---")
    
    # Nicho
    st.markdown("**🎯 Nicho**")
    nichos = obter_todos_nichos()
    nicho_sel = st.selectbox("Nicho principal", nichos, index=0)
    
    categorias = obter_categorias_nicho(nicho_sel)
    categoria_sel = st.selectbox("Categoria", ["Todas"] + categorias, index=0)
    
    st.markdown("---")
    
    buscar_btn = st.button("🔍 Buscar Leads", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.success("✅ 100% Gratuito")
    st.caption(f"🗺️ {len(estados_ibge)} estados")
    st.caption("🌍 OpenStreetMap + IBGE")


# Buscar
if buscar_btn:
    if categoria_sel != "Todas":
        tags_busca = [tag for tag in obter_tags_osm_nicho(nicho_sel) if categoria_sel.lower() in tag.lower()]
        if not tags_busca:
            tags_busca = obter_tags_osm_nicho(nicho_sel)
    else:
        tags_busca = obter_tags_osm_nicho(nicho_sel)
    
    st.session_state.df_leads = buscar_leads_overpass_api(cidade_sel, uf, raio, nicho_sel, tags_busca)
    
    if not st.session_state.df_leads.empty:
        st.success(f"✅ {len(st.session_state.df_leads)} leads encontrados!")
        st.session_state.selecionados = {}

df = st.session_state.df_leads.copy()


# ========== HEADER ==========
st.title("🧭 Agente de Prospecção LP Design")
st.caption("Análise inteligente e automática de oportunidades")

if not df.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df))
    col2.metric("Alta Prioridade", len(df[df["prioridade"].str.contains("Alta")]))
    col3.metric("Selecionados", len(st.session_state.selecionados))
    col4.metric("Score Médio", f"{df['score'].mean():.0f}")

st.markdown("---")

# ========== TABS ==========
tab_results, tab_pipeline = st.tabs(["📊 Resultados", "📌 Pipeline"])

# TAB RESULTADOS
with tab_results:
    if df.empty:
        st.info("👆 Configure filtros e clique em **Buscar Leads**")
    else:
        # Ordenar por score
        df = df.sort_values("score", ascending=False)
        
        for _, row in df.iterrows():
            lead_key = row["key"]
            
            # Container com borda
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 3, 3])
                
                # === COLUNA 1: INFO ===
                with col1:
                    # Logo + Nome
                    logo_url = buscar_logo_site(row.get("site"))
                    if logo_url:
                        st.image(logo_url, width=60)
                    
                    st.markdown(f"### {row['empresa']}")
                    st.caption(f"📍 {row['endereco']}")
                    st.caption(f"📞 {row['telefone_bruto'] if row['telefone_bruto'] else 'Não informado'}")
                    
                    if row.get("site"):
                        st.markdown(f"🌐 [{row['site']}]({row['site']})")
                    else:
                        st.caption("🌐 Sem site")
                    
                    # Diagnóstico técnico
                    st.markdown("**Diagnóstico:**")
                    analise = row["analise_site"]
                    st.code(
                        f"Status: {'Online' if analise['responde'] else 'Offline'}\n"
                        f"HTTPS: {'✅' if analise['tem_https'] else '❌'}\n"
                        f"Mobile: {'✅' if analise['tem_mobile'] else '❌'}\n"
                        f"WordPress: {'✅' if analise['wordpress'] else '❌'}\n"
                        f"Tempo: {analise['tempo_resposta']}s\n"
                        f"SEO Score: {analise['score_seo']}/100"
                    )
                
                # === COLUNA 2: PRIORIDADE/SCORE ===
                with col2:
                    st.markdown(f"## {row['prioridade']}")
                    st.metric("Score de Oportunidade", f"{row['score']}/100")
                    st.caption(f"**Motivo:** {row['motivo']}")
                    
                    st.markdown("**💰 Oportunidades:**")
                    for sug in row["sugestoes"]:
                        st.warning(f"👉 {sug}")
                
                # === COLUNA 3: AÇÕES ===
                with col3:
                    # Checkbox seleção
                    sel = st.checkbox("📌 Selecionar", key=f"sel_{lead_key}")
                    if sel:
                        if lead_key not in st.session_state.selecionados:
                            st.session_state.selecionados[lead_key] = row.to_dict()
                    else:
                        st.session_state.selecionados.pop(lead_key, None)
                    
                    # Mensagem editável
                    msg_base = gerar_mensagem_primeiro_contato(
                        row["empresa"],
                        cidade_sel,
                        row
                    )
                    msg_edit = st.text_area(
                        "Mensagem inicial (editável)",
                        value=msg_base,
                        height=120,
                        key=f"msg_{lead_key}"
                    )
                    
                    # Botão WhatsApp
                    link_zap = montar_link_whatsapp(row["whatsapp"], msg_edit)
                    if link_zap:
                        st.link_button("📲 WhatsApp", link_zap, type="primary", use_container_width=True)
                    else:
                        st.caption("Telefone não disponível")
                    
                    # Relatório completo
                    if st.button("📄 Ver Relatório", key=f"rel_{lead_key}", use_container_width=True):
                        st.session_state[f"show_rel_{lead_key}"] = not st.session_state.get(f"show_rel_{lead_key}", False)
                
                # Relatório expandido
                if st.session_state.get(f"show_rel_{lead_key}", False):
                    with st.expander("📋 Relatório Completo", expanded=True):
                        st.markdown("### Análise Técnica Detalhada")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Status", "Online" if analise["responde"] else "Offline")
                            st.metric("Score SEO", f"{analise['score_seo']}/100")
                        with col_b:
                            st.metric("Tempo Resposta", f"{analise['tempo_resposta']}s")
                            st.metric("Score Design", f"{analise['score_design']}/100")
                        with col_c:
                            st.metric("HTTPS", "Sim" if analise["tem_https"] else "Não")
                            st.metric("Responsivo", "Sim" if analise["tem_mobile"] else "Não")
                        
                        st.markdown("### 📱 Redes Sociais")
                        if row.get("facebook"):
                            st.markdown(f"- [Facebook]({row['facebook']})")
                        if row.get("instagram"):
                            st.markdown(f"- [Instagram]({row['instagram']})")
                        if not row.get("facebook") and not row.get("instagram"):
                            st.warning("❌ Sem redes sociais - **Grande oportunidade!**")
                        
                        st.markdown("### 💼 Recomendações Prioritárias")
                        for i, sug in enumerate(row["sugestoes"], 1):
                            st.markdown(f"{i}. {sug}")

# TAB PIPELINE
with tab_pipeline:
    st.markdown("## 📌 Leads Selecionados")
    
    if not st.session_state.selecionados:
        st.info("Nenhum lead selecionado. Marque os leads na aba Resultados.")
    else:
        for lead_key, lead in st.session_state.selecionados.items():
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"### {lead['empresa']}")
                    st.caption(f"{lead['prioridade']} | Score: {lead['score']}/100")
                    st.caption(f"📍 {lead['endereco']}")
                    st.caption(f"📞 {lead.get('telefone_bruto', 'Não informado')}")
                
                with col2:
                    msg = gerar_mensagem_primeiro_contato(lead["empresa"], cidade_sel, lead)
                    link = montar_link_whatsapp(lead["whatsapp"], msg)
                    if link:
                        st.link_button("📲 WhatsApp", link, type="primary", use_container_width=True)
        
        # Export
        if st.button("⬇️ Exportar Pipeline (CSV)", use_container_width=True):
            export_data = []
            for lead in st.session_state.selecionados.values():
                export_data.append({
                    "Empresa": lead["empresa"],
                    "Prioridade": lead["prioridade"],
                    "Score": lead["score"],
                    "Telefone": lead.get("telefone_bruto", ""),
                    "Site": lead.get("site", ""),
                    "Cidade": lead["cidade"],
                    "Estado": lead["estado"]
                })
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download CSV",
                csv,
                f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv"
            )
