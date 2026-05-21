import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
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

# --- CONFIGURAÇÃO DA IA SEGURA ---
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    GOOGLE_API_KEY = "# --- CONFIGURAÇÃO DA IA SEGURA ---
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    GOOGLE_API_KEY = "AIzaSyDBItQq-Qu6atbjZL7Od1Buz6Fonmy_v6s" 

genai.configure(api_key=GOOGLE_API_KEY)" 

genai.configure(api_key=GOOGLE_API_KEY)

def buscar_modelo():
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        prioridade = ['models/gemini-1.5-flash', 'models/gemini-pro']
        for p in prioridade:
            if p in modelos: return genai.GenerativeModel(p)
        return genai.GenerativeModel(modelos[0])
    except: return genai.GenerativeModel('gemini-1.5-flash')

model = buscar_modelo()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AgroTech Mobile", layout="wide", page_icon="🚜", initial_sidebar_state="collapsed")

# --- DESIGN SYSTEM ULTRA-MOBILE (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; color: #C9D1D9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    h1 { font-size: 1.8rem !important; font-weight: 800 !important; color: #2ea043; text-align: center; margin-bottom: 5px !important; }
    h2 { font-size: 1.4rem !important; font-weight: 700 !important; color: #ffffff; }
    h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: #8b949e; }

    .stTabs [data-baseweb="tab-list"] { 
        gap: 5px; background-color: #161b22; padding: 6px; border-radius: 14px; border-bottom: none; margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent; border-radius: 10px; padding: 12px 10px;
        color: #8b949e !important; font-weight: bold; font-size: 0.85rem !important;
        border: none !important; flex-grow: 1; text-align: center;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #21262d !important; color: #2ea043 !important;
        border: 1px solid #30363d !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }

    .mobile-card {
        background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px;
        margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;
    }
    .mobile-card-title { color: #8b949e; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
    .mobile-card-value { color: #ffffff; font-size: 1.4rem; font-weight: 700; margin-top: 2px; }

    input, select, .stSelectbox, div[data-baseweb="select"] {
        background-color: #21262d !important; border-radius: 8px !important; color: white !important;
    }
    
    .stButton>button {
        background-color: #238636 !important; color: white !important; border-radius: 12px !important;
        padding: 16px !important; font-size: 1rem !important; font-weight: 700 !important;
        width: 100%; border: none !important; box-shadow: 0 4px 12px rgba(35,134,54,0.3);
    }
    .stButton>button:active { background-color: #2ea043 !important; }
    
    .stDeployButton, footer, header, .stSidebar { display: none !important; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO temporário ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'eh_admin' not in st.session_state: st.session_state.eh_admin = False
if 'diagnostico_ia' not in st.session_state: st.session_state.diagnostico_ia = ""

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1>🚜 AGROTECH PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#8b949e; font-size:0.9rem;'>Monitoramento Inteligente de Solo</p>", unsafe_allow_html=True)
    
    aba_login, aba_cadastro = st.tabs(["🔒 ENTRAR", "✨ NOVA CONTA"])
    
    with aba_login:
        with st.form("form_login"):
            user_input = st.text_input("Usuário", placeholder="Ex: produtor1")
            senha_input = st.text_input("Senha", type="password", placeholder="******")
            btn_login = st.form_submit_button("ENTRAR NO APP")
            
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
                    st.error("Dados incorretos.")
                    
    with aba_cadastro:
        with st.form("form_cadastro"):
            novo_user = st.text_input("Escolha o Usuário")
            nova_senha = st.text_input("Crie uma Senha", type="password")
            btn_cadastrar = st.form_submit_button("CADASTRAR")
            
            if btn_cadastrar:
                novo_user_limpo = novo_user.strip().lower()
                nova_senha_limpa = nova_senha.strip()
                if novo_user_limpo and nova_senha_limpa:
                    if usuarios_coll.find_one({"usuario": novo_user_limpo}): 
                        st.warning("Usuário indisponível.")
                    else:
                        usuarios_coll.insert_one({"usuario": novo_user_limpo, "senha": nova_senha_limpa, "tipo": "comum"})
                        st.success("Cadastrado com sucesso! Mude para a aba 'ENTRAR'.")
                else: 
                    st.error("Preencha todos os campos.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
if st.session_state.eh_admin:
    dados_do_banco = list(historico_coll.find({}))
else:
    dados_do_banco = list(historico_coll.find({"usuario": st.session_state.usuario_logado}))

df_filtrado = pd.DataFrame(dados_do_banco)

# --- MINI BARRA DE TOPO APP ---
top_c1, top_c2 = st.columns([3, 1])
with top_c1:
    tag = "👑 Admin" if st.session_state.eh_admin else "👨‍🌾 Campo"
    st.markdown(f"<p style='margin: 0; padding-top: 5px; font-size: 1rem; color: white;'><b>{st.session_state.usuario_logado}</b> <span style='color:#2ea043;'>({tag})</span></p>", unsafe_allow_html=True)
with top_c2:
    if st.button("🚪 Sair", key="logout_btn"):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.session_state.eh_admin = False
        st.session_state.diagnostico_ia = ""
        st.rerun()

st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)

# --- ABAS DE NAVEGAÇÃO APP ---
if st.session_state.eh_admin:
    abas_sistema = ["📊 DASHBOARD GERAL", "🛠️ MODERAR DADOS"]
else:
    abas_sistema = ["📊 MEU PAINEL", "📝 ENVIAR DADOS", "📋 REGISTROS"]

abas = st.tabs(abas_sistema)

# --- ABA 1: DASHBOARD ---
with abas[0]:
    if st.session_state.eh_admin and not df_filtrado.empty:
        usuarios_disponiveis = ["Todos os Produtores"] + list(df_filtrado["usuario"].unique())
        filtro_usuario = st.selectbox("Ver dados de:", usuarios_disponiveis)
        if filtro_usuario != "Todos os Produtores":
            df_filtrado = df_filtrado[df_filtrado["usuario"] == filtro_usuario]

    if not df_filtrado.empty:
        ult = df_filtrado.iloc[-1]
        
        # Grid de Cards Customizados
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>🌱 Acidez pH</div><div class='mobile-card-value'>{ult['pH']}</div></div><div style='font-size:1.8rem;'>🧪</div></div>""", unsafe_allow_html=True)
        with c_p2:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>💧 Umidade</div><div class='mobile-card-value'>{ult['Umidade']}%</div></div><div style='font-size:1.8rem;'>💧</div></div>""", unsafe_allow_html=True)
            
        c_p3, c_p4 = st.columns(2)
        with c_p3:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>📍 Setor Ativo</div><div class='mobile-card-value' style='font-size:0.95rem; padding-top:6px;'>{ult['Sensor']}</div></div></div>""", unsafe_allow_html=True)
        with c_p4:
            st.markdown(f"""<div class='mobile-card'><div style='text-align:left;'><div class='mobile-card-title'>📈 Envios</div><div class='mobile-card-value'>{len(df_filtrado)}</div></div><div style='font-size:1.8rem;'>📊</div></div>""", unsafe_allow_html=True)

        # Seção Visual
        col_visual_esq, col_visual_dir = st.columns([1.2, 1])
        
        with col_visual_esq:
            st.markdown("<h3>📈 Histórico Recente de Umidade</h3>", unsafe_allow_html=True)
            cor_grafico = "usuario" if st.session_state.eh_admin and filtro_usuario == "Todos os Produtores" else "Sensor"
            fig = px.line(df_filtrado.tail(10), x="Hora", y="Umidade", color=cor_grafico, markers=True, height=220)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                font_color="#8b949e", margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#21262d")
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with col_visual_dir:
            st.markdown("<h3>📍 Localização dos Sensores</h3>", unsafe_allow_html=True)
            st.map(df_filtrado, height=220)
            
        # IA Agrônomo com persistência no session_state
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🤖 GERAR DIAGNÓSTICO IA DA LAVOURA"):
            with st.spinner("Analisando solo..."):
                try:
                    prompt = f"Você é um agrônomo. Resuma de forma muito direta (máximo 3 tópicos curtos de celular) o estado desse solo: {df_filtrado.tail(3).to_string()}"
                    st.session_state.diagnostico_ia = model.generate_content(prompt).text
                except: 
                    st.session_state.diagnostico_ia = "Erro ao conectar com a IA do Google. Verifique sua chave de API."
        
        if st.session_state.diagnostico_ia:
            st.markdown("<div style='background-color:#161b22; padding:15px; border-radius:10px; border-left:4px solid #2ea043;'>", unsafe_allow_html=True)
            st.write(st.session_state.diagnostico_ia)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Nenhum dado cadastrado para exibição.")

# --- COMPORTAMENTO DO PRODUTOR ---
if not st.session_state.eh_admin:
    with abas[1]:
        st.markdown("<h2>📝 Nova Coleta de Solo</h2>", unsafe_allow_html=True)
        with st.form("form_mobile_clean", clear_on_submit=True):
            f_sensor = st.selectbox("Qual o Talhão / Área?", ["Talhão Norte", "Talhão Sul", "Setor Leste", "Estufa 01", "Estufa 02"])
            f_ph = st.number_input("Nível de pH medido (0.0 a 14.0)", min_value=0.0, max_value=14.0, value=6.5, step=0.1, format="%.1f")
            f_umidade = st.number_input("Porcentagem de Umidade (%)", min_value=0, max_value=100, value=50, step=1)
            
            st.markdown("<p style='color:#8b949e; margin-bottom:0;'>📍 Localização GPS</p>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            f_lat = c1.number_input("Lat", value=-23.5874, format="%.4f")
            f_lon = c2.number_input("Lon", value=-46.6576, format="%.4f")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            enviado = st.form_submit_button("🚀 ENVIAR LEITURA AGORA")
            
            if enviado:
                nova_leitura = {
                    "usuario": st.session_state.usuario_logado,
                    "Sensor": f_sensor, "pH": float(f_ph), "Umidade": int(f_umidade),
                    "latitude": float(f_lat), "longitude": float(f_lon),
                    "Hora": pd.Timestamp.now().strftime("%H:%M:%S")
                }
                historico_coll.insert_one(nova_leitura)
                st.success("Dados enviados com sucesso! Confira na aba de registros.")

    with abas[2]:
        st.markdown("<h2>📋 Seus Dados Enviados</h2>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            df_tab = df_filtrado.copy().drop(columns=['_id', 'usuario'], errors='ignore')
            st.dataframe(df_tab, use_container_width=True, hide_index=True)
        else: 
            st.warning("Sem dados cadastrados.")

# --- COMPORTAMENTO DO ADMIN ---
else:
    with abas[1]:
        st.markdown("<h2>🛠️ Painel Host de Moderação</h2>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            df_editor = df_filtrado.copy()
            df_editor['_id'] = df_editor['_id'].astype(str)
            
            dados_editados = st.data_editor(
                df_editor, use_container_width=True, hide_index=True,
                disabled=["usuario", "Hora", "_id"],
                column_config={"_id": None, "latitude": None, "longitude": None}
            )
            
            if st.button("💾 GRAVAR ALTERAÇÕES"):
                for index, row in dados_editados.iterrows():
                    historico_coll.update_one(
                        {"_id": ObjectId(row['_id'])},
                        {"$set": {"Sensor": row['Sensor'], "pH": float(row['pH']), "Umidade": int(row['Umidade'])}}
                    )
                st.success("Banco Atualizado com Sucesso!")
                st.rerun()
                
            st.markdown("---")
            st.markdown("<h3>🗑️ Apagar Registro</h3>", unsafe_allow_html=True)
            opcoes_delecao = [f"[{i}] {row['usuario']} | {row['Sensor']}" for i, row in df_filtrado.iterrows()]
            escolha_registro = st.selectbox("Selecione a linha:", opcoes_delecao)
            
            if st.button("🗑️ REMOVER PERMANENTEMENTE"):
                idx_original = int(escolha_registro.split(']')[0].replace('[', ''))
                id_para_deletar = df_filtrado.iloc[idx_original]['_id']
                historico_coll.delete_one({"_id": ObjectId(id_para_deletar)})
                st.success("Registro removido!")
                st.rerun()
