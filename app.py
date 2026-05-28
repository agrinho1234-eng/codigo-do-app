import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from pymongo import MongoClient
import urllib.parse
from bson.objectid import ObjectId

# --- CONFIGURAÇÃO DO MONGODB ---
usuario = "agrinho1234_db_user"
senha_pura = "Agrinho@2000"
senha_codificada = urllib.parse.quote_plus(senha_pura)
MONGO_URI = f"mongodb+srv://{usuario}:{senha_codificada}@agrinho.n5jnpdu.mongodb.net/"

@st.cache_resource
def iniciar_conexao():
    return MongoClient(MONGO_URI)

client = iniciar_conexao()
db = client["AgroData"]
usuarios_coll = db["usuarios"]
historico_coll = db["historico_sensores"]

# --- CONFIGURAÇÃO DA CHAVE DE API ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    elif st.config.get_option("secrets.GOOGLE_API_KEY"):
        GOOGLE_API_KEY = st.config.get_option("secrets.GOOGLE_API_KEY")
    else:
        GOOGLE_API_KEY = ""
except:
    GOOGLE_API_KEY = ""

# --- FUNÇÃO DE REQUISIÇÃO DIRETA ---
def chamar_gemini_vias_puras(prompt_texto, api_key):
    # Atualizado para o modelo oficial e ativo gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt_texto
            }]
        }]
    }
    
    try:
        resposta = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            return dados['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Erro na IA (Status {resposta.status_code}). Detalhes: {resposta.text}"
            
    except Exception as e:
        return f"Falha de conexão com os servidores da Google: {str(e)}"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AgroTech Mobile", layout="wide", page_icon="🚜", initial_sidebar_state="collapsed")

# --- DESIGN SYSTEM ULTRA PREMIUM LUXURY (CSS MASTER) ---
st.markdown("""
    <style>
    /* Reset e Fundo Cinematic */
    .stApp { background: radial-gradient(circle at top, #111827 0%, #070A10 100%); color: #E2E8F0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    
    /* Títulos Magnéticos com Glow */
    h1 { font-size: 2.2rem !important; font-weight: 900 !important; color: #00E676; text-align: center; margin-bottom: 5px !important; letter-spacing: -1px; text-shadow: 0px 0px 20px rgba(0,230,118,0.35); }
    h2 { font-size: 1.6rem !important; font-weight: 800 !important; color: #FFFFFF; border-bottom: 2px solid #1E293B; padding-bottom: 10px; margin-bottom: 20px; }
    h3 { font-size: 1.2rem !important; font-weight: 700 !important; color: #94A3B8; margin-top: 15px; margin-bottom: 12px; }

    /* Abas Minimalistas Estilo iOS/Android Premium */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 10px; background-color: rgba(21, 31, 50, 0.7); padding: 8px; border-radius: 20px; border-bottom: none; margin-bottom: 25px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.02);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent; border-radius: 14px; padding: 14px 10px;
        color: #64748B !important; font-weight: 700; font-size: 0.85rem !important;
        border: none !important; flex-grow: 1; text-align: center; transition: all 0.25s ease;
    }
    .stTabs [aria-selected="true"] { 
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important; color: #00E676 !important;
        border: 1px solid rgba(0,230,118,0.15) !important; box-shadow: 0px 8px 20px rgba(0,0,0,0.5);
    }

    /* Cards Futuristas Glassmorphism */
    .mobile-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(17, 24, 39, 0.7) 100%); 
        border: 1px solid rgba(255, 255, 255, 0.04); 
        border-radius: 20px; padding: 20px; margin-bottom: 15px; 
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.3); backdrop-filter: blur(5px);
        position: relative; overflow: hidden;
    }
    .mobile-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-top: 1px solid rgba(255,255,255,0.07); border-radius: 20px; pointer-events: none; }
    .mobile-card-title { color: #94A3B8; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
    .mobile-card-value { color: #FFFFFF; font-size: 1.75rem; font-weight: 900; margin-top: 5px; text-shadow: 0px 2px 4px rgba(0,0,0,0.5); }

    /* Elementos de Formulário Smooth */
    input, select, .stSelectbox, div[data-baseweb="select"], .stNumberInput input {
        background-color: #0F172A !important; border: 1px solid #1E293B !important; border-radius: 14px !important; color: #F8FAFC !important; padding: 4px !important;
    }
    input:focus, select:focus { border-color: #00E676 !important; }
    
    /* BOTÕES REESTILIZADOS: Visual Cyber Minimalista (Sem mistura de azul) */
    .stButton>button {
        background: #0F172A !important; 
        color: #00E676 !important; 
        border: 2px solid #00E676 !important; 
        border-radius: 16px !important;
        padding: 14px !important; 
        font-size: 1rem !important; 
        font-weight: 800 !important;
        width: 100%; 
        box-shadow: 0 4px 15px rgba(0, 230, 118, 0.1); 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton>button:hover { 
        background: #00E676 !important; 
        color: #070A10 !important; 
        box-shadow: 0 0 25px rgba(0, 230, 118, 0.4);
        transform: translateY(-1px);
    }
    
    /* Botão Sair Clean */
    div[data-testid="column"] button[key*="logout_btn"] {
        background: rgba(30, 41, 59, 0.5) !important; color: #F87171 !important; border: 1px solid rgba(248,113,113,0.2) !important; padding: 10px !important; font-size: 0.85rem !important; box-shadow: none !important; border-radius: 12px !important;
    }
    div[data-testid="column"] button[key*="logout_btn"]:hover {
        background: #F87171 !important; color: #FFFFFF !important;
    }

    /* Ocultar Elementos Streamlit */
    .stDeployButton, footer, header, .stSidebar { display: none !important; }
    
    /* Chat Avançado Modo Mensageria */
    .chat-container { display: flex; flex-direction: column; gap: 14px; margin-top: 20px; padding: 5px; }
    
    .chat-block-user { display: flex; justify-content: flex-end; width: 100%; }
    .chat-user { background: linear-gradient(135deg, #00C853 0%, #009624 100%); border-radius: 20px 20px 4px 20px; padding: 14px 18px; color: #FFFFFF; font-weight: 500; max-width: 80%; box-shadow: 0 4px 15px rgba(0,200,83,0.2); border: 1px solid rgba(255,255,255,0.1); text-align: left; }
    
    .chat-block-ia { display: flex; justify-content: flex-start; width: 100%; }
    .chat-ia { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-radius: 20px 20px 20px 4px; padding: 16px 20px; border-left: 5px solid #00E676; border-top: 1px solid rgba(255,255,255,0.03); color: #E2E8F0; max-width: 80%; box-shadow: 0 6px 20px rgba(0,0,0,0.3); text-align: left; line-height: 1.5; }
    
    /* Bloco Diagnóstico de Destaque */
    .diagnostico-box { background: linear-gradient(145deg, #0F172A 0%, #070A10 100%); padding: 22px; border-radius: 18px; border-left: 5px solid #00E676; box-shadow: 0 8px 30px rgba(0,0,0,0.4); margin-bottom: 25px; border-top: 1px solid rgba(255,255,255,0.03); }
    
    /* Configuração Dataframe */
    .stDataFrame { background-color: #0F172A !important; border-radius: 16px !important; overflow: hidden; border: 1px solid #1E293B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO TEMPORÁRIO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'eh_admin' not in st.session_state: st.session_state.eh_admin = False
if 'diagnostico_ia' not in st.session_state: st.session_state.diagnostico_ia = ""
if 'historico_conversa' not in st.session_state: st.session_state.historico_conversa = []

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1>🚜 AGROTECH PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#64748B; font-size:1rem; font-weight:500; letter-spacing: 0.5px;'>Inteligência e Monitoramento de Solo</p>", unsafe_allow_html=True)
    
    aba_login, aba_cadastro = st.tabs(["🔒 ACESSAR CONTA", "✨ NOVA CONTA"])
    
    with aba_login:
        with st.form("form_login"):
            user_input = st.text_input("Usuário", placeholder="Ex: produtor1")
            senha_input = st.text_input("Senha", type="password", placeholder="******")
            btn_login = st.form_submit_button("ENTRAR NO SISTEMA")
            
            if btn_login:
                user_limpo = user_input.strip().lower()
                senha_limpa = senha_input.strip()
                usuario_no_banco = usuarios_coll.find_one({"usuario": user_limpo, "senha": senha_limpa})
                if usuario_no_banco:
                    st.session_state.autenticado = True
                    st.session_state.usuario_logado = user_limpo
                    st.session_state.eh_admin = usuario_no_banco.get("tipo") == "admin"
                    st.rerun()
                else: 
                    st.error("Usuário ou senha inválidos.")
                        
    with aba_cadastro:
        with st.form("form_cadastro"):
            novo_user = st.text_input("Defina o Usuário")
            nova_senha = st.text_input("Crie uma Senha Forte", type="password")
            
            perfil_personalizado = st.selectbox(
                "Qual é o seu perfil na lavoura?", 
                [
                    "Pequeno Produtor (Agricultura Familiar e Orgânicos)", 
                    "Médio Produtor (Cultivos Comerciais e Grãos)", 
                    "Grande Produtor (Alta Tecnologia e Larga Escala)", 
                    "Agrônomo / Consultor (Foco em Relatórios Técnicos)",
                    "Acadêmico",
                    "Entusiasta / Usuário de Testes (Apenas conhecendo o app)"
                ]
            )
            btn_cadastrar = st.form_submit_button("FINALIZAR CADASTRO")
            
            if btn_cadastrar:
                novo_user_limpo = novo_user.strip().lower()
                nova_senha_limpa = nova_senha.strip()
                if novo_user_limpo and nova_senha_limpa:
                    if usuarios_coll.find_one({"usuario": novo_user_limpo}): 
                        st.warning("Este nome já está sendo utilizado.")
                    else:
                        usuarios_coll.insert_one({
                            "usuario": novo_user_limpo, 
                            "senha": nova_senha_limpa, 
                            "tipo": "comum",
                            "perfil": perfil_personalizado
                        })
                        st.success("Cadastro efetuado! Acesse a aba de login.")
                else: 
                    st.error("Por favor, preencha todos os campos.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
if st.session_state.eh_admin:
    dados_do_banco = list(historico_coll.find({}))
else:
    dados_do_banco = list(historico_coll.find({"usuario": st.session_state.usuario_logado}))

df_filtrado = pd.DataFrame(dados_do_banco)

# --- MINI BARRA DE TOPO APP ---
top_c1, top_c2 = st.columns([4, 1])
with top_c1:
    tag = "👑 Admin" if st.session_state.eh_admin else "👨‍🌾 Campo"
    st.markdown(f"<p style='margin:0; padding-top:10px; font-size:1.1rem; color:#FFFFFF;'>Painel de: <b style='color:#00E676;'>{st.session_state.usuario_logado}</b> <span style='color:#64748B; font-size:0.85rem;'>({tag})</span></p>", unsafe_allow_html=True)
with top_c2:
    if st.button("🚪 Sair", key="logout_btn"):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.session_state.eh_admin = False
        st.session_state.diagnostico_ia = ""
        st.session_state.historico_conversa = []
        st.rerun()

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# --- ABAS DE NAVEGAÇÃO APP ---
if st.session_state.eh_admin:
    abas_sistema = ["📊 DASHBOARD GERAL", "🛠️ MODERAR DADOS", "👥 GERENCIAR CONTAS"]
else:
    abas_sistema = ["📊 MEU PAINEL", "📝 ENVIAR DADOS", "📋 REGISTROS"]

abas = st.tabs(abas_sistema)

# --- ABA 1: DASHBOARD ---
with abas[0]:
    if st.session_state.eh_admin and not df_filtrado.empty:
        usuarios_disponiveis = ["Todos os Produtores"] + list(df_filtrado["usuario"].unique())
        filtro_usuario = st.selectbox("Escolha o produtor para auditar:", usuarios_disponiveis)
        if filtro_usuario != "Todos os Produtores":
            df_filtrado = df_filtrado[df_filtrado["usuario"] == filtro_usuario]

    if not df_filtrado.empty:
        ult = df_filtrado.iloc[-1]
        
        # Grid de Cards Customizados Luxury Glassmorphism
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>🌱 Potencial de Hidrogênio</div><div class='mobile-card-value'>{ult['pH']} pH</div></div><div style='font-size:2.2rem; filter: drop-shadow(0 0 10px rgba(0,230,118,0.5));'>🧪</div></div>""", unsafe_allow_html=True)
        with c_p2:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>💧 Umidade da Camada</div><div class='mobile-card-value'>{ult['Umidade']}%</div></div><div style='font-size:2.2rem; filter: drop-shadow(0 0 10px #00B0FF);'>💧</div></div>""", unsafe_allow_html=True)
            
        c_p3, c_p4 = st.columns(2)
        with c_p3:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>📍 Zona Monitorada</div><div class='mobile-card-value' style='font-size:1.15rem; padding-top:8px;'>{ult['Sensor']}</div></div><div style='font-size:2rem;'>🗺️</div></div>""", unsafe_allow_html=True)
        with c_p4:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>📈 Amostras de Solo</div><div class='mobile-card-value'>{len(df_filtrado)}</div></div><div style='font-size:2.2rem;'>📊</div></div>""", unsafe_allow_html=True)

        # Seção Avançada de Gráficos e Mapas
        col_visual_esq, col_visual_dir = st.columns([1.3, 1])
        
        with col_visual_esq:
            st.markdown("<h3>📈 Comportamento de Umidade</h3>", unsafe_allow_html=True)
            cor_grafico = "usuario" if st.session_state.eh_admin and filtro_usuario == "Todos os Produtores" else "Sensor"
            
            eixo_x = "Hora" if "Data" not in df_filtrado.columns else "Data"
            
            paleta_neon_custom = ["#00E676", "#00B0FF", "#D500F9", "#651FFF", "#FF6D00"]
            
            fig = px.line(
                df_filtrado.tail(10), x=eixo_x, y="Umidade", color=cor_grafico, 
                markers=True, height=220, color_discrete_sequence=paleta_neon_custom
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                font_color="#94A3B8", margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#1E293B")
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with col_visual_dir:
            st.markdown("<h3>📍 Mapeamento dos Sensores (GPS)</h3>", unsafe_allow_html=True)
            st.map(df_filtrado, height=220)
            
        # IA Agrônomo - Diagnóstico Fixo Estilizado
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        dados_usuario = usuarios_coll.find_one({"usuario": st.session_state.usuario_logado})
        perfil_usuario = dados_usuario.get("perfil", "Pequeno Produtor") if dados_usuario else "Pequeno Produtor"

        if "Entusiasta" in perfil_usuario or "Testes" in perfil_usuario:
            st.markdown("<h3 style='color:#00E676;'>⚙️ PAINEL DE SIMULAÇÃO DE PERFIL</h3>", unsafe_allow_html=True)
            perfil_simulado = st.selectbox(
                "Simular comportamento para:",
                ["Pequeno Produtor", "Médio Produtor", "Grande Produtor", "Agrônomo / Consultor", "Acadêmico"]
            )
            perfil_alvo_ia = perfil_simulado
        else:
            perfil_alvo_ia = perfil_usuario

        if st.button("✨ GERAR RELATÓRIO AGROIA PROFISSONAL"):
            if not GOOGLE_API_KEY:
                st.error("A chave de comunicação da IA não foi localizada.")
            else:
                with st.spinner("Computando laudo técnico do solo..."):
                    prompt = f"""
                    Você é um agrônomo sênior especialista em IA e inteligência de dados de solo.
                    Analise os seguintes dados recentes de solo coletados: {df_filtrado.tail(3).to_string()}
                    
                    Gere um diagnóstico personalizado de no máximo 3 tópicos curtos adaptado para o perfil: "{perfil_alvo_ia}".
                    
                    Siga estritamente esta estratégia de resposta para o perfil selecionado:
                    - Se for Pequeno Produtor: Foque em soluções práticas, manejos manuais ou orgânicos e adubos de baixo custo. Use linguagem simples.
                    - Se for Médio Produtor: Foque em eficiência, custo-benefício de fertilizantes e táticas para aumentar a produtividade por hectare.
                    - Se for Grande Produtor: Foque em alta tecnologia, correção de solo para maquinário pesado, agricultura de precisão e metas de larga escala.
                    - Se for Agrônomo / Consultor: Forneça uma análise técnica detalhada dos parâmetros de pH e umidade, simulando um parecer técnico ou laudo profissional.
                    - Se for Acadêmico: Forneça uma análise totalmente focada em conceitos teóricos, científicos e de pesquisa. Use terminologia estritamente científica.
                    """
                    st.session_state.diagnostico_ia = chamar_gemini_vias_puras(prompt, GOOGLE_API_KEY)
        
        if st.session_state.diagnostico_ia:
            st.markdown(f"<div class='diagnostico-box'>", unsafe_allow_html=True)
            if "Entusiasta" in perfil_usuario or "Testes" in perfil_usuario:
                st.markdown(f"<span style='color:#00B0FF; font-size:0.85rem; font-weight:700;'>💡 Perfil Simulado: {perfil_alvo_ia}</span><br><br>", unsafe_allow_html=True)
            st.write(st.session_state.diagnostico_ia)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEÇÃO DO CHAT CHAT LADO A LADO ESTILO APP PREMIUM ---
        st.markdown("---")
        st.markdown("<h3>💬 Consultoria Direta via AgroIA</h3>", unsafe_allow_html=True)
        
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for msg in st.session_state.historico_conversa:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-block-user'><div class='chat-user'><b>Você:</b><br>{msg['text']}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-block-ia'><div class='chat-ia'>🤖 <b>AgroIA:</b><br>{msg['text']}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        pergunta_usuario = st.chat_input("Deseja saber como corrigir o solo ou gerenciar a umidade? Pergunte aqui...")
        
        if pergunta_usuario:
            st.session_state.historico_conversa.append({"role": "user", "text": pergunta_usuario})
            
            if not GOOGLE_API_KEY:
                st.session_state.historico_conversa.append({"role": "ia", "text": "Erro técnico no motor da IA."})
            else:
                with st.spinner("Analisando cenário técnico..."):
                    prompt_chat = f"""
                    Você é um Assistente Agrônomo Virtual Inteligente criado para o projeto Agrinho. 
                    Seu objetivo é ajudar produtores rurais de forma prática e direta.
                    Contexto recente da lavoura: {df_filtrado.tail(3).to_string()}
                    Perfil: {perfil_alvo_ia}
                    Responda de forma completa porém legível: "{pergunta_usuario}"
                    """
                    resposta_ia = chamar_gemini_vias_puras(prompt_chat, GOOGLE_API_KEY)
                    st.session_state.historico_conversa.append({"role": "ia", "text": resposta_ia})
            st.rerun()
    else:
        st.info("Aguardando inserção de dados para consolidar o painel.")

# --- COMPORTAMENTO DO PRODUTOR / ACADÊMICO / TESTE ---
if not st.session_state.eh_admin:
    with abas[1]:
        st.markdown("<h2>📝 Nova Amostragem Técnica</h2>", unsafe_allow_html=True)
        with st.form("form_mobile_clean", clear_on_submit=True):
            f_sensor = st.selectbox("Identificação do Talhão/Estufa:", ["Talhão Norte", "Talhão Sul", "Setor Leste", "Estufa 01", "Estufa 02"])
            f_ph = st.number_input("Medição de pH de Solo (0.0 a 14.0)", min_value=0.0, max_value=14.0, value=6.5, step=0.1, format="%.1f")
            f_umidade = st.number_input("Higrometria / Umidade Relativa (%)", min_value=0, max_value=100, value=50, step=1)
            
            st.markdown("<p style='color:#94A3B8; margin-top:15px; margin-bottom:5px; font-weight:700;'>📍 Posicionamento Geográfico por Satélite</p>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            f_lat = c1.number_input("Coordenada Latitude", value=-23.5874, format="%.4f")
            f_lon = c2.number_input("Coordenada Longitude", value=-46.6576, format="%.4f")
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            enviado = st.form_submit_button("🚀 TRANSMITIR LEITURA PARA O SERVIDOR")
            
            if enviado:
                agora = pd.Timestamp.now()
                nova_leitura = {
                    "usuario": st.session_state.usuario_logado,
                    "Sensor": f_sensor, "pH": float(f_ph), "Umidade": int(f_umidade),
                    "latitude": float(f_lat), "longitude": float(f_lon),
                    "Data": agora.strftime("%d/%m/%Y"),
                    "Hora": agora.strftime("%H:%M:%S")
                }
                historico_coll.insert_one(nova_leitura)
                st.success("Leitura registrada com sucesso no banco AgroData!")

    with abas[2]:
        st.markdown("<h2>📋 Histórico Consolidado de Amostras</h2>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            df_tab = df_filtrado.copy().drop(columns=['_id', 'usuario'], errors='ignore')
            colunas_certas = [c for c in ["Data", "Hora", "Sensor", "pH", "Umidade", "latitude", "longitude"] if c in df_tab.columns]
            st.dataframe(df_tab[colunas_certas], use_container_width=True, hide_index=True)
        else: 
            st.warning("Nenhum registro encontrado vinculado a esta conta.")

# --- COMPORTAMENTO DO ADMIN ---
else:
    with abas[1]:
        st.markdown("<h2>🛠️ Moderação e Auditoria de Leituras</h2>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            df_editor = df_filtrado.copy()
            df_editor['_id'] = df_editor['_id'].astype(str)
            
            dados_editados = st.data_editor(
                df_editor, use_container_width=True, hide_index=True,
                disabled=["usuario", "Hora", "Data", "_id"],
                column_config={"_id": None, "latitude": None, "longitude": None}
            )
            
            if st.button("💾 SALVAR MODERAÇÕES NO BANCO"):
                for index, row in dados_editados.iterrows():
                    historico_coll.update_one(
                        {"_id": ObjectId(row['_id'])},
                        {"$set": {"Sensor": row['Sensor'], "pH": float(row['pH']), "Umidade": int(row['Umidade'])}}
                    )
                st.success("Registros sincronizados com o MongoDB!")
                st.rerun()
                
            st.markdown("---")
            st.markdown("<h3>🗑️ Expurgar Amostragem</h3>", unsafe_allow_html=True)
            
            opcoes_delecao = []
            for i, row in df_filtrado.iterrows():
                dt_str = row.get('Data', 'Sem Data')
                opcoes_delecao.append(f"[{i}] {dt_str} {row['Hora']} | {row['usuario']} -> {row['Sensor']}")
                
            escolha_registro = st.selectbox("Escolha qual linha deletar de forma definitiva:", opcoes_delecao)
            
            if st.button("🗑️ DELETAR REGISTRO SELECIONADO"):
                idx_original = int(escolha_registro.split(']')[0].replace('[', ''))
                id_para_deletar = df_filtrado.iloc[idx_original]['_id']
                historico_coll.delete_one({"_id": ObjectId(id_para_deletar)})
                st.success("Item removido do histórico global.")
                st.rerun()

    with abas[2]:
        st.markdown("<h2>👥 Gestão de Contas e Acessos</h2>", unsafe_allow_html=True)
        todas_contas = list(usuarios_coll.find({}))
        df_contas = pd.DataFrame(todas_contas)
        
        if not df_contas.empty:
            df_contas_exibicao = df_contas.copy().drop(columns=['_id', 'senha'], errors='ignore')
            st.markdown("### Credenciais Ativas")
            st.dataframe(df_contas_exibicao, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("<h3>🚨 Revogar Conta e Banir do Ecossistema</h3>", unsafe_allow_html=True)
            
            lista_usuarios = [row['usuario'] for _, row in df_contas.iterrows() if row['usuario'] != st.session_state.usuario_logado]
            
            if lista_usuarios:
                conta_para_deletar = st.selectbox("Escolha o usuário para deleção total:", lista_usuarios)
                confirmar_exclusao = st.checkbox(f"Estou ciente de que a exclusão do usuário '{conta_para_deletar}' apagará também todo o histórico dele.")
                
                if st.button("❌ CONFIRMAR EXCLUSÃO PERMANENTE"):
                    if confirmar_exclusao:
                        historico_coll.delete_many({"usuario": conta_para_deletar})
                        usuarios_coll.delete_one({"usuario": conta_para_deletar})
                        st.success(f"O cadastro de {conta_para_deletar} foi apagado da nuvem.")
                        st.rerun()
                    else:
                        st.warning("É necessário marcar a caixa de confirmação para prosseguir.")
            else:
                st.info("Não há outras contas de usuários criadas além do seu admin.")
        else:
            st.info("Nenhuma conta localizada na coleção.")
