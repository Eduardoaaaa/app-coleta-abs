import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Coleta ABS - Login", page_icon="🔐", layout="centered")

@st.cache_resource
def conectar_banco():
    return create_engine(st.secrets["DATABASE_URL"])

# --- FUNÇÃO DE AUTENTICAÇÃO ---
def autenticar(usuario, senha):
    try:
        engine = conectar_banco()
        query = text("SELECT nome_completo, perfil FROM usuarios_abs WHERE login = :u AND senha = :s")
        with engine.connect() as conn:
            result = conn.execute(query, {"u": usuario.lower(), "s": senha}).fetchone()
            return result
    except:
        return None

# --- TELA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.title("🔐 Acesso Lojas ABS")
    with st.form("login_form"):
        user_input = st.text_input("Usuário (Login)")
        pass_input = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar", use_container_width=True)
        
        if btn_login:
            user_data = autenticar(user_input, pass_input)
            if user_data:
                st.session_state["autenticado"] = True
                st.session_state["usuario_nome"] = user_data[0]
                st.session_state["usuario_perfil"] = user_data[1]
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# --- INTERFACE APÓS LOGIN ---
st.sidebar.markdown(f"👤 **Usuário:** {st.session_state['usuario_nome']}")
st.sidebar.markdown(f"🏷️ **Perfil:** {st.session_state['usuario_perfil'].capitalize()}")
if st.sidebar.button("Sair"):
    del st.session_state["autenticado"]
    st.rerun()

st.title("📱 Coleta de Estoque")

if st.session_state["usuario_perfil"] == "gerente":
    st.info("🔓 Modo Gerencial: Todas as opções de conferência e logs estão liberadas.")

# --- FORMULÁRIO DE CONTAGEM ---
loja_atual = st.selectbox("🏬 Loja atual:", ["ZE - ABS CLUBE", "ZE - ABS CLUBE - B", "ZE - ABS CLUBE - N", "ZE - ABS CLUBE - V"])

# >>> AQUI OCORREU A MUDANÇA (Busca da nova tabela oficial) <<<
@st.cache_data(ttl=60)
def buscar_produtos():
    try:
        engine = conectar_banco()
        with engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT nome_produto FROM produtos_cadastrados ORDER BY nome_produto"), conn)
            return df['nome_produto'].tolist()
    except:
        return []

lista_prods = buscar_produtos()

with st.form("coleta_form", clear_on_submit=True):
    produto = st.selectbox("🔍 Produto:", [""] + lista_prods)
    quantidade = st.number_input("📦 Quantidade:", min_value=1, step=1)
    
    if st.form_submit_button("Registrar Contagem", use_container_width=True):
        if produto:
            try:
                engine = conectar_banco()
                dados = pd.DataFrame([{
                    'data_entrega': datetime.now().strftime('%Y-%m-%d'),
                    'cod_loja': '-',
                    'nome_loja': loja_atual,
                    'cod_produto': 'COLETA_MOBILE',
                    'nome_produto': produto,
                    'quantidade': float(quantidade),
                    'usuario': st.session_state["usuario_nome"] 
                }])
                with engine.connect() as conn:
                    dados.to_sql('movimentacoes_entrada', con=conn, if_exists='append', index=False)
                st.success(f"✅ {produto} registrado por {st.session_state['usuario_nome']}")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
        else:
            st.warning("Selecione um produto.")
